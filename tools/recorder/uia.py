import sys
import uiautomation as auto
import time
import pyautogui
import threading
import tkinter as tk
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.uia import get_element_info

class HighlightWindow:
    def __init__(self):
        self.root = None
        self.canvas = None
        self.thread = threading.Thread(target=self.create_window)
        self.thread.daemon = True
        self.thread.start()
        time.sleep(1)

    def create_window(self):
        self.root = tk.Tk()
        self.root.title("Highlight Window")
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', 0.5)
        self.root.attributes('-topmost', True)
        self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")

        self.canvas = tk.Canvas(self.root, bg='white', highlightthickness=0)
        self.root.wm_attributes('-transparentcolor', 'white')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.root.mainloop()

    def show_rectangle(self, rect, element_id):
        if not self.canvas:
            return
        self.canvas.delete("all")
        if rect:
            self.canvas.create_rectangle(rect.left, rect.top, rect.right, rect.bottom, outline='red', width=3)
            if element_id:
                self.canvas.create_text(rect.left, rect.top - 10, text=element_id, fill='red', font=('Arial', 10))

    def stop(self):
        if self.root:
            self.root.after(0, self.root.destroy)

class UIAHelper:
    def __init__(self):
        self.element_ids = {}
        self.is_highlighting = False
        self.highlight_thread = None
        self.highlight_window = None

    def start_highlighting(self):
        self.is_highlighting = True
        self.highlight_window = HighlightWindow()
        self.highlight_thread = threading.Thread(target=self._highlight_element)
        self.highlight_thread.start()

    def stop_highlighting(self):
        self.is_highlighting = False
        if self.highlight_thread:
            self.highlight_thread.join()
        if self.highlight_window:
            self.highlight_window.stop()

    def _highlight_element(self):
        print("[UIAHelper] Highlight thread started.")
        auto.UIAutomationInitializerInThread()
        while self.is_highlighting:
            try:
                x, y = pyautogui.position()
                element = auto.ControlFromPoint(x, y)
                if element:
                    rect = element.BoundingRectangle
                    info = get_element_info(element, self.element_ids)
                    element_id = info['element_id'] if info else ''
                    self.highlight_window.show_rectangle(rect, element_id)
                else:
                    self.highlight_window.show_rectangle(None, None)
            except Exception:
                self.highlight_window.show_rectangle(None, None)
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
            info = get_element_info(current, element_ids=self.element_ids)
            if info:
                if not process_names or (info.get('process_name') and info['process_name'].lower() in [p.lower() for p in process_names]):
                    hierarchy.append(info)
            try:
                current = current.GetParentControl()
            except Exception:
                current = None
        return hierarchy
