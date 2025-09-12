## Goal
- Generate a robust windows desktop automation script using python [uiautomation package](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows).

## UIA Documentation
For more details on UI Automation elements and patterns, refer to the official Microsoft documentation:
- [AutomationElement Class](https://learn.microsoft.com/en-us/dotnet/api/system.windows.automation.automationelement?view=windowsdesktop-9.0)
- [UI Automation Control Patterns](https://learn.microsoft.com/en-us/dotnet/framework/ui-automation/ui-automation-control-patterns)

## Inputs
- A video file with narration of the test scenario.
- A json file with the UIA properties of the clicked and focused elements.
- A series of screenshots for each user interaction, with annotations.

## JSON Format
The JSON file contains a list of events, each with the following structure:
```json
{
    "timestamp": 12.345,
    "event_type": "mouse_click",
    "event_data": { ... },
    "element_hierarchy": [
        {
            "id": "element-1",
            "name": "Button",
            "class_name": "Button",
            "control_type": "ButtonControl",
            "patterns": { ... },
            ...
        },
        ...
    ]
}
```
- Each element in the `element_hierarchy` has a unique `id`.
- The `patterns` object lists all the UI Automation patterns supported by the element. Refer to this to understand the available actions for an element (e.g., `InvokePattern`, `ValuePattern`).

## Element Screenshots
For each new UI element detected in the hierarchy, a screenshot of that element is captured and saved in the `recording/images` folder.
- The screenshot is taken of the element's bounding rectangle.
- Screenshots are only taken for elements that are on-screen and have a valid, non-zero rectangle.
- The filename for each screenshot is in the format `{element_id}__{timestamp}.png`, where the timestamp is the number of milliseconds from the start of the recording.

## Guidelines
- The script should be robust and able to handle various UI scenarios.
- If ambiguity arises in identifying elements, consider using additional properties or a combination of properties to disambiguate.
- Use appropriate error handling to manage unexpected UI states.
- Include comments in the code to explain the logic and flow.
- Provide logging of your actions and any errors encountered.
- Listen to the video's audio, there might be additional context or information that can help with element identification.

## Identifying elements correctly
- Use the `name`, `automation_id`, `class_name`, and `control_type` properties from the JSON file to uniquely identify elements.
- Ignore `N/A` values, they cannot be used as identifiers.
- If multiple elements match the criteria, use additional properties or a combination of properties to disambiguate.
- Always refer to the `element_hierarchy` in the JSON to understand the context of each element.
- **Do not** try to to get the names from the UI
- If no unique element can be identified, consider looking for the image in the screenshot using pyautogui bitmap matching
- Use the patterns in the json file to understand the control's behavior and available actions.
- You can cross correlate the element id with screenshot filename, to better understand where it is

## Usual workflow
- Identify the main window of the application
- Activate it at the start of the recording
- Based on the narration, video and json, identify the key uia elements involved, and their unique properties
- Use the elements identified in the script
- After generating the script, review it to ensure all elements are correctly identified and the actions are appropriate.

### Conversational Refinement
If you are provided with a log file from a previous execution (`automation_log.txt`) or a full UI dump (`dump.json`), use them to refine the script.
- **`automation_log.txt`**: This file contains the output of a previous run of the generated script. Analyze any errors or failures in the log to identify the root cause. Modify the script to fix these issues. For example, if an element was not found, you may need to adjust the selectors or add a wait condition.
- **`dump.json`**: This file contains a full snapshot of the application's UI tree. Use this as a reference to find more robust selectors for elements that were problematic in the previous run. It can also help you understand the overall structure of the application and discover alternative ways to automate a task.

Your goal is to iteratively improve the script based on the feedback from previous runs.