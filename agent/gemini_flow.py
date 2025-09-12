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
UI_DUMP_PATH = "user_scripts/ui_dump.json"

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

# --- Tools ---

def run_python_script(script_path: str):
    """
    Runs a python script.
    Returns a dictionary with 'stdout' on success or 'stderr' on failure.
    """
    if not os.path.exists(script_path):
        return {'stderr': f"Error: Script not found at {script_path}"}
    try:
        result = subprocess.run(
            ["python", script_path],
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

def read_file(file_path: str):
    """
    Reads content from a file.
    """
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"
    with open(file_path, "r", encoding='utf-8') as f:
        return f.read()

# --- Main Flow ---

def process_model_turn(chat, current_parts, tools):
    """Handles a single turn of conversation with the model, including tool calls."""
    while True:
        response = chat.send_message(
            current_parts,
            config=types.GenerateContentConfig(tools=tools, 
                                               system_instruction=system_prompt)
        )

        if not response.function_calls:
            # first we look for ```python ... ``` block
            python_code = response.text.split("```python")
            if len(python_code) > 1:
                python_code = python_code[1].split("```")[0].strip()
            return python_code
            
        function_calls = response.function_calls
        tool_parts = []
        print("\n--- Executing Tools ---")
        for function_call in function_calls:
            function_name = function_call.name
            function_args = dict(function_call.args)

            tool_function = next((t for t in tools if t.__name__ == function_name), None)
            if tool_function:
                # Special handling for write_file to ensure it uses the constant path
                if function_name == 'write_file':
                    function_args['file_path'] = GENERATED_SCRIPT_PATH

                print(f"Calling: {function_name}(...)", end="", flush=True)
                try:
                    result = tool_function(**function_args)
                    print(" -> Done")
                    tool_parts.append(types.Part.from_function_response(name=function_name, response={'result': result}))
                except Exception as e:
                    print(f" -> Error: {e}")
                    tool_parts.append(types.Part.from_function_response(name=function_name, response={'error': str(e)}))
            else:
                print(f"Error: Tool '{function_name}' not found.")
                tool_parts.append(types.Part.from_function_response(name=function_name, response={'error': 'Tool not found'}))

        current_parts = [types.Content(role='tool', parts=tool_parts)]

def main():
    """Main function to run the Gemini agent with iterative refinement."""
    parser = argparse.ArgumentParser(description="Gemini UI Automation Agent")
    parser.add_argument("recording_dir", help="Path to the recording directory.")
    args = parser.parse_args()

    chat = client.chats.create(model='gemini-2.5-flash')
    tools = [
        run_python_script,
        write_file,
        read_file
    ]

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
        #if ends with json move it json.txt
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
                continue

            initial_prompt_parts.append(uploaded_file)
        except Exception as e:
            print(f"\nError uploading file {file_path}: {e}")
            continue

    initial_prompt_parts.append(f"\n\nPlease generate the python script now. The script should be written to '{GENERATED_SCRIPT_PATH}'.")

    # --- Initial Generation ---
    print("\nGenerating initial script... (This may take a moment)")
    process_model_turn(chat, initial_prompt_parts, tools)
    print(f"Initial script written to {GENERATED_SCRIPT_PATH}")

    # --- Iterative Refinement Loop ---
    for i in range(MAX_REFINEMENT_ATTEMPTS):
        print(f"\n--- Attempt {i + 1}/{MAX_REFINEMENT_ATTEMPTS}: Running Script ---")

        # We don't use the tool here directly, but call the function
        run_result = run_python_script(GENERATED_SCRIPT_PATH)

        if 'stdout' in run_result and 'stderr' not in run_result:
            print("\n--- Script Executed Successfully! ---")
            print(run_result['stdout'])
            return # Success!

        print("\n--- Script Failed! Initiating Refinement ---")
        error_logs = run_result.get('stderr', 'No stderr output.')
        print(f"Error Details:\n{error_logs}")

        # Dump the UI for context
        print("Dumping current UI state...")
        # We need to find the window to dump. Let's try to get it from the recording's json
        process_name, window_title = None, None
        json_path = next((f for f in files_to_upload if f.endswith('.json')), None)
        if json_path:
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                    # Heuristic: Find the first valid process/window name from the hierarchy
                    for event in data:
                        if 'element_hierarchy' in event:
                            for element in event['element_hierarchy']:
                                if not process_name and element.get('process_name') and element['process_name'] != 'explorer.exe':
                                    process_name = element['process_name']
                                if not window_title and element.get('control_type') == 'WindowControl':
                                    window_title = element.get('name')
                                if process_name and window_title: break
                            if process_name and window_title: break
            except Exception as e:
                print(f"Could not extract process/window name from JSON: {e}")

        command = ["python", "agent/uia_dumper.py", "-o", UI_DUMP_PATH]
        if process_name:
            command.extend(["-p", process_name])
        elif window_title:
            command.extend(["-w", window_title])

        if len(command) > 4: # If either process or window title was added
            try:
                dump_result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
                print(dump_result.stdout)
            except subprocess.CalledProcessError as e:
                print(f"Error dumping UI: {e.stderr}")
        else:
            print("Could not determine process or window to dump; skipping UI dump.")

        # Prepare refinement prompt
        refinement_prompt = [
            "The previously generated script failed to execute correctly.",
            f"Error logs:\n```\n{error_logs}\n```",
            f"I have captured the current state of the UI, which is available in the attached file: {UI_DUMP_PATH}. Please analyze the error and the UI dump to provide a corrected version of the script.",
            f"Write the corrected script to '{GENERATED_SCRIPT_PATH}'."
        ]

        # Upload the UI dump file for the model to analyze
        print(f"Uploading UI dump file: {UI_DUMP_PATH}")
        try:
            dump_file = client.files.upload(file=UI_DUMP_PATH)
            # Wait for the file to be processed.
            while dump_file.state.name == "PROCESSING":
                print(".", end="", flush=True)
                time.sleep(2)
                dump_file = client.files.get(name=dump_file.name)
            print()

            if dump_file.state.name == "FAILED":
                 print(f"Error: UI dump file upload failed.")
                 # We can still proceed, but the model will have less context.
            else:
                refinement_prompt.append(dump_file)

        except Exception as e:
            print(f"\nError uploading UI dump file: {e}")

        print("\nRequesting script correction from model...")
        process_model_turn(chat, refinement_prompt, tools)
        print(f"Corrected script written to {GENERATED_SCRIPT_PATH}")

    print(f"\n--- Max Retries Reached! ---")
    print("Could not fix the script after multiple attempts.")

if __name__ == "__main__":
    main()
