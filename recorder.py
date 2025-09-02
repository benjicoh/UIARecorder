import json
import threading
import time
import pyautogui
import uiautomation as auto
import numpy as np
import cv2
import sounddevice as sd
from scipy.io.wavfile import write as write_wav
import subprocess
import os
import ast
from PIL import Image, ImageDraw, ImageFont

from pynput import keyboard, mouse

class Recorder:
    def __init__(self, output_folder="recording"):
        self.output_folder = output_folder
        self.images_folder = f"{self.output_folder}/images"
        os.makedirs(self.images_folder, exist_ok=True)

        print(f"[Recorder] Output folder set to: {self.output_folder}")

        self.video_file = f"{self.output_folder}/video.mp4"
        self.json_file = f"{self.output_folder}/annotations.json"
        self.temp_video_file = f"{self.output_folder}/temp_video.avi"
        self.temp_audio_file = f"{self.output_folder}/temp_audio.wav"

        print(f"[Recorder] Video will be saved to: {self.video_file}")
        print(f"[Recorder] Annotations will be saved to: {self.json_file}")

        self.is_recording = False
        self.start_time = None
        self.annotations = []
        self.element_id_counter = 1
        self.element_ids = {}
        self.screenshot_counter = 1

        self.screen_size = pyautogui.size()
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.video_writer = None
        self.audio_frames = []

        self.keyboard_listener = None
        self.mouse_listener = None
        self.highlight_thread = None

    def _record_video(self):
        print("[Recorder] Video recording thread started.")
        self.video_writer = cv2.VideoWriter(self.temp_video_file, self.fourcc, 20.0, (self.screen_size.width, self.screen_size.height))
        while self.is_recording:
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.video_writer.write(frame)
        print("[Recorder] Video recording thread stopped.")

    def _record_audio(self):
        print("[Recorder] Audio recording thread started.")
        try:
            samplerate = 44100
            channels = 1
            self.audio_frames = []

            def callback(indata, frames, time, status):
                if status:
                    print(f"[Recorder] Audio status: {status}")
                self.audio_frames.append(indata.copy())

            with sd.InputStream(samplerate=samplerate, channels=channels, callback=callback):
                while self.is_recording:
                    time.sleep(0.1)
        except Exception as e:
            print(f"[Recorder] Audio recording failed: {e}")
        print("[Recorder] Audio recording thread stopped.")

    def start(self):
        print("[Recorder] Starting recording...")
        self.is_recording = True
        self.start_time = time.time()

        self.video_thread = threading.Thread(target=self._record_video)
        self.audio_thread = threading.Thread(target=self._record_audio)
        self.highlight_thread = threading.Thread(target=self._highlight_element)

        self.video_thread.start()
        self.audio_thread.start()
        self.highlight_thread.start()

        self.keyboard_listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self.mouse_listener = mouse.Listener(on_click=self._on_click)

        self.keyboard_listener.start()
        self.mouse_listener.start()

        print("[Recorder] Recording started.")

    def _highlight_element(self):
        print("[Recorder] Highlight thread started.")
        auto.UIAutomationInitializerInThread()
        while self.is_recording:
            try:
                x, y = pyautogui.position()
                element = auto.ControlFromPoint(x, y)
                if element:
                    element.ShowDesktopRectangle(color=0xFF0000, width=3)
            except Exception:
                pass # Ignore errors
            time.sleep(0.1)
        print("[Recorder] Highlight thread stopped.")

    def stop(self):
        print("[Recorder] Stopping recording...")
        self.is_recording = False

        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()

        if hasattr(self, 'highlight_thread'):
            self.highlight_thread.join()

        self.video_thread.join()
        self.audio_thread.join()

        if self.video_writer:
            self.video_writer.release()

        if self.audio_frames:
            print("[Recorder] Saving audio to file...")
            samplerate = 44100
            write_wav(self.temp_audio_file, samplerate, np.concatenate(self.audio_frames, axis=0))

            # Combine video and audio with ffmpeg
            print("[Recorder] Combining video and audio with ffmpeg...")
            cmd = [
                'ffmpeg',
                '-y', # Overwrite output file if it exists
                '-i', self.temp_video_file,
                '-i', self.temp_audio_file,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-strict', 'experimental',
                self.video_file
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(f"[Recorder] Video with audio saved to {self.video_file}")
            except subprocess.CalledProcessError as e:
                print("[Recorder] ffmpeg error:")
                print(e.stderr)

            # Clean up temp files
            if os.path.exists(self.temp_video_file):
                os.remove(self.temp_video_file)
            if os.path.exists(self.temp_audio_file):
                os.remove(self.temp_audio_file)
        else:
            # If no audio, just rename the video file
            if os.path.exists(self.temp_video_file):
                os.rename(self.temp_video_file, self.video_file)
            print(f"[Recorder] Video saved to {self.video_file} (no audio)")

        with open(self.json_file, 'w') as f:
            json.dump(self.annotations, f, indent=4)
        print(f"[Recorder] Annotations saved to {self.json_file}")

        print("[Recorder] Recording stopped.")

    def _log_annotation(self, event_type, event_data, element_hierarchy=None):
        timestamp = time.time() - self.start_time
        annotation = {
            "timestamp": timestamp,
            "event_type": event_type,
            "event_data": event_data,
            "element_hierarchy": element_hierarchy
        }
        self.annotations.append(annotation)
        

    def _capture_and_annotate_screenshot(self, hierarchy):
        screenshot_path = f"{self.images_folder}/screenshot_{self.screenshot_counter}.png"
        img = pyautogui.screenshot()

        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 15)
        except IOError:
            font = ImageFont.load_default()

        colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF"]
        legend_items = []

        if hierarchy:
            for i, element_info in enumerate(hierarchy):
                if element_info and not element_info['is_offscreen']:
                    try:
                        rect_str = element_info['bounding_rectangle'].split('[')[0]
                        rect = ast.literal_eval(rect_str)

                        color = colors[i % len(colors)]
                        draw.rectangle(rect, outline=color, width=3)

                        element_id = element_info['id']
                        legend_items.append((color, element_id))
                    except (ValueError, SyntaxError, KeyError) as e:
                        print(f"Could not parse or draw for element: {element_info}. Error: {e}")

        # Draw legend
        legend_y = 10
        for color, element_id in legend_items:
            legend_text = f"{element_id}"
            draw.rectangle([(10, legend_y), (30, legend_y + 20)], fill=color)
            draw.text((40, legend_y + 5), legend_text, fill="white", font=font)
            legend_y += 25

        img.save(screenshot_path)
        self.screenshot_counter += 1
        return screenshot_path

    def _on_press(self, key):
        element = auto.GetFocusedControl()
        hierarchy = self._get_element_hierarchy(element)
        self._capture_and_annotate_screenshot(hierarchy)
        self._log_annotation("key_press", str(key), hierarchy)

    def _on_release(self, key):
        # The main hotkey listener handles Esc
        element = auto.GetFocusedControl()
        hierarchy = self._get_element_hierarchy(element)
        self._log_annotation("key_release", str(key), hierarchy)

    def _on_click(self, x, y, button, pressed):
        action = 'pressed' if pressed else 'released'
        element = auto.ControlFromPoint(x, y)
        hierarchy = self._get_element_hierarchy(element)
        self._capture_and_annotate_screenshot(hierarchy)
        self._log_annotation("mouse_click", {"x": x, "y": y, "button": str(button), "action": action}, hierarchy)

    def _get_element_info(self, element):
        if not element:
            return None

        runtime_id = element.RuntimeId
        if runtime_id not in self.element_ids:
            self.element_ids[runtime_id] = f"element-{self.element_id_counter}"
            self.element_id_counter += 1

        element_id = self.element_ids[runtime_id]

        return {
            'id': element_id,
            'name': element.Name,
            'class_name': element.ClassName,
            'control_type': element.ControlTypeName,
            'bounding_rectangle': str(element.BoundingRectangle),
            'is_offscreen': element.IsOffscreen
        }

    def _get_element_hierarchy(self, element):
        if not element:
            return None
        hierarchy = []
        current = element
        while current:
            hierarchy.append(self._get_element_info(current))
            current = current.GetParentControl()
        return hierarchy

if __name__ == "__main__":
    recorder = Recorder()

    def on_activate_record():
        if recorder.is_recording:
            recorder.stop()
        else:
            recorder.start()

    hotkey = keyboard.HotKey(
        keyboard.HotKey.parse('<alt>+<shift>+r'),
        on_activate_record)

    def on_press(key):
        hotkey.press(listener.canonical(key))

    def on_release(key):
        hotkey.release(listener.canonical(key))
        if key == keyboard.Key.esc:
            if recorder.is_recording:
                recorder.stop()
            return False # Stop listener

    print("[Main] Press Alt+Shift+R to start/stop recording. Press Esc to exit.")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        print("[Main] Hotkey listener started.")
        listener.join()
    print("[Main] Exiting script.")
