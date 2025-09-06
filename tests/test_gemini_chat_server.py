import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import json
import io
import sys

# Add the parent directory to sys.path for module resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock google.genai and its components before importing the server
MOCK_MODULES = {
    'google.genai': MagicMock(),
}

@patch.dict('sys.modules', MOCK_MODULES)
class TestGeminiChatServer(unittest.TestCase):

    def setUp(self):
        # This has to be done before the import
        self.patcher = patch.dict('sys.modules', MOCK_MODULES)
        self.patcher.start()

        global app, configure_gemini
        from tools.gemini_chat_server import app, configure_gemini

        self.mock_genai = sys.modules['google.genai']
        self.mock_genai.reset_mock()

        # Configure mocks
        self.mock_client = self.mock_genai.Client.return_value
        self.mock_chat = self.mock_client.chats.create.return_value
        self.mock_chat.send_message.return_value.text = "Test response"

        self.mock_uploaded_file = MagicMock()
        self.mock_uploaded_file.name = 'uploaded_file_name'
        self.mock_uploaded_file.uri = 'file_uri'
        self.mock_uploaded_file.state = MagicMock()
        self.mock_uploaded_file.state.name = 'ACTIVE'
        self.mock_client.files.upload.return_value = self.mock_uploaded_file
        self.mock_client.files.get.return_value = self.mock_uploaded_file

        os.environ['GEMINI_API_KEY'] = 'test-api-key'

        # We need to mock open for the system prompt
        with patch('builtins.open', mock_open(read_data='system prompt')):
            configure_gemini()

        app.config['TESTING'] = True
        self.client_app = app.test_client()

    def tearDown(self):
        self.patcher.stop()
        if 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']

    @patch('builtins.open', new_callable=mock_open, read_data='system prompt')
    def test_new_chat(self, mock_file):
        response = self.client_app.post('/gemini/newchat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {"message": "New chat session started."})
        self.mock_client.chats.create.assert_called_once()

    @patch('tempfile.NamedTemporaryFile')
    @patch('os.unlink')
    def test_upload_file_success(self, mock_unlink, mock_tempfile):
        # Mock the temporary file creation
        mock_temp_file = MagicMock()
        mock_temp_file.name = "temp_file_path"
        mock_tempfile.return_value.__enter__.return_value = mock_temp_file

        # Create a mock file object
        data = (io.BytesIO(b"file content"), 'test.png')

        # First, start a new chat
        self.client_app.post('/gemini/newchat')

        response = self.client_app.post(
            '/gemini/uploadfile',
            content_type='multipart/form-data',
            data={'file': data}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("File 'test.png' uploaded successfully.", json.loads(response.data)['message'])
        self.mock_client.files.upload.assert_called_once()

    def test_send_message_success(self):
        # First, start a new chat
        self.client_app.post('/gemini/newchat')

        response = self.client_app.post(
            '/gemini/sendmessage',
            content_type='application/json',
            data=json.dumps({"message": "Hello, Gemini!"})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {"response": "Test response"})
        self.mock_chat.send_message.assert_called_once_with(content=["Hello, Gemini!"])

    def test_send_message_no_chat(self):
        response = self.client_app.post(
            '/gemini/sendmessage',
            content_type='application/json',
            data=json.dumps({"message": "Hello, Gemini!"})
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("No active chat session", json.loads(response.data)['error'])

if __name__ == '__main__':
    unittest.main()
