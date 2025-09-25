## Goal
- Generate a robust Windows desktop automation script using C# and the [FlaUI library](https://github.com/FlaUI/FlaUI).

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
- The code must have correct indentation for easy reading.
- The generated code will be a test method inside the `GeneratedTests` class. The project is an MSTest project.
- The solution contains pre-existing helper classes: `Helpers.cs`, `Logger.cs`, `Xpaths.cs`, and `Extensions.cs`. You should use them.
- The logging must use the `Logger` class.

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
- The `[TestInitialize]` method in `GeneratedTests.cs` will handle launching or attaching to the application. Your generated code should be placed within the `[TestMethod]`.
- Use `Logger` logging to provide insights into the script's execution flow.
- Prefer FlaUI `Find*XPath` methods when possible for better readability. Store new XPath strings in the `Xpaths.cs` file.
- Use MSTest's `Assert` methods to verify outcomes. `Logger.LogPassed` or `Logger.LogFailed` can be used to provide additional detail on the test result.

## Identifying elements correctly
- Use the `Name`, `AutomationId`, `ClassName`, and `ControlType` properties from the JSON file to uniquely identify elements.
- Ignore `N/A` values, they cannot be used as identifiers.
- If multiple elements match the criteria, use additional properties or a combination of properties to disambiguate.
- Always refer to the `element_hierarchy` in the JSON to understand the context of each element.
- **Do not** try to to get the names from the UI
- Use the patterns in the json file to understand the control's behavior and available actions.
- You can cross correlate the element id with screenshot filename, to better understand where it is


## Usual workflow

### Initial Script Generation
- Based on the narration, video and json, identify the key uia elements involved, and their unique properties.
- Add new XPath selectors to `Xpaths.cs`.
- Implement the test logic within the `TestMethod1` of the `GeneratedTests.cs` file.
- After generating the script, review it to ensure all elements are correctly identified and the actions are appropriate.

### Actual Runs Refinement
If you are provided with a log file from a previous execution and / or a full UI dump, use them to refine the script.
- **Logs**: This file contains the output of a previous run of the generated script. Analyze any errors or failures in the log to identify the root cause. Modify the script to fix these issues. For example, if an element was not found, you may need to adjust the selectors or add a wait condition.
- **UI Dump**: This file contains a full snapshot of the application's UI tree. Use this as a reference to find more robust selectors for elements that were problematic in the previous run. It can also help you understand the overall structure of the application and discover alternative ways to automate a task.

## Code Template
```csharp
using Microsoft.VisualStudio.TestTools.UnitTesting;
using FlaUI.Core;
using FlaUI.UIA3;
using FlaUI.Core.AutomationElements;

namespace FlaUI.Generated
{
    [TestClass]
    public class GeneratedTests
    {
        private UIA3Automation automation;
        private Application app;

        [TestInitialize]
        public void Setup()
        {
            automation = new UIA3Automation();
            // TODO: Launch or attach to the application
            // app = Application.Launch("notepad.exe");
            // app = Application.Attach("process_name");
        }

        [TestCleanup]
        public void Teardown()
        {
            app?.Close();
            automation?.Dispose();
        }

        [TestMethod]
        public void TestMethod1()
        {
            // Your test logic goes here.
        }
    }
}
```

## Project Structure and Helper Functions

**Do not implement these classes/functions, they are already implemented and ready to be used.**

### `Logger.cs`
Provides static methods for logging.
```csharp
Logger.LogInfo("This is an info message");
Logger.LogWarning("This is a warning message");
Logger.LogError("This is an error message");
Logger.LogPassed("Test passed successfully");
Logger.LogFailed("Test failed with an error");
```

### `Xpaths.cs`
A static class to store all XPath strings.
```csharp
public static class Xpaths
{
    public const string NotepadEditor = "/Window/Document";
}

// Usage in a test:
var editor = app.WaitFor(automation, Xpaths.NotepadEditor, 5000);
```

### `Helpers.cs`
Contains helper methods for finding windows.
```csharp
Helpers.GetWindowByName(automation, app, "Window Name");
Helpers.GetWindowByAutomationID(automation, app, "AutomationId");
```

### `Extensions.cs`
Provides extension methods for `Application` and `AutomationElement`.

**`ApplicationExtensions`**
```csharp
// Waits for the main window to appear and then finds an element by XPath.
// Throws TimeoutException if the window or element is not found.
AutomationElement element = app.WaitFor(automation, "//Button[@Name='OK']", 5000);
```

**`AutomationElementExtensions`**
```csharp
// Waits for a descendant element to appear.
AutomationElement childElement = parentElement.WaitFor("//ListItem[3]", 2000);

// Clicks an element with a relative offset.
// Clicks 10 pixels right and 5 pixels down from the top-left corner of the element.
element.Click(10, 5);
```

## FLA UI API Reference
This guide provides API documentation for FlaUI developers using UIA3. It focuses on core concepts like the `AutomationElement`, locating elements with XPath, simulating user input with the mouse and keyboard, and using control patterns for advanced interaction.

(The rest of the API reference remains the same)
...