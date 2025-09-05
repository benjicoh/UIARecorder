"""
uia_dumper.py - Dump UI Automation tree to JSON

Usage examples:
    # Dump the UI tree for a window with a specific title
    python uia_dumper.py --window "AI Shelveset Linter" --output ai_shelveset_linter_dump.json

    # Dump the UI tree for a process by name
    python uia_dumper.py --process explorer.exe --output explorer_ui.json
"""
import uiautomation as auto
import psutil

def get_process_name(element):
    if not element:
        return None
    try:
        return psutil.Process(element.ProcessId).name()
    except psutil.NoSuchProcess:
        return None

def get_element_info(element):
    """
    Extracts relevant information from a UI Automation element.
    """
    if not element:
        return None

    info = {
        'id': element.GetRuntimeId(),
        'name': element.Name,
        'automation_id': element.AutomationId,
        'class_name': element.ClassName,
        'control_type': element.ControlTypeName,
        'bounding_rectangle': str(element.BoundingRectangle),  # Convert rect to string for serialization
        'is_offscreen': element.IsOffscreen,
        'process_name': get_process_name(element),
        'children': []
    }

    # Extract pattern information
    patterns = {}

    # Note: A simple try/except is used because checking for pattern availability
    # and then getting it can still fail in some race conditions. This is more robust.

    try:
        p = element.GetDockPattern()
        patterns['DockPattern'] = {'DockPosition': str(p.DockPosition)}
    except Exception: pass

    try:
        p = element.GetExpandCollapsePattern()
        patterns['ExpandCollapsePattern'] = {'ExpandCollapseState': str(p.ExpandCollapseState)}
    except Exception: pass

    try:
        p = element.GetGridPattern()
        patterns['GridPattern'] = {'RowCount': p.RowCount, 'ColumnCount': p.ColumnCount}
    except Exception: pass

    try:
        p = element.GetGridItemPattern()
        patterns['GridItemPattern'] = {'Row': p.Row, 'Column': p.Column, 'RowSpan': p.RowSpan, 'ColumnSpan': p.ColumnSpan}
    except Exception: pass

    try:
        if element.IsInvokePatternAvailable():
            patterns['InvokePattern'] = {'Available': True}
    except Exception: pass

    try:
        p = element.GetMultipleViewPattern()
        patterns['MultipleViewPattern'] = {'CurrentView': p.CurrentView, 'SupportedViews': p.GetSupportedViews()}
    except Exception: pass

    try:
        p = element.GetRangeValuePattern()
        patterns['RangeValuePattern'] = {
            'Value': p.Value, 'IsReadOnly': p.IsReadOnly, 'LargeChange': p.LargeChange,
            'SmallChange': p.SmallChange, 'Maximum': p.Maximum, 'Minimum': p.Minimum
        }
    except Exception: pass

    try:
        if element.IsScrollItemPatternAvailable():
            patterns['ScrollItemPattern'] = {'Available': True}
    except Exception: pass

    try:
        p = element.GetScrollPattern()
        patterns['ScrollPattern'] = {
            'HorizontalScrollPercent': p.HorizontalScrollPercent, 'VerticalScrollPercent': p.VerticalScrollPercent,
            'HorizontalViewSize': p.HorizontalViewSize, 'VerticalViewSize': p.VerticalViewSize,
            'HorizontallyScrollable': p.HorizontallyScrollable, 'VerticallyScrollable': p.VerticallyScrollable
        }
    except Exception: pass

    try:
        p = element.GetSelectionPattern()
        patterns['SelectionPattern'] = {
            'CanSelectMultiple': p.CanSelectMultiple, 'IsSelectionRequired': p.IsSelectionRequired,
            'Selection': [item.Name for item in p.GetSelection()]
        }
    except Exception: pass

    try:
        p = element.GetSelectionItemPattern()
        patterns['SelectionItemPattern'] = {'IsSelected': p.IsSelected}
    except Exception: pass

    try:
        p = element.GetTablePattern()
        patterns['TablePattern'] = {
            'RowCount': p.RowCount, 'ColumnCount': p.ColumnCount,
            'RowOrColumnMajor': str(p.RowOrColumnMajor)
        }
    except Exception: pass

    try:
        p = element.GetTableItemPattern()
        patterns['TableItemPattern'] = {
            'Row': p.Row, 'Column': p.Column, 'RowSpan': p.RowSpan, 'ColumnSpan': p.ColumnSpan
        }
    except Exception: pass

    try:
        p = element.GetTextPattern()
        # Getting full text can be long, so we get a snippet.
        patterns['TextPattern'] = {'Text': p.DocumentRange.GetText(256)}
    except Exception: pass

    try:
        p = element.GetTogglePattern()
        patterns['TogglePattern'] = {'ToggleState': str(p.ToggleState)}
    except Exception: pass

    try:
        p = element.GetTransformPattern()
        patterns['TransformPattern'] = {'CanMove': p.CanMove, 'CanResize': p.CanResize, 'CanRotate': p.CanRotate}
    except Exception: pass

    try:
        p = element.GetValuePattern()
        patterns['ValuePattern'] = {'Value': p.Value, 'IsReadOnly': p.IsReadOnly}
    except Exception: pass

    try:
        p = element.GetWindowPattern()
        patterns['WindowPattern'] = {
            'CanMaximize': p.CanMaximize, 'CanMinimize': p.CanMinimize, 'IsModal': p.IsModal,
            'IsTopmost': p.IsTopmost, 'WindowVisualState': str(p.WindowVisualState),
            'WindowInteractionState': str(p.WindowInteractionState)
        }
    except Exception: pass

    info['patterns'] = patterns

    # Screenshot logic
    try:
        # Only take screenshot if element is visible and has a bounding rectangle
        if not element.IsOffscreen and element.BoundingRectangle:
            # Activate top-level window first
            # top_window = element.GetTopLevelControl()
            # if top_window:
            #     top_window.SetActive()
            # Get runtime id for filename
            runtime_id = element.GetRuntimeId()
            if runtime_id:
                # Convert runtime_id to string for filename
                runtime_id_str = '_'.join(str(i) for i in runtime_id)
                import os
                screenshots_dir = os.path.join(os.path.dirname(__file__), 'screenshots')
                os.makedirs(screenshots_dir, exist_ok=True)
                screenshot_path = os.path.join(screenshots_dir, f'{runtime_id_str}.png')
                # Take screenshot
                bmp = element.ToBitmap()
                bmp.ToFile(screenshot_path)
                info['screenshot'] = screenshot_path
            else:
                info['screenshot'] = None
        else:
            info['screenshot'] = None
    except Exception as e:
        info['screenshot'] = None

    return info


