import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

import unittest
from unittest.mock import MagicMock, patch
import psutil

class TestUia(unittest.TestCase):

    def setUp(self):
        # Mock the entire modules that are platform-specific
        self.MOCK_MODULES = {
            'uiautomation': MagicMock(),
            'comtypes': MagicMock(),
        }

        # Start patching sys.modules
        self.patcher = patch.dict('sys.modules', self.MOCK_MODULES)
        self.patcher.start()

        # Now that the modules are mocked, we can import the code that depends on them.
        from tools.common.uia import get_process_name, get_element_info
        global get_process_name, get_element_info

        # Also reset the mocks before each test
        self.MOCK_MODULES['uiautomation'].reset_mock()
        self.MOCK_MODULES['comtypes'].reset_mock()

    def tearDown(self):
        # Stop patching
        self.patcher.stop()

    @patch('tools.common.uia.psutil.Process')
    def test_get_process_name(self, mock_process):
        # Arrange
        mock_process.return_value.name.return_value = 'test_process.exe'
        mock_element = MagicMock()
        mock_element.ProcessId = 123

        # Act
        process_name = get_process_name(mock_element)

        # Assert
        self.assertEqual(process_name, "test_process.exe")
        mock_process.assert_called_once_with(123)

    @patch('tools.common.uia.psutil.Process')
    def test_get_process_name_no_such_process(self, mock_process):
        # Arrange
        mock_process.side_effect = psutil.NoSuchProcess
        mock_element = MagicMock()
        mock_element.ProcessId = 123

        # Act
        with patch('tools.common.uia.psutil.NoSuchProcess', new=Exception):
            process_name = get_process_name(mock_element)

        # Assert
        self.assertIsNone(process_name)

    def test_get_element_info_basic(self):
        # Arrange
        mock_element = MagicMock()
        mock_element.GetRuntimeId.return_value = (1, 2, 3)
        mock_element.Name = "Test Element"
        mock_element.AutomationId = "test-id"
        mock_element.ClassName = "TestClass"
        mock_element.ControlTypeName = "Button"
        mock_element.BoundingRectangle = MagicMock()
        mock_element.BoundingRectangle.__str__.return_value = "(0, 0, 100, 100)"
        mock_element.IsOffscreen = False
        mock_element.ProcessId = 123

        with patch('tools.common.uia.get_process_name', return_value='test_process.exe') as mock_get_name:
            # Act
            info = get_element_info(mock_element)

            # Assert
            self.assertEqual(info['name'], "Test Element")
            self.assertEqual(info['automation_id'], "test-id")
            self.assertEqual(info['process_name'], "test_process.exe")
            self.assertIn('patterns', info)


    @patch('os.makedirs')
    def test_get_element_info_with_screenshot(self, mock_makedirs):
        # Arrange
        mock_element = MagicMock()
        mock_element.GetRuntimeId.return_value = (1, 2, 3)
        mock_element.IsOffscreen = False

        rect_mock = MagicMock()
        rect_mock.left = 10
        rect_mock.top = 20
        rect_mock.right = 110
        rect_mock.bottom = 120
        rect_mock.__str__.return_value = "(10, 20, 110, 120)"
        mock_element.BoundingRectangle = rect_mock

        mock_bitmap = MagicMock()
        mock_element.ToBitmap.return_value = mock_bitmap

        with patch('tools.common.uia.get_process_name', return_value='test_process.exe'):
            # Act
            info = get_element_info(mock_element, screenshot_dir='screenshots')

            # Assert
            mock_makedirs.assert_called_once_with('screenshots', exist_ok=True)
            expected_path = 'screenshots/1_2_3.png'
            mock_element.ToBitmap.assert_called_once()
            mock_bitmap.ToFile.assert_called_once_with(expected_path)
            self.assertEqual(info['screenshot'], expected_path)

if __name__ == '__main__':
    unittest.main()
