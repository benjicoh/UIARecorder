import sys
import os
import json
import argparse
import threading
import time

import uiautomation as auto
import psutil
import pyautogui
from python.common.logger import get_logger

logger = get_logger(__name__)


# --- Core Functions ---

def get_process_name(element):
    """
    Gets the process name of a UI Automation element.
    Returns None if the process does not exist.
    """
    if not element:
        return None
    try:
        logger.debug(f"get_process_name: element={element}, ProcessId={element.ProcessId}")
        process = psutil.Process(element.ProcessId)
        logger.debug(f"get_process_name: process={process}")
        name = process.name()
        logger.debug(f"get_process_name: name={name}")
        return name
    except psutil.NoSuchProcess:
        return None

def get_element_info(element, element_ids=None, screenshot_dir=None):
    """
    Extracts comprehensive information from a UI Automation element.
    """
    if not element:
        return None

    try:
        runtime_id = element.GetRuntimeId()
        runtime_id = '_'.join(str(i) for i in runtime_id) if isinstance(runtime_id, tuple) else str(runtime_id)
    except Exception:
        return None

    info = {'id': runtime_id}

    def get_prop(name, getter):
        try:
            return getter()
        except Exception:
            return 'N/A'

    info['name'] = get_prop('Name', lambda: element.Name)
    info['automation_id'] = get_prop('AutomationId', lambda: element.AutomationId)
    info['class_name'] = get_prop('ClassName', lambda: element.ClassName)
    info['control_type'] = get_prop('ControlTypeName', lambda: element.ControlTypeName)
    info['bounding_rectangle'] = get_prop('BoundingRectangle', lambda: element.BoundingRectangle)
    info['is_offscreen'] = get_prop('IsOffscreen', lambda: element.IsOffscreen)
    info['process_name'] = get_process_name(element)

    patterns = {}
    def get_pattern(pattern_name, getter_func):
        try:
            p = getattr(element, f'Get{pattern_name}Pattern')()
            patterns[pattern_name + 'Pattern'] = getter_func(p)
        except Exception:
            pass

    def get_simple_pattern(pattern_name):
         try:
            if getattr(element, f'Is{pattern_name}PatternAvailable')():
                patterns[pattern_name + 'Pattern'] = {'Available': True}
         except Exception: pass

    get_pattern('Dock', lambda p: {'DockPosition': str(p.DockPosition)})
    get_pattern('ExpandCollapse', lambda p: {'ExpandCollapseState': str(p.ExpandCollapseState)})
    get_pattern('Grid', lambda p: {'RowCount': p.RowCount, 'ColumnCount': p.ColumnCount})
    get_pattern('GridItem', lambda p: {'Row': p.Row, 'Column': p.Column, 'RowSpan': p.RowSpan, 'ColumnSpan': p.ColumnSpan})
    get_simple_pattern('Invoke')
    get_pattern('MultipleView', lambda p: {'CurrentView': p.CurrentView, 'SupportedViews': p.GetSupportedViews()})
    get_pattern('RangeValue', lambda p: {'Value': p.Value, 'IsReadOnly': p.IsReadOnly, 'LargeChange': p.LargeChange, 'SmallChange': p.SmallChange, 'Maximum': p.Maximum, 'Minimum': p.Minimum})
    get_simple_pattern('ScrollItem')
    get_pattern('Scroll', lambda p: {'HorizontalScrollPercent': p.HorizontalScrollPercent, 'VerticalScrollPercent': p.VerticalScrollPercent, 'HorizontalViewSize': p.HorizontalViewSize, 'VerticalViewSize': p.VerticalViewSize, 'HorizontallyScrollable': p.HorizontallyScrollable, 'VerticallyScrollable': p.VerticallyScrollable})
    get_pattern('Selection', lambda p: {'CanSelectMultiple': p.CanSelectMultiple, 'IsSelectionRequired': p.IsSelectionRequired, 'Selection': [item.Name for item in p.GetSelection()]})
    get_pattern('SelectionItem', lambda p: {'IsSelected': p.IsSelected})
    get_pattern('Table', lambda p: {'RowCount': p.RowCount, 'ColumnCount': p.ColumnCount, 'RowOrColumnMajor': str(p.RowOrColumnMajor)})
    get_pattern('TableItem', lambda p: {'Row': p.Row, 'Column': p.Column, 'RowSpan': p.RowSpan, 'ColumnSpan': p.ColumnSpan})
    get_pattern('Text', lambda p: {'Text': p.DocumentRange.GetText(256)})
    get_pattern('Toggle', lambda p: {'ToggleState': str(p.ToggleState)})
    get_pattern('Transform', lambda p: {'CanMove': p.CanMove, 'CanResize': p.CanResize, 'CanRotate': p.CanRotate})
    get_pattern('Value', lambda p: {'Value': p.Value, 'IsReadOnly': p.IsReadOnly})
    get_pattern('Window', lambda p: {'CanMaximize': p.CanMaximize, 'CanMinimize': p.CanMinimize, 'IsModal': p.IsModal, 'IsTopmost': p.IsTopmost, 'WindowVisualState': str(p.WindowVisualState), 'WindowInteractionState': str(p.WindowInteractionState)})

    info['patterns'] = patterns

    if screenshot_dir:
        try:
            if not info['is_offscreen'] and element.BoundingRectangle:
                os.makedirs(screenshot_dir, exist_ok=True)
                screenshot_path = os.path.join(screenshot_dir, f'{runtime_id}.png')
                element.ToBitmap().ToFile(screenshot_path)
                info['screenshot'] = screenshot_path
            else:
                info['screenshot'] = None
        except Exception:
            info['screenshot'] = None

    return info

