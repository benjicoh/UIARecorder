import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

import pyautogui

class ElementScreenshotter:
    def __init__(self, output_folder):
        self.output_folder = output_folder
        self.images_folder = f"{self.output_folder}/images"
        self.seen_element_ids = set()

    def capture_element_screenshot(self, element_info, timestamp):
        if not element_info or element_info.get('is_offscreen', True):
            return

        element_id = element_info['id']
        if element_id in self.seen_element_ids:
            return

        rect = element_info['bounding_rectangle']
        if not rect or (rect.right - rect.left) == 0 or (rect.bottom - rect.top) == 0:
            return

        width = rect.right - rect.left
        height = rect.bottom - rect.top

        screenshot_path = f"{self.images_folder}/{element_id}__{int(timestamp * 1000)}.png"

        try:
            img = pyautogui.screenshot(region=(rect.left, rect.top, width, height))
            img.save(screenshot_path)
            self.seen_element_ids.add(element_id)
            print(f"[ElementScreenshotter] Captured screenshot for element {element_id} at {screenshot_path}")
        except Exception as e:
            print(f"[ElementScreenshotter] Error capturing screenshot for element {element_id}: {e}")
