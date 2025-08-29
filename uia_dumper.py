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
