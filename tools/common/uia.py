import uiautomation as auto
import psutil
import os

def get_process_name(element):
    """
    Gets the process name of a UI Automation element.
    Returns None if the process does not exist.
    """
    if not element:
        return None
    try:
        return psutil.Process(element.ProcessId).name()
    except psutil.NoSuchProcess:
        return None

def get_element_info(element, element_ids=None, screenshot_dir=None):
    """
    Extracts comprehensive information from a UI Automation element.

    Args:
        element: The UI Automation element.
        element_ids (dict, optional): A dictionary to manage custom element IDs.
                                     If provided, a custom ID will be generated and used.
                                     Defaults to None, in which case runtime_id is used.
        screenshot_dir (str, optional): If provided, a screenshot of the element will be taken
                                        and saved to this directory. Defaults to None.

    Returns:
        A dictionary containing element information, or None if the element is invalid.
    """
    if not element:
        return None

    # --- Element ID ---
    try:
        runtime_id = element.GetRuntimeId()
        if element_ids is not None:
            if runtime_id not in element_ids:
                element_ids[runtime_id] = f"element-{len(element_ids) + 1}"
            element_id = element_ids[runtime_id]
        else:
            element_id = runtime_id
    except Exception:
        return None

    info = {'id': element_id}

    # --- Basic Properties (with robust error handling) ---
    def get_prop(name, getter):
        try:
            return getter()
        except Exception:
            return 'N/A'

    info['name'] = get_prop('Name', lambda: element.Name)
    info['automation_id'] = get_prop('AutomationId', lambda: element.AutomationId)
    info['class_name'] = get_prop('ClassName', lambda: element.ClassName)
    info['control_type'] = get_prop('ControlTypeName', lambda: element.ControlTypeName)
    info['bounding_rectangle'] = get_prop('BoundingRectangle', lambda: str(element.BoundingRectangle))
    info['is_offscreen'] = get_prop('IsOffscreen', lambda: element.IsOffscreen)
    info['process_name'] = get_process_name(element)

    # --- Patterns ---
    patterns = {}

    # A generic pattern getter to reduce boilerplate
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

    # --- Screenshot Logic ---
    if screenshot_dir:
        try:
            if not info['is_offscreen'] and element.BoundingRectangle:
                os.makedirs(screenshot_dir, exist_ok=True)
                # Use a more readable ID for the filename
                id_str = '_'.join(str(i) for i in runtime_id) if isinstance(runtime_id, tuple) else str(runtime_id)
                screenshot_path = os.path.join(screenshot_dir, f'{id_str}.png')
                element.ToBitmap().ToFile(screenshot_path)
                info['screenshot'] = screenshot_path
            else:
                info['screenshot'] = None
        except Exception:
            info['screenshot'] = None

    return info
