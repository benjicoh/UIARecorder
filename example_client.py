import asyncio
import time
from fastmcp import Client

async def main():
    """
    An example client to connect to the UIADumpServer and call its tools.

    To use this:
    1. Run the server in a separate terminal: `python mcp_server.py`
    2. Run this client script: `python example_client.py`
    """
    async with Client("mcp_server.py") as client:
        print("Connected to server. Listing available tools...")
        tools = await client.list_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")

        # Example 1: Dump Notepad's UI using its window title
        print("\n--- Example 1: Dumping Notepad UI by Window Title ---")
        try:
            result = await client.call_tool(
                "DumpUIAsJson",
                {"processOrTopLevelWindow": "Notepad", "jsonPath": "notepad_dump_by_title.json"}
            )
            print(f"Server response: {result.text}")
        except Exception as e:
            print(f"An error occurred: {e}")
            print("This is expected if not on Windows or Notepad is not running.")

        # Example 2: Placeholder for dumping by Process ID
        print("\n--- Example 2: Dumping by Process ID (Placeholder) ---")
        print("To test this, replace '12345' with an actual PID.")
        try:
            result = await client.call_tool(
                "DumpUIAsJson",
                {"processOrTopLevelWindow": "12345", "jsonPath": "dump_by_pid.json"}
            )
            print(f"Server response: {result.text}")
        except Exception as e:
            print(f"An error occurred: {e}")

        # Example 3: Full workflow for taking a screenshot
        print("\n--- Example 3: Full Workflow for Screenshot ---")
        dump_file = "full_workflow_dump.json"
        screenshot_file = "title_bar_screenshot.png"
        try:
            print(f"Step 1: Dumping UI for 'Notepad' to {dump_file}")
            await client.call_tool(
                "DumpUIAsJson",
                {"processOrTopLevelWindow": "Notepad", "jsonPath": dump_file}
            )
            query = "$.children[0]"
            print(f"Step 2: Capturing element from query '{query}' to {screenshot_file}")
            result = await client.call_tool(
                "CaptureElementScreenshot",
                {"jsonPath": dump_file, "query": query, "screenshotPath": screenshot_file}
            )
            print(f"Server response: {result.text}")
        except Exception as e:
            print(f"An error occurred during the full workflow: {e}")

        # Example 4: User Input Simulation
        print("\n--- Example 4: User Input Simulation ---")
        print("Note: These examples will interact with your screen. Make sure Notepad is focused.")
        time.sleep(3)
        try:
            print("\n- Sending keystrokes to type 'Hello, World!'")
            await client.call_tool("SendKeyStrokes", {"string": "Hello, World!"})

            file_menu_location = (30, 50)
            print(f"\n- Sending mouse click to location {file_menu_location}")
            await client.call_tool("SendMouseClick", {"location": file_menu_location})
            time.sleep(1)

            start_drag = (100, 150)
            end_drag = (300, 150)
            print(f"\n- Sending mouse drag from {start_drag} to {end_drag}")
            await client.call_tool("SendMouseDrag", {"startLocation": start_drag, "endLocation": end_drag})
        except Exception as e:
            print(f"An error occurred during input simulation: {e}")

if __name__ == "__main__":
    asyncio.run(main())
