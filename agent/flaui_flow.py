import os
import argparse
import time
from pydantic import BaseModel
from google.genai import types
from tools.common.logger import get_logger
from tools.recorder.main_recorder import Recorder
from agent.common_flow import (
    initialize_gemini_client,
    send_message_with_retries,
    run_command,
    write_file,
    upload_dir_files,
)

logger = get_logger(__name__)

# --- Constants ---
MAX_COMPILATION_ATTEMPTS = 4
MAX_EXECUTION_ATTEMPTS = 4
RUN_OUTPUT_DIR = "generated_scripts/{timestamp}"
COMPILATION_ITERATION_DIR = "{run_output_dir}/compilation/iteration{i}"
EXECUTION_ITERATION_DIR = "{run_output_dir}/execution/iteration{i}"
MODEL = "gemini-2.5-flash"
FLAUI_PROJECT_DIR = "fla-ui/TemplateTest"
FLAUI_PROJECT_PATH = f"{FLAUI_PROJECT_DIR}/TemplateTest.csproj"
FLAUI_SOURCE_PATH = f"{FLAUI_PROJECT_DIR}/TestClass.cs"

# --- Configuration ---
client = initialize_gemini_client()


# -- Structured Output --
class CodeResponse(BaseModel):
    code_lines: list[str]
    failure_reason: str = None
    comments: str = None

# --- Prompts ---
try:
    cur_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(cur_path, 'flaui_prompt.md'), 'r', encoding='utf-8') as f:
        system_prompt = f.read()
except FileNotFoundError:
    logger.error(f"Error: `flaui_prompt.md` not found.")
    exit()

# --- Helper Functions ---
# All helper functions moved to agent/common_flow.py
# --- Main Flow ---
def main():
    parser = argparse.ArgumentParser(description="Gemini UI Automation Agent for FlaUI")
    parser.add_argument("recording_dir", help="Path to the recording directory.")
    parser.add_argument("-p", "--process-name", help="The process name of the target application.")
    parser.add_argument("-w", "--window-title", help="The window title of the target application.")
    args = parser.parse_args()

    run_output_dir = RUN_OUTPUT_DIR.format(timestamp=time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(run_output_dir, exist_ok=True)
    logger.info(f"Run output directory: {run_output_dir}")

    chat = client.chats.create(model=MODEL)

    logger.info(f"Analyzing data in: {args.recording_dir}")
    initial_files = upload_dir_files(client, args.recording_dir)
    prompt_parts = []
    logger.info("Generating initial script... (This may take a moment)")
    prompt_parts.extend(initial_files)
    prompt_parts.append("Generate the initial C# script to perform the recorded scenario using FlaUI and MSTest.")

    # --- Compilation Loop ---
    compilation_success = False
    code_response = None
    iteration_dir = ""
    for i in range(MAX_COMPILATION_ATTEMPTS):
        logger.info(f"--- Compilation Attempt {i+1}/{MAX_COMPILATION_ATTEMPTS} ---")
        

        # --- Generate Script ---
        if i > 0:
            prompt_parts = ["The previously generated script failed to compile.\nAttached are the compilation logs for analysis and script refinement."]
            prompt_parts.extend(upload_dir_files(client, iteration_dir))
        response = send_message_with_retries(
            chat,
            prompt_parts,
            types.GenerateContentConfig(
                response_schema=CodeResponse,
                response_mime_type="application/json",
                system_instruction=system_prompt
            )
        )
            
        code_response: CodeResponse = response.parsed
        iteration_dir = COMPILATION_ITERATION_DIR.format(run_output_dir=run_output_dir, i=i)
        # --- Write Script to File ---
        code = "\n".join(code_response.code_lines)
        write_file(f"{FLAUI_SOURCE_PATH}", code)
        logger.info(f"Script written to {FLAUI_SOURCE_PATH}")
        write_file(iteration_dir + "/script.cs.txt", code, True)

        # --- Compile Script ---
        logger.info(f"Compiling script: {FLAUI_PROJECT_PATH}")
        compilation_result = run_command(["dotnet", "build"], FLAUI_PROJECT_DIR)

        log_path = iteration_dir + "/compilation_log.txt"
        log_output = f"STDOUT:\n{compilation_result['stdout']}\n\nSTDERR:\n{compilation_result['stderr']}"
        write_file(log_path, log_output)
        logger.info(f"Compilation log file written to {log_path}")

        if compilation_result['returncode'] == 0:
            logger.info("--- Compilation Successful! ---")
            compilation_success = True
            break

        logger.warning("--- Compilation Failed! ---")
        if i == MAX_COMPILATION_ATTEMPTS - 1: break

    if not compilation_success:
        logger.error("--- Max Compilation Retries Reached! Could not compile the script. ---")
        return

    # --- Execution Loop ---
    execution_success = False
    for i in range(MAX_EXECUTION_ATTEMPTS):
        logger.info(f"--- Execution Attempt {i+1}/{MAX_EXECUTION_ATTEMPTS} ---")
        iteration_dir = EXECUTION_ITERATION_DIR.format(run_output_dir=run_output_dir, i=i + MAX_COMPILATION_ATTEMPTS)

        # --- Run Script ---
        logger.info(f"Running test: {FLAUI_PROJECT_PATH}")
        generated_recording_dir = iteration_dir + "/recordings"
        recorder = Recorder(output_folder=generated_recording_dir, take_screenshots=False)
        recorder.start()
        execution_result = run_command(["dotnet", "test"], FLAUI_PROJECT_DIR)
        recorder.stop()

        # --- Log Execution Results ---
        log_path = iteration_dir + "/execution_log.txt"
        log_output = f"STDOUT:\n{execution_result['stdout']}\n\nSTDERR:\n{execution_result['stderr']}"
        write_file(log_path, log_output)
        logger.info(f"Execution log file written to {log_path}")

        if "!Passed!" in execution_result['stdout']:
            logger.info("--- Test Executed Successfully! ---")
            execution_success = True
            break

        logger.warning("--- Test Execution Failed! ---")
        if i == MAX_EXECUTION_ATTEMPTS - 1: break

        logger.info("Collecting and sending data for refinement...")
        prompt_parts = ["The previously generated script failed to execute correctly.\nAttached are the logs of the failed run for analysis, and script refinement."]
        prompt_parts.extend(upload_dir_files(client, iteration_dir))

        # --- Generate Script ---
        response = send_message_with_retries(
            chat,
            prompt_parts,
            types.GenerateContentConfig(
                response_schema=CodeResponse,
                response_mime_type="application/json",
                system_instruction=system_prompt
            )
        )
        code_response = response.parsed
        # --- Write Script to File ---
        code = "\n".join(code_response.code_lines)
        write_file(f"{FLAUI_SOURCE_PATH}", code)
        logger.info(f"Script written to {FLAUI_SOURCE_PATH}")
        write_file(iteration_dir + "/script.cs.txt", code, True)

    if not execution_success:
        logger.error("--- Max Execution Retries Reached! Could not fix the script. ---")

if __name__ == "__main__":
    main()