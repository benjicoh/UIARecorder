import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import time
import google.genai as genai
from pydantic import BaseModel

# --- Pydantic Models ---
class CodeResponse(BaseModel):
    """A Pydantic model for the structured response from the Gemini API."""
    code: str

# --- Globals ---
client = None
chat_session = None
uploaded_files = []

# --- Gemini Configuration ---
def configure_gemini():
    """Configures the Gemini API key."""
    global client
    if client:
        return
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    client = genai.Client(api_key=api_key)

def get_system_prompt():
    """Reads the system prompt from the file."""
    script_dir = os.path.dirname(__file__)
    prompt_file = os.path.join(script_dir, 'recorder', 'recording_to_script.md')
    with open(prompt_file, 'r') as f:
        return f.read()

# --- Core Functions ---
def new_chat_session():
    """Starts a new chat session, clearing history."""
    global chat_session, uploaded_files, client
    configure_gemini()
    # The Chat history is managed by the SDK.
    chat_session = client.chats.create(model="gemini-2.5-pro")
    uploaded_files = []
    return "New chat session started."

def upload_file_to_gemini(file_path: str):
    """Uploads a single file to Gemini."""
    global uploaded_files, client
    configure_gemini()
    # If the file is .json, create a .txt copy for Gemini
    base, ext = os.path.splitext(file_path)
    upload_path = file_path
    if ext.lower() == ".json":
        txt_path = base + ".json.txt"
        with open(file_path, "r", encoding="utf-8") as src, open(txt_path, "w", encoding="utf-8") as dst:
            dst.write(src.read())
        upload_path = txt_path
        print(f"Converted .json to .txt for Gemini: {upload_path}")
    print(f"Uploading file: {upload_path}")
    gemini_file = client.files.upload(file=upload_path)
    while gemini_file.state.name == "PROCESSING":
        print(f"Waiting for file {os.path.basename(file_path)} to be processed...")
        time.sleep(2)
        gemini_file = client.files.get(name=gemini_file.name)

    if gemini_file.state.name == "FAILED":
        raise ValueError(f"File upload failed for {os.path.basename(file_path)}")

    uploaded_files.append(gemini_file)
    return f"File '{os.path.basename(upload_path)}' uploaded successfully."

def upload_folder_to_gemini(folder_path: str, allowed_extensions: list[str]):
    """Uploads all files in a folder with allowed extensions."""
    if not os.path.isdir(folder_path):
        return f"Folder not found: {folder_path}"

    uploaded_count = 0
    for root, _, files in os.walk(folder_path):
        for filename in files:
            if any(filename.endswith(ext) for ext in allowed_extensions):
                file_path = os.path.join(root, filename)
                try:
                    upload_file_to_gemini(file_path)
                    uploaded_count += 1
                except Exception as e:
                    print(f"Could not upload file {file_path}: {e}")
    return f"Folder processed. Found and uploaded {uploaded_count} files."

def send_message_to_gemini(message: str):
    """Sends a message to the Gemini model and returns the response."""
    global chat_session, uploaded_files
    if not chat_session:
        return "No active chat session. Please start a new chat."

    # Prepend the system prompt only if it's the first message in the chat.
    is_first_message = len(chat_session.get_history()) == 0
    if is_first_message:
        contents = [get_system_prompt()] + uploaded_files + [message]
    else:
        contents = uploaded_files + [message]

    response = chat_session.send_message(
        contents,
        config={
            "response_mime_type": "application/json",
            "response_schema": CodeResponse,
        }
    )

    uploaded_files = []
    return response.text

if __name__ == "__main__":
    # Example usage
    new_chat_session()
    upload_folder_to_gemini("tools\\recorder\\output", [
        ".mp4"
    ])
    response = send_message_to_gemini("Can you generate a python script based on the recording?")
    print(response)
