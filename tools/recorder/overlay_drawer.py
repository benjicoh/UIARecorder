import cv2
import numpy as np

def draw_rectangle(image, bounding_box, color, width, element_id):
    """Draws a rectangle and element ID on the image."""
    left, top, right, bottom = bounding_box
    # Draw the rectangle
    cv2.rectangle(image, (left, top), (right, bottom), color, width)
    # Put the element ID on top of the rectangle
    cv2.putText(image, element_id, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
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
    cv2.line(image, (x - cursor_size, y), (x + cursor_size, y), cursor_color, 2)
    cv2.line(image, (x, y - cursor_size), (x, y + cursor_size), cursor_color, 2)
    return image
