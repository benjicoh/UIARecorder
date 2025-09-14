
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
MAX_REFINEMENT_ATTEMPTS = 3
RUN_OUTPUT_DIR = "generated_scripts/{timestamp}"
ITERATION_OUTPUT_DIR = "{run_output_dir}/iteration{i}"
MODEL = "gemini-2.5-flash"

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
    with open(os.path.join(cur_path, 'prompt.md'), 'r', encoding='utf-8') as f:
        system_prompt = f.read()
except FileNotFoundError:
    logger.error("Error: `agent/prompt.md` not found.")
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

def run_python_script(script_path: str):
    """
    Runs a python script and captures its output.
    Returns a dictionary containing 'stdout' and 'stderr'.
    """
    if not os.path.exists(script_path):
        return {'stdout': '', 'stderr': f"Error: Script not found at {script_path}"}

    # Try to use venv python if available
    venv_python = os.path.join(os.path.dirname(__file__), "..", ".venv", "Scripts", "python.exe")
    python_executable = venv_python if os.path.exists(venv_python) else "python"

    try:
        result = subprocess.run(
            [python_executable, script_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=120  # Add a timeout for safety
        )
        return {'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.TimeoutExpired as e:
        error_output = f"TimeoutExpired: Script execution timed out after 120 seconds.\n"
        error_output += f"STDOUT:\n{e.stdout}\n\nSTDERR:\n{e.stderr}"
        return {'stdout': e.stdout or "", 'stderr': error_output}
    except Exception as e:
        return {'stdout': '', 'stderr': f"An unexpected error occurred: {e}"}

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
    """Main function to run the Gemini agent with iterative refinement."""
    parser = argparse.ArgumentParser(description="Gemini UI Automation Agent")
    parser.add_argument("recording_dir", help="Path to the recording directory.")
    parser.add_argument("-p", "--process-name", help="The process name of the target application.")
    parser.add_argument("-w", "--window-title", help="The window title of the target application.")
    args = parser.parse_args()

    run_output_dir = RUN_OUTPUT_DIR.format(timestamp=time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(run_output_dir, exist_ok=True)
    logger.info(f"Run output directory: {run_output_dir}")

    chat = client.chats.create(model=MODEL)

    # --- Initial Prompt Construction ---
    logger.info(f"Analyzing data in: {args.recording_dir}")
    initial_files = upload_dir_files(client, args.recording_dir)
    prompt_parts = []
    logger.info("Generating initial script... (This may take a moment)")
    prompt_parts.extend(initial_files)
    prompt_parts.append("Generate the initial script to perform the recorded scenario.")
    # --- Iterative Refinement Loop ---
    last_run_result = None
    for i in range(MAX_REFINEMENT_ATTEMPTS):
        logger.info(f"--- Attempt {i+1}/{MAX_REFINEMENT_ATTEMPTS} ---")
        iteration_dir = ITERATION_OUTPUT_DIR.format(run_output_dir=run_output_dir, i=i)
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
        code_response: CodeResponse = response.parsed
        # --- Write Script to File ---
        script_path = iteration_dir + "/run.py"
        write_file(script_path, code_response.code)
        logger.info(f"Script written to {script_path}")
        # --- Model Feedback ---
        if code_response.failure_reason:
            logger.info(f"LLM Failure Reason: {code_response.failure_reason}")
        if code_response.comments:
            logger.info(f"LLM Comments: {code_response.comments}")
        # --- Run Script ---
        logger.info(f"Running script: {script_path}")
        generated_recording_dir = iteration_dir + "/recordings"
        recorder = Recorder(output_folder=generated_recording_dir, take_screenshots=False)
        recorder.start()
        last_run_result = run_python_script(script_path)
        recorder.stop()
        # --- Log Results ---
        log_path = iteration_dir + "/log.txt"
        log_output = f"STDOUT:\n{last_run_result['stdout']}\n\nSTDERR:\n{last_run_result['stderr']}"
        write_file(log_path, log_output)
        logger.info(f"Log file written to {log_path}")
         # --- Check for Success ---
        if "Scenario completed successfully" in last_run_result['stdout']:
            logger.info("--- Script Executed Successfully! ---")
            logger.info(log_output)
            return  # Success!
        # --- Prepare for Next Iteration ---
        # if this is the last iteration no need to prepare for next
        if i == MAX_REFINEMENT_ATTEMPTS - 1:
            break
        logger.warning("--- Script Failed! ---")
        logger.info("Collecting and sending data for refinement...")
        prompt_parts = []
        prompt_parts.append("The previously generated script failed to execute correctly.\nAttached are the logs and recordings of the failed run for analysis, and script refinement.")
        # --- 6. Dump UI for next attempt (if not the last attempt) ---
        logger.info("Dumping current UI state for context...")
        ui_dump_path = iteration_dir + "/ui_dump.json.txt"
        try:
            from agent.uia_dumper import dump_ui
            if args.process_name or args.window_title:
                result = dump_ui(
                    process_name=args.process_name,
                    window_title=args.window_title,
                    output_file=ui_dump_path,
                    whitelist=None,
                    screenshots=False
                )
                logger.info(result)
            else:
                logger.warning("Process name or window title not provided. Skipping UI dump.")
        except Exception as e:
            logger.error(f"Error dumping UI: {e}")
        # Upload all files from the iteration for context
        prompt_parts.extend(upload_dir_files(client, iteration_dir))
         

    # --- Final Status Check ---
    logger.warning(f"--- Max Retries Reached! ---")
    if last_run_result and "Scenario completed successfully" not in last_run_result['stdout']:
        logger.warning("Could not fix the script after multiple attempts.")
        logger.warning(f"Final log output:\n{log_output}")


if __name__ == "__main__":
    main()
    