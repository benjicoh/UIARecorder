import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import json
import builtins
import sys

# Add the parent directory to sys.path for module resolution
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock google.genai and its components
MOCK_MODULES = {
    'google.genai': MagicMock(),
    'google.genai.types': MagicMock(),
}

@patch.dict('sys.modules', MOCK_MODULES)
class TestAskGemini(unittest.TestCase):

    def setUp(self):
        # This has to be done before the import
        self.patcher = patch.dict('sys.modules', MOCK_MODULES)
        self.patcher.start()

        global ask_gemini
        from tools.ask_gemini import ask_gemini
        
        self.mock_genai = sys.modules['google.genai']
        self.mock_genai_types = sys.modules['google.genai.types']
        self.mock_genai.reset_mock()
        self.mock_genai_types.reset_mock()

        self.mock_client = self.mock_genai.GenerativeModel.return_value
        self.mock_response = self.mock_client.generate_content.return_value
        self.mock_response.text = json.dumps({"code": "print('Hello, World!')"})

        # Make the mock file have a state that can be updated
        self.mock_uploaded_file = MagicMock()
        self.mock_uploaded_file.name = 'uploaded_file_name'
        self.mock_uploaded_file.display_name = 'test.png' # Set a real string here
        self.mock_uploaded_file.state = MagicMock()
        self.mock_uploaded_file.state.name = 'PROCESSING'

        def upload_side_effect(*args, **kwargs):
            return self.mock_uploaded_file

        def get_file_side_effect(*args, **kwargs):
            self.mock_uploaded_file.state.name = 'ACTIVE'
            return self.mock_uploaded_file

        self.mock_genai.upload_file.side_effect = upload_side_effect
        self.mock_genai.get_file.side_effect = get_file_side_effect

    def tearDown(self):
        self.patcher.stop()

    @patch('os.environ.get', return_value='fake_api_key')
    @patch('os.path.exists')
    @patch('os.walk')
    @patch('builtins.open', new_callable=mock_open)
    @patch('time.sleep', return_value=None)
    def test_ask_gemini_success(self, mock_sleep, mock_open_func, mock_walk, mock_path_exists, mock_env_get):
        # Arrange
        mock_walk.return_value = [
            ('/fake_dir', [], ['test.png', 'data.json']),
        ]

        def path_exists_side_effect(path):
            if 'gemini_uploads.json' in path or 'recording_to_script.md' in path:
                return True
            return False
        mock_path_exists.side_effect = path_exists_side_effect

        def open_side_effect(file_path, mode='r', **kwargs):
            if 'gemini_uploads.json' in file_path and mode == 'r':
                return mock_open(read_data='{}').return_value
            if 'recording_to_script.md' in file_path:
                return mock_open(read_data='prompt').return_value
            if 'data.json' in file_path:
                 return mock_open(read_data='{"key": "value"}').return_value
            return mock_open().return_value

        mock_open_func.side_effect = open_side_effect

        # Act
        output_file = ask_gemini('fake_dir', 'output.py')

        # Assert
        self.mock_genai.configure.assert_called_once_with(api_key='fake_api_key')
        self.mock_client.generate_content.assert_called_once()
        self.assertEqual(output_file, 'output.py')


    @patch('os.environ.get', return_value=None)
    def test_ask_gemini_no_api_key(self, mock_env_get):
        with self.assertRaises(ValueError):
            ask_gemini('any_dir')


    @patch('os.environ.get', return_value='fake_api_key')
    @patch('os.path.exists', return_value=False)
    @patch('os.walk', return_value=[])
    @patch('builtins.open', new_callable=mock_open)
    def test_ask_gemini_no_files_found(self, mock_open_func, mock_walk, mock_path_exists, mock_env_get):
        mock_open_func.side_effect = [
            mock_open(read_data='{}').return_value,
            mock_open(read_data='prompt').return_value
        ]
        with self.assertRaises(FileNotFoundError):
            ask_gemini('empty_dir')


if __name__ == '__main__':
    unittest.main()
