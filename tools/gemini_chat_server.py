import os
import io
import json
import time
import tempfile
from flask import Flask, request, jsonify
import google.genai as genai
from google.genai.types import content_types

# --- Globals ---
app = Flask(__name__)
chat_session = None
uploaded_files = []
model = None

# --- Gemini Configuration ---
def configure_gemini():
    """Configures the Gemini API key."""
    global model
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        system_instruction=get_system_prompt()
    )


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
    global chat_session, uploaded_files, model
    try:
        if model is None:
            configure_gemini()
        chat_session = model.start_chat()
        uploaded_files = []
        return jsonify({"message": "New chat session started."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/gemini/uploadfile', methods=['POST'])
def upload_file():
    """Uploads a file to Gemini for the current chat session."""
    global uploaded_files
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        try:
            print(f"Uploading file: {file.filename}")
            # The google.generativeai.upload_file function expects a file path.
            # To handle in-memory uploads from a web request, we save the file
            # to a temporary location on disk and then pass the path to the SDK.
            with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as temp_file:
                file.save(temp_file.name)
                gemini_file = genai.upload_file(path=temp_file.name, display_name=file.filename)

                # Wait for the file to become active
                while gemini_file.state.name != 'ACTIVE':
                    print(f"Waiting for file {file.filename} to become active...")
                    time.sleep(2)
                    gemini_file = genai.get_file(name=gemini_file.name)

                uploaded_files.append(gemini_file)

            os.unlink(temp_file.name) # Clean up the temporary file

            return jsonify({
                "message": f"File '{file.filename}' uploaded successfully.",
                "file_uri": gemini_file.uri
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "File upload failed."}), 500


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
    # To start a default chat session on server startup
    chat_session = model.start_chat()
    print("Default chat session started.")

    app.run(host='0.0.0.0', port=5000)
