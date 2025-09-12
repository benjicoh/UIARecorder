
import os
import argparse
import subprocess
import time
import json
from pydantic import BaseModel
from google import genai
from google.genai import types

# --- Constants ---
MAX_REFINEMENT_ATTEMPTS = 3
GENERATED_SCRIPT_PATH = "user_scripts/generated_script.py"
GENERATED_SCRIPT_LOG_PATH = "user_scripts/generated_script.log.txt"
UI_DUMP_PATH = "user_scripts/ui_dump.json.txt"

# --- Configuration ---
try:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    print(f"Error creating client: {e}")
    print("Please make sure you have set up your API key or ADC correctly.")
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
    print("Error: `agent/prompt.md` not found.")
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
                print(f"503 Service Unavailable. Retry {attempt}/{max_retries}...")
                time.sleep(retry_delay)
            elif '503' in str(e):
                print(f"503 Service Unavailable. Retry {attempt}/{max_retries}...")
                time.sleep(retry_delay)
            else:
                raise
    raise Exception(f"Failed after {max_retries} retries due to repeated 503 errors.")

def run_python_script(script_path: str):
    """
    Runs a python script.
    Returns a dictionary with 'stdout' on success or 'stderr' on failure.
    """
    if not os.path.exists(script_path):
        return {'stderr': f"Error: Script not found at {script_path}"}
    # Try to use venv python if available
    venv_python = os.path.join(os.path.dirname(__file__), "..", ".venv", "Scripts", "python.exe")
    python_executable = venv_python if os.path.exists(venv_python) else "python"
    try:
        result = subprocess.run(
            [python_executable, script_path],
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        return {'stdout': result.stdout}
    except subprocess.CalledProcessError as e:
        # Combine stdout and stderr for more context on failure
        error_output = f"STDOUT:\n{e.stdout}\n\nSTDERR:\n{e.stderr}"
        return {'stderr': error_output}

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
            print(".", end="", flush=True)
            time.sleep(2)
            uploaded_file = client.files.get(name=uploaded_file.name)
        print() # Newline after processing dots
        if uploaded_file.state.name == "FAILED":
            print(f"Error: File upload failed for {file_path}. Uploading the next file.")
            return None
        return uploaded_file
    except Exception as e:
        print(f"\nError uploading file {file_path}: {e}")
        return None

# --- Main Flow ---

def main():
    """Main function to run the Gemini agent with iterative refinement."""
    parser = argparse.ArgumentParser(description="Gemini UI Automation Agent")
    parser.add_argument("recording_dir", help="Path to the recording directory.")
    parser.add_argument("-p", "--process-name", help="The process name of the target application.")
    parser.add_argument("-w", "--window-title", help="The window title of the target application.")
    args = parser.parse_args()

    chat = client.chats.create(model='gemini-2.5-flash')

    # --- Initial Prompt Construction ---
    initial_prompt_parts = []
    print(f"Analyzing data in: {args.recording_dir}")


    # Simplified file upload logic
    files_to_upload = []
    for dirpath, _, filenames in os.walk(args.recording_dir):
        for filename in filenames:
            if filename.endswith((".json", ".mp4", ".png", ".txt")):
                files_to_upload.append(os.path.join(dirpath, filename))

    for file_path in files_to_upload:
        print(f"Uploading {os.path.basename(file_path)}...")
        uploaded_file = upload_file(client, file_path)
        if uploaded_file:
            initial_prompt_parts.append(uploaded_file)

    initial_prompt_parts.append(f"\n\nPlease generate the python script now.")

    # --- Initial Generation ---
    print("\nGenerating initial script... (This may take a moment)")
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
    write_file(GENERATED_SCRIPT_PATH, code_response.code)
    print(f"Initial script written to {GENERATED_SCRIPT_PATH}")

    # --- Iterative Refinement Loop ---
    for i in range(MAX_REFINEMENT_ATTEMPTS):
        print(f"\n--- Attempt {i + 1}/{MAX_REFINEMENT_ATTEMPTS}: Running Script ---")

        run_result = run_python_script(GENERATED_SCRIPT_PATH)
        write_file(GENERATED_SCRIPT_LOG_PATH, str(run_result))
        if 'stdout' in run_result and 'stderr' not in run_result:
            print("\n--- Script Executed Successfully! ---")
            print(run_result['stdout'])
            return # Success!

        print("\n--- Script Failed! Initiating Refinement ---")
        error_logs = run_result.get('stderr', 'No stderr output.')
        print(f"Error Details:\n{error_logs}")

        # Dump the UI for context
        print("Dumping current UI state...")
        command = ["python", "agent/uia_dumper.py", "-o", UI_DUMP_PATH]
        if args.process_name:
            command.extend(["-p", args.process_name])
        elif args.window_title:
            command.extend(["-w", args.window_title])

        if len(command) > 4:
            try:
                dump_result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
                print(dump_result.stdout)
            except subprocess.CalledProcessError as e:
                print(f"Error dumping UI: {e.stderr}")
        else:
            print("Process name or window title not provided. Skipping UI dump.")

        refinement_prompt_parts = [
            "The previously generated script failed to execute correctly."
        ]
        for file in [UI_DUMP_PATH, GENERATED_SCRIPT_LOG_PATH]:
            if os.path.exists(file):
                print(f"Uploading file: {file}")
                uploaded_file = upload_file(client, file)
                if uploaded_file:
                    refinement_prompt_parts.append(uploaded_file)

        print("\nRequesting script correction from model...")
        response = send_message_with_retries(
            chat,
            refinement_prompt_parts,
            types.GenerateContentConfig(
                response_schema=CodeResponse,
                system_instruction=system_prompt
            )
        )
        write_file(GENERATED_SCRIPT_PATH, response.candidates[0].content.parts[0].function_call.args['code'])
        print(f"Corrected script written to {GENERATED_SCRIPT_PATH}")

    print(f"\n--- Max Retries Reached! ---")
    print("Could not fix the script after multiple attempts.")

if __name__ == "__main__":
    main()
    #run_result = run_python_script(GENERATED_SCRIPT_PATH)