# --- UIA Helper Class (for Recorder) ---

class UIAHelper:
    def __init__(self):
        self.element_ids = {}

    def get_element_from_point(self, x, y):
        try:
            return auto.ControlFromPoint(x, y)
        except Exception:
            return None

    def get_focused_element(self):
        try:
            return auto.GetFocusedControl()
        except Exception:
            return None

    def get_element_hierarchy(self, element, process_names=None):
        if not element:
            return None
        hierarchy = []
        current = element
        while current:
            info = get_element_info(current, element_ids=self.element_ids)
            if info:
                if not process_names or (info.get('process_name') and info['process_name'].lower() in [p.lower() for p in process_names]):
                    hierarchy.append(info)
            try:
                current = current.GetParentControl()
            except Exception:
                current = None
        return hierarchy

# --- UI Dumper Functionality (for Agent) ---

def serialize_rects(obj):
    """
    Recursively convert Rect objects to dictionaries in the given object.
    """
    if isinstance(obj, auto.Rect):
        return {'left': obj.left, 'top': obj.top, 'right': obj.right, 'bottom': obj.bottom}
    elif isinstance(obj, dict):
        return {k: serialize_rects(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_rects(v) for v in obj]
    else:
        return obj

def traverse_element_tree(element, whitelist=None, screenshot_dir=None):
    """
    Recursively traverses the UI Automation tree and builds a dictionary representation.
    """
    if not element:
        return None

    children = []
    for child in element.GetChildren():
        child_tree = traverse_element_tree(child, whitelist, screenshot_dir)
        if child_tree:
            children.append(child_tree)

    is_match = False
    process_name = get_process_name(element)
    if whitelist:
        if process_name and process_name.lower() in [p.lower() for p in whitelist]:
            is_match = True
    else:
        is_match = True

    if is_match or children:
        tree = get_element_info(element, screenshot_dir=screenshot_dir)
        if not tree:
            return None
        tree['children'] = children
        return tree

    return None

def dump_ui(process_name=None, window_title=None, output_file=None, whitelist=None, screenshots=False):
    """
    Dumps the UI Automation tree for a given process or window to a JSON file.
    """
    with auto.UIAutomationInitializerInThread():
        screenshot_dir = None
        if screenshots:
            screenshot_dir = os.path.join(os.path.dirname(os.path.abspath(output_file)), 'screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)

        roots = []
        root_control = auto.GetRootControl()
        if process_name:
            for w in root_control.GetChildren():
                if get_process_name(w) and get_process_name(w).lower() == process_name.lower():
                    roots.append(w)
                    w.SetActive()
            if not roots:
                return f"Process '{process_name}' not found."
        elif window_title:
            for w in root_control.GetChildren():
                if w.Name and window_title.lower() in w.Name.lower():
                    roots = [w]
                    w.SetActive()
                    break
            if not roots:
                return f"Window with title containing '{window_title}' not found."

        trees = []
        for root in roots:
            tree = traverse_element_tree(root, whitelist=whitelist, screenshot_dir=screenshot_dir)
            if tree:
                trees.append(tree)
        trees_serialized = serialize_rects(trees)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(trees_serialized, f, ensure_ascii=False, indent=2)

        result_message = f"UI tree dumped to {output_file}"
        if screenshot_dir:
            result_message += f"\nScreenshots saved to {screenshot_dir}"

        logger.info('\007')
        return result_message

# --- Main execution block for dumping UI tree ---
def main():
    parser = argparse.ArgumentParser(description="Dump UI Automation tree to JSON.")
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument('-p', '--process', type=str, help='Process name.')
    target_group.add_argument('-w', '--window', type=str, help='Window title.')
    parser.add_argument('-o', '--output', type=str, required=True, help='Output JSON file.')
    parser.add_argument('-wh', '--whitelist', type=str, nargs='+', help='Process whitelist.')
    parser.add_argument('-s', '--screenshots', action='store_true', help='Enable screenshots.')
    args = parser.parse_args()

    result_container = [None]
    def dump_ui_wrapper():
        result_container[0] = dump_ui(
            args.process,
            args.window,
            args.output,
            args.whitelist,
            args.screenshots
        )

    thread = threading.Thread(target=dump_ui_wrapper, daemon=True)
    thread.start()
    thread.join(timeout=10)

    if thread.is_alive():
        logger.error("Error: UI dump timed out after 10 seconds.")
    elif result_container[0]:
        logger.info(result_container[0])

if __name__ == "__main__":
    main()