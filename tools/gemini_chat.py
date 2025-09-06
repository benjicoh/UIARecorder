import os
import time
import google.genai as genai
from google.genai import types
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
    genai.configure(api_key=api_key)
    client = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=get_system_prompt(),
    )

def get_system_prompt():
    """Reads the system prompt from the file."""
    script_dir = os.path.dirname(__file__)
    prompt_file = os.path.join(script_dir, 'recorder', 'recording_to_script.md')
    with open(prompt_file, 'r') as f:
        return f.read()

# --- Core Functions ---
def new_chat_session():
    """Starts a new chat session, clearing history."""
    global chat_session, uploaded_files
    configure_gemini()
    chat_session = client.start_chat()
    uploaded_files = []
    return "New chat session started."

def upload_file_to_gemini(file_path: str):
    """Uploads a single file to Gemini."""
    global uploaded_files, client
    configure_gemini()
    print(f"Uploading file: {file_path}")
    gemini_file = genai.upload_file(path=file_path)
    while gemini_file.state.name == "PROCESSING":
        print(f"Waiting for file {os.path.basename(file_path)} to be processed...")
        time.sleep(2)
        gemini_file = genai.get_file(gemini_file.name)

    if gemini_file.state.name == "FAILED":
        raise ValueError(f"File upload failed for {os.path.basename(file_path)}")

    uploaded_files.append(gemini_file)
    return f"File '{os.path.basename(file_path)}' uploaded successfully."

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

    prompt_parts = []
    if uploaded_files:
        prompt_parts.extend(uploaded_files)
    prompt_parts.append(message)

    response = chat_session.send_message(
        prompt_parts,
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json",
            response_schema=CodeResponse,
        )
    )

    uploaded_files = []
    return response.text
