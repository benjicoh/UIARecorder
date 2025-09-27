# AI-Powered C# UI Automation Generator

This tool lets a user record their interactions on Windows and uses a Large Language Model (LLM) to automatically generate a C# UI automation project using the FlaUI library and Page Object Model (POM) to try and replicate the user's actions in a robust automation script.

## How to Install

1.  **Clone the repository:**
    ```powershell
    git clone <repository-url>
    cd <repository-folder>
    ```
2.  **Install Python dependencies:**
    It is recommended to use a virtual environment.
    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r pyproject.toml
    ```
3.  **Set up your Gemini API Key:**
    This project uses the Google Gemini API to generate code. You need to provide your API key as an environment variable named `GEMINI_API_KEY`.
    ```powershell
    $env:GEMINI_API_KEY = "YOUR_API_KEY"
    ```
    **Note:** This sets the environment variable for the current session only. For a permanent solution, you can set it in your system's environment variables.

## How to Run (Using PowerShell)

**Note:** Running the automation scripts requires administrator privileges.

1.  **Open PowerShell as Administrator.**
2.  **First, record UI interactions:**
    The `Record.ps1` script starts a recorder. Use the hotkey `Alt+Shift+R` to start and stop recording. The recorded actions will be saved in the `generated_scripts/user_recording` directory.
    ```powershell
    .\Record.ps1 -ProcessName notepad.exe
    ```
3.  **Then, generate the C# automation project:**
    The `Generate.ps1` script takes the recorded data, sends it to an AI model, and generates a C# project.
    ```powershell
    .\Generate.ps1 -Folder generated_scripts\user_recording -ProcessName notepad.exe
    ```
    The generated project will be located in a timestamped folder inside `generated_scripts`.

## Developer Notes

### AI Prompt

The prompt used to instruct the AI model is located in [flaui_prompt.md](agent/flaui_prompt.md). You can modify this file to change the instructions given to the AI for generating the C# code.

### C# Template Project

The C# project is generated from a template located in `fla-ui/TemplateTest`. This template can be customized to change the structure of the generated projects.

### Workflow

The end-to-end workflow is as follows:
1.  The `Record.ps1` script runs `tools/recorder_tool.py` to capture UI events, screen recording video, and narration.
2.  The `Generate.ps1` script runs `agent/flaui_flow.py`.
3.  [flaui_flow.py](agent/flaui_flow.py) reads the recorded data, combines it with the C# template from `fla-ui/TemplateTest` and the prompt for the [flaui_prompt.md](agent/flaui_prompt.md)
4.  This information is sent to the Gemini AI, which generates the C# code for the UI automation.
5.  The script then attempts to compile and run the generated C# project, with a retry mechanism that uses the AI to fix compilation or runtime errors.