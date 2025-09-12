import uiautomation as auto
import psutil
import json
import os
import argparse

def get_process_name(element):
    """
    Gets the process name of a UI Automation element.
    Returns None if the process does not exist.
    """
    if not element:
        return None
    try:
        process = psutil.Process(element.ProcessId)
        return process.name()
    except psutil.NoSuchProcess:
        return None

def get_element_info(element, screenshot_dir=None):
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

    get_simple_pattern('Invoke')
    get_pattern('Value', lambda p: {'Value': p.Value, 'IsReadOnly': p.IsReadOnly})
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
        if len(roots) == 0:
            return f"Process '{process_name}' not found."
    elif window_title:
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

    print('\007')
    return result_message

def main():
    parser = argparse.ArgumentParser(description="Dump UI Automation tree to JSON.")
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument('-p', '--process', type=str, help='Process name.')
    target_group.add_argument('-w', '--window', type=str, help='Window title.')
    parser.add_argument('-o', '--output', type=str, required=True, help='Output JSON file.')
    parser.add_argument('-wh', '--whitelist', type=str, nargs='+', help='Process whitelist.')
    parser.add_argument('-s', '--screenshots', action='store_true', help='Enable screenshots.')
    args = parser.parse_args()
    result = dump_ui(
        process_name=args.process,
        window_title=args.window,
        output_file=args.output,
        whitelist=args.whitelist,
        screenshots=args.screenshots
    )
    print(result)

if __name__ == "__main__":
    main()
