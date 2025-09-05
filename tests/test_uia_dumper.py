import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys

# Mock the platform-specific modules
MOCK_MODULES = {
    'uiautomation': MagicMock(),
    'psutil': MagicMock(),
    'comtypes': MagicMock(),
    'tools.common.uia': MagicMock(),
}

@patch.dict('sys.modules', MOCK_MODULES)
class TestUiaDumper(unittest.TestCase):

    def setUp(self):
        self.patcher = patch.dict('sys.modules', MOCK_MODULES)
        self.patcher.start()

        if 'tools.uia_dumper' in sys.modules:
            del sys.modules['tools.uia_dumper']

        from tools.uia_dumper import traverse_element_tree
        global traverse_element_tree

        self.mock_uia = sys.modules['uiautomation']
        self.mock_common_uia = sys.modules['tools.common.uia']
        self.mock_uia.reset_mock()
        self.mock_common_uia.reset_mock()

    def tearDown(self):
        self.patcher.stop()
        if 'tools.uia_dumper' in sys.modules:
            del sys.modules['tools.uia_dumper']

    def test_traverse_element_tree(self):
        # ... (same as before)
        mock_child1 = MagicMock()
        mock_child2 = MagicMock()
        mock_root = MagicMock()
        mock_root.GetChildren.return_value = [mock_child1, mock_child2]
        mock_child1.GetChildren.return_value = []
        mock_child2.GetChildren.return_value = []

        def get_element_info_side_effect(element, screenshot_dir=None):
            if element == mock_root:
                return {'name': 'root', 'children': []}
            if element == mock_child1:
                return {'name': 'child1', 'children': []}
            if element == mock_child2:
                return {'name': 'child2', 'children': []}
            return None
        self.mock_common_uia.get_element_info.side_effect = get_element_info_side_effect
        self.mock_common_uia.get_process_name.return_value = 'test_process.exe'
        tree = traverse_element_tree(mock_root)
        self.assertIsNotNone(tree)
        self.assertEqual(tree['name'], 'root')
        self.assertEqual(len(tree['children']), 2)


    def test_traverse_element_tree_with_filter(self):
        # ... (same as before)
        mock_child = MagicMock()
        mock_root = MagicMock()
        mock_root.GetChildren.return_value = [mock_child]
        mock_child.GetChildren.return_value = []
        self.mock_common_uia.get_element_info.side_effect = [{'name': 'root', 'children': []}, {'name': 'child', 'children': []}]
        def get_process_name_side_effect(element):
            if element == mock_root:
                return 'good_process.exe'
            if element == mock_child:
                return 'bad_process.exe'
        self.mock_common_uia.get_process_name.side_effect = get_process_name_side_effect
        with patch('tools.uia_dumper.get_process_name', self.mock_common_uia.get_process_name):
             tree = traverse_element_tree(mock_root, process_names=['good_process.exe'])
        self.assertIsNotNone(tree)
        self.assertEqual(tree['name'], 'root')
        self.assertEqual(len(tree['children']), 0)


    @patch('sys.argv', ['__main__', '--process', 'explorer.exe', '--output', 'dump.json'])
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('tools.uia_dumper.traverse_element_tree', return_value={'name': 'root_tree'})
    @patch('tools.uia_dumper.get_process_name')
    @patch('sys.exit')
    def test_main_execution_process(self, mock_exit, mock_get_process_name, mock_traverse, mock_json_dump, mock_open_file):
        # Arrange
        from tools.uia_dumper import main

        mock_window = MagicMock()
        mock_window.Name = "Window 1"
        self.mock_uia.GetRootControl.return_value.GetChildren.return_value = [mock_window]

        def get_process_name_side_effect(element):
            if element == mock_window:
                return 'explorer.exe'
            return 'other_process.exe'
        mock_get_process_name.side_effect = get_process_name_side_effect

        # Act
        main()

        # Assert
        mock_exit.assert_not_called()
        mock_open_file.assert_called_once_with('dump.json', 'w', encoding='utf-8')
        mock_json_dump.assert_called_once()
        args, kwargs = mock_json_dump.call_args
        dumped_data = args[0]
        self.assertEqual(dumped_data[0]['name'], 'root_tree')


if __name__ == '__main__':
    unittest.main()
