"""
uia_dumper.py - Dump UI Automation tree to JSON

Usage examples:
    # Dump the UI tree for a window with a specific title
    python uia_dumper.py --window "AI Shelveset Linter" --output ai_shelveset_linter_dump.json

    # Dump the UI tree for a process by name
    python uia_dumper.py --process explorer.exe --output explorer_ui.json
"""
import uiautomation as auto

def get_element_info(element):
    """
    Extracts relevant information from a UI Automation element.
    """
    if not element:
        return None

    info = {
        'name': element.Name,
        'class_name': element.ClassName,
        'control_type': element.ControlTypeName,
        'bounding_rectangle': str(element.BoundingRectangle),  # Convert rect to string for serialization
        'is_offscreen': element.IsOffscreen,
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

    return info


def traverse_element_tree(element):
    """
    Recursively traverses the UI Automation tree and builds a dictionary representation.
    """
    if not element:
        return None

    tree = get_element_info(element)

    for child in element.GetChildren():
        child_tree = traverse_element_tree(child)
        if child_tree:
            tree['children'].append(child_tree)

    return tree


if __name__ == "__main__":
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Dump UI Automation tree to JSON.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--process', type=str, help='Process name to dump the UI tree for')
    group.add_argument('--window', type=str, help='Top-level window title to dump the UI tree for')
    parser.add_argument('--output', type=str, required=True, help='Output JSON file')
    args = parser.parse_args()

    root = None
    if args.process:
        # Find the process by name
        for w in auto.GetRootControl().GetChildren():
            if w.ProcessName.lower() == args.process.lower():
                root = w
                break
        if not root:
            print(f"Process '{args.process}' not found.", file=sys.stderr)
            sys.exit(1)
    elif args.window:
        # Find the window by title
        for w in auto.GetRootControl().GetChildren():
            if w.Name and args.window.lower() in w.Name.lower():
                root = w
                break
        if not root:
            print(f"Window with title containing '{args.window}' not found.", file=sys.stderr)
            sys.exit(1)

    tree = traverse_element_tree(root)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)
    print(f"UI tree dumped to {args.output}")
