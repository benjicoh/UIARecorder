import pyautogui
import logging
from typing import List, Tuple

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_keystrokes(string: str, modifiers: List[str] = None):
    """
    Sends keystrokes or a hotkey combination.

    Args:
        string: The text to type or the key to press in a hotkey.
        modifiers: A list of modifier keys (e.g., ['ctrl', 'shift']).
    """
    pyautogui.FAILSAFE = False
    if modifiers:
        # Use hotkey for combinations like Ctrl+C
        pyautogui.hotkey(*modifiers, string)
        logging.info(f"Sent hotkey: {'+'.join(modifiers)} + {string}")
    else:
        # Just type the string
        pyautogui.write(string, interval=0.05)
        logging.info(f"Typed string: {string}")

def send_mouse_click(location: Tuple[int, int], button: str = 'left'):
    """
    Performs a mouse click at a given location.

    Args:
        location: A tuple (x, y) for the screen coordinates.
        button: The mouse button to click ('left', 'middle', 'right').
    """
    pyautogui.FAILSAFE = False
    x, y = location
    pyautogui.click(x, y, button=button)
    logging.info(f"Clicked {button} button at {location}")

def send_mouse_drag(start_location: Tuple[int, int], end_location: Tuple[int, int], button: str = 'left'):
    """
    Performs a mouse drag from a start to an end location.

    Args:
        start_location: A tuple (x, y) for the starting screen coordinates.
        end_location: A tuple (x, y) for the ending screen coordinates.
        button: The mouse button to hold during the drag.
    """
    pyautogui.FAILSAFE = False
    start_x, start_y = start_location
    end_x, end_y = end_location
    pyautogui.moveTo(start_x, start_y)
    pyautogui.dragTo(end_x, end_y, button=button, duration=0.5)
    logging.info(f"Dragged {button} button from {start_location} to {end_location}")

def send_mouse_double_click(location: Tuple[int, int], button: str = 'left'):
    """
    Performs a mouse double click at a given location.

    Args:
        location: A tuple (x, y) for the screen coordinates.
        button: The mouse button to double-click.
    """
    pyautogui.FAILSAFE = False
    x, y = location
    pyautogui.doubleClick(x, y, button=button)
    logging.info(f"Double-clicked {button} button at {location}")
