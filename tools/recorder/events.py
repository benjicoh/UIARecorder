import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from pynput import keyboard, mouse

class InputListener:
    def __init__(self, on_press_callback, on_click_callback, on_release_callback):
        self.on_press_callback = on_press_callback
        self.on_click_callback = on_click_callback
        self.on_release_callback = on_release_callback
        self.keyboard_listener = None
        self.mouse_listener = None

    def start(self):
        self.keyboard_listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self.mouse_listener = mouse.Listener(on_click=self._on_click)
        self.keyboard_listener.start()
        self.mouse_listener.start()
        print("[InputListener] Listeners started.")

    def stop(self):
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()
        print("[InputListener] Listeners stopped.")

    def _on_press(self, key):
        if self.on_press_callback:
            self.on_press_callback(key)

    def _on_release(self, key):
        if self.on_release_callback:
            self.on_release_callback(key)

    def _on_click(self, x, y, button, pressed):
        if self.on_click_callback:
            self.on_click_callback(x, y, button, pressed)
