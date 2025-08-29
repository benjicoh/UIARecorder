import json
import re
from jsonpath_ng import parse as jsonpath_parse
from PIL import ImageGrab

def _parse_bounding_rectangle(rect_str: str) -> tuple[int, int, int, int] | None:
    """
    Parses a string like '(L10, T20, R30, B40)' into a tuple of integers.
    """
    # This regex is more robust to variations in whitespace.
    match = re.search(r'L(\d+),\s*T(\d+),\s*R(\d+),\s*B(\d+)', rect_str)
    if match:
        return tuple(map(int, match.groups()))
    return None

def take_screenshot_of_element(json_path: str, query: str, screenshot_path: str):
    """
    Finds an element in a UI dump JSON file using a JSONPath query and
    captures a screenshot of its bounding rectangle, after checking if it's visible.

    Args:
        json_path: Path to the UI dump JSON file.
        query: JSONPath query string to find the element.
        screenshot_path: Path to save the output screenshot.
    """
    # Load the JSON data
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Parse the query and find the match
    jsonpath_expression = jsonpath_parse(query)
    matches = [match.value for match in jsonpath_expression.find(data)]

    # Validate the result
    if not matches:
        raise ValueError(f"Query '{query}' returned no results.")
    if len(matches) > 1:
        raise ValueError(f"Query '{query}' returned {len(matches)} results. It must return exactly one.")

    element_node = matches[0]

    # Check for visibility
    if element_node.get('is_offscreen', False):
        raise RuntimeError(f"Element found by query '{query}' is off-screen and cannot be captured.")

    if 'bounding_rectangle' not in element_node:
        raise ValueError("Found element does not have a 'bounding_rectangle' property.")

    # Parse the bounding rectangle
    rect_str = element_node['bounding_rectangle']
    bbox = _parse_bounding_rectangle(rect_str)

    if bbox is None:
        raise ValueError(f"Could not parse bounding rectangle string: '{rect_str}'")

    print(f"Found visible element with bounding box: {bbox}")

    # Capture the screenshot
    # Note: ImageGrab.grab is Windows-only, which is consistent with this project.
    screenshot = ImageGrab.grab(bbox=bbox)

    # Save the screenshot
    screenshot.save(screenshot_path)
    print(f"Screenshot saved to {screenshot_path}")
