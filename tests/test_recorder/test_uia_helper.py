import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

import unittest
from unittest.mock import patch, MagicMock

# Mock the platform-specific dependencies
MOCK_MODULES = {
    'uiautomation': MagicMock(),
    'pyautogui': MagicMock(),
    'tools.common.uia': MagicMock(),
}

@patch.dict('sys.modules', MOCK_MODULES)
class TestUiaHelper(unittest.TestCase):

    def setUp(self):
        self.patcher = patch.dict('sys.modules', MOCK_MODULES)
        self.patcher.start()

        from tools.recorder.uia import UIAHelper
        global UIAHelper

        self.mock_auto = sys.modules['uiautomation']
        self.mock_pyautogui = sys.modules['pyautogui']
        self.mock_common_uia = sys.modules['tools.common.uia']

    def tearDown(self):
        self.patcher.stop()

    def test_get_element_hierarchy(self):
        # Arrange
        helper = UIAHelper()

        # Create a mock element hierarchy: child -> parent -> grandparent
        mock_child = MagicMock()
        mock_parent = MagicMock()
        mock_grandparent = MagicMock()

        mock_child.GetParentControl.return_value = mock_parent
        mock_parent.GetParentControl.return_value = mock_grandparent
        mock_grandparent.GetParentControl.return_value = None # End of hierarchy

        # Mock the get_element_info to return predictable data
        def get_info_side_effect(element, element_ids):
            if element == mock_child:
                return {'id': 'child', 'process_name': 'test.exe'}
            if element == mock_parent:
                return {'id': 'parent', 'process_name': 'test.exe'}
            if element == mock_grandparent:
                return {'id': 'grandparent', 'process_name': 'test.exe'}
            return None
        self.mock_common_uia.get_element_info.side_effect = get_info_side_effect

        # Act
        hierarchy = helper.get_element_hierarchy(mock_child)

        # Assert
        self.assertEqual(len(hierarchy), 3)
        self.assertEqual(hierarchy[0]['id'], 'child')
        self.assertEqual(hierarchy[1]['id'], 'parent')
        self.assertEqual(hierarchy[2]['id'], 'grandparent')


if __name__ == '__main__':
    unittest.main()
