import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

import unittest
from unittest.mock import patch, MagicMock


# Mock the recorder dependency
MOCK_MODULES = {
    'tools.recorder.media': MagicMock(),
}

# Dummy BaseTestCase for tests to use
from tools.player.test_case import BaseTestCase

@patch.dict('sys.modules', MOCK_MODULES)
class TestMainPlayer(unittest.TestCase):

    def setUp(self):
        self.patcher = patch.dict('sys.modules', MOCK_MODULES)
        self.patcher.start()

        if 'tools.player.main_player' in sys.modules:
            del sys.modules['tools.player.main_player']

        from tools.player.main_player import Player
        global Player

        # Create a dummy test script file for loading
        self.script_path = 'dummy_test_script.py'
        with open(self.script_path, 'w') as f:
            f.write("""
from tools.player.test_case import BaseTestCase
class TestCase(BaseTestCase):
    def run(self):
        print("Running the dummy test")
""")

    def tearDown(self):
        self.patcher.stop()
        if os.path.exists(self.script_path):
            os.remove(self.script_path)

    @patch('os.makedirs')
    def test_load_test_case_success(self, mock_makedirs):
        # Arrange
        player = Player(self.script_path, 'output', record_video=False)

        # Act
        test_case_instance = player._load_test_case()

        # Assert
        self.assertIsNotNone(test_case_instance)
        self.assertTrue(isinstance(test_case_instance, BaseTestCase))

    @patch('os.makedirs')
    def test_load_test_case_not_found(self, mock_makedirs):
        # Arrange
        player = Player('non_existent_script.py', 'output', record_video=False)

        # Assert
        with self.assertRaises(FileNotFoundError):
            player._load_test_case()


    @patch('os.makedirs')
    def test_run_executes_sequence(self, mock_makedirs):
        # Arrange
        player = Player(self.script_path, 'output', record_video=False)

        mock_test_case = MagicMock()

        with patch.object(player, '_load_test_case', return_value=mock_test_case) as mock_load:
            # Act
            player.run()

            # Assert
            mock_load.assert_called_once()
            mock_test_case.setup.assert_called_once()
            mock_test_case.run.assert_called_once()
            mock_test_case.teardown.assert_called_once()


if __name__ == '__main__':
    unittest.main()
