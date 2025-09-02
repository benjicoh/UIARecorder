## Goal
- Generate a robust windows desktop automation script using python uiautomation package

## Inputs
- A video file with narration of the test scenario
- A json file with the UIA properties of the clicked elements and the focused elements in the following format
```json
{
    [
        "timestamp": 11.212849378585815, // relative to video start in seconds
        "event_type": "mouse_click",
        "event_data": {
            "x": 1179,
            "y": 422,
            "button": "Button.left",
            "action": "released"
        },
        "element_hierarchy": [ //route to desktop from element from point traversing its parents
            {
                "name": "Display is 3",
                "class_name": "",
                "control_type": "TextControl",
                "bounding_rectangle": "(879,396,1199,471)[320x75]",
                "is_offscreen": false
            },
            ...
            {
                "name": "Calculator",
                "class_name": "ApplicationFrame",
                "control_type": "Window",
                "bounding_rectangle": "(100,100,800,600)[700x500]",
                "is_offscreen": false
            }]
        },...
    ]
}
```

## Guidelines
- The script should be robust and able to handle various UI scenarios.
- Pay close attention to the element hierarchy and control properties defined in the JSON file. Correctly identify the elements based on that.
- If ambiguity arises in identifying elements, consider using additional properties or a combination of properties to disambiguate.
- Use appropriate error handling to manage unexpected UI states.
- Include comments in the code to explain the logic and flow.
- Provide logging of your actions and any errors encountered.