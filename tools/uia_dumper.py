"""
uia_dumper.py - Dump UI Automation tree to JSON

Usage examples:
    # Dump the UI tree for a window with a specific title
    python -m tools.uia_dumper --window "My Window Title" --output dump.json

    # Dump the UI tree for a process by name and capture screenshots
    python -m tools.uia_dumper --process explorer.exe --output explorer_ui.json --screenshots
"""
import uiautomation as auto
import os
import argparse
import json
import sys
from .common.uia import get_element_info, get_process_name

def traverse_element_tree(element, process_names=None, screenshot_dir=None):
    """
    Recursively traverses the UI Automation tree and builds a dictionary representation.
    If process_names is provided, only elements from those processes (and their ancestors) are included.
    """
    if not element:
        return None

    children = []
    for child in element.GetChildren():
        child_tree = traverse_element_tree(child, process_names, screenshot_dir)
        if child_tree:
            children.append(child_tree)

    is_match = False
    process_name = get_process_name(element)
    if process_names:
        if process_name and process_name.lower() in [p.lower() for p in process_names]:
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

def main():
    parser = argparse.ArgumentParser(description="Dump UI Automation tree to JSON.", formatter_class=argparse.RawTextHelpFormatter)

    # Group for specifying the target
    target_group = parser.add_argument_group('Target Selection (must specify one)')
    target_exclusive_group = target_group.add_mutually_exclusive_group(required=True)
    target_exclusive_group.add_argument('--process', type=str, help='Process name to dump the UI tree for (e.g., "explorer.exe").')
    target_exclusive_group.add_argument('--window', type=str, help='Top-level window title to dump the UI tree for (e.g., "Calculator").')

    # Group for output and filtering options
    options_group = parser.add_argument_group('Output and Filtering')
    options_group.add_argument('--output', type=str, required=True, help='Path to the output JSON file.')
    options_group.add_argument('--process_names', type=str, nargs='+', help='Filter: Only include elements from these process names.')
    options_group.add_argument('--screenshots', action='store_true', help='Enable capturing screenshots of elements.')

    args = parser.parse_args()

    screenshot_dir = None
    if args.screenshots:
        # Create screenshots dir relative to the output file
        screenshot_dir = os.path.join(os.path.dirname(os.path.abspath(args.output)), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)


    roots = []
    root_control = auto.GetRootControl()
    if args.process:
        # Find the process by name
        for w in root_control.GetChildren():
            if get_process_name(w) and get_process_name(w).lower() == args.process.lower():
                roots.append(w)
                w.SetActive()
                
        if len(roots) == 0:
            print(f"Process '{args.process}' not found.", file=sys.stderr)
            sys.exit(1)
    elif args.window:
        # Find the window by title
        for w in root_control.GetChildren():
            if w.Name and args.window.lower() in w.Name.lower():
                roots = [w]
                w.SetActive()
                break
        if len(roots) == 0:
            print(f"Window with title containing '{args.window}' not found.", file=sys.stderr)
            sys.exit(1)

    trees = []
    for root in roots:
        tree = traverse_element_tree(root, process_names=args.process_names, screenshot_dir=screenshot_dir)
        if tree:
            trees.append(tree)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(trees, f, ensure_ascii=False, indent=2)

    print(f"UI tree dumped to {args.output}")
    if screenshot_dir:
        print(f"Screenshots saved to {screenshot_dir}")

    # Play notification sound
    print('\007')

if __name__ == "__main__":
    main()
