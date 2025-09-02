import json
import time
import pyautogui
import ast
from PIL import Image, ImageDraw, ImageFont
import os

class Annotator:
    def __init__(self, output_folder):
        self.output_folder = output_folder
        self.images_folder = f"{self.output_folder}/images"
        self.json_file = f"{self.output_folder}/annotations.json"
        self.annotations = []
        self.screenshot_counter = 1
        self.start_time = None

    def start(self):
        self.start_time = time.time()
        self.annotations = []
        self.screenshot_counter = 1

    def stop(self):
        with open(self.json_file, 'w') as f:
            json.dump(self.annotations, f, indent=4)
        print(f"[Annotator] Annotations saved to {self.json_file}")

    def log_annotation(self, event_type, event_data, element_hierarchy=None):
        timestamp = time.time() - self.start_time
        annotation = {
            "timestamp": timestamp,
            "event_type": event_type,
            "event_data": event_data,
            "element_hierarchy": element_hierarchy
        }
        self.annotations.append(annotation)

    def capture_and_annotate_screenshot(self, hierarchy):
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
                if element_info and not element_info.get('is_offscreen', True):
                    try:
                        # Handle cases where bounding_rectangle might be 'N/A'
                        if 'N/A' in str(element_info['bounding_rectangle']):
                            continue
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
