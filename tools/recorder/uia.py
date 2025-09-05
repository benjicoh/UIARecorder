import sys
import uiautomation as auto
import time
import pyautogui
import threading
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.uia import get_element_info

class UIAHelper:
    def __init__(self):
        self.element_ids = {}

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
            info = get_element_info(current, element_ids=self.element_ids)
            if info:
                if not process_names or (info.get('process_name') and info['process_name'].lower() in [p.lower() for p in process_names]):
                    hierarchy.append(info)
            try:
                current = current.GetParentControl()
            except Exception:
                current = None
        return hierarchy
