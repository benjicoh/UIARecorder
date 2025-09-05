# Tools

This directory contains various tools for UI automation, recording, and playback.

## Ask Gemini (`ask_gemini.py`)

A tool that uses Google Gemini 2.5 Pro LLM to generate a Python test script from a folder of UIA recording files (JSON, screenshots, video). It uploads relevant files, sends them to Gemini, and saves the generated script.

### Usage
```powershell
python tools/ask_gemini.py recorder/output --output_file my_script.py
```
- `recording_folder`: Path to the folder containing recording files (JSON, PNG, MP4).
- `--output_file`: (Optional) Path to save the generated script. Default is `../user_scripts/test_scenario.py`.

## UIA Dumper (`uia_dumper.py`)

A tool to dump the UI Automation (UIA) tree of a running application to a JSON file. This is useful for inspecting the UI hierarchy and element properties.

### Usage
```bash
python tools/uia_dumper.py --window "My Window Title" --output dump.json
python tools/uia_dumper.py --process "my_process.exe" --output dump.json
```

## Recorder (`recorder.py`)

This tool records user interactions (mouse clicks, key presses) with an application and saves them as a sequence of events in a JSON file, along with screenshots of the interacted elements. The user should run this tool directly to start and stop recording.

### Usage
```powershell
python tools/recorder.py --process_names myapp.exe anotherapp.exe
```
- `--process_names`: (Optional) Filter recording by one or more process names.

Press `Alt+Shift+R` to start/stop recording. Press `Esc` to exit the tool.

## Player (`player/`)

This tool plays back a recorded scenario, which consists of one or more test cases. It reads a JSON scenario file and executes the defined tests.

### Usage
The main entry point is `player.py` in the root directory.
