import os
import argparse
import time
import google.generativeai as genai
from google.generativeai import types
from pydantic import BaseModel

# A structured output for the generated script.
class PythonScript(BaseModel):
    code: str

def ask_gemini(
    recording_folder: str,
    output_file: str = 'generated_script.py',
    log_file: str = None,
    dump_file: str = None
) -> str:
    """
    Calls the Gemini 1.5 Pro LLM with the recording folder and optional context files
    to generate or refine a Python script.

    Args:
        recording_folder: The path to the folder containing the recording files.
        output_file: The path to save the generated script.
        log_file: (Optional) The path to a log file from a previous execution.
        dump_file: (Optional) The path to a JSON dump of the UI tree.

    Returns:
        The generated Python script.
    """
    if log_file or dump_file:
        print(f"Starting script refinement for recording in '{recording_folder}'...")
    else:
        print(f"Starting script generation for recording in '{recording_folder}'...")

    # Initialize the Gemini client
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    client = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")


    # Read the system prompt
    script_dir = os.path.dirname(__file__)
    prompt_file = os.path.join(script_dir, 'recorder', 'recording_to_script.md')
    with open(prompt_file, 'r') as f:
        system_prompt = f.read()

    # --- Prepare prompt parts ---
    prompt_parts = []

    # 1. Add context files (logs, dumps) as text
    if log_file and os.path.exists(log_file):
        with open(log_file, 'r') as f:
            log_content = f.read()
            prompt_parts.append(f"automation_log.txt:\n```\n{log_content}\n```")
        print(f"Added log file: {log_file}")

    if dump_file and os.path.exists(dump_file):
        with open(dump_file, 'r') as f:
            dump_content = f.read()
            prompt_parts.append(f"dump.json:\n```json\n{dump_content}\n```")
        print(f"Added UI dump file: {dump_file}")

    # 2. Find and upload the recording files
    uploaded_files = []
    #get all files recursively in the recording folder
    for root, dirs, files in os.walk(recording_folder):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            # JSON files are added as text, others are uploaded
            if file_name.endswith('json'):
                with open(file_path, 'r', encoding='utf-8') as jf:
                    content = jf.read()
                    prompt_parts.append(f"{file_name}\n```json\n{content}\n```")
                continue

            if file_name.endswith(('mp4','.png')):
                print(f"Uploading file: {file_path}")
                print(f"Uploading file: {file_path}")
                uploaded_file = genai.upload_file(path=file_path)
                
                # Wait for the file to become active
                while uploaded_file.state.name != 'ACTIVE':
                    print(f"Waiting for file {file_name} to become active...")
                    time.sleep(2)
                    uploaded_file = genai.get_file(name=uploaded_file.name)

                uploaded_files.append(uploaded_file)

    if not uploaded_files and not any('.json' in p for p in prompt_parts):
        raise FileNotFoundError("No recording files (json, mp4, png) found in the specified folder.")

    # Add uploaded files to the beginning of the prompt
    prompt_parts = uploaded_files + prompt_parts

    # Call the Gemini API
    print("Calling Gemini Pro to generate the script...")

    response = client.generate_content(
        contents=prompt_parts,
        system_instruction=system_prompt,
        generation_config=types.GenerationConfig(
            response_mime_type='application/json',
            response_schema=PythonScript,
        ),
        request_options=types.RequestOptions(
            timeout=600
        )
    )

    # Extract the generated script
    try:
        # Using response.text because of the structured response
        script_obj = PythonScript.model_validate_json(response.text)
        generated_code = script_obj.code
    except Exception as e:
        print("Error parsing Gemini response:")
        print(response.text)
        raise e


    # Save the script
    with open(output_file, 'w') as f:
        f.write(generated_code)

    print(f"Script saved to '{output_file}'")
    return output_file

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate or refine a Python script from a recording folder.')
    parser.add_argument('recording_folder', type=str, help='The path to the recording folder.')
    parser.add_argument('--output_file', type=str, default='../user_scripts/test_scenario.py', help='The path to save the generated script.')
    parser.add_argument('--log_file', type=str, help='(Optional) The path to a log file from a previous execution.')
    parser.add_argument('--dump_file', type=str, help='(Optional) The path to a JSON dump of the UI tree.')

    args = parser.parse_args()

    ask_gemini(
        args.recording_folder,
        output_file=args.output_file,
        log_file=args.log_file,
        dump_file=args.dump_file
    )
