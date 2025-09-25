import os
import sys
sys.path.append(os.getcwd())
import argparse
import subprocess
import time
import json
from pydantic import BaseModel
import google.generativeai as genai
from google.generativeai import types
from tools.common.logger import get_logger


logger = get_logger(__name__)

# --- Constants ---
MAX_COMPILATION_ATTEMPTS = 3
MAX_EXECUTION_ATTEMPTS = 3
RUN_OUTPUT_DIR = "generated_scripts/{timestamp}"
ITERATION_OUTPUT_DIR = "{run_output_dir}/iteration{i}"
MODEL = "gemini-1.5-flash-latest"
FLAUI_PROJECT_DIR = "fla-ui"
FLAUI_PROJECT_PATH = f"{FLAUI_PROJECT_DIR}/FlaUI.Generated.csproj"
FLAUI_SOURCE_PATH = f"{FLAUI_PROJECT_DIR}/GeneratedTests.cs"

# --- Configuration ---
try:
    if not os.getenv("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    logger.error(f"Error configuring Gemini: {e}")
    logger.error("Please make sure you have set up your API key.")
    exit()

# -- Structured Output --
class CodeResponse(BaseModel):
    code: str
    failure_reason: str = None
    comments: str = None

# --- Prompts ---
try:
    cur_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(cur_path, '..', FLAUI_PROJECT_DIR, 'prompt.md'), 'r', encoding='utf-8') as f:
        system_prompt = f.read()
except FileNotFoundError:
    logger.error(f"Error: `{FLAUI_PROJECT_DIR}/prompt.md` not found.")
    exit()

# --- Helper Functions ---
def send_message_with_retries(chat, prompt_parts, generation_config, max_retries=3, retry_delay=2):
    """
    Sends a message using chat.send_message, retries up to max_retries if a 503 error is returned.
    Returns the response or raises the last exception.
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = chat.send_message(prompt_parts, generation_config=generation_config)
            return response
        except Exception as e:
            if '503' in str(e):
                logger.warning(f"503 Service Unavailable. Retry {attempt}/{max_retries}...")
                time.sleep(retry_delay)
            else:
                raise
    raise Exception(f"Failed after {max_retries} retries due to repeated 503 errors.")

def run_command(command: list[str]):
    """
    Runs a command and captures its output.
    Returns a dictionary containing 'stdout' and 'stderr'.
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=300
        )
        return {'stdout': result.stdout, 'stderr': result.stderr, 'returncode': result.returncode}
    except subprocess.TimeoutExpired as e:
        error_output = f"TimeoutExpired: Command execution timed out after 300 seconds.\n"
        error_output += f"STDOUT:\n{e.stdout}\n\nSTDERR:\n{e.stderr}"
        return {'stdout': e.stdout or "", 'stderr': error_output, 'returncode': -1}
    except Exception as e:
        return {'stdout': '', 'stderr': f"An unexpected error occurred: {e}", 'returncode': -1}

def write_file(file_path: str, content: str):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding='utf-8') as f:
        f.write(content)
    return f"File '{file_path}' written successfully."

def upload_file(file_path):
    if file_path.endswith('.json'):
        new_path = file_path + '.txt'
        os.rename(file_path, new_path)
        file_path = new_path
    try:
        logger.info(f"Uploading {os.path.basename(file_path)}...")
        uploaded_file = genai.upload_file(path=file_path)
        while uploaded_file.state.name == "PROCESSING":
            logger.info("\tWaiting for file to be processed...")
            time.sleep(2)
            uploaded_file = genai.get_file(name=uploaded_file.name)
        if uploaded_file.state.name == "FAILED":
            logger.error(f"Error: File upload failed for {file_path}.")
            return None
        return uploaded_file
    except Exception as e:
        logger.error(f"\nError uploading file {file_path}: {e}")
        return None

def upload_dir_files(dir_path, extensions=(".json", ".mp4", ".png", ".txt")):
    uploaded_files = []
    files_to_upload = []
    for dirpath, _, filenames in os.walk(dir_path):
        for filename in filenames:
            if filename.endswith(extensions):
                files_to_upload.append(os.path.join(dirpath, filename))
    for file_path in files_to_upload:
        uploaded_file = upload_file(file_path)
        if uploaded_file:
            uploaded_files.append(uploaded_file)
    return uploaded_files

def insert_code_into_template(code: str):
    with open(FLAUI_SOURCE_PATH, 'r', encoding='utf-8') as f:
        template = f.read()
    final_code = template.replace("// Test code will be generated here", code)
    with open(FLAUI_SOURCE_PATH, 'w', encoding='utf-8') as f:
        f.write(final_code)

