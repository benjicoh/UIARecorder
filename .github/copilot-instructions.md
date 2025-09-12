# Copilot Instructions for the UI Automation Project

## Project Overview
This codebase is a Windows-only UI automation platform for recording, playing back, and generating test scripts for desktop applications.
- **`agent/`**: Contains the AI agent that uses the Gemini API to generate Python automation scripts from recordings.
- **`tools/`**: Contains the core tools for recording and playing back UI interactions.
  - **`tools/recorder/`**: Captures user interactions (mouse, keyboard), screen video, and UI element data.
  - **`tools/player/`**: Executes test scripts and scenarios.
- **`tools/common/`**: Shared utilities for logging and UI automation.

## Key Workflows & Commands

- **Record User Interactions**: Use `tools/recorder_tool.py` to capture a user session.
  ```bash
  python -m tools.recorder_tool -wh "process_name.exe"
  ```
  - Press `Alt+Shift+R` to start/stop recording. Press `Esc` to exit.
  - Output is saved to `recorder/output/`.

- **Play Back a Test**: Use `tools/player_tool.py` to run a test script or a scenario.
  ```bash
  # Run a single script
  python -m tools.player_tool -s path/to/test_script.py

  # Run a scenario
  python -m tools.player_tool -sc path/to/scenario.json
  ```

- **Generate a Script with the Agent**: Use `agent/gemini_flow.py` to generate a script from a recording.
  ```bash
  python -m agent.gemini_flow "path/to/recording_directory" -p "process_name.exe"
  ```

- **Dump UI Automation Tree**: Use `agent/uia_dumper.py` to inspect the UI of an application.
  ```bash
  python -m agent.uia_dumper -w "Window Title" -o dump.json
  ```

## Conventions & Patterns
- **Test Cases**: All test scripts must contain a class `TestCase` that inherits from `tools.player.test_case.BaseTestCase`.
- **Logging**: Use the provided `self.logger` instance within test cases for standardized logging.
- **Windows-Only**: The project relies on the `uiautomation` library and is only compatible with Windows.
- **Gemini API**: The agent uses the `google-genai` SDK to interact with the Gemini API. The model in use is `gemini-2.5-flash`.
- **Data Flow**: The recorder produces data that is used by the agent to generate scripts. These scripts are then executed by the player.

## Important Files
- **`AGENTS.md`**: Provides high-level instructions for AI agents working with this codebase.
- **`tools/README.md`**: The main README for the tools, with detailed usage instructions.
- **`tools/player/README.md`**: Explains how to create test cases and scenarios for the player.
- **`tools/player/example/`**: Contains example scripts and scenarios.

---
**Feedback requested:** Are any workflows, conventions, or integration points unclear or missing? Please specify areas needing more detail or examples.