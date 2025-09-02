import os
import shutil
import time
from pynput import keyboard

from .annotator import Annotator
from .events import InputListener
from .media import MediaRecorder
from .uia import UIAHelper

class Recorder:
    def __init__(self, output_folder="recording"):
        self.output_folder = output_folder
        self.images_folder = f"{self.output_folder}/images"
        print(f"[Recorder] Output folder set to: {self.output_folder}")

        self.is_recording = False

        self.annotator = Annotator(self.output_folder)
        self.media_recorder = MediaRecorder(self.output_folder)
        self.uia_helper = UIAHelper()
        self.input_listener = InputListener(
            on_press_callback=self._handle_press,
            on_click_callback=self._handle_click,
            on_release_callback=self._handle_release
        )

    def start(self):
        if os.path.exists(self.output_folder):
            shutil.rmtree(self.output_folder)
        os.makedirs(self.images_folder, exist_ok=True)

        print("[Recorder] Starting recording...")
        self.is_recording = True

        self.annotator.start()
        self.media_recorder.start()
        self.uia_helper.start_highlighting()
        self.input_listener.start()

        print("[Recorder] Recording started.")

    def stop(self):
        if not self.is_recording:
            return

        print("[Recorder] Stopping recording...")
        self.is_recording = False

        self.media_recorder.stop()
        self.uia_helper.stop_highlighting()
        self.input_listener.stop()
        self.annotator.stop()

        print("[Recorder] Recording stopped.")

    def _handle_press(self, key):
        try:
            element = self.uia_helper.get_focused_element()
            hierarchy = self.uia_helper.get_element_hierarchy(element)
            self.annotator.capture_and_annotate_screenshot(hierarchy)
            self.annotator.log_annotation("key_press", str(key), hierarchy)
        except Exception as e:
            print(f"[Recorder] Error in _handle_press: {e}")
            self.annotator.log_annotation("key_press", str(key), None)

    def _handle_release(self, key):
        try:
            element = self.uia_helper.get_focused_element()
            hierarchy = self.uia_helper.get_element_hierarchy(element)
            self.annotator.log_annotation("key_release", str(key), hierarchy)
        except Exception as e:
            print(f"[Recorder] Error in _handle_release: {e}")
            self.annotator.log_annotation("key_release", str(key), None)

    def _handle_click(self, x, y, button, pressed):
        action = 'pressed' if pressed else 'released'
        try:
            element = self.uia_helper.get_element_from_point(x, y)
            hierarchy = self.uia_helper.get_element_hierarchy(element)
            self.annotator.capture_and_annotate_screenshot(hierarchy)
            self.annotator.log_annotation("mouse_click", {"x": x, "y": y, "button": str(button), "action": action}, hierarchy)
        except Exception as e:
            print(f"[Recorder] Error in _handle_click: {e}")
            self.annotator.log_annotation("mouse_click", {"x": x, "y": y, "button": str(button), "action": action}, None)
