import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

import threading
import time
import pyautogui
import numpy as np
import cv2
import sounddevice as sd
from scipy.io.wavfile import write as write_wav
import subprocess
from tools.recorder import overlay_drawer

class MediaRecorder:
    def __init__(self, output_folder, record_audio=True):
        self.output_folder = output_folder
        self.video_file = f"{self.output_folder}/video.mp4"
        self.temp_video_file = f"{self.output_folder}/temp_video.avi"
        self.temp_audio_file = f"{self.output_folder}/temp_audio.wav"
        self.record_audio = record_audio

        self.is_recording = False
        self.screen_size = pyautogui.size()
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.video_writer = None
        self.audio_frames = []
        self.video_thread = None
        self.audio_thread = None
        self.overlays = []
        self.click_overlay = None

    def start(self):
        self.is_recording = True
        self.video_thread = threading.Thread(target=self._record_video)
        self.video_thread.start()
        if self.record_audio:
            self.audio_thread = threading.Thread(target=self._record_audio)
            self.audio_thread.start()

    def stop(self):
        self.is_recording = False
        if self.video_thread:
            self.video_thread.join()
        if self.record_audio and self.audio_thread:
            self.audio_thread.join()

        if self.video_writer:
            self.video_writer.release()

        if self.record_audio and self.audio_frames:
            samplerate = 44100
            write_wav(self.temp_audio_file, samplerate, np.concatenate(self.audio_frames, axis=0))

            cmd = [
                'ffmpeg', '-y', '-i', self.temp_video_file, '-i', self.temp_audio_file,
                '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental', self.video_file
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                print(f"[MediaRecorder] ffmpeg error: {e.stderr}")

            if os.path.exists(self.temp_video_file):
                os.remove(self.temp_video_file)
            if os.path.exists(self.temp_audio_file):
                os.remove(self.temp_audio_file)
        else:
            if os.path.exists(self.temp_video_file):
                # Convert AVI to MP4 using ffmpeg
                cmd = [
                    'ffmpeg', '-y', '-i', self.temp_video_file,
                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '22',
                    self.video_file
                ]
                try:
                    print("[MediaRecorder] Converting video to MP4...")
                    subprocess.run(cmd, check=True, capture_output=True, text=True)
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    stderr = e.stderr if hasattr(e, 'stderr') else "ffmpeg not found"
                    print(f"[MediaRecorder] ffmpeg error: {stderr}")
                    print("[MediaRecorder] Falling back to renaming AVI file.")
                    # Fallback to renaming if ffmpeg fails or is not installed
                    os.rename(self.temp_video_file, f"{self.output_folder}/video.avi")
                finally:
                    if os.path.exists(self.temp_video_file):
                        os.remove(self.temp_video_file)

    def add_overlay(self, bounding_box, element_id, color):
        self.overlays.append({
            "bounding_box": bounding_box,
            "element_id": element_id,
            "color": color,
            "ttl": 20
        })

    def set_clickoverlay(self, x, y, button):
        self.click_overlay = {
            "x": x,
            "y": y,
            "button": button,
            "ttl": 20
        }

    def _record_video(self):
        print("[MediaRecorder] Video recording thread started.")
        self.video_writer = cv2.VideoWriter(self.temp_video_file, self.fourcc, 20.0, (self.screen_size.width, self.screen_size.height))
        while self.is_recording:
            try:
                img = pyautogui.screenshot()
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Draw overlays
                for overlay in self.overlays:
                    frame = overlay_drawer.draw_rectangle(frame, overlay["bounding_box"], overlay["color"], 2, overlay["element_id"])
                # Draw mouse cursor
                mouse_x, mouse_y = pyautogui.position()
                frame = overlay_drawer.draw_cursor(frame, (mouse_x, mouse_y))
                # Draw click overlay if exists
                if self.click_overlay:
                    frame = overlay_drawer.draw_circle(frame, (self.click_overlay["x"], self.click_overlay["y"]), 15, (0, 255, 0) if self.click_overlay["button"] == 'Button.left' else (255, 0, 0))
                    self.click_overlay["ttl"] -= 1
                    if self.click_overlay["ttl"] <= 0:
                        self.click_overlay = None
                # Update overlays TTL
                self.overlays = [overlay for overlay in self.overlays if overlay["ttl"] > 0]
                for overlay in self.overlays:
                    overlay["ttl"] -= 1

                self.video_writer.write(frame)
            except Exception as e:
                print(f"[MediaRecorder] Error during video frame capture: {e}")
                time.sleep(0.1)
        print("[MediaRecorder] Video recording thread stopped.")

    def _record_audio(self):
        print("[MediaRecorder] Audio recording thread started.")
        try:
            samplerate = 44100
            channels = 1
            self.audio_frames = []

            def callback(indata, frames, time, status):
                if status:
                    print(f"[MediaRecorder] Audio status: {status}")
                self.audio_frames.append(indata.copy())

            with sd.InputStream(samplerate=samplerate, channels=channels, callback=callback):
                while self.is_recording:
                    time.sleep(0.1)
        except Exception as e:
            print(f"[MediaRecorder] Audio recording failed: {e}")
        print("[MediaRecorder] Audio recording thread stopped.")
