## Goal
- Generate a robust windows desktop automation script using python [uiautomation package](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows).

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
            ...
        },
        ...
    ]
}
```
Each element in the `element_hierarchy` now has a unique `id`.

## Annotated Screenshots
For each mouse click and key press, a screenshot is captured. These images are saved in the `recording/images` folder.
The screenshots include:
- A colored border around each UI element in the path to the root.
- A legend at the top-left of the image that maps each color to its corresponding `id` from the JSON file.

## Guidelines
- The script should be robust and able to handle various UI scenarios.
- Pay close attention to the element hierarchy and control properties defined in the JSON file. Correctly identify the elements based on that.
- If ambiguity arises in identifying elements, consider using additional properties or a combination of properties to disambiguate.
- Use appropriate error handling to manage unexpected UI states.
- Include comments in the code to explain the logic and flow.
- Provide logging of your actions and any errors encountered.