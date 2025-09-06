# Tools

This directory contains various tools for UI automation, recording, and playback. They are all exposed as MCP HTTP requests via the `mcp_server.py`.

## Running the MCP Server
To run the server and expose all tools, use the following command:
```bash
export GEMINI_API_KEY="YOUR_API_KEY"
python -m tools.mcp_server
```

## Gemini Tools

A set of tools for interacting with Google's Gemini Pro LLM. They can be used to generate Python test scripts from a folder of UIA recording files (JSON, screenshots, video).

The following tools are available via the MCP server:

- **`gemini_new_chat`**: Starts a new chat session, clearing history.
- **`gemini_upload_file`**: Uploads a single file to the current chat session.
- **`gemini_upload_folder`**: Uploads all files in a folder (and its subfolders) with allowed extensions.
- **`gemini_send_message`**: Sends a message (and any uploaded files) to the Gemini model and returns the response.

## UIA Dumper (`uia_dumper.py`)

A tool to dump the UI Automation (UIA) tree of a running application to a JSON file. This is useful for inspecting the UI hierarchy and element properties. This tool is also available via the `dump_ui_tree` MCP tool.

### Usage
```bash
# Dump UI tree for a window
python -m tools.uia_dumper -w "My Window Title" -o dump.json

# Dump UI tree for a process and capture screenshots
python -m tools.uia_dumper -p "my_process.exe" -o dump.json -s
```
- `-p, --process`: Process name to dump the UI tree for.
- `-w, --window`: Top-level window title to dump the UI tree for.
- `-o, --output`: Path to the output JSON file.
- `-s, --screenshots`: (Optional) Enable capturing screenshots of UI elements.
- `-wh, --whitelist`: (Optional) Filter: Only include elements from these process names.


## Recorder (`recorder.py`)

This tool records user interactions (mouse clicks, key presses) with an application and saves them as a sequence of events in a JSON file, along with screenshots of the interacted elements. This tool is also available via the `start_recording` and `stop_recording` MCP tools.

### Usage
```bash
python -m tools.recorder -p myapp.exe anotherapp.exe
```
- `-p, --process_names`: (Optional) Filter recording by one or more process names.

Press `Alt+Shift+R` to start/stop recording. Press `Esc` to exit the tool.

## Player (`player/`)

This tool plays back a recorded scenario, which consists of one or more test cases. It reads a JSON scenario file and executes the defined tests. This tool is also available via the `run_script` and `run_scenario` MCP tools.

### Usage
The main entry point is `player.py`.
```bash
python -m tools.player -sc path/to/your/scenario.json
```
- `-s, --script`: Path to the test script to run.
- `-sc, --scenario`: Path to the scenario JSON to run.
- `-o, --output`: Path to the output folder.
- `-nv, --no-video`: Disable video recording.

## Common (`common/`)
This directory contains shared modules used by the other tools, such as the `uia.py` module for common UI Automation functions.
