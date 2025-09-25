import os
import argparse
import subprocess
import time
import json
from pydantic import BaseModel
from google import genai
from google.genai import types
from tools.common.logger import get_logger
from tools.recorder.main_recorder import Recorder

logger = get_logger(__name__)

# --- Constants ---
MAX_COMPILATION_ATTEMPTS = 3
MAX_EXECUTION_ATTEMPTS = 3
RUN_OUTPUT_DIR = "generated_scripts/{timestamp}"
COMPILATION_ITERATION_DIR = "{run_output_dir}/compilation/iteration{i}"
EXECUTION_ITERATION_DIR = "{run_output_dir}/execution/iteration{i}"
MODEL = "gemini-2.5-flash"
FLAUI_PROJECT_DIR = "fla-ui/GeneratedTests"
FLAUI_PROJECT_PATH = f"{FLAUI_PROJECT_DIR}/FlaUI.Generated.csproj"
FLAUI_SOURCE_PATH = f"{FLAUI_PROJECT_DIR}/GeneratedTests.cs"

# --- Configuration ---
# --- Configuration ---
try:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    logger.error(f"Error creating client: {e}")
    logger.error("Please make sure you have set up your API key or ADC correctly.")
    exit()


# -- Structured Output --
class CodeResponse(BaseModel):
    code: str
    failure_reason: str = None
    comments: str = None

# --- Prompts ---
try:
    cur_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(cur_path, '..', FLAUI_PROJECT_DIR, '..', 'prompt.md'), 'r', encoding='utf-8') as f:
        system_prompt = f.read()
except FileNotFoundError:
    logger.error(f"Error: `{FLAUI_PROJECT_DIR}/prompt.md` not found.")
    exit()

# --- Helper Functions ---
def send_message_with_retries(chat, prompt_parts, config, max_retries=3, retry_delay=2):
    """
    Sends a message using chat.send_message, retries up to max_retries if a 503 error is returned.
    Returns the response or raises the last exception.
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = chat.send_message(prompt_parts, config=config)
            return response
        except Exception as e:
            # Check for 503 error in exception message
            if hasattr(e, 'status_code') and e.status_code == 503:
                logger.warning(f"503 Service Unavailable. Retry {attempt}/{max_retries}...")
                time.sleep(retry_delay)
            elif '503' in str(e):
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
    """
    Writes content to a file.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding='utf-8') as f:
        f.write(content)
    return f"File '{file_path}' written successfully."

def upload_file(client, file_path):
    """
    Uploads a file using the Gemini client, handles .json renaming, and waits for processing.
    Returns the uploaded file object or None if failed.
    """
    # If ends with .json, rename to .json.txt
    if file_path.endswith('.json'):
        new_path = file_path + '.txt'
        os.rename(file_path, new_path)
        file_path = new_path
    try:
        uploaded_file = client.files.upload(file=file_path)
        # Wait for the file to be processed.
        while uploaded_file.state.name == "PROCESSING":
            logger.info("\tWaiting for file to be processed...")
            time.sleep(2)
            uploaded_file = client.files.get(name=uploaded_file.name)
        if uploaded_file.state.name == "FAILED":
            logger.error(f"Error: File upload failed for {file_path}. Uploading the next file.")
            return None
        return uploaded_file
    except Exception as e:
        logger.error(f"\nError uploading file {file_path}: {e}")
        return None

# Upload all files in a directory matching certain extensions
def upload_dir_files(client, dir_path, extensions=(".json", ".mp4", ".png", ".txt")):
    """
    Uploads all files in a directory (recursively) matching the given extensions.
    Returns a list of uploaded file objects.
    """
    uploaded_files = []
    files_to_upload = []
    for dirpath, _, filenames in os.walk(dir_path):
        for filename in filenames:
            if filename.endswith(extensions):
                files_to_upload.append(os.path.join(dirpath, filename))
    for file_path in files_to_upload:
        logger.info(f"Uploading {os.path.basename(file_path)}...")
        uploaded_file = upload_file(client, file_path)
        if uploaded_file:
            uploaded_files.append(uploaded_file)
    return uploaded_files
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

    chat = client.chats.create(model=MODEL)

    logger.info(f"Analyzing data in: {args.recording_dir}")
    initial_files = upload_dir_files(client, args.recording_dir)
    prompt_parts = []
    logger.info("Generating initial script... (This may take a moment)")
    prompt_parts.extend(initial_files)
    prompt_parts.append("Generate the initial C# script to perform the recorded scenario using FlaUI and MSTest.")

    # --- Compilation Loop ---
    compilation_success = False
    code_response = None
    for i in range(MAX_COMPILATION_ATTEMPTS):
        logger.info(f"--- Compilation Attempt {i+1}/{MAX_COMPILATION_ATTEMPTS} ---")
        iteration_dir = COMPILATION_ITERATION_DIR.format(run_output_dir=run_output_dir, i=i)

        # --- Generate Script ---
        if i == 0:
            response = send_message_with_retries(
                chat,
                prompt_parts,
                types.GenerateContentConfig(
                    response_schema=CodeResponse,
                    response_mime_type="application/json",
                    system_instruction=system_prompt
                )
            )
            code_response: CodeResponse = response.parsed
        else:
            prompt_parts = ["The previously generated script failed to compile.\nAttached are the compilation logs for analysis and script refinement."]
            prompt_parts.extend(upload_dir_files(client, iteration_dir))
            response = send_message_with_retries(
                chat,
                prompt_parts,
                types.GenerateContentConfig(
                    response_schema=CodeResponse,
                    response_mime_type="application/json",
                    system_instruction=system_prompt
                )
            )
            code_response: CodeResponse = response.parsed

        # --- Write Script to File ---
        write_file(f"{FLAUI_SOURCE_PATH}", code_response.code)
        logger.info(f"Script written to {FLAUI_SOURCE_PATH}")
        write_file(iteration_dir + "/script.cs", code_response.code)

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

    if not compilation_success:
        logger.error("--- Max Compilation Retries Reached! Could not compile the script. ---")
        return

    # --- Execution Loop ---
    execution_success = False
    for i in range(MAX_EXECUTION_ATTEMPTS):
        logger.info(f"--- Execution Attempt {i+1}/{MAX_EXECUTION_ATTEMPTS} ---")
        iteration_dir = EXECUTION_ITERATION_DIR.format(run_output_dir=run_output_dir, i=i + MAX_COMPILATION_ATTEMPTS)

        # --- Run Script ---
        logger.info(f"Running test: {FLAUI_PROJECT_PATH}")
        generated_recording_dir = iteration_dir + "/recordings"
        recorder = Recorder(output_folder=generated_recording_dir, take_screenshots=False)
        recorder.start()
        execution_result = run_command(["dotnet", "test", FLAUI_PROJECT_PATH])
        recorder.stop()

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
        prompt_parts.extend(upload_dir_files(client, iteration_dir))

        # --- Generate Script ---
        response = send_message_with_retries(
            chat,
            prompt_parts,
            types.GenerateContentConfig(
                response_schema=CodeResponse,
                response_mime_type="application/json",
                system_instruction=system_prompt
            )
        )
        code_response = response.parsed
        # --- Write Script to File ---
        write_file(f"{FLAUI_SOURCE_PATH}", code_response.code)
        logger.info(f"Script written to {FLAUI_SOURCE_PATH}")
        write_file(iteration_dir + "/script.cs", code_response.code)

    if not execution_success:
        logger.error("--- Max Execution Retries Reached! Could not fix the script. ---")

if __name__ == "__main__":
    main()