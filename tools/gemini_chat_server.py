import os
import time
import tempfile
from flask import Flask, request, jsonify
import google.genai as genai
from google.genai import types
# --- Globals ---
app = Flask(__name__)
client = None
chat_session = None
uploaded_files = []

# --- Gemini Configuration ---
def configure_gemini():
    """Configures the Gemini API key."""
    global client
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    # No need for genai.configure, the client will use the environment variable
    client = genai.Client()


def get_system_prompt():
    """Reads the system prompt from the file."""
    script_dir = os.path.dirname(__file__)
    prompt_file = os.path.join(script_dir, 'recorder', 'recording_to_script.md')
    with open(prompt_file, 'r') as f:
        return f.read()

# --- Flask Endpoints ---
@app.route('/gemini/newchat', methods=['POST'])
def new_chat():
    """Starts a new chat session, clearing history."""
    global chat_session, uploaded_files, client
    try:
        if client is None:
            configure_gemini()
        chat_session = client.chats.create(
            model="gemini-2.5-pro",
            config=types.GenerateContentConfig(
                system_instruction=get_system_prompt()
            )
        )
        uploaded_files = []
        return jsonify({"message": "New chat session started."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/gemini/uploadfile', methods=['POST'])
def upload_file():
    """Uploads a file to Gemini for the current chat session."""
    global uploaded_files, client
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        try:
            print(f"Uploading file: {file.filename}")
            # The google.generativeai.upload_file function expects a file path.
            with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as temp_file:
                file.save(temp_file.name)
                gemini_file = client.files.upload(file=temp_file.name)

                while gemini_file.state.name != 'ACTIVE':
                    print(f"Waiting for file {file.filename} to become active...")
                    time.sleep(2)
                    gemini_file = client.files.get(name=gemini_file.name)

                uploaded_files.append(gemini_file)

            os.unlink(temp_file.name) # Clean up the temporary file

            return jsonify({
                "message": f"File '{file.filename}' uploaded successfully.",
                "file_uri": gemini_file.uri
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "File upload failed."}), 500


@app.route('/gemini/uploadfolder', methods=['POST'])
def upload_folder():
    """Uploads all files in a folder (and subfolders) with allowed extensions."""
    global uploaded_files, client
    data = request.get_json()
    if not data or 'folder' not in data or 'allowed_extensions' not in data:
        return jsonify({"error": "Missing 'folder' or 'allowed_extensions' in request body."}), 400

    folder_path = data['folder']
    allowed_extensions = data['allowed_extensions']

    if not os.path.isdir(folder_path):
        return jsonify({"error": f"Folder not found: {folder_path}"}), 400

    uploaded_file_details = []

    try:
        for root, _, files in os.walk(folder_path):
            for filename in files:
                if any(filename.endswith(ext) for ext in allowed_extensions):
                    file_path = os.path.join(root, filename)
                    try:
                        print(f"Uploading file: {file_path}")
                        gemini_file = client.files.upload(file=file_path)

                        while gemini_file.state.name != 'ACTIVE':
                            print(f"Waiting for file {filename} to become active...")
                            time.sleep(2)
                            gemini_file = client.files.get(name=gemini_file.name)

                        uploaded_files.append(gemini_file)
                        uploaded_file_details.append({
                            "file_name": filename,
                            "file_uri": gemini_file.uri
                        })
                    except Exception as e:
                        print(f"Could not upload file {file_path}: {e}")

        return jsonify({
            "message": f"Folder processed. Found and uploaded {len(uploaded_file_details)} files.",
            "uploaded_files": uploaded_file_details
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/gemini/sendmessage', methods=['POST'])
def send_message():
    """Sends a message to the Gemini model and returns the response."""
    global chat_session, uploaded_files
    if not chat_session:
        return jsonify({"error": "No active chat session. Please start a new chat."}), 400

    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "No message provided."}), 400

    message_text = data['message']

    try:
        # Combine text message with any uploaded files
        prompt_parts = []
        if uploaded_files:
            prompt_parts.extend(uploaded_files)

        prompt_parts.append(message_text)
        
        response = chat_session.send_message(prompt_parts)

        # Clear uploaded files after sending the message, as they are now part of the history
        uploaded_files = []

        # The user wants a structured JSON response.
        # The 'text' attribute of the response contains the model's output.
        # If the model is prompted to return JSON, this text can be parsed.
        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    configure_gemini()
    chat_session = client.chats.create(
        model="gemini-2.5-pro",
        config=types.GenerateContentConfig(
            system_instruction=get_system_prompt()
        )
    )
    print("Default chat session started.")

    app.run(host='0.0.0.0', port=5000)
