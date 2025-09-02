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

from pynput import keyboard, mouse

class Recorder:
    def __init__(self, output_folder="recording"):
        self.output_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)

        self.video_file = f"{self.output_folder}/video.mp4"
        self.json_file = f"{self.output_folder}/annotations.json"
        self.temp_video_file = f"{self.output_folder}/temp_video.avi"
        self.temp_audio_file = f"{self.output_folder}/temp_audio.wav"

        self.is_recording = False
        self.start_time = None
        self.annotations = []

        self.screen_size = pyautogui.size()
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.video_writer = None
        self.audio_frames = []

        self.keyboard_listener = None
        self.mouse_listener = None
        self.highlight_thread = None

    def _record_video(self):
        self.video_writer = cv2.VideoWriter(self.temp_video_file, self.fourcc, 20.0, (self.screen_size.width, self.screen_size.height))
        while self.is_recording:
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.video_writer.write(frame)

    def _record_audio(self):
        try:
            samplerate = 44100
            channels = 2
            self.audio_frames = []

            def callback(indata, frames, time, status):
                if status:
                    print(status)
                self.audio_frames.append(indata.copy())

            with sd.InputStream(samplerate=samplerate, channels=channels, callback=callback):
                while self.is_recording:
                    time.sleep(0.1)
        except Exception as e:
            print(f"Audio recording failed: {e}")

    def start(self):
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

        print("Recording started.")

    def _highlight_element(self):
        while self.is_recording:
            try:
                x, y = pyautogui.position()
                element = auto.ControlFromPoint(x, y)
                if element:
                    element.ShowDesktopRectangle(color=0xFF0000, width=3)
            except Exception:
                pass # Ignore errors
            time.sleep(0.1)

    def stop(self):
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
            samplerate = 44100
            write_wav(self.temp_audio_file, samplerate, np.concatenate(self.audio_frames, axis=0))

            # Combine video and audio with ffmpeg
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
            except subprocess.CalledProcessError as e:
                print("ffmpeg error:")
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

        with open(self.json_file, 'w') as f:
            json.dump(self.annotations, f, indent=4)

        print("Recording stopped.")

    def _log_annotation(self, event_type, event_data, element_hierarchy=None):
        timestamp = time.time() - self.start_time
        self.annotations.append({
            "timestamp": timestamp,
            "event_type": event_type,
            "event_data": event_data,
            "element_hierarchy": element_hierarchy
        })

    def _on_press(self, key):
        element = auto.GetFocusedControl()
        hierarchy = get_element_hierarchy(element)
        self._log_annotation("key_press", str(key), hierarchy)

    def _on_release(self, key):
        # The main hotkey listener handles Esc
        element = auto.GetFocusedControl()
        hierarchy = get_element_hierarchy(element)
        self._log_annotation("key_release", str(key), hierarchy)

    def _on_click(self, x, y, button, pressed):
        action = 'pressed' if pressed else 'released'
        element = auto.ControlFromPoint(x, y)
        hierarchy = get_element_hierarchy(element)
        self._log_annotation("mouse_click", {"x": x, "y": y, "button": str(button), "action": action}, hierarchy)

def get_element_info(element):
    if not element:
        return None
    return {
        'name': element.Name,
        'class_name': element.ClassName,
        'control_type': element.ControlTypeName,
        'bounding_rectangle': str(element.BoundingRectangle),
        'is_offscreen': element.IsOffscreen
    }

def get_element_hierarchy(element):
    if not element:
        return None
    hierarchy = []
    current = element
    while current:
        hierarchy.append(get_element_info(current))
        current = current.GetParentControl()
    return hierarchy

if __name__ == "__main__":
    recorder = Recorder()
    hotkey_pressed = set()

    def on_press(key):
        global recorder, hotkey_pressed
        # Use a specific set for the hotkey to avoid conflicts
        hotkey_combo = {keyboard.Key.alt_l, keyboard.Key.shift, keyboard.KeyCode.from_char('r')}

        if key in hotkey_combo:
            hotkey_pressed.add(key)
            if hotkey_pressed == hotkey_combo:
                if recorder.is_recording:
                    recorder.stop()
                else:
                    recorder.start()

    def on_release(key):
        global hotkey_pressed, listener
        if key in hotkey_pressed:
            hotkey_pressed.remove(key)

        if key == keyboard.Key.esc:
            if recorder.is_recording:
                recorder.stop()
            # Stop the main listener
            listener.stop()

    print("Press Alt+Shift+R to start/stop recording. Press Esc to exit.")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
