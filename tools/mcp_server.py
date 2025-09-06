from fastmcp import FastMCP
import gemini_chat

mcp = FastMCP("UIAutomation Tools Server")

@mcp.tool
def dump_ui_tree(process_name: str = None, window_title: str = None, output_file: str = None, whitelist: list[str] = None, screenshots: bool = False) -> str:
    """
    Dumps the UI Automation tree for a given process or window to a JSON file.

    Args:
        process_name: Process name to dump the UI tree for (e.g., "explorer.exe").
        window_title: Top-level window title to dump the UI tree for (e.g., "Calculator").
        output_file: Path to the output JSON file.
        whitelist: Filter: Only include elements from these process names.
        screenshots: Enable capturing screenshots of elements.
    """
    try:
        import uia_dumper
    except ImportError as e:
        return f"Error importing uia_dumper: {e}. This tool is likely Windows-only."

    if not process_name and not window_title:
        return "Error: Either process_name or window_title must be provided."
    if not output_file:
        return "Error: output_file must be provided."

    return uia_dumper.dump_uia_tree(
        process_name=process_name,
        window_title=window_title,
        output_file=output_file,
        whitelist=whitelist,
        screenshots=screenshots
    )

@mcp.tool
def start_recording(whitelist: list[str] = None, output_folder: str = "recorder/output") -> str:
    """
    Starts a new recording session.

    Args:
        whitelist: Filter recording by process name(s).
        output_folder: The folder to save the recording data.
    """
    try:
        import recorder_tool
    except ImportError as e:
        return f"Error importing recorders: {e}. This tool is likely Windows-only."
    return recorder_tool.start_recording(whitelist=whitelist, output_folder=output_folder)

@mcp.tool
def stop_recording() -> str:
    """
    Stops the current recording session.
    """
    try:
        import recorder_tool
    except ImportError as e:
        return f"Error importing recorder_tool: {e}. This tool is likely Windows-only."
    return recorder_tool.stop_recording()

@mcp.tool
def run_script(script_path: str, output_folder: str = "output", no_video: bool = False, variables: dict = None) -> str:
    """
    Runs a single test script.

    Args:
        script_path: Path to the test script to run.
        output_folder: Path to the output folder.
        no_video: Disable video recording.
        variables: Variables to pass to the test case.
    """
    try:
        import player_tool
    except ImportError as e:
        return f"Error importing player_tool: {e}. This tool is likely Windows-only."
    return player_tool.run_script(script_path, output_folder, no_video, variables)

@mcp.tool
def run_scenario(scenario_path: str, output_folder: str = "output") -> str:
    """
    Runs a test scenario.

    Args:
        scenario_path: Path to the scenario JSON to run.
        output_folder: Path to the output folder.
    """
    try:
        import player_tool
    except ImportError as e:
        return f"Error importing player: {e}. This tool is likely Windows-only."
    return player_tool.run_scenario(scenario_path, output_folder)

@mcp.tool
def gemini_new_chat() -> str:
    """
    Starts a new chat session with Gemini, clearing history.
    """
    return gemini_chat.new_chat_session()

@mcp.tool
def gemini_upload_file(file_path: str) -> str:
    """
    Uploads a single file to Gemini for the current chat session.

    Args:
        file_path: The path to the file to upload.
    """
    return gemini_chat.upload_file_to_gemini(file_path)

@mcp.tool
def gemini_upload_folder(folder_path: str, allowed_extensions: list[str] = None) -> str:
    """
    Uploads all files in a folder (and subfolders) with allowed extensions.

    Args:
        folder_path: The path to the folder to upload.
        allowed_extensions: A list of file extensions to allow (e.g., [".json", ".png"]).
    """
    if allowed_extensions is None:
        allowed_extensions = [".json", ".png", ".mp4", ".py"]
    return gemini_chat.upload_folder_to_gemini(folder_path, allowed_extensions)

@mcp.tool
def gemini_send_message(message: str) -> str:
    """
    Sends a message to the Gemini model and returns the response.

    Args:
        message: The message to send to the model.
    """
    return gemini_chat.send_message_to_gemini(message)

if __name__ == "__main__":
    mcp.run()
