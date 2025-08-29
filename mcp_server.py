from fastmcp import FastMCP, Context
import uiautomation as auto
import json
import time
from uia_dumper import traverse_element_tree
from screenshot_tool import take_screenshot_of_element
from input_tools import (
    send_keystrokes,
    send_mouse_click,
    send_mouse_drag,
    send_mouse_double_click,
)

# Create a server instance
mcp = FastMCP(name="UIADumpServer")

@mcp.tool
async def DumpUIAsJson(processOrTopLevelWindow: str, jsonPath: str, ctx: Context) -> str:
    """
    Dumps the UI Automation tree of a given process or top-level window to a JSON file.

    Args:
        processOrTopLevelWindow: The process ID, or the name/title of the top-level window to dump.
        jsonPath: The path to the output JSON file.
    """
    await ctx.info(f"Attempting to dump UI for: {processOrTopLevelWindow}")
    try:
        window = None
        try:
            pid = int(processOrTopLevelWindow)
            await ctx.info(f"Interpreted '{processOrTopLevelWindow}' as a Process ID. Searching for window with PID: {pid}")
            window = auto.WindowControl(ProcessId=pid)
        except ValueError:
            await ctx.info(f"Interpreted '{processOrTopLevelWindow}' as a window name/title.")
            window = auto.WindowControl(searchDepth=1, Name=processOrTopLevelWindow)

        if not window or not window.Exists(5, 1):
            await ctx.info(f"Window for '{processOrTopLevelWindow}' not found with exact match. Trying regex search.")
            window = auto.WindowControl(searchDepth=1, searchInterval=1, RegexName=f'.*{processOrTopLevelWindow}.*')

        if not window or not window.Exists(5, 1):
            raise Exception(f"Could not find a window or process matching '{processOrTopLevelWindow}'.")

        await ctx.info(f"Found window: {window.Name}")
        uia_tree = traverse_element_tree(window)
        with open(jsonPath, 'w', encoding='utf-8') as f:
            json.dump(uia_tree, f, indent=4, ensure_ascii=False)

        success_message = f"Successfully dumped UI tree to {jsonPath}"
        await ctx.info(success_message)
        return success_message
    except Exception as e:
        error_message = f"Error during UI dump: {e}"
        await ctx.error(error_message)
        return error_message

@mcp.tool
async def CaptureElementScreenshot(jsonPath: str, query: str, screenshotPath: str, ctx: Context) -> str:
    """
    Captures a screenshot of a single element identified by a JSONPath query
    against a UI dump file.
    """
    await ctx.info(f"Attempting to capture screenshot from '{jsonPath}' with query '{query}'")
    try:
        take_screenshot_of_element(jsonPath, query, screenshotPath)
        success_message = f"Screenshot successfully saved to {screenshotPath}"
        await ctx.info(success_message)
        return success_message
    except (ValueError, RuntimeError) as e:
        error_message = f"Error capturing screenshot: {e}"
        await ctx.error(error_message)
        return error_message

@mcp.tool
async def SendKeyStrokes(string: str, modifiers: list = None, ctx: Context) -> str:
    await ctx.info(f"Sending keystrokes: '{string}' with modifiers: {modifiers}")
    send_keystrokes(string, modifiers)
    return "Keystrokes sent."

@mcp.tool
async def SendMouseClick(location: tuple, button: str = 'left', ctx: Context) -> str:
    await ctx.info(f"Sending mouse click to {location} with button '{button}'")
    send_mouse_click(location, button)
    return "Mouse click sent."

@mcp.tool
async def SendMouseDrag(startLocation: tuple, endLocation: tuple, button: str = 'left', ctx: Context) -> str:
    await ctx.info(f"Sending mouse drag from {startLocation} to {endLocation}")
    send_mouse_drag(startLocation, endLocation, button)
    return "Mouse drag sent."

@mcp.tool
async def SendMouseDoubleClick(location: tuple, button: str = 'left', ctx: Context) -> str:
    await ctx.info(f"Sending mouse double click to {location}")
    send_mouse_double_click(location, button)
    return "Mouse double click sent."

if __name__ == "__main__":
    mcp.run()
