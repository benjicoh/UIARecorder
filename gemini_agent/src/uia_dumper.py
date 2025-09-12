"""
uia_dumper.py - Dump UI Automation tree to JSON

Usage examples:
    # Dump the UI tree for a window with a specific title
    python -m tools.uia_dumper -w "My Window Title" -o dump.json

    # Dump the UI tree for a process by name and capture screenshots
    python -m tools.uia_dumper -p explorer.exe -o explorer_ui.json -s
"""
import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

import uiautomation as auto
import argparse
import json
from tools.common.uia import get_element_info, get_process_name

def serialize_rects(obj):
    """
    Recursively convert Rect objects to dictionaries in the given object.
    """
    import uiautomation as auto
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
    If whitelist is provided, only elements from those processes (and their ancestors) are included.
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
        is_match = True  # No filter, so everything is a match

    if is_match or children:
        # Use the shared get_element_info function
        tree = get_element_info(element, screenshot_dir=screenshot_dir)
        if not tree:
            return None
        tree['children'] = children
        return tree

    return None

def dump_uia_tree(process_name=None, window_title=None, output_file=None, whitelist=None, screenshots=False):
    """
    Dumps the UI Automation tree for a given process or window to a JSON file.
    """
    screenshot_dir = None
    if screenshots:
        # Create screenshots dir relative to the output file
        screenshot_dir = os.path.join(os.path.dirname(os.path.abspath(output_file)), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)

    roots = []
    root_control = auto.GetRootControl()
    if process_name:
        # Find the process by name
        for w in root_control.GetChildren():
            if get_process_name(w) and get_process_name(w).lower() == process_name.lower():
                roots.append(w)
                w.SetActive()
                
        if len(roots) == 0:
            return f"Process '{process_name}' not found."
    elif window_title:
        # Find the window by title
        for w in root_control.GetChildren():
            if w.Name and window_title.lower() in w.Name.lower():
                roots = [w]
                w.SetActive()
                break
        if len(roots) == 0:
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

    # Play notification sound
    print('\007')
    return result_message

def main():
    parser = argparse.ArgumentParser(description="Dump UI Automation tree to JSON.", formatter_class=argparse.RawTextHelpFormatter)

    # Group for specifying the target
    target_group = parser.add_argument_group('Target Selection (must specify one)')
    target_exclusive_group = target_group.add_mutually_exclusive_group(required=True)
    target_exclusive_group.add_argument('-p', '--process', type=str, help='Process name to dump the UI tree for (e.g., "explorer.exe").')
    target_exclusive_group.add_argument('-w', '--window', type=str, help='Top-level window title to dump the UI tree for (e.g., "Calculator").')

    # Group for output and filtering options
    options_group = parser.add_argument_group('Output and Filtering')
    options_group.add_argument('-o', '--output', type=str, required=True, help='Path to the output JSON file.')
    options_group.add_argument('-wh', '--whitelist', type=str, nargs='+', help='Filter: Only include elements from these process names.')
    options_group.add_argument('-s', '--screenshots', action='store_true', help='Enable capturing screenshots of elements.')

    args = parser.parse_args()

    result = dump_uia_tree(
        process_name=args.process,
        window_title=args.window,
        output_file=args.output,
        whitelist=args.whitelist,
        screenshots=args.screenshots
    )
    print(result)

if __name__ == "__main__":
    main()
