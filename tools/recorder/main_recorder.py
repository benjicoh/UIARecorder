import os
import shutil
import time
import json
import psutil

from .element_screenshotter import ElementScreenshotter
from .events import InputListener
from .media import MediaRecorder
from .uia import UIAHelper

class Recorder:
    def __init__(self, output_folder="recorder/output", whitelist=None):
        self.output_folder = output_folder
        self.images_folder = f"{self.output_folder}/images"
        self.json_file = f"{self.output_folder}/annotations.json"
        print(f"[Recorder] Output folder set to: {self.output_folder}")

        self.whitelist = whitelist
        if self.whitelist:
            print(f"[Recorder] Filtering by process names: {self.whitelist}")
        self.is_recording = False
        self.start_time = None
        self.annotations = []

        self.element_screenshotter = ElementScreenshotter(self.output_folder)
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
        self.start_time = time.time()
        self.annotations = []

        self.media_recorder.start()
        self.input_listener.start()

        print("[Recorder] Recording started.")

    def stop(self):
        if not self.is_recording:
            return

        print("[Recorder] Stopping recording...")
        self.is_recording = False

        self.media_recorder.stop()
        self.input_listener.stop()

        with open(self.json_file, 'w') as f:
            json.dump(self.annotations, f, indent=4)
        print(f"[Recorder] Annotations saved to {self.json_file}")

        print("[Recorder] Recording stopped.")

    def _get_process_name(self, element):
        if not element:
            return None
        try:
            return psutil.Process(element.ProcessId).name()
        except psutil.NoSuchProcess:
            return None

    def _log_annotation(self, event_type, event_data, element_hierarchy=None):
        timestamp = time.time() - self.start_time

        # Take screenshots of new elements
        if element_hierarchy:
            for element_info in element_hierarchy:
                self.element_screenshotter.capture_element_screenshot(element_info, timestamp)

        # Serialize bounding_rectangle for JSON output
        import copy
        log_hierarchy = copy.deepcopy(element_hierarchy)
        if log_hierarchy:
            for element_info in log_hierarchy:
                rect = element_info.get('bounding_rectangle')
                if rect:
                    element_info['bounding_rectangle'] = (rect.left, rect.top, rect.right, rect.bottom)

        annotation = {
            "timestamp": timestamp,
            "event_type": event_type,
            "event_data": event_data,
            "element_hierarchy": log_hierarchy
        }
        self.annotations.append(annotation)

    def _handle_press(self, key):
        pass

    def _handle_release(self, key):
        try:
            element = self.uia_helper.get_focused_element()
            process_name = self._get_process_name(element)
            if self.whitelist and (not process_name or process_name.lower() not in [p.lower() for p in self.whitelist]):
                return
            self.media_recorder.overlays.clear()
            hierarchy = self.uia_helper.get_element_hierarchy(element, self.whitelist)
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255)]
            if hierarchy:
                for i, element_info in enumerate(hierarchy):
                    rect = element_info.get('bounding_rectangle')
                    if rect:
                        color = colors[i % len(colors)]
                        self.media_recorder.add_overlay((rect.left, rect.top, rect.right, rect.bottom), element_info['id'], color)
            self._log_annotation("key_release", str(key), hierarchy)
        except Exception as e:
            print(f"[Recorder] Error in _handle_release: {e}")
            self._log_annotation("key_release", str(key), None)

    def _handle_click(self, x, y, button, pressed):
        action = 'pressed' if pressed else 'released'
        try:
            element = self.uia_helper.get_element_from_point(x, y)
            process_name = self._get_process_name(element)
            if self.whitelist and (not process_name or process_name.lower() not in [p.lower() for p in self.whitelist]):
                return
            self.media_recorder.overlays.clear()
            hierarchy = self.uia_helper.get_element_hierarchy(element, self.whitelist)
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255)]
            if hierarchy:
                # Reverse the hierarchy to draw from parent to child
                for i, element_info in enumerate(reversed(hierarchy)):
                    rect = element_info.get('bounding_rectangle')
                    if rect:
                        color = colors[i % len(colors)]
                        self.media_recorder.add_overlay((rect.left, rect.top, rect.right, rect.bottom), element_info['id'], color)
            self.media_recorder.set_clickoverlay(x, y, str(button))
            self._log_annotation("mouse_click", {"x": x, "y": y, "button": str(button), "action": action}, hierarchy)
        except Exception as e:
            print(f"[Recorder] Error in _handle_click: {e}")
            self._log_annotation("mouse_click", {"x": x, "y": y, "button": str(button), "action": action}, None)