def traverse_element_tree(element, process_names=None):
    """
    Recursively traverses the UI Automation tree and builds a dictionary representation.
    If process_names is provided, only elements from those processes (and their ancestors) are included.
    """
    if not element:
        return None

    children = []
    for child in element.GetChildren():
        child_tree = traverse_element_tree(child, process_names)
        if child_tree:
            children.append(child_tree)

    is_match = False
    if process_names:
        process_name = get_process_name(element)
        if process_name and process_name.lower() in [p.lower() for p in process_names]:
            is_match = True
    else:
        is_match = True  # No filter, so everything is a match

    if is_match or children:
        tree = get_element_info(element)
        tree['children'] = children
        return tree

    return None


if __name__ == "__main__":
    import argparse
    import json
    import sys

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

    args = parser.parse_args()

    roots = []
    if args.process:
        # Find the process by name
        for w in auto.GetRootControl().GetChildren():
            if get_process_name(w).lower() == args.process.lower():
                roots.append(w)
                w.SetActive()
                
        if len(roots) == 0:
            print(f"Process '{args.process}' not found.", file=sys.stderr)
            sys.exit(1)
    elif args.window:
        # Find the window by title
        for w in auto.GetRootControl().GetChildren():
            if w.Name and args.window.lower() in w.Name.lower():
                roots = [w]
                w.SetActive()
                break
        if len(roots) == 0:
            print(f"Window with title containing '{args.window}' not found.", file=sys.stderr)
            sys.exit(1)
    trees = []
    for root in roots:
        tree = traverse_element_tree(root, process_names=args.process_names)
        trees.append(tree)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(trees, f, ensure_ascii=False, indent=2)
    print(f"UI tree dumped to {args.output}")
    #play notification sound
    print('\007')
