import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

import unittest
from unittest.mock import patch, MagicMock

# Mock the pynput dependency
MOCK_MODULES = {
    'pynput': MagicMock(),
}

@patch.dict('sys.modules', MOCK_MODULES)
class TestInputListener(unittest.TestCase):

    def setUp(self):
        self.patcher = patch.dict('sys.modules', MOCK_MODULES)
        self.patcher.start()

        from tools.recorder.events import InputListener
        global InputListener

        self.mock_pynput = sys.modules['pynput']
        self.mock_keyboard_listener = self.mock_pynput.keyboard.Listener
        self.mock_mouse_listener = self.mock_pynput.mouse.Listener

    def tearDown(self):
        self.patcher.stop()

    def test_start_and_stop(self):
        # Arrange
        listener = InputListener(None, None, None)

        # Act
        listener.start()

        # Assert
        self.mock_keyboard_listener.assert_called_once()
        self.mock_mouse_listener.assert_called_once()
        listener.keyboard_listener.start.assert_called_once()
        listener.mouse_listener.start.assert_called_once()

        # Act
        listener.stop()

        # Assert
        listener.keyboard_listener.stop.assert_called_once()
        listener.mouse_listener.stop.assert_called_once()

    def test_callbacks(self):
        # Arrange
        mock_press_cb = MagicMock()
        mock_click_cb = MagicMock()
        mock_release_cb = MagicMock()

        listener = InputListener(
            on_press_callback=mock_press_cb,
            on_click_callback=mock_click_cb,
            on_release_callback=mock_release_cb
        )

        # Act
        listener._on_press('key_a')
        listener._on_click(1, 2, 'btn', True)
        listener._on_release('key_b')

        # Assert
        mock_press_cb.assert_called_once_with('key_a')
        mock_click_cb.assert_called_once_with(1, 2, 'btn', True)
        mock_release_cb.assert_called_once_with('key_b')


if __name__ == '__main__':
    unittest.main()
