import unittest
from unittest.mock import patch, MagicMock
import sys

# Mock the pyautogui dependency
MOCK_MODULES = {
    'pyautogui': MagicMock(),
}

@patch.dict('sys.modules', MOCK_MODULES)
class TestElementScreenshotter(unittest.TestCase):

    def setUp(self):
        self.patcher = patch.dict('sys.modules', MOCK_MODULES)
        self.patcher.start()

        global ElementScreenshotter
        from tools.recorder.element_screenshotter import ElementScreenshotter
        

        self.mock_pyautogui = sys.modules['pyautogui']
        self.mock_pyautogui.reset_mock()

    def tearDown(self):
        self.patcher.stop()

    def test_capture_element_screenshot(self):
        # Arrange
        screenshotter = ElementScreenshotter('output')
        mock_img = MagicMock()
        self.mock_pyautogui.screenshot.return_value = mock_img

        rect = MagicMock()
        rect.left, rect.top, rect.right, rect.bottom = 10, 20, 110, 120
        element_info = {
            'id': 'elem1',
            'is_offscreen': False,
            'bounding_rectangle': rect
        }

        # Act
        screenshotter.capture_element_screenshot(element_info, 123.456)

        # Assert
        self.mock_pyautogui.screenshot.assert_called_once_with(region=(10, 20, 100, 100))
        expected_path = 'output/images/elem1__123456.png'
        mock_img.save.assert_called_once_with(expected_path)
        self.assertIn('elem1', screenshotter.seen_element_ids)

    def test_capture_element_screenshot_already_seen(self):
        # Arrange
        screenshotter = ElementScreenshotter('output')
        screenshotter.seen_element_ids.add('elem1')

        element_info = {'id': 'elem1'}

        # Act
        screenshotter.capture_element_screenshot(element_info, 123)

        # Assert
        self.mock_pyautogui.screenshot.assert_not_called()


if __name__ == '__main__':
    unittest.main()
