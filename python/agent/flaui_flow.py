import os
import argparse
import time
import shutil
from pydantic import BaseModel
from google.genai import types
from python.common.logger import get_logger
from python.recorder.main_recorder import Recorder
from python.common.common_flow import (
    initialize_gemini_client,
    send_message_with_retries,
    run_command,
    write_file,
    upload_dir_files,
    dump_ui_tree,
)

logger = get_logger(__name__)

# --- Constants ---
MAX_COMPILATION_ATTEMPTS = 6
MAX_EXECUTION_ATTEMPTS = 6
RUN_OUTPUT_DIR = "generated_scripts/{timestamp}"
COMPILATION_ITERATION_DIR = "{run_output_dir}/compilation/iteration{i}"
EXECUTION_ITERATION_DIR = "{run_output_dir}/execution/iteration{i}"
MODEL = "gemini-flash-latest"
TEMPLATE_PROJECT_DIR = "fla-ui/TemplateTest"

# --- Configuration ---
client = initialize_gemini_client()


# -- Structured Output --
class CodeResponse(BaseModel):
    testcase_code_lines: list[str]
    application_page_code_lines: list[str]
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
def write_response_files(response: CodeResponse, target_dir: str, rename_to_txt: bool = False):
    write_file(os.path.join(target_dir, "TestClass.cs"), "\n".join(response.testcase_code_lines))
    write_file(os.path.join(target_dir, "ApplicationPage.cs"), "\n".join(response.application_page_code_lines))
    if rename_to_txt:
        os.rename(os.path.join(target_dir, "TestClass.cs"), os.path.join(target_dir, "TestClass.cs.txt"))
        os.rename(os.path.join(target_dir, "ApplicationPage.cs"), os.path.join(target_dir, "ApplicationPage.cs.txt"))

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

    # --- Copy Template Project ---
    project_dir = os.path.join(run_output_dir, "TemplateTest")
    shutil.copytree(TEMPLATE_PROJECT_DIR, project_dir)
    logger.info(f"Copied template project to {project_dir}")

    flaui_project_path = f"{project_dir}/TemplateTest.csproj"

   
    chat = client.chats.create(model=MODEL)

    logger.info(f"Analyzing data in: {args.recording_dir}")
    initial_files = upload_dir_files(client, args.recording_dir)

    # Copy project all cs, csproj as txt to temp dir for upload
    tmp_dir = os.path.join(run_output_dir, "tmp")
    shutil.copytree(TEMPLATE_PROJECT_DIR, tmp_dir)
    # Rename in tmpdir all cs , csproj file to txt
    for dirpath, _, filenames in os.walk(tmp_dir):
        if dirpath.endswith("bin") or dirpath.endswith("obj"):
            continue
        for filename in filenames:
            if filename.endswith((".cs", ".csproj")):
                original_path = os.path.join(dirpath, filename)
                new_path = original_path + ".txt"
                shutil.move(original_path, new_path)
            else:
                #delete it
                os.remove(os.path.join(dirpath, filename))

    prompt_parts = []
    logger.info("Generating initial script... (This may take a moment)")
    prompt_parts.extend(initial_files)
    prompt_parts.extend(upload_dir_files(client, tmp_dir))
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
        if i == 0:
            # Delete temp dir after first use
            shutil.rmtree(tmp_dir)
        code_response: CodeResponse = response.parsed
        if code_response.failure_reason:
            logger.info(f"LLM failure reason: {code_response.failure_reason}")
        if code_response.comments:
            logger.info(f"LLM comments: {code_response.comments}")
        iteration_dir = COMPILATION_ITERATION_DIR.format(run_output_dir=run_output_dir, i=i)
        # --- Write Scripts to File ---
        write_response_files(code_response, project_dir)
        write_response_files(code_response, iteration_dir, rename_to_txt=True)

        # --- Compile Script ---
        logger.info(f"Compiling scripts: {flaui_project_path}")
        compilation_result = run_command(["dotnet", "build"], project_dir)
        logger.info(f"--- Compilation Output ---\n{compilation_result['stdout']}\n{compilation_result['stderr']}\n---")

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
        logger.info(f"Running test: {flaui_project_path}")
        generated_recording_dir = iteration_dir + "/recordings"
        recorder = Recorder(output_folder=generated_recording_dir, take_screenshots=False)
        recorder.start()
        execution_result = run_command(["dotnet", "test", "--logger", "console;verbosity=detailed"], project_dir)
        logger.info(f"--- Execution Output ---\n{execution_result['stdout']}\n{execution_result['stderr']}\n---")
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
         # --- Dump UI Tree ---
        ui_dump_path = os.path.join(iteration_dir, "ui_dump.json.txt")
        res = dump_ui_tree(process_name=args.process_name, window_title=args.window_title, output_file=ui_dump_path, whitelist=args.process_name, screenshots=False)
        logger.info(f"UI tree dump : {res}")

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
        if code_response.failure_reason:
            logger.info(f"LLM failure reason: {code_response.failure_reason}")
        if code_response.comments:
            logger.info(f"LLM comments: {code_response.comments}")
        # --- Write Script to File ---
        write_response_files(code_response, project_dir)
        write_response_files(code_response, iteration_dir, rename_to_txt=True)

    if not execution_success:
        logger.error("--- Max Execution Retries Reached! Could not fix the script. ---")

if __name__ == "__main__":
    main()