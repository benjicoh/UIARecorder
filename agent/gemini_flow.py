
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
RUN_OUTPUT_DIR = "run_output/{timestamp}"
GENERATED_SCRIPT_PATH = "{run_output_dir}/iteration{i}.py"
GENERATED_SCRIPT_LOG_PATH = "{run_output_dir}/iteration{i}.log.txt"
UI_DUMP_PATH = "{run_output_dir}/ui_dump{i}.json.txt"
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
    initial_prompt_parts = []
    logger.info(f"Analyzing data in: {args.recording_dir}")


    # Simplified file upload logic
    files_to_upload = []
    for dirpath, _, filenames in os.walk(args.recording_dir):
        for filename in filenames:
            if filename.endswith((".json", ".mp4", ".png", ".txt")):
                files_to_upload.append(os.path.join(dirpath, filename))

    for file_path in files_to_upload:
        logger.info(f"Uploading {os.path.basename(file_path)}...")
        uploaded_file = upload_file(client, file_path)
        if uploaded_file:
            initial_prompt_parts.append(uploaded_file)

    initial_prompt_parts.append(f"\n\nPlease generate the python script now.")

    # --- Initial Generation ---
    logger.info("Generating initial script... (This may take a moment)")
    response = send_message_with_retries(
        chat,
        initial_prompt_parts,
        types.GenerateContentConfig(
            response_schema=CodeResponse,
            response_mime_type="application/json",
            system_instruction=system_prompt
        )
    )
    code_response : CodeResponse = response.parsed
    script_path = GENERATED_SCRIPT_PATH.format(run_output_dir=run_output_dir, i=0)
    write_file(script_path, code_response.code)
    logger.info(f"Initial script written to {script_path}")

    # --- Iterative Refinement Loop ---
    for i in range(1, MAX_REFINEMENT_ATTEMPTS + 1):
        script_path_prev = GENERATED_SCRIPT_PATH.format(run_output_dir=run_output_dir, i=i-1)
        script_path_curr = GENERATED_SCRIPT_PATH.format(run_output_dir=run_output_dir, i=i)
        log_path = GENERATED_SCRIPT_LOG_PATH.format(run_output_dir=run_output_dir, i=i)
        ui_dump_path = UI_DUMP_PATH.format(run_output_dir=run_output_dir, i=i)
        logger.info(f"--- Attempt {i}/{MAX_REFINEMENT_ATTEMPTS}: Running Script ---")

        recorder = Recorder(output_folder=run_output_dir, take_screenshots=False)
        recorder.start()
        run_result = run_python_script(script_path_prev)
        recorder.stop()

        # Combine stdout and stderr for logging
        log_output = f"STDOUT:\n{run_result['stdout']}\n\nSTDERR:\n{run_result['stderr']}"
        write_file(log_path, log_output)

        # Check for success marker in stdout
        if "Scenario completed successfully" in run_result['stdout']:
            logger.info("--- Script Executed Successfully! ---")
            logger.info(log_output)
            return  # Success!

        logger.warning("--- Script Failed! Initiating Refinement ---")
        logger.warning(f"For details see log: {log_path}")

        # Dump the UI for context
        logger.info("Dumping current UI state...")
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

        refinement_prompt_parts = [
            "The previously generated script failed to execute correctly."
        ]
        # Upload run output files
        for file in [ui_dump_path, log_path, os.path.join(run_output_dir, "video.mp4")]:
            if os.path.exists(file):
                logger.info(f"Uploading file: {file}")
                uploaded_file = upload_file(client, file)
                if uploaded_file:
                    refinement_prompt_parts.append(uploaded_file)

        logger.info("Requesting script correction from model...")
        response = send_message_with_retries(
            chat,
            refinement_prompt_parts,
            types.GenerateContentConfig(
                response_schema=CodeResponse,
                response_mime_type="application/json",
                system_instruction=system_prompt
            )
        )
        code_response : CodeResponse = response.parsed
        write_file(script_path_curr, code_response.code)
        logger.info(f"Corrected script written to {script_path_curr}")

    logger.warning(f"--- Max Retries Reached! ---")
    logger.warning("Could not fix the script after multiple attempts.")

if __name__ == "__main__":
    main()
    