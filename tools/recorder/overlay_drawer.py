import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

import cv2
import numpy as np

def draw_rectangle(image, bounding_box, color, width, element_id):
    """Draws a rectangle and element ID on the image."""
    left, top, right, bottom = bounding_box
    # Draw the rectangle
    image = cv2.rectangle(image, (left, top), (right, bottom), color, width)
    # Put the element ID on top of the rectangle, with outline for better visibility
    image = cv2.putText(image, element_id, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 4)
    image = cv2.putText(image, element_id, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
    return image

def draw_circle(image, position, radius, color):
    """Draws a semi-transparent circle on the image."""
    overlay = image.copy()
    cv2.circle(overlay, position, radius, color, -1)
    alpha = 0.4
    image = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
    return image

def draw_cursor(image, position):
    """Draws the mouse cursor on the image."""
    cursor_color = (0, 0, 255)  # Red color for the cursor
    cursor_size = 10
    # Draw a simple crosshair cursor
    x, y = position
    image = cv2.line(image, (x - cursor_size, y), (x + cursor_size, y), cursor_color, 2)
    image = cv2.line(image, (x, y - cursor_size), (x, y + cursor_size), cursor_color, 2)
    return image
