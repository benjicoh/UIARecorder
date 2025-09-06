# Tools

This directory contains various tools for UI automation, recording, and playback. It is structured as a Python package to allow for shared modules.

## Gemini Server (`gemini_chat_server.py`)

A Flask-based server that provides an API for interacting with Google's Gemini Pro LLM. It can be used to generate Python test scripts from a folder of UIA recording files (JSON, screenshots, video).

### Running the server
```bash
export GEMINI_API_KEY="YOUR_API_KEY"
python -m tools.gemini_chat_server
```

### Endpoints

#### `POST /gemini/newchat`
Starts a new chat session, clearing the history of any previous conversations or uploaded files.

**Example:**
```bash
curl -X POST http://127.0.0.1:5000/gemini/newchat
```

#### `POST /gemini/uploadfile`
Uploads a single file to the current chat session.

**Example:**
```bash
curl -X POST -F "file=@/path/to/your/file.png" http://127.0.0.1:5000/gemini/uploadfile
```

#### `POST /gemini/uploadfolder`
Uploads all files in a folder (and its subfolders) that have the allowed extensions.

**Request Body (JSON):**
```json
{
  "folder": "/path/to/your/folder",
  "allowed_extensions": [".json", ".png", ".mp4"]
}
```

**Example:**
```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"folder": "recorder/output", "allowed_extensions": [".json", ".png", ".mp4"]}' \
     http://127.0.0.1:5000/gemini/uploadfolder
```

#### `POST /gemini/sendmessage`
Sends a message (and any uploaded files) to the Gemini model and returns the response.

**Request Body (JSON):**
```json
{
  "message": "Generate a python script based on the recording."
}
```

**Example:**
```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"message": "Generate a python script based on the recording."}' \
     http://127.0.0.1:5000/gemini/sendmessage
```

## UIA Dumper (`uia_dumper.py`)

A tool to dump the UI Automation (UIA) tree of a running application to a JSON file. This is useful for inspecting the UI hierarchy and element properties.

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

This tool records user interactions (mouse clicks, key presses) with an application and saves them as a sequence of events in a JSON file, along with screenshots of the interacted elements.

### Usage
```bash
python -m tools.recorder -p myapp.exe anotherapp.exe
```
- `-p, --process_names`: (Optional) Filter recording by one or more process names.

Press `Alt+Shift+R` to start/stop recording. Press `Esc` to exit the tool.

## Player (`player/`)

This tool plays back a recorded scenario, which consists of one or more test cases. It reads a JSON scenario file and executes the defined tests.

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
