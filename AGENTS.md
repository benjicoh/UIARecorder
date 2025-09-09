# Agent Instructions

This document provides instructions for agents working with this codebase.

## Gemini API

This project uses the new Google AI for Python SDK (`google-genai`). When working with the Gemini API, please refer to the following documentation:

*   **Files API**: https://ai.google.dev/gemini-api/docs/files
*   **Text Generation**: https://ai.google.dev/gemini-api/docs/text-generation
*   **Structured Output**: https://ai.google.dev/gemini-api/docs/structured-output
*   **Video Understanding**: https://ai.google.dev/gemini-api/docs/video-understanding

Please ensure that all code interacting with the Gemini API is up-to-date with the latest SDK version and follows the best practices outlined in the documentation.

The model currently in use is `gemini-2.5-pro`.

## Windows-only Dependencies

Please be aware that this project uses the `uiautomation` library, which is only compatible with the Windows operating system. The tools that depend on this library, such as `uia_dumper`, cannot be tested or run in a Linux environment. When working on these tools, please ensure you are on a Windows machine for testing.
