import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os

# Mock all the dependencies of the recorder
MOCK_MODULES = {
    'psutil': MagicMock(),
    'pynput': MagicMock(),
    'tools.recorder.element_screenshotter': MagicMock(),
    'tools.recorder.events': MagicMock(),
    'tools.recorder.media': MagicMock(),
    'tools.recorder.uia': MagicMock(),
}

@patch.dict('sys.modules', MOCK_MODULES)
class TestMainRecorder(unittest.TestCase):

    def setUp(self):
        self.patcher = patch.dict('sys.modules', MOCK_MODULES)
        self.patcher.start()

        if 'tools.recorder.main_recorder' in sys.modules:
            del sys.modules['tools.recorder.main_recorder']

        from tools.recorder.main_recorder import Recorder
        global Recorder

        self.mock_element_screenshotter = sys.modules['tools.recorder.element_screenshotter'].ElementScreenshotter
        self.mock_media_recorder = sys.modules['tools.recorder.media'].MediaRecorder
        self.mock_uia_helper = sys.modules['tools.recorder.uia'].UIAHelper
        self.mock_input_listener = sys.modules['tools.recorder.events'].InputListener

    def tearDown(self):
        self.patcher.stop()

    @patch('shutil.rmtree')
    @patch('os.makedirs')
    def test_start_and_stop(self, mock_makedirs, mock_rmtree):
        # Arrange
        recorder = Recorder()

        # Act
        recorder.start()

        # Assert
        self.assertTrue(recorder.is_recording)
        self.mock_media_recorder.return_value.start.assert_called_once()
        self.mock_uia_helper.return_value.start_highlighting.assert_called_once()
        self.mock_input_listener.return_value.start.assert_called_once()

        # Act
        with patch('builtins.open', mock_open()) as mock_file:
            recorder.stop()

        # Assert
        self.assertFalse(recorder.is_recording)
        self.mock_media_recorder.return_value.stop.assert_called_once()
        self.mock_uia_helper.return_value.stop_highlighting.assert_called_once()
        self.mock_input_listener.return_value.stop.assert_called_once()
        mock_file.assert_called_once_with('recorder/output/annotations.json', 'w')


    @patch('time.time', side_effect=[100.0, 101.0]) # Mock timestamps
    def test_handle_click(self, mock_time):
        # Arrange
        recorder = Recorder()
        recorder.start_time = 100.0 # Set a start time for timestamp calculation

        mock_element = MagicMock()
        recorder.uia_helper.get_element_from_point.return_value = mock_element
        recorder.uia_helper.get_element_hierarchy.return_value = [{'id': 'elem1'}]

        # Mock the internal _get_process_name to return a valid process
        recorder._get_process_name = MagicMock(return_value='test_process.exe')

        # Act
        with patch.object(recorder, '_log_annotation') as mock_log:
            recorder._handle_click(10, 20, 'Button.left', True)

            # Assert
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            self.assertEqual(args[0], "mouse_click")
            self.assertEqual(args[1]['x'], 10)
            self.assertEqual(args[2][0]['id'], 'elem1')

if __name__ == '__main__':
    unittest.main()
