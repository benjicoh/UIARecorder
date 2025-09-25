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
- The code must have correct indentation for easy reading
- The code should be like the `Code Template` below, fully self-contained except the `Helpers` and `Logger` classes, compilable and with namespace `FlaUI.Generated`.
- The logging must use the logging described in the `Logger` class below.

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
- Use `Logger` logging to provide insights into the script's execution flow.
- Prefer FlaUI `Find*XPath` methods when possible, for better readibility.
- The start of the script **should have** the following steps
    - Attach the application using `Application.Attach(process name)`
    - Find the main window of the application using `Helpers.GetWindowByName` or `Helpers.GetWindowByAutomationID`
    - Activate the main window using `window.SetForeground()`
- The end of the run **must either call** `Logger.LogPassed` or `Logger.LogFailed` depending on the success of the run.

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

namespace FlaUI.Generated
{
    public class GeneratedTests
    {

        public static int Main()
        {
            //Test execution code here
        }
    }
}
```

## Helper functions

**Do not implement these functions, they are already implemented and ready to be used**
These functions are implemented and ready to be used with the code you are generatin, but you should to call them:

```csharp
Helpers.GetWindowByName(automation, app, "Window Name");
Helpers.GetWindowByAutomationID(automation, app, "AutomationId");
//Logging
Logger.LogInfo("This is an info message");
Logger.LogWarning("This is a warning message");
Logger.LogError("This is an error message");
Logger.LogPassed("This is a passed message");
Logger.LogFailed("This is a failed message");
```

## FLA UI API Referernce
This guide provides API documentation for FlaUI developers using UIA3. It focuses on core concepts like the `AutomationElement`, locating elements with XPath, simulating user input with the mouse and keyboard, and using control patterns for advanced interaction.

### The AutomationElement

The `AutomationElement` is the central object in FlaUI, representing any UI component you interact with. Every button, text field, window, or grid is an `AutomationElement`. While you can perform generic actions like clicking on any element, you can gain access to more specific methods by converting the generic element into a specialized type.

**Example:**

```csharp
using FlaUI.Core.AutomationElements;
using FlaUI.UIA3;

using var automation = new UIA3Automation();
var app = Application.Attach("EditorProcess.exe");
var window = Helpers.GetWindowByName(automation, app, "Editor Window");

// Find a generic element using XPath, perhaps a button inside a specific toolbar
var saveButtonElement = window.FindFirstByXPath("//ToolBar[@Name='Main Toolbar']/Button[@AutomationId='SaveButton']");

// Perform a generic click
saveButtonElement.Click();

// Find another element and cast it to its specific type for more functionality
var notesField = window.FindFirstByXPath("//Group[@Name='Editor']/Edit[@AutomationId='NotesTextBox']").AsTextBox();

// Use a method specific to the TextBox type
notesField.Enter("This is some text.");
```

### Finding Elements by XPath

XPath is a powerful method for navigating the UI automation tree, allowing for precise and flexible element selection, especially in complex or dynamic user interfaces. FlaUI implements `FindFirstByXPath` to get a single element and `FindAllByXPath` to get a collection of elements.

**Common XPath Expressions:**

*   `//Button[@Name='OK']`: Finds any button with the name "OK" anywhere in the UI tree.
*   `/Window/Custom/DataItem[@Name='Row 3']`: Finds a `DataItem` named "Row 3" following a specific path from the root window.
*   `//Group[@AutomationId='UserDetails']/Edit`: Finds the `Edit` control (text box) that is a child of the `Group` with the AutomationId "UserDetails".
*   `//Tab/TabItem[3]`: Finds the third `TabItem` within a `Tab` control.

**Example in C#:**

```csharp
using FlaUI.Core.AutomationElements;
using FlaUI.UIA3;

// ...
using var automation = new UIA3Automation();
var app = Application.Attach("SettingsProcess.exe");
var window = Helpers.GetWindowByName(automation, app, "Settings Window");

// Find the "Close" button inside the title bar using a specific path
var closeButton = window.FindFirstByXPath("/TitleBar/Button[@Name='Close']");
closeButton?.Click();

// Find all checkboxes within a group element
var optionsGroup = window.FindFirstByXPath("//Group[@AutomationId='SettingsPanel']");
var allCheckBoxes = optionsGroup.FindAllByXPath("//CheckBox");

foreach (var checkBox in allCheckBoxes)
{
    // Toggle each checkbox found
    if (checkBox.AsCheckBox().IsChecked == false) {
        checkBox.AsCheckBox().Toggle();
    }
}```

### Mouse and Keyboard Interaction

For scenarios requiring direct hardware simulation, FlaUI provides static `Mouse` and `Keyboard` classes to control the cursor and send keystrokes.

#### Mouse Actions

The `Mouse` class can simulate clicks, movement, and dragging operations at specific screen coordinates.

**Example:**

```csharp
using FlaUI.Core.Input;
using System.Drawing;

// Move the mouse to a specific coordinate
Mouse.MoveTo(new Point(500, 350));

// Perform a left click at the new position
Mouse.Click(MouseButton.Left);

// Drag an item from a start point to an end point
var startPoint = new Point(200, 200);
var endPoint = new Point(600, 400);
Mouse.Drag(MouseButton.Left, startPoint, endPoint);
```

#### Keyboard Actions

The `Keyboard` class simulates typing text and pressing individual keys, including combinations with modifiers like Ctrl, Alt, and Shift.

**Example:**

```csharp
using FlaUI.Core.Input;
using FlaUI.Core.WindowsAPI; // Required for VirtualKeyShort

// Type a string of text
Keyboard.Type("Hello world, this is a test.");

// Press the Enter key
Keyboard.Press(VirtualKeyShort.ENTER);

// Simulate a "Save" command (Ctrl + S)
Keyboard.TypeSimultaneously(VirtualKeyShort.CONTROL, VirtualKeyShort.KEY_S);

// Simulate "Select All" (Ctrl + A) followed by "Delete"
Keyboard.TypeSimultaneously(VirtualKeyShort.CONTROL, VirtualKeyShort.KEY_A);
Keyboard.Press(VirtualKeyShort.DELETE);
```

### Using Control Patterns

Patterns expose the specific capabilities of a control. For example, a scroll bar supports the `ScrollPattern`, and an editable combo box supports the `ValuePattern`. Using patterns provides a reliable way to interact with an element's functionality. You should always check if a pattern is supported before using it.

**Example:**

```csharp
using FlaUI.Core.AutomationElements;
using FlaUI.UIA3;
using FlaUI.UIA3.Patterns;

// ...
var app = Application.Attach("LoginProcess.exe");
var window = Helpers.GetWindowByName(automation, app, "Login Window");

// Use the InvokePattern on a "Login" button found via XPath
var loginButton = window.FindFirstByXPath("//Button[@AutomationId='LoginButton']");
if (loginButton.Patterns.Invoke.IsSupported)
{
    loginButton.Patterns.Invoke.Pattern.Invoke();
}

// Use the ValuePattern to get or set text in a password field
var passwordBox = window.FindFirstByXPath("//Edit[@AutomationId='PasswordBox']");
if (passwordBox.Patterns.Value.IsSupported)
{
    var valuePattern = passwordBox.Patterns.Value.Pattern;
    valuePattern.SetValue("MySecretPassword123");
}

// Use the SelectionItemPattern on a list view item
var thirdItem = window.FindFirstByXPath("//List[@AutomationId='UserList']/ListItem[3]");
if (thirdItem.Patterns.SelectionItem.IsSupported)
{
    thirdItem.Patterns.SelectionItem.Pattern.Select();
}