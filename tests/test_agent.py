import unittest
from unittest.mock import patch, MagicMock, ANY
import sys
import os
import subprocess

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Mock the uiautomation library before it is imported
sys.modules['uiautomation'] = MagicMock()

from tools.agent.runner import run_agent
from tools.agent.main import CodeResponse

class TestAgent(unittest.TestCase):

    @patch('tools.agent.main.client')
    @patch('tools.agent.main.configure_gemini')
    @patch('tools.uia_dumper.dump_uia_tree')
    @patch('subprocess.run')
    @patch('builtins.open')
    def test_agent_workflow(self, mock_open, mock_subprocess_run, mock_dump_ui, mock_configure_gemini, mock_client):
        # --- Mock setup ---

        # Mock the Gemini client and chat session
        mock_chat_session = MagicMock()
        mock_client.chats.create.return_value = mock_chat_session

        # 1. Mock Gemini's response to generate the initial script
        mock_response = MagicMock()
        mock_response.text = CodeResponse(code="print('hello')")
        mock_chat_session.send_message.return_value = mock_response

        # 2. Mock the script execution
        #    - First time it fails
        #    - Second time it succeeds
        mock_subprocess_run.side_effect = [
            subprocess.CalledProcessError(1, "cmd", stderr="Error: something went wrong"),
            MagicMock(stdout="hello", returncode=0)
        ]

        # 3. Mock the UI dumper
        mock_dump_ui.return_value = "UI dumped successfully"

        # 4. Mock file operations
        mock_open.return_value = MagicMock()

        # --- Run the agent ---
        initial_prompt = (
            "Please generate a python script based on the recording in 'tools/recorder/output'. "
            "The recording consists of a video file and a JSON file with UI events. "
            "First, upload the contents of the 'tools/recorder/output' folder with .mp4 and .json extensions, then generate the script."
        )
        run_agent(initial_prompt)

        # --- Assertions ---

        # Check that gemini is configured
        mock_configure_gemini.assert_called_once()

        # Check that a chat session was created
        mock_client.chats.create.assert_called_once()

        # Check that the message was sent to Gemini
        mock_chat_session.send_message.assert_called_once()

        # Check that the script was written
        mock_open.assert_any_call("output.py", "w")

        # Check that the script was run
        self.assertGreaterEqual(mock_subprocess_run.call_count, 1)

if __name__ == '__main__':
    unittest.main()
