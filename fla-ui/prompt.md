## Goal
- Generate a robust Windows desktop automation script using C# and the [FlaUI library](https://github.com/FlaUI/FlaUI).
- The generated code should be placed within the `GeneratedTest` method of the `FlaUI.Generated.GeneratedTests` class.
- Use MSTest assertions to verify the success of the automation.

## Inputs

### Recording Directory
- A video file with narration of the test scenario.
- A JSON file with the UIA properties of the clicked and focused elements.
### Failed Run Artifacts (Optional)
- A video of the failed execution.
- Log file from a previous execution of the generated script, containing errors or failures.
- A full JSON snapshot of the application's UI tree from a previous run, useful for refining element selectors.

## Output
- C# code that uses the FlaUI library to automate the described scenario.
- The code should be like the `Code Template` below, fully self-contained and compilable.

## Recording JSON Format
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

## Guidelines
- The script should be robust and able to handle various UI scenarios.
- If ambiguity arises in identifying elements, consider using additional properties or a combination of properties to disambiguate.
- Use appropriate error handling to manage unexpected UI states.
- Include comments in the code to explain the logic and flow.
- Listen to the video's audio, there might be additional context or information that can help with element identification.
- It is useful to identify the main window of the application, and activate it at the start of the script.
- Use MSTest logging to provide insights into the script's execution flow (`Logger.LogMessage` under `Microsoft.VisualStudio.TestTools.UnitTesting.Logging`).

## Identifying elements correctly
- Use the `Name`, `AutomationId`, `ClassName`, and `ControlType` properties from the JSON file to uniquely identify elements.
- Ignore `N/A` values, they cannot be used as identifiers.
- If multiple elements match the criteria, use additional properties or a combination of properties to disambiguate.
- Always refer to the `element_hierarchy` in the JSON to understand the context of each element.
- **Do not** try to to get the names from the UI
- Use the patterns in the json file to understand the control's behavior and available actions.
- You can cross correlate the element id with screenshot filename, to better understand where it is

## FlaUI Best Practices
- Use the `automation` object to interact with the application.
- Use `app.GetMainWindow(automation)` to get the main window of the application.
- Use `mainWindow.FindFirstDescendant(cf => cf.ByAutomationId("MyButton"))` to find elements.
- Use `element.Click()` to click on elements.
- Use `element.AsTextBox().Enter("text")` to enter text into text boxes.
- Use `Assert.IsTrue()` to verify conditions.

## Usual workflow

### Initial Script Generation
- Based on the narration, video and json, identify the key uia elements involved, and their unique properties
- Use the elements identified in the script
- After generating the script, review it to ensure all elements are correctly identified and the actions are appropriate.

### Actual Runs Refinement
If you are provided with a log file from a previous execution and / or a full UI dump, use them to refine the script.
- **Logs**: This file contains the output of a previous run of the generated script. Analyze any errors or failures in the log to identify the root cause. Modify the script to fix these issues. For example, if an element was not found, you may need to adjust the selectors or add a wait condition.
- **UI Dump**: This file contains a full snapshot of the application's UI tree. Use this as a reference to find more robust selectors for elements that were problematic in the previous run. It can also help you understand the overall structure of the application and discover alternative ways to automate a task.

## Code Template
```csharp
using FlaUI.Core;
using FlaUI.Core.AutomationElements;
using FlaUI.Core.Conditions;
using FlaUI.UIA3;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using System.Diagnostics;

namespace FlaUI.Generated
{
    [TestClass]
    public class GeneratedTests
    {
        private readonly UIA3Automation _automation = new UIA3Automation();

        [TestCleanup]
        public void Cleanup()
        {
            _automation.Dispose();
        }

        [TestMethod]
        public void GeneratedTest()
        {
            // Test code will be generated here
        }
    }
}
```