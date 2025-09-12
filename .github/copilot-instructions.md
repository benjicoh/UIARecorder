# Copilot Instructions for UIARecorder (Win32UICrawlerMcp)

## Project Overview
- This codebase is a Windows-only UI automation platform for recording, playing back, and analyzing user interactions with desktop applications.
- Major components:
  - `agent/`: Orchestrates flows, integrates Gemini AI, and manages agent logic.
  - `tools/`: Core automation tools, including UIA tree dumping, event recording, and playback.
  - `tools/player/`: Scenario runner and test case framework for automated UI testing.
  - `tools/recorder/`: Captures user events and screenshots, outputs annotated data.

## Key Workflows
- **Run MCP Server**: Exposes all tools via HTTP API. Start with:
  ```powershell
  $env:GEMINI_API_KEY="YOUR_API_KEY"; python -m tools.mcp_server
  ```
- **Dump UI Automation Tree**: Use `tools/uia_dumper.py` to export UI hierarchy and screenshots:
  ```powershell
  python -m tools.uia_dumper -w "Window Title" -o dump.json
  python -m tools.uia_dumper -p "process.exe" -o dump.json -s
  ```
- **Record User Interactions**: Use `tools/recorder/` to capture events and screenshots:
  ```powershell
  python -m tools.recorder -p process.exe
  ```
- **Play Back Scenarios**: Write test cases in `tools/player/` using the `BaseTestCase` pattern:
  ```python
  from tools.player.test_case import BaseTestCase
  class TestCase(BaseTestCase):
      def setup(self): pass
      def run(self): pass
      def teardown(self): pass
  ```
  - Use `self.logger` for structured logging in tests.

## Conventions & Patterns
- All test cases must subclass `BaseTestCase` and implement `run(self)`.
- Logging is standardized via `self.logger` (console + file output).
- Windows-only: The `uiautomation` dependency and related tools require Windows for development and testing.
- Gemini API integration uses `google-genai` (see [Gemini API docs](https://ai.google.dev/gemini-api/docs)).
- Data files (JSON, screenshots, video) are stored in `tools/recorder/output/` and referenced in player scenarios.

## Integration Points
- MCP server exposes tools as HTTP endpoints for automation and AI workflows.
- Gemini tools support file/folder upload, chat, and code generation for UI test scripts.
- UIA tree and event data are used to generate and validate automated test scenarios.

## Examples
- See `tools/player/example/` for sample scenarios and test scripts.
- Refer to `tools/README.md` and `AGENTS.md` for tool usage and agent-specific instructions.

---

**Feedback requested:** Are any workflows, conventions, or integration points unclear or missing? Please specify areas needing more detail or examples.