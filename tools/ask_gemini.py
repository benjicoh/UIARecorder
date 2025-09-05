import os
import argparse
import time
from google import genai
from google.genai import types
from pydantic import BaseModel

# A structured output for the generated script.
class PythonScript(BaseModel):
    code: str

def ask_gemini(recording_folder: str) -> str:
    """
    Calls the Gemini 2.5 Pro LLM with the recording folder and returns the generated script.

    Args:
        recording_folder: The path to the folder containing the recording files.

    Returns:
        The generated Python script.
    """
    print(f"Starting script generation for recording in '{recording_folder}'...")

    # Initialize the Gemini client
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    client = genai.Client(api_key=api_key)

    # Read the system prompt
    with open('recorder/recording_to_script.md', 'r') as f:
        system_prompt = f.read()

    # Find and upload the recording files
    uploaded_files = []
    jsons = []
    #get all files recursively in the recording folder
    for root, dirs, files in os.walk(recording_folder):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if file_name.endswith(('mp4','.png', 'json')):
                if file_name.endswith('json'):
                    #append aits content to jsons
                    with open(file_path, 'r') as jf:
                        content = jf.read()
                        jsons.append(f"{file_name}\n```json\n{content}\n```")
                    continue
                print(f"Uploading file: {file_path}")
                uploaded_file = client.files.upload(file=file_path)
                uploaded_files.append(uploaded_file)
                
                #wait for the file to become active
                while uploaded_file.state.name != 'ACTIVE':
                    print(f"Waiting for file {file_name} to become active...")
                    time.sleep(2)
                    uploaded_file = client.files.get(name=uploaded_file.name)

    if not uploaded_files:
        raise FileNotFoundError("No recording files found in the specified folder.")

    # Create the prompt
    prompt_parts = uploaded_files + jsons

    # Call the Gemini API
    print("Calling Gemini 2.5 Pro to generate the script...")
    model = "gemini-2.5-pro"
    response = client.models.generate_content(
        model=model,
        contents=prompt_parts,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type='application/json',
            response_schema=PythonScript,
        ),
    )

    # Extract the generated script
    script_obj: PythonScript = response.parsed
    generated_code = script_obj.code

    # Save the script
    script_path = 'generated_script.py'
    with open(script_path, 'w') as f:
        f.write(generated_code)

    print(f"Script saved to '{script_path}'")
    return script_path

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a Python script from a recording folder.')
    parser.add_argument('recording_folder', type=str, help='The path to the recording folder.')
    args = parser.parse_args()

    ask_gemini(args.recording_folder)
