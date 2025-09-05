import uiautomation as auto
import time
import pyautogui
import threading
from ..common.uia import get_element_info

class UIAHelper:
    def __init__(self):
        self.element_ids = {}
        self.is_highlighting = False
        self.highlight_thread = None

    def start_highlighting(self):
        self.is_highlighting = True
        self.highlight_thread = threading.Thread(target=self._highlight_element)
        self.highlight_thread.start()

    def stop_highlighting(self):
        self.is_highlighting = False
        if self.highlight_thread:
            self.highlight_thread.join()

    def _highlight_element(self):
        print("[UIAHelper] Highlight thread started.")
        auto.UIAutomationInitializerInThread()
        while self.is_highlighting:
            try:
                x, y = pyautogui.position()
                element = auto.ControlFromPoint(x, y)
                if element:
                    element.ShowDesktopRectangle(color=0xFF0000, width=3)
            except Exception:
                pass
            time.sleep(0.1)
        print("[UIAHelper] Highlight thread stopped.")

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
            # Use the shared get_element_info function, passing the element_ids dict
            info = get_element_info(current, element_ids=self.element_ids)
            if info:
                # Filter by process name if specified
                if not process_names or (info.get('process_name') and info['process_name'].lower() in [p.lower() for p in process_names]):
                    hierarchy.append(info)

            try:
                current = current.GetParentControl()
            except Exception:
                current = None
        return hierarchy
