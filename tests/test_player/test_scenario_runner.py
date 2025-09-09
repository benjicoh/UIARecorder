import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

import unittest
from unittest.mock import patch, MagicMock, mock_open
import json


# Mock the Player class
MOCK_MODULES = {
    'player.main_player': MagicMock(),
    'player.logger': MagicMock(),
}

@patch.dict('sys.modules', MOCK_MODULES)
class TestScenarioRunner(unittest.TestCase):

    def setUp(self):
        self.patcher = patch.dict('sys.modules', MOCK_MODULES)
        self.patcher.start()

        if 'tools.player.scenario_runner' in sys.modules:
            del sys.modules['tools.player.scenario_runner']

        from tools.player.scenario_runner import ScenarioRunner
        global ScenarioRunner

        self.mock_player_class = sys.modules['player.main_player'].Player
        self.mock_player_instance = self.mock_player_class.return_value

        self.mock_player_class.reset_mock()
        self.mock_player_instance.reset_mock()

    def tearDown(self):
        self.patcher.stop()

    @patch('os.makedirs')
    def test_run_single_test_case(self, mock_makedirs):
        # Arrange
        scenario_data = {
            "name": "Test Scenario",
            "test_cases": [{"name": "My Test", "script": "path/to/test.py"}]
        }
        scenario_json = json.dumps(scenario_data)

        with patch('builtins.open', mock_open(read_data=scenario_json)):
            runner = ScenarioRunner('fake_scenario.json', 'output_folder')
            runner.run()

        # Assert
        self.mock_player_class.assert_called_once()
        args, kwargs = self.mock_player_class.call_args
        self.assertEqual(kwargs['script_path'], 'path/to/test.py')
        self.mock_player_instance.run.assert_called_once()

    @patch('os.makedirs')
    @patch('os.path.exists', return_value=True)
    def test_run_with_csv_data(self, mock_exists, mock_makedirs):
        # Arrange
        scenario_data = {
            "name": "CSV Scenario", "csv_data": "data.csv",
            "test_cases": [{
                "name": "My Test", "script": "path/to/test.py",
                "variables": {"username": "$user", "password": "$pwd"}
            }]
        }
        scenario_json = json.dumps(scenario_data)
        csv_content = "user,pwd\njohn,123\njane,456"

        # This side effect function will return the right content for each file
        def open_side_effect(path, mode='r'):
            if 'scenario.json' in path:
                return mock_open(read_data=scenario_json).return_value
            if 'data.csv' in path:
                return mock_open(read_data=csv_content).return_value
            return mock_open().return_value

        with patch('builtins.open', side_effect=open_side_effect):
            # The runner's __init__ opens the scenario file to get the name
            runner = ScenarioRunner('fake_scenario.json', 'output_folder')
            # The run method opens it again
            runner.run()

        # Assert
        self.assertEqual(self.mock_player_class.call_count, 2)
        self.assertEqual(self.mock_player_instance.run.call_count, 2)

        args, kwargs = self.mock_player_class.call_args
        self.assertEqual(kwargs['variables']['username'], 'jane')
        self.assertEqual(kwargs['variables']['password'], '456')


if __name__ == '__main__':
    unittest.main()
