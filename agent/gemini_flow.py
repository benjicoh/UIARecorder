import os
import subprocess
import time
from google import genai
from google.genai import types
from agent.uia_dumper import dump_ui

# --- Configuration ---
# The client will automatically pick up the GOOGLE_API_KEY or GEMINI_API_KEY
# from the environment. If the user said no key is needed, it's likely
# this is running in an environment with Application Default Credentials (ADC).
try:
    client = genai.Client()
except Exception as e:
    print(f"Error creating client: {e}")
    print("Please make sure you have set up your API key or ADC correctly.")
    exit()

# --- Tools ---

def run_python_script(script_path: str):
    """
    Runs a python script and returns the output.
    """
    if not os.path.exists(script_path):
        return f"Error: Script not found at {script_path}"

    try:
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error running script:\n{e.stderr}"

def write_file(file_path: str, content: str):
    """
    Writes content to a file.
    """
    with open(file_path, "w") as f:
        f.write(content)
    return f"File '{file_path}' written successfully."

# --- Main Flow ---

def main():
    """
    Main function to run the simplified Gemini agent.
    """
    # Load the system prompt
    try:
        with open('agent/prompt.md', 'r', encoding='utf-8') as f:
            system_prompt = f.read()
    except FileNotFoundError:
        print("Error: `agent/prompt.md` not found.")
        system_prompt = "You are a helpful assistant."


    history = []
    tools = [run_python_script, dump_ui, write_file]

    print("--- Simplified Gemini Agent (Manual History) ---")
    print("Enter 'exit' to end the conversation.")
    print("To upload a file, type 'upload <file_path>' and then your prompt.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break

        parts = []
        if user_input.lower().startswith('upload '):
            parts_from_input = user_input.split(' ', 1)
            if len(parts_from_input) > 1:
                file_path = parts_from_input[1].split(' ', 1)[0]
                prompt = user_input.replace(f"upload {file_path}", "").strip()

                if os.path.exists(file_path):
                    print(f"Uploading {file_path}...")
                    try:
                        uploaded_file = client.files.upload(file=file_path)

                        # Wait for the file to be processed.
                        while uploaded_file.state.name == "PROCESSING":
                            print(".", end="", flush=True)
                            time.sleep(1)
                            uploaded_file = client.files.get(name=uploaded_file.name)

                        if uploaded_file.state.name == "FAILED":
                            print(f"Error: File upload failed for {file_path}.")
                            continue

                        print("File uploaded successfully.")
                        parts.append(uploaded_file)

                        if prompt:
                            parts.append(types.Part.from_text(text=prompt))
                        else:
                            parts.append(types.Part.from_text(text=f"File {file_path} uploaded. What should I do with it?"))
                    except Exception as e:
                        print(f"Error uploading file: {e}")
                        continue
                else:
                    print(f"File not found: {file_path}")
                    continue
            else:
                print("Please provide a file path after 'upload'.")
                continue
        else:
            parts.append(types.Part.from_text(text=user_input))

        history.append(types.Content(role='user', parts=parts))

        while True:
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=history,
                config=types.GenerateContentConfig(
                    tools=tools,
                    system_instruction=system_prompt
                )
            )

            if not response.function_calls:
                break  # No tool called, exit the loop

            # Execute the tool calls
            function_calls = response.function_calls
            tool_parts = []
            for function_call in function_calls:
                function_name = function_call.name
                function_args = function_call.args
                print(f"Executing tool: {function_name}({function_args})")

                # Find the tool function
                tool_function = next((t for t in tools if t.__name__ == function_name), None)

                if tool_function:
                    try:
                        result = tool_function(**dict(function_args))
                        tool_parts.append(types.Part.from_function_response(name=function_name, response={'result': result}))
                    except Exception as e:
                        print(f"Error executing tool {function_name}: {e}")
                        tool_parts.append(types.Part.from_function_response(name=function_name, response={'error': str(e)}))
                else:
                    print(f"Tool {function_name} not found.")
                    tool_parts.append(types.Part.from_function_response(name=function_name, response={'error': 'Tool not found'}))

            # Add the tool response to the history
            history.append(types.Content(role='tool', parts=tool_parts))
            # Continue the loop to get the model's response to the tool output

        # Print the model's final response and add it to the history
        if response.text:
            print(f"Model: {response.text}")
            history.append(response.candidates[0].content)

if __name__ == "__main__":
    main()
