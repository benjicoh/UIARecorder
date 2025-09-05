# Tools

This directory contains various tools for UI automation, recording, and playback.

## UIA Dumper (`uia_dumper.py`)

A tool to dump the UI Automation (UIA) tree of a running application to a JSON file. This is useful for inspecting the UI hierarchy and element properties.

### Usage
```bash
python tools/uia_dumper.py --window "My Window Title" --output dump.json
python tools/uia_dumper.py --process "my_process.exe" --output dump.json
```

## Recorder (`recorder/`)

This tool records user interactions (mouse clicks, key presses) with an application and saves them as a sequence of events in a JSON file, along with screenshots of the interacted elements.

### Usage
The main entry point is `recorder.py` in the root directory.

## Player (`player/`)

This tool plays back a recorded scenario, which consists of one or more test cases. It reads a JSON scenario file and executes the defined tests.

### Usage
The main entry point is `player.py` in the root directory.
