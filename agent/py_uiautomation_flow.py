
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
    run_python_script,
    write_file,
    upload_dir_files,
)

logger = get_logger(__name__)

# --- Constants ---
MAX_REFINEMENT_ATTEMPTS = 3
RUN_OUTPUT_DIR = "generated_scripts/{timestamp}"
ITERATION_OUTPUT_DIR = "{run_output_dir}/iteration{i}"
MODEL = "gemini-2.5-flash"

# --- Configuration ---
client = initialize_gemini_client()

# -- Structured Output --
class CodeResponse(BaseModel):
    code: str
    failure_reason: str = None
    comments: str = None

# --- Prompts ---
try:
    cur_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(cur_path, 'prompt.md'), 'r', encoding='utf-8') as f:
        system_prompt = f.read()
except FileNotFoundError:
    logger.error("Error: `agent/prompt.md` not found.")
    exit()

# --- Helper Functions ---
# All helper functions moved to agent/common_flow.py
# --- Main Flow ---

def main():
    """Main function to run the Gemini agent with iterative refinement."""
    parser = argparse.ArgumentParser(description="Gemini UI Automation Agent")
    parser.add_argument("recording_dir", help="Path to the recording directory.")
    parser.add_argument("-p", "--process-name", help="The process name of the target application.")
    parser.add_argument("-w", "--window-title", help="The window title of the target application.")
    args = parser.parse_args()

    run_output_dir = RUN_OUTPUT_DIR.format(timestamp=time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(run_output_dir, exist_ok=True)
    logger.info(f"Run output directory: {run_output_dir}")

    chat = client.chats.create(model=MODEL)

    # --- Initial Prompt Construction ---
    logger.info(f"Analyzing data in: {args.recording_dir}")
    initial_files = upload_dir_files(client, args.recording_dir)
    prompt_parts = []
    logger.info("Generating initial script... (This may take a moment)")
    prompt_parts.extend(initial_files)
    prompt_parts.append("Generate the initial script to perform the recorded scenario.")
    # --- Iterative Refinement Loop ---
    last_run_result = None
    for i in range(MAX_REFINEMENT_ATTEMPTS):
        logger.info(f"--- Attempt {i+1}/{MAX_REFINEMENT_ATTEMPTS} ---")
        iteration_dir = ITERATION_OUTPUT_DIR.format(run_output_dir=run_output_dir, i=i)
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
        code_response: CodeResponse = response.parsed
        # --- Write Script to File ---
        script_path = iteration_dir + "/run.py"
        write_file(script_path, code_response.code)
        logger.info(f"Script written to {script_path}")
        # --- Model Feedback ---
        if code_response.failure_reason:
            logger.info(f"LLM Failure Reason: {code_response.failure_reason}")
        if code_response.comments:
            logger.info(f"LLM Comments: {code_response.comments}")
        # --- Run Script ---
        logger.info(f"Running script: {script_path}")
        generated_recording_dir = iteration_dir + "/recordings"
        recorder = Recorder(output_folder=generated_recording_dir, take_screenshots=False)
        recorder.start()
        last_run_result = run_python_script(script_path)
        recorder.stop()
        # --- Log Results ---
        log_path = iteration_dir + "/log.txt"
        log_output = f"STDOUT:\n{last_run_result['stdout']}\n\nSTDERR:\n{last_run_result['stderr']}"
        write_file(log_path, log_output)
        logger.info(f"Log file written to {log_path}")
         # --- Check for Success ---
        if "Scenario completed successfully" in last_run_result['stdout']:
            logger.info("--- Script Executed Successfully! ---")
            logger.info(log_output)
            return  # Success!
        # --- Prepare for Next Iteration ---
        # if this is the last iteration no need to prepare for next
        if i == MAX_REFINEMENT_ATTEMPTS - 1:
            break
        logger.warning("--- Script Failed! ---")
        logger.info("Collecting and sending data for refinement...")
        prompt_parts = []
        prompt_parts.append("The previously generated script failed to execute correctly.\nAttached are the logs and recordings of the failed run for analysis, and script refinement.")
        # --- 6. Dump UI for next attempt (if not the last attempt) ---
        logger.info("Dumping current UI state for context...")
        ui_dump_path = iteration_dir + "/ui_dump.json.txt"
        try:
            from agent.uia_dumper import dump_ui
            if args.process_name or args.window_title:
                result = dump_ui(
                    process_name=args.process_name,
                    window_title=args.window_title,
                    output_file=ui_dump_path,
                    whitelist=None,
                    screenshots=False
                )
                logger.info(result)
            else:
                logger.warning("Process name or window title not provided. Skipping UI dump.")
        except Exception as e:
            logger.error(f"Error dumping UI: {e}")
        # Upload all files from the iteration for context
        prompt_parts.extend(upload_dir_files(client, iteration_dir))
         

    # --- Final Status Check ---
    logger.warning(f"--- Max Retries Reached! ---")
    if last_run_result and "Scenario completed successfully" not in last_run_result['stdout']:
        logger.warning("Could not fix the script after multiple attempts.")
        logger.warning(f"Final log output:\n{log_output}")


if __name__ == "__main__":
    main()
    