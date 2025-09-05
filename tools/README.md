# Tools

This directory contains various tools for UI automation, recording, and playback. It is structured as a Python package to allow for shared modules.

## Ask Gemini (`ask_gemini.py`)

A tool that uses Google's Gemini Pro LLM to generate a Python test script from a folder of UIA recording files (JSON, screenshots, video). It uploads relevant files, sends them to Gemini, and saves the generated script.

### Usage
```bash
python -m tools.ask_gemini -r recorder/output -o my_script.py
```
- `-r, --recording_folder`: Path to the folder containing recording files (JSON, PNG, MP4).
- `-o, --output_file`: (Optional) Path to save the generated script. Default is `../user_scripts/test_scenario.py`.

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
