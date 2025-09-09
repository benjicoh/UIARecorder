import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the uiautomation library before it is imported
sys.modules['uiautomation'] = MagicMock()

from tools.agent.runner import run_agent

class TestAgent(unittest.TestCase):

    @patch('tools.agent.main.dump_uia_tree')
    @patch('tools.agent.main.send_message_to_gemini')
    @patch('tools.agent.main.run_python_script')
    def test_agent_workflow(self, mock_run_script, mock_send_message, mock_dump_ui):
        # --- Mock setup ---

        # 1. Mock Gemini's response to generate the initial script
        mock_send_message.return_value = '{"code": "print(\'hello\')"}'

        # 2. Mock the script execution
        #    - First time it fails
        #    - Second time it succeeds
        mock_run_script.side_effect = [
            "Error: something went wrong",
            "hello"
        ]

        # 3. Mock the UI dumper
        mock_dump_ui.return_value = "UI dumped successfully"

        # --- Run the agent ---

        initial_prompt = "Start by generating a script from the recording at 'tools/recorder/output'."
        run_agent(initial_prompt)

        # --- Assertions ---

        # Check that Gemini was called to generate the initial script
        mock_send_message.assert_any_call("Generate a python script based on the recording.")

        # Check that the script was run twice
        self.assertEqual(mock_run_script.call_count, 2)

        # Check that the UI was dumped once
        mock_dump_ui.assert_called_once()

        # Check that Gemini was called to refine the script
        mock_send_message.assert_any_call("The script failed. Here is the UI dump and the log. Please refine the script.")

if __name__ == '__main__':
    unittest.main()
