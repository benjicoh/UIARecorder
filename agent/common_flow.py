import os
import subprocess
import threading
import time
import shutil
from google import genai
from tools.common.logger import get_logger

logger = get_logger(__name__)

def initialize_gemini_client():
    """Initializes and returns the Gemini client."""
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        return client
    except Exception as e:
        logger.error(f"Error creating Gemini client: {e}")
        logger.error("Please make sure you have set up your API key or ADC correctly.")
        exit()

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

def run_command(command: list[str], cwd: str = None, timeout: int = 300) -> dict:
    """
    Runs a command and captures its output.
    Returns a dictionary containing 'stdout', 'stderr', and 'returncode'.
    """
    logger.info(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=timeout
        )
        return {'stdout': result.stdout, 'stderr': result.stderr, 'returncode': result.returncode}
    except subprocess.TimeoutExpired as e:
        error_output = f"TimeoutExpired: Command execution timed out after {timeout} seconds.\n"
        error_output += f"STDOUT:\n{e.stdout}\n\nSTDERR:\n{e.stderr}"
        return {'stdout': e.stdout or "", 'stderr': error_output, 'returncode': -1}
    except Exception as e:
        return {'stdout': '', 'stderr': f"An unexpected error occurred: {e}", 'returncode': -1}


def run_python_script(script_path: str, timeout: int = 120):
    """
    Runs a python script and captures its output.
    Returns a dictionary containing 'stdout' and 'stderr'.
    """
    if not os.path.exists(script_path):
        return {'stdout': '', 'stderr': f"Error: Script not found at {script_path}", 'returncode': -1}

    # Try to use venv python if available
    venv_python = os.path.join(os.path.dirname(__file__), "..", ".venv", "Scripts", "python.exe")
    python_executable = venv_python if os.path.exists(venv_python) else "python"

    result = run_command([python_executable, script_path], timeout=timeout)
    # Adapt output to old format for compatibility, run_command already includes stdout/stderr
    return result


def write_file(file_path: str, content: str, with_line_numbers: bool = False) -> str:
    """
    Writes content to a file. Optionally adds line numbers.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if with_line_numbers:
        lines = content.splitlines()
        content = "\n".join(f"{i+1:04d}: {line}" for i, line in enumerate(lines))
    with open(file_path, "w", encoding='utf-8') as f:
        f.write(content)
    logger.info(f"File '{file_path}' written successfully.")
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
        logger.info(f"Uploading {os.path.basename(file_path)}...")
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

def upload_dir_files(client, dir_path, extensions=(".mp4", ".png", ".txt")):
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
        uploaded_file = upload_file(client, file_path)
        if uploaded_file:
            uploaded_files.append(uploaded_file)
    return uploaded_files

def dump_ui_tree(process_name: str = None, window_title: str = None, output_file: str = None, whitelist: list[str] = None, screenshots: bool = False) -> str:
    """
    Dumps the UI Automation tree for a given process or window to a JSON file.
    """
    from agent.uia_dumper import dump_ui, dump_ui_res
    # run on a different thread to avoid blocking, set a timeout for 10 seconds and abort if exceeds
    # store the result in a variable
    thread = threading.Thread(target=dump_ui, args=(process_name, window_title, output_file, whitelist, screenshots), daemon=True)  
    thread.start()
    thread.join(timeout=10)
    if thread.is_alive():
        return "Error: UI dump timed out after 10 seconds."
    else:
        return dump_ui_res
    