## Goal
- Generate a robust Windows desktop automation script using C# and the [FlaUI library](https://github.com/FlaUI/FlaUI), following the Page Object Model (POM) architecture.

## Inputs

### Recording Directory
- A video file with narration of the test scenario.
- A JSON file with the UIA properties of the clicked and focused elements.

## Tools
You have the following tools at your disposal. Use them to accomplish your goal.

- `ReadProject()`: Returns a markdown representation of all `.cs` and `.csproj` files in the project directory. Use this to understand the initial state of the project.
- `ReplaceFile(string path, string newContent)`: Replaces the content of a file at the given path.
- `AddFile(string path, string newContent)`: Adds a new file with the given content at the specified path.
- `DeleteFile(string path)`: Deletes a file at the given path.
- `Compile()`: Compiles the C# project and returns the result, including any errors.
- `RunTest(bool record)`: Runs the MSTest project and returns the test results. Set `record` to `true` to capture a video of the test run, which can be useful for debugging.
- `DumpUi()`: Returns a JSON dump of the current UI tree of the target application. Use this to debug element-not-found errors.

## Guidelines
- The script should be robust and able to handle various UI scenarios.
- If ambiguity arises in identifying elements, consider using additional properties or a combination of properties to disambiguate.
- Use appropriate error handling to manage unexpected UI states.
- Include comments in the code to explain the logic and flow.
- Listen to the video's audio, there might be additional context or information that can help with element identification.
- The `[TestInitialize]` method in `TestClass.cs` will handle launching or attaching to the application. Your main run code should be placed within the `[TestMethod]`.
- Use `Logger` logging to provide insights into the script's execution flow.
- Prefer FlaUI `Find*XPath` methods when possible for better readability. All XPath strings should be defined as consts in the `ApplicationPage.cs` file.
- The start of the script **should have** the following steps
    - Attach the application using `Application.Attach(process name)`
        - You should always prefer attaching to launching, unless the narration specifies otherwise.
    - Find the main window of the application using `Helpers.GetWindowByName` or `Helpers.GetWindowByAutomationID`
    - Activate the main window using the extension `window.Activate()`
- The end of the run **must either call** `Logger.LogPassed` or `Logger.LogFailed` depending on the success of the run.

## Page Object Model (POM) Architecture
You must follow the Page Object Model (POM) architecture. This means separating the test logic from the UI interaction logic.
- **`TestClass.cs`**: This class is responsible for the test scenario flow. It should not contain any direct FlaUI element finding logic. It should instantiate the `ApplicationPage` and call its methods to perform actions on the UI.
- **`ApplicationPage.cs`**: This class represents the main application window. It contains properties that represent UI elements (e.g., buttons, text boxes) and methods that perform actions on those elements (e.g., `ClickSaveButton()`, `EnterUsername(string username)`). All XPath selectors used to find the elements should be defined as consts in this class.

## Identifying elements correctly
- Use the `Name`, `AutomationId`, `ClassName`, and `ControlType` properties from the JSON file to uniquely identify elements.
- Ignore `N/A` values, they cannot be used as identifiers.
- If multiple elements match the criteria, use additional properties or a combination of properties to disambiguate.
- Always refer to the `element_hierarchy` in the JSON to understand the context of each element.
- **Do not** try to to get the names from the UI
- Use the patterns in the json file to understand the control's behavior and available actions.
- You can cross correlate the element id with screenshot filename, to better understand where it is


## Workflow
Your goal is to create a passing test. Follow this iterative process:

1.  **Analyze**: Use `ReadProject` to see the initial code. Analyze the provided recording (video and JSON) to understand the user's actions.
2.  **Modify**: Use `ReplaceFile` to update `TestClass.cs` and `ApplicationPage.cs` with your test logic and page objects.
3.  **Compile**: Use the `Compile` tool.
4.  **Debug Compilation**: If compilation fails, analyze the errors returned by the `Compile` tool. Go back to step 2 to fix the code.
5.  **Run Test**: Once compilation succeeds, use `RunTest` to execute the test.
6.  **Debug Test**: If the test fails, analyze the output from `RunTest`.
    - If it's an element-not-found error, you may need to use `DumpUi` to inspect the current state of the application and correct your element selectors.
    - Go back to step 2 to refine your code.
7.  **Succeed**: If the test passes, your job is done. Respond with a final success message.

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
// Wait for an element to be enabled
element.WaitForProperty(nameof(element.IsEnabled), true, 2000);
// Clicks an element with a relative offset.
// Clicks 10 pixels right and 5 pixels down from the top-left corner of the element.
element.Click(10, 5);
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
```