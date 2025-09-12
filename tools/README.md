# Tools

This directory contains various tools for UI automation, including recording user actions, playing back test scenarios, and an AI agent for script generation.

## Recorder (`recorder_tool.py`)

This tool records user interactions (mouse clicks, key presses) with an application. It generates a video of the session, a JSON file containing a detailed log of events, and screenshots of the UI elements the user interacted with.

### Usage
To run the recorder, use the following command. You can optionally provide a whitelist of process names to filter which applications are recorded.

```bash
python -m tools.recorder_tool -wh "my_app.exe" "another_app.exe"
```

- `-wh, --whitelist`: (Optional) Filter recording by one or more process names.

Press `Alt+Shift+R` to start and stop the recording. Press `Esc` to exit the tool. The output will be saved in the `recorder/output` directory by default.

## Player (`player_tool.py`)

This tool plays back automated test scripts and scenarios.

### Usage
You can run a single test script or a full scenario defined in a JSON file.

```bash
# Run a single test script
python -m tools.player_tool -s path/to/your/test_script.py

# Run a scenario
python -m tools.player_tool -sc path/to/your/scenario.json
```
- `-s, --script`: Path to the test script to run.
- `-sc, --scenario`: Path to the scenario JSON to run.
- `-o, --output`: Path to the output folder (defaults to `output`).
- `-nv, --no-video`: Disable video recording.

For details on how to structure a test script or a scenario file, see the [Player README](player/README.md).

## Agent (`agent/`)

The agent is a more advanced tool that uses the Gemini large language model to automatically generate Python test scripts from recordings.

It takes a directory of recording files (JSON annotations, video, screenshots) and uses them to generate a script. If the generated script fails, the agent can use a dump of the application's current UI state to refine the script and try again.

The main entry point for the agent is `agent/gemini_flow.py`.

### Usage
```bash
python -m agent.gemini_flow "path/to/recording_directory" -p "my_process.exe"
```
- `recording_dir`: Path to the directory containing the recording files.
- `-p, --process-name`: The process name of the target application.
- `-w, --window-title`: The window title of the target application.

## UIA Dumper (`agent/uia_dumper.py`)

A utility to dump the UI Automation (UIA) tree of a running application to a JSON file. This is useful for inspecting the UI hierarchy and element properties.

### Usage
```bash
# Dump UI tree for a window
python -m agent.uia_dumper -w "My Window Title" -o dump.json

# Dump UI tree for a process and capture screenshots
python -m agent.uia_dumper -p "my_process.exe" -o dump.json -s
```
- `-p, --process`: Process name to dump the UI tree for.
- `-w, --window`: Top-level window title to dump the UI tree for.
- `-o, --output`: Path to the output JSON file.
- `-s, --screenshots`: (Optional) Enable capturing screenshots of UI elements.
- `-wh, --whitelist`: (Optional) Filter: Only include elements from these process names.

## Common (`common/`)
This directory contains shared modules used by the other tools, such as the `uia.py` module for common UI Automation functions and a shared `logger.py`.
