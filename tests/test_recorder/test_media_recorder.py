import unittest
from unittest.mock import patch, MagicMock
import sys

# Mock all the hardware/ffmpeg dependencies
MOCK_MODULES = {
    'pyautogui': MagicMock(),
    'cv2': MagicMock(),
    'sounddevice': MagicMock(),
    'numpy': MagicMock(),
    'scipy.io.wavfile': MagicMock(),
    'subprocess': MagicMock(),
}

@patch.dict('sys.modules', MOCK_MODULES)
class TestMediaRecorder(unittest.TestCase):

    def setUp(self):
        self.patcher = patch.dict('sys.modules', MOCK_MODULES)
        self.patcher.start()

        from tools.recorder.media import MediaRecorder
        global MediaRecorder

        self.mock_pyautogui = sys.modules['pyautogui']
        self.mock_cv2 = sys.modules['cv2']
        self.mock_sd = sys.modules['sounddevice']
        self.mock_subprocess = sys.modules['subprocess']

    def tearDown(self):
        self.patcher.stop()

    @patch('threading.Thread')
    def test_start(self, mock_thread):
        # Arrange
        recorder = MediaRecorder('output')

        # Act
        recorder.start()

        # Assert
        self.assertEqual(mock_thread.call_count, 2) # Video and Audio threads
        # Check that the threads were started
        self.assertEqual(mock_thread.return_value.start.call_count, 2)

    @patch('os.path.exists', return_value=True)
    @patch('os.remove')
    def test_stop_with_audio(self, mock_remove, mock_exists):
        # Arrange
        recorder = MediaRecorder('output', record_audio=True)
        recorder.video_writer = MagicMock()
        recorder.audio_frames = [1, 2, 3] # Some dummy audio frames

        # Act
        recorder.stop()

        # Assert
        recorder.video_writer.release.assert_called_once()
        # Check that ffmpeg was called to combine the files
        self.mock_subprocess.run.assert_called_once()
        cmd_args = self.mock_subprocess.run.call_args[0][0]
        cmd_str = " ".join(cmd_args)
        self.assertIn('ffmpeg', cmd_str)
        self.assertIn('temp_video.avi', cmd_str)
        self.assertIn('temp_audio.wav', cmd_str)
        self.assertIn('video.mp4', cmd_str)

        # Check that temp files were removed
        self.assertEqual(mock_remove.call_count, 2)


if __name__ == '__main__':
    unittest.main()