# --- Main Flow ---
def main():
    parser = argparse.ArgumentParser(description="Gemini UI Automation Agent for FlaUI")
    parser.add_argument("recording_dir", help="Path to the recording directory.")
    parser.add_argument("-p", "--process-name", help="The process name of the target application.")
    parser.add_argument("-w", "--window-title", help="The window title of the target application.")
    args = parser.parse_args()

    run_output_dir = RUN_OUTPUT_DIR.format(timestamp=time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(run_output_dir, exist_ok=True)
    logger.info(f"Run output directory: {run_output_dir}")

    model = genai.GenerativeModel(MODEL, system_instruction=system_prompt)
    chat = model.start_chat()

    logger.info(f"Analyzing data in: {args.recording_dir}")
    initial_files = upload_dir_files(args.recording_dir)
    prompt_parts = []
    logger.info("Generating initial script... (This may take a moment)")
    prompt_parts.extend(initial_files)
    prompt_parts.append("Generate the initial C# script to perform the recorded scenario using FlaUI and MSTest.")

    # --- Compilation Loop ---
    compilation_success = False
    for i in range(MAX_COMPILATION_ATTEMPTS):
        logger.info(f"--- Compilation Attempt {i+1}/{MAX_COMPILATION_ATTEMPTS} ---")
        iteration_dir = ITERATION_OUTPUT_DIR.format(run_output_dir=run_output_dir, i=i)

        # --- Generate Script ---
        response = send_message_with_retries(
            chat,
            prompt_parts,
            generation_config=types.GenerationConfig(
                response_mime_type="application/json"
            )
        )

        try:
            # The model sometimes returns the JSON wrapped in markdown, so we need to clean it up
            cleaned_json = response.text.strip().replace('```json', '').replace('```', '').strip()
            code_response = CodeResponse(**json.loads(cleaned_json))
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {response.text}")
            # Prepare for next iteration
            if i == MAX_COMPILATION_ATTEMPTS - 1: break
            prompt_parts = ["The previous response was not valid JSON. Please provide the response in the correct JSON format.", response.text]
            continue

        # --- Write Script to File ---
        insert_code_into_template(code_response.code)
        logger.info(f"Script written to {FLAUI_SOURCE_PATH}")

        # --- Compile Script ---
        logger.info(f"Compiling script: {FLAUI_PROJECT_PATH}")
        compilation_result = run_command(["dotnet", "build", FLAUI_PROJECT_PATH])

        log_path = iteration_dir + "/compilation_log.txt"
        log_output = f"STDOUT:\n{compilation_result['stdout']}\n\nSTDERR:\n{compilation_result['stderr']}"
        write_file(log_path, log_output)
        logger.info(f"Compilation log file written to {log_path}")

        if compilation_result['returncode'] == 0:
            logger.info("--- Compilation Successful! ---")
            compilation_success = True
            break

        logger.warning("--- Compilation Failed! ---")
        if i == MAX_COMPILATION_ATTEMPTS - 1: break

        logger.info("Collecting and sending data for refinement...")
        prompt_parts = ["The previously generated script failed to compile.\nAttached are the compilation logs for analysis and script refinement."]
        prompt_parts.extend(upload_dir_files(iteration_dir))

    if not compilation_success:
        logger.error("--- Max Compilation Retries Reached! Could not compile the script. ---")
        return

    # --- Execution Loop ---
    execution_success = False
    for i in range(MAX_EXECUTION_ATTEMPTS):
        logger.info(f"--- Execution Attempt {i+1}/{MAX_EXECUTION_ATTEMPTS} ---")
        iteration_dir = ITERATION_OUTPUT_DIR.format(run_output_dir=run_output_dir, i=i + MAX_COMPILATION_ATTEMPTS)

        # --- Run Script ---
        logger.info(f"Running test: {FLAUI_PROJECT_PATH}")
        execution_result = run_command(["dotnet", "test", FLAUI_PROJECT_PATH])

        # --- Log Execution Results ---
        log_path = iteration_dir + "/execution_log.txt"
        log_output = f"STDOUT:\n{execution_result['stdout']}\n\nSTDERR:\n{execution_result['stderr']}"
        write_file(log_path, log_output)
        logger.info(f"Execution log file written to {log_path}")

        if "Test Run Successful." in execution_result['stdout'] or "Passed!" in execution_result['stdout']:
            logger.info("--- Test Executed Successfully! ---")
            execution_success = True
            break

        logger.warning("--- Test Execution Failed! ---")
        if i == MAX_EXECUTION_ATTEMPTS - 1: break

        logger.info("Collecting and sending data for refinement...")
        prompt_parts = ["The previously generated script failed to execute correctly.\nAttached are the logs of the failed run for analysis, and script refinement."]
        prompt_parts.extend(upload_dir_files(iteration_dir, extensions=(".txt")))

    if not execution_success:
        logger.error("--- Max Execution Retries Reached! Could not fix the script. ---")

if __name__ == "__main__":
    main()