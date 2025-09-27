## Goal
- Generate a robust windows desktop automation script using python [uiautomation package](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows).


## Inputs

### Recording Directory
- A video file with narration of the test scenario.
- A json file with the UIA properties of the clicked and focused elements.
### Failed Run Artifacts (Optional)
- A video of the failed execution.
- Log file from a previous execution of the generated script, containing errors or failures.
- A full json snapshot of the application's UI tree from a previous run, useful for refining element selectors.

## Output
- A python script that uses the uiautomation package to automate the described scenario.
- **DO NOT** generate any  text other than the python code.

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
- Provide detailed logging of your actions and any errors encountered.
- Listen to the video's audio, there might be additional context or information that can help with element identification.
- It is useful to identify the main window of the application, and activate it at the start of the script.
- Use the API as it is documented in appendix A - UIAutomation Module API Reference.

## Logging and Output
- The logging format is `%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s`
- Use `logging.info()` to log the script's progress to standard output. This is useful for tracking the script's execution flow.
- Use `logging.warning()` to log non-critical errors. These are issues that do not prevent the script from completing its task.
- Use `logging.error()` to log critical errors that prevent the script from continuing.
- **To signal that the script has completed successfully, print the following line at the very end of the script:** - `Scenario completed successfully`
  

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

### Initial Script Generation
- Based on the narration, video and json, identify the key uia elements involved, and their unique properties
- Use the elements identified in the script
- After generating the script, review it to ensure all elements are correctly identified and the actions are appropriate.

### Actual Runs Refinement
If you are provided with a log file, video file from a previous execution and / or a full UI dump, use them to refine the script.
- **Logs**: This file contains the output of a previous run of the generated script. Analyze any errors or failures in the log to identify the root cause. Modify the script to fix these issues. For example, if an element was not found, you may need to adjust the selectors or add a wait condition.
- **UI Dump**: This file contains a full snapshot of the application's UI tree. Use this as a reference to find more robust selectors for elements that were problematic in the previous run. It can also help you understand the overall structure of the application and discover alternative ways to automate a task.
- **Video**: The screen recording of the failed run, use it to understand the visual context of the issue.
---

## A Developer's Guide to `uiautomation.py` and its Microsoft COM Underpinnings

The `uiautomation.py` script is a powerful Pythonic wrapper around Microsoft's UI Automation (UIA) framework. UIA is the modern accessibility and automated testing framework for Windows, succeeding the older Microsoft Active Accessibility (MSAA). To fully leverage this Python library, it's essential to understand how its classes and functions map to the core concepts of the UIA COM API.

The Microsoft UIA framework is built on three fundamental concepts:

1.  **Elements (`IUIAutomationElement`):** Every UI component (a window, button, text box, etc.) is represented as an "Element." These elements are organized in a hierarchical tree structure, with the Desktop as the root.
2.  **Control Patterns (`IUIAutomation...Pattern`):** These are specific COM interfaces that expose the functionality of an element. For example, a button supports the `Invoke` pattern (for clicking), while a checkbox supports the `Toggle` pattern. An element can support multiple patterns.
3.  **Properties (`PROPERTYID`):** These are data points that describe an element, such as its Name, ClassName, ControlType, or whether it's enabled.

This guide will break down how `uiautomation.py` abstracts these concepts.

### 1. Initialization and Core Objects

The script handles the complex COM initialization for you.

*   **Python API:** The core UIA functionality is lazily initialized when you first perform an action that requires it (e.g., calling `GetRootControl()`). This happens through the singleton `_AutomationClient`.
*   **Microsoft COM Equivalent:** This process involves:
    1.  Calling `CoInitializeEx` to initialize the COM library for the current thread.
    2.  Creating an instance of the central UIA object: `CUIAutomation`. The script does this with `comtypes.client.CreateObject("{ff48dba4-60ef-4201-aa87-54103eef594e}", interface=IUIAutomation)`.
    3.  Getting a `TreeWalker` object (`IUIAutomationTreeWalker`) from the main `IUIAutomation` interface, which is used for navigating the element tree. The script primarily uses the `RawViewWalker`.

### 2. The `Control` Class: The `IUIAutomationElement` Wrapper

The `Control` class is the heart of the library. Every object representing a UI element, like `WindowControl` or `ButtonControl`, inherits from `Control`.

*   **Python API:** `uiautomation.Control`, `uiautomation.WindowControl`, `uiautomation.ButtonControl`, etc.
*   **Microsoft COM Equivalent:** Each `Control` object holds a pointer to an `IUIAutomationElement` COM interface. All the properties and methods on the `Control` object are wrappers around calls to this interface.

#### 2.1. Finding Controls

Finding a UI element is the first step in any automation task.

*   **Python API:**
    ```python
    # Search from the root (Desktop)
    notepadWindow = uiautomation.WindowControl(Name='Untitled - Notepad')

    # Search from within another control
    documentControl = notepadWindow.EditControl(AutomationId='15')
    ```
*   **Microsoft COM Equivalent:** This is a multi-step process that the library simplifies immensely.
    1.  **Get a Starting Point:** The search starts from an existing `IUIAutomationElement` (e.g., the root element obtained via `IUIAutomation::GetRootElement`).
    2.  **Traverse the Tree:** The script uses an `IUIAutomationTreeWalker` (`GetFirstChildElement`, `GetNextSiblingElement`) to traverse the UI tree recursively from the starting point. This is encapsulated in the `WalkControl` and `FindControl` helper functions.
    3.  **Match Properties:** For each element visited, the script checks its properties against the search criteria. This involves calling methods on the `IUIAutomationElement` interface like `get_CurrentName`, `get_CurrentClassName`, `get_CurrentControlType`, etc., and comparing the results to the user's provided values (`Name='...', ClassName='...'`).

#### 2.2. Accessing Element Properties

*   **Python API:** Properties are accessed directly on the control object.
    ```python
    print(f"Name: {notepadWindow.Name}")
    print(f"Class: {notepadWindow.ClassName}")
    print(f"Enabled: {notepadWindow.IsEnabled}")
    print(f"Rectangle: {notepadWindow.BoundingRectangle}")
    ```
*   **Microsoft COM Equivalent:** Each Python property access translates to a COM method call on the underlying `IUIAutomationElement` interface.
    *   `control.Name` -> `IUIAutomationElement::get_CurrentName()`
    *   `control.ClassName` -> `IUIAutomationElement::get_CurrentClassName()`
    *   `control.IsEnabled` -> `IUIAutomationElement::get_CurrentIsEnabled()`
    *   `control.AutomationId` -> `IUIAutomationElement::get_CurrentAutomationId()`
    *   `control.BoundingRectangle` -> `IUIAutomationElement::get_CurrentBoundingRectangle()`
    *   `control.ControlType` -> `IUIAutomationElement::get_CurrentControlType()`

### 3. Control Patterns: Interacting with Elements

Control Patterns are the standard way to interact with an element's functionality. The library provides clean Python classes to wrap these patterns.

*   **Python API:** You get a pattern from a control object and then call methods on it.
    ```python
    # Get the InvokePattern for a button
    invokePattern = saveButton.GetInvokePattern()
    if invokePattern:
        invokePattern.Invoke() # Click the button

    # Get the ValuePattern for an edit box
    valuePattern = editControl.GetValuePattern()
    if valuePattern:
        valuePattern.SetValue("Hello from uiautomation!")
    ```
*   **Microsoft COM Equivalent:**
    1.  **Get the Pattern:** The `control.Get...Pattern()` methods call `IUIAutomationElement::GetCurrentPattern(patternId)`. The `patternId` is an integer constant from the `PatternId` class (e.g., `PatternId.InvokePattern` which corresponds to `UIA_InvokePatternId`).
    2.  **Use the Pattern:** The returned COM pointer is then wrapped in a corresponding Python pattern class (e.g., `InvokePattern`). Calling a method on the Python object translates directly to a call on the COM interface.
        *   `invokePattern.Invoke()` -> `IUIAutomationInvokePattern::Invoke()`
        *   `valuePattern.SetValue(...)` -> `IUIAutomationValuePattern::SetValue(...)`
        *   `togglePattern.Toggle()` -> `IUIAutomationTogglePattern::Toggle()`
        *   `expandCollapsePattern.Expand()` -> `IUIAutomationExpandCollapsePattern::Expand()`
        *   `windowPattern.SetWindowVisualState(...)` -> `IUIAutomationWindowPattern::SetWindowVisualState(...)`

### 4. Constants and Enumerations

The script defines numerous classes that serve as enumerations for constants defined in the UIA and Win32 headers. This makes the code readable and avoids "magic numbers."

*   **Python API:** `ControlType`, `PatternId`, `PropertyId`, `Keys`, `SW` (ShowWindow constants), etc.
*   **Microsoft COM/Win32 Equivalent:** These directly map to constants defined in Microsoft's header files (`UIAutomationClient.h`, `WinUser.h`).
    *   `ControlType.ButtonControl` -> `UIA_ButtonControlTypeId`
    *   `PatternId.InvokePattern` -> `UIA_InvokePatternId`
    *   `PropertyId.NameProperty` -> `UIA_NamePropertyId`
    *   `Keys.VK_ENTER` -> `VK_RETURN` (virtual key code)
    *   `SW.Maximize` -> `SW_MAXIMIZE` (ShowWindow command)

### 5. Win32 API Integration

For robust automation, UIA is not always sufficient. The library seamlessly integrates direct Win32 API calls for actions like mouse movement, keyboard input, and window management. These are not part of the UIA COM API but are part of the broader Windows API.

*   **Python API:**
    *   `uiautomation.Click(x, y)`
    *   `uiautomation.SendKeys("{Ctrl}c")`
    *   `uiautomation.SetCursorPos(x, y)`
    *   `control.ShowWindow(SW.Minimize)`
*   **Microsoft Win32 Equivalent:** These functions use `ctypes` to call functions directly from system DLLs like `user32.dll` and `kernel32.dll`.
    *   `Click()` uses `SetCursorPos` and `mouse_event`.
    *   `SendKeys()` is a sophisticated wrapper around `keybd_event` or `SendInput` for simulating keyboard presses.
    *   `ShowWindow()` directly calls the `ShowWindow` Win32 function.
    *   `GetWindowText()` directly calls the `GetWindowTextW` Win32 function.

### Summary of the Mapping

| Python `uiautomation.py` API | Underlying Microsoft API | Description |
| :--- | :--- | :--- |
| `Control` and its subclasses | `IUIAutomationElement` Interface | Represents a single UI element like a window or button. |
| `control.Name`, `control.ClassName` etc. | `IUIAutomationElement::get_Current...()` | Accesses descriptive properties of an element. |
| `control.GetParentControl()`, `GetChildren()` | `IUIAutomationTreeWalker` Interface | Navigates the hierarchical UI tree. |
| `InvokePattern`, `ValuePattern`, etc. | `IUIAutomation...Pattern` Interfaces | Exposes the specific functionality of an element. |
| `control.GetInvokePattern()` | `IUIAutomationElement::GetCurrentPattern()` | Retrieves a specific control pattern from an element. |
| `ControlType`, `PatternId`, `PropertyId` | `UIA_...` Constants | Integer constants that identify types, patterns, and properties. |
| `Click()`, `SendKeys()`, `SetCursorPos()` | Win32 API (`user32.dll`) | Low-level mouse and keyboard simulation. |
| `ShowWindow()`, `SetForegroundWindow()` | Win32 API (`user32.dll`) | Direct manipulation of native window handles (`HWND`). |

By understanding this mapping, you can use the intuitive `uiautomation.py` library while also being able to refer to the official Microsoft UI Automation documentation for in-depth details on specific patterns, properties, or behaviors. The script acts as an effective and powerful bridge between the Python world and the native Windows automation framework.

---

## In-Depth Guide: Finding Controls with `uiautomation.py`

Finding the correct UI element is the most critical and often most challenging part of UI automation. The `uiautomation.py` library provides a flexible and powerful query model that simplifies the underlying complexity of traversing the Microsoft UI Automation tree.

### The Search Model: A Query-Based Approach

At its core, finding a control is a **query**. You define a set of criteria, and the library searches the UI tree for the first element that matches all of them.

```python
# This is a query for a WindowControl element that has a Name property of 'Untitled - Notepad'
# The search starts from the root of the UI tree (the Desktop).
notepad_window = uiautomation.WindowControl(Name='Untitled - Notepad')
```

#### The Search Context ("From Where?")

Every search has a starting point, or a **search context**.

1.  **From the Root (Global Search):** If you call a control constructor directly from the `uiautomation` module, the search begins from the top-level Desktop element. This is useful for finding main application windows.
    ```python
    import uiautomation as auto
    # Searches the entire UI tree for a window named 'Calculator'
    calc_window = auto.WindowControl(Name='Calculator')
    ```

2.  **From an Existing Control (Scoped Search):** If you call a control method from an existing `Control` object, the search is scoped to the descendants of that object. This is **highly recommended** as it's faster and more reliable.
    ```python
    # First, find the Notepad window
    notepad_window = auto.WindowControl(Name='Untitled - Notepad')
    
    # NOW, search ONLY within the children of notepad_window
    edit_area = notepad_window.EditControl()
    ```
    *   **Underlying COM Mechanism:** This corresponds to starting the `IUIAutomationTreeWalker` traversal from a specific `IUIAutomationElement` pointer instead of the root element.

---

### Core Search Parameters (The "What")

These parameters define the properties of the element you are looking for. You can combine any of them to make your search more specific.

#### `Name`
The most common way to find a control. It's the visible text associated with the element.
*   **Microsoft UIA Property:** `UIA_NamePropertyId`
*   **Use Case:** Finding buttons with labels ("OK", "Save"), text fields with associated labels, window titles.
*   **Example:** `uiautomation.ButtonControl(Name='Save')`
*   **Caution:** The `Name` can change based on application language or state. It's not always the most reliable identifier.

#### `SubName`
Performs a substring match on the `Name` property. This is a convenience provided by the library.
*   **Use Case:** When the full name is dynamic but contains a static part. For example, a document window named "Document1 - Word".
*   **Example:** `uiautomation.WindowControl(SubName='Word')`

#### `RegexName`
Performs a regular expression match on the `Name` property.
*   **Use Case:** For complex or unpredictable naming patterns where `SubName` is not sufficient.
*   **Example:** `uiautomation.ListItemControl(RegexName=r'Item \d+')` will match "Item 1", "Item 2", etc.

#### `AutomationId`
This is often the **most reliable and recommended** property for finding controls. It's a unique, non-localized ID assigned by the developer of the application.
*   **Microsoft UIA Property:** `UIA_AutomationIdPropertyId`
*   **Use Case:** The primary choice for stable and robust automation scripts, especially in well-designed applications (WPF, UWP).
*   **Example:** `uiautomation.ButtonControl(AutomationId='SaveButton')`

#### `ClassName`
The name of the underlying Win32 window class.
*   **Microsoft UIA Property:** `UIA_ClassNamePropertyId`
*   **Use Case:** Useful for older applications (Win32, MFC) where `AutomationId` is not available. Also good for identifying generic controls like "Edit" or "Button".
*   **Example:** `uiautomation.WindowControl(ClassName='Notepad')`

#### `ControlType`
The fundamental type of the control as defined by UI Automation. Using a specific control class like `ButtonControl` sets this implicitly.
*   **Microsoft UIA Property:** `UIA_ControlTypePropertyId`
*   **Use Case:** To narrow down a search to only elements of a specific type, improving performance and accuracy.
*   **Example:** `uiautomation.Control(ControlType=uiautomation.ControlType.ButtonControl, Name='OK')` is equivalent to `uiautomation.ButtonControl(Name='OK')`.

---

### Advanced Search Parameters (The "How")

These parameters control the *behavior* of the search algorithm.

#### `searchDepth` / `Depth`
Limits how deep the search will traverse into the UI tree from its starting point. `Depth` is a strict equality check, while `searchDepth` is a maximum.
*   **Use Case:**
    *   `searchDepth=1`: Finds direct children only. This is very fast.
    *   `Depth=2`: Finds elements that are exactly two levels down (grandchildren).
*   **Example:**
    ```python
    # Find the "File" menu item, which is a direct child of the menu bar
    menu_bar = window.MenuBarControl()
    file_menu = menu_bar.MenuItemControl(Name='File', searchDepth=1)
    ```

#### `foundIndex`
Finds the Nth matching control. **Note: This is 1-based, not 0-based.**
*   **Use Case:** When multiple elements match your criteria and you need one that isn't the first. For example, a toolbar with several identical-looking buttons.
*   **Example:** `uiautomation.ButtonControl(Name='Delete', foundIndex=2)` will find the second button named "Delete".

#### `Compare`
The ultimate power feature. It allows you to provide a custom function (or lambda) to perform the match. The function receives the control object and its depth as arguments and must return `True` for a match.
*   **Use Case:** For complex conditions that simple property matching cannot handle, such as:
    *   Matching multiple properties with OR logic.
    *   Checking a property of a control's pattern.
    *   Checking properties relative to a parent or sibling.
*   **Example:** Find a `ListItem` that is both selected and enabled.
    ```python
    list_item = list_control.ListItemControl(
        Compare=lambda c, d: c.GetSelectionItemPattern().IsSelected and c.IsEnabled
    )
    ```

---

### The Search Process and Timing

Understanding *when* a search happens is crucial for writing non-flaky scripts.

#### Implicit Waits vs. Explicit Waits

*   **Implicit Wait:** When you define a control and then immediately call a method on it (like `.Click()`), the library automatically searches for the control. If not found, it keeps retrying until the global timeout (`TIME_OUT_SECOND`, default 10s) is reached. If it still can't find it, it raises a `LookupError`.
    ```python
    # Defines the control, but does NOT search yet
    save_button = uiautomation.ButtonControl(Name='Save')
    
    # NOW the search happens. It will wait up to 10 seconds.
    save_button.Click()
    ```

*   **Explicit Wait:** You can explicitly check for a control's existence using the `.Exists()` method. This is the preferred way to handle controls that may take time to appear.

    *   **`control.Exists(maxSearchSeconds, searchIntervalSeconds)`**:
        Returns `True` if the control is found within the timeout, `False` otherwise. It does **not** raise an exception on failure.
        ```python
        save_dialog = uiautomation.WindowControl(Name='Save As')
        if save_dialog.Exists(5): # Wait for up to 5 seconds
            print("Save dialog appeared!")
            save_dialog.ButtonControl(Name='Cancel').Click()
        else:
            print("Timed out waiting for save dialog.")
        ```

    *   **`control.Disappears(maxSearchSeconds, searchIntervalSeconds)`**:
        The opposite of `Exists`. Returns `True` if the control becomes inaccessible within the timeout. Useful for waiting for progress bars or dialogs to close.

    *   **`control.Refind()`**:
        This explicitly re-runs the search for a control, waiting up to the global timeout. It's useful if the UI has changed and you need to ensure your control object points to the current, valid element.

### Best Practices for Reliable Searching

1.  **Be Specific and Scoped:** Always start your search from the closest, most specific parent control you can reliably find. Avoid global searches (`uiautomation.ButtonControl(...)`) unless absolutely necessary.
2.  **Prioritize `AutomationId`:** When available, `AutomationId` is almost always the best choice. It's unique and language-independent.
3.  **Combine Criteria:** Don't rely on just one property. Combining `Name` and `ControlType`, or `ClassName` and `AutomationId`, makes your search much less likely to find the wrong element.
4.  **Use `Exists()` for Dynamic UI:** Never assume a control is immediately available. Use `control.Exists(timeout)` to wait for elements that appear after an action.
5.  **Inspect the UI Tree:** Use tools to understand the structure. The `uiautomation` library itself provides a great one: run `python -m uiautomation -t 0` in your console and hover your mouse over UI elements to see their properties. This will reveal the best properties (`AutomationId`, `ClassName`, etc.) to use for your searches.

# Appendix A : UIAutomaion Module API Reference

This reference outlines the primary components and functionalities of the `uiautomation.py` library, a Python wrapper for Microsoft UI Automation.

---

## I. Global Functions

Functions available directly under the `uiautomation` module.

### Mouse & Keyboard Simulation

*   `uiautomation.Click(x: int, y: int, waitTime: float = 0.5) -> None`
    *   Simulates a left mouse click at screen coordinates `(x, y)`.
*   `uiautomation.RightClick(x: int, y: int, waitTime: float = 0.5) -> None`
    *   Simulates a right mouse click at screen coordinates `(x, y)`.
*   `uiautomation.DoubleClick(x: int, y: int, waitTime: float = 0.5) -> None`
    *   Simulates a left mouse double-click at screen coordinates `(x, y)`.
*   `uiautomation.MoveTo(x: int, y: int, moveSpeed: float = 1, waitTime: float = 0.5) -> None`
    *   Moves the mouse cursor smoothly to screen coordinates `(x, y)`.
*   `uiautomation.DragDrop(x1: int, y1: int, x2: int, y2: int, moveSpeed: float = 1, waitTime: float = 0.5) -> None`
    *   Simulates dragging the left mouse button from `(x1, y1)` to `(x2, y2)`.
*   `uiautomation.WheelDown(wheelTimes: int = 1, interval: float = 0.05, waitTime: float = 0.5) -> None`
    *   Simulates scrolling the mouse wheel down.
*   `uiautomation.WheelUp(wheelTimes: int = 1, interval: float = 0.05, waitTime: float = 0.5) -> None`
    *   Simulates scrolling the mouse wheel up.
*   `uiautomation.SendKey(key: int, waitTime: float = 0.5) -> None`
    *   Simulates pressing and releasing a single virtual key code. Use `uiautomation.Keys` for `key`.
*   `uiautomation.SendKeys(text: str, interval: float = 0.01, waitTime: float = 0.5, charMode: bool = True, debug: bool = False) -> None`
    *   Simulates typing a sequence of keys. Supports special keys in curly braces `{}` (e.g., `{Ctrl}a`, `{Enter}`). See docstring for syntax.
*   `uiautomation.IsKeyPressed(key: int) -> bool`
    *   Checks if a given virtual key is currently pressed.

### Control Retrieval

*   `uiautomation.GetRootControl() -> PaneControl`
    *   Returns the root UI Automation element, which is the Desktop window.
*   `uiautomation.GetFocusedControl() -> Optional[Control]`
    *   Returns the currently focused UI Automation element.
*   `uiautomation.GetForegroundControl() -> Control`
    *   Returns the UI Automation element of the foreground window.
*   `uiautomation.ControlFromPoint(x: int, y: int) -> Optional[Control]`
    *   Returns the UI Automation element at the given screen coordinates.
*   `uiautomation.ControlFromHandle(handle: int) -> Optional[Control]`
    *   Returns the UI Automation element associated with a given native window handle (`HWND`).
*   `uiautomation.ControlsAreSame(control1: Control, control2: Control) -> bool`
    *   Compares two `Control` objects to check if they refer to the same UI element.

### System & Utility

*   `uiautomation.SetGlobalSearchTimeout(seconds: float) -> None`
    *   Sets the default maximum time (in seconds) the library will wait when searching for controls. (Default: 10s)
*   `uiautomation.WaitForExist(control: Control, timeout: float) -> bool`
    *   Waits for a `Control` to exist within the specified `timeout` seconds.
*   `uiautomation.WaitForDisappear(control: Control, timeout: float) -> bool`
    *   Waits for a `Control` to disappear within the specified `timeout` seconds.
*   `uiautomation.LogControl(control: Control, depth: int = 0, showAllName: bool = True, showPid: bool = False) -> None`
    *   Prints and logs detailed properties of a single `Control` object to the console and log file.
*   `uiautomation.EnumAndLogControl(control: Control, maxDepth: int = 0xFFFFFFFF, showAllName: bool = True, showPid: bool = False, startDepth: int = 0) -> None`
    *   Recursively enumerates and logs properties of a control and its descendants.
*   `uiautomation.GetScreenSize() -> Tuple[int, int]`
    *   Returns the width and height of the primary screen.
*   `uiautomation.GetCursorPos() -> Tuple[int, int]`
    *   Returns the current `(x, y)` screen coordinates of the mouse cursor.
*   `uiautomation.SetConsoleColor(color: int) -> bool`
    *   Sets the console text color. Use `uiautomation.ConsoleColor` for `color`.
*   `uiautomation.ResetConsoleColor() -> bool`
    *   Resets the console text color to default.

---

## II. Class `Control` (Base UI Automation Element)

The `Control` class is the foundation for all UI Automation elements. It wraps the `IUIAutomationElement` COM interface. All specific control types (`ButtonControl`, `WindowControl`, etc.) inherit from `Control`.

```python
class Control:
    def __init__(self,
                 searchFromControl: Optional['Control'] = None,
                 searchDepth: int = 0xFFFFFFFF,
                 searchInterval: float = 0.5,
                 foundIndex: int = 1,
                 element=None, # Internal COM element
                 ControlType: Optional[int] = None,
                 Name: Optional[str] = None,
                 SubName: Optional[str] = None,
                 RegexName: Optional[str] = None,
                 ClassName: Optional[str] = None,
                 AutomationId: Optional[str] = None,
                 Depth: Optional[int] = None,
                 Compare: Optional[Callable[[TreeNode, int], bool]] = None,
                 **searchProperties):
        # ... (initialization details) ...
```

### Constructor Parameters (Search Criteria)

When you instantiate a `Control` (or any of its subclasses), you are defining a **search query**. The actual search is performed when you first access a property or call a method that requires the underlying UI Automation element to be found.

*   `searchFromControl` (`Control`, optional): The control from which to start the search. If `None`, the search starts from the Desktop (`GetRootControl()`).
*   `searchDepth` (`int`, default `0xFFFFFFFF`): The maximum depth to search from `searchFromControl`.
*   `searchInterval` (`float`, default `0.5`): The interval (in seconds) between search attempts when waiting for a control to exist.
*   `foundIndex` (`int`, default `1`): If multiple controls match the criteria, specifies which one to return (1-based index).
*   `element` (internal): Used by the library to wrap an existing `IUIAutomationElement`.
*   `ControlType` (`int`, optional): Matches the control's type (e.g., `uiautomation.ControlType.ButtonControl`).
*   `Name` (`str`, optional): Matches the control's exact `Name` property.
*   `SubName` (`str`, optional): Matches if the control's `Name` property contains this substring.
*   `RegexName` (`str`, optional): Matches if the control's `Name` property matches this regular expression.
*   `ClassName` (`str`, optional): Matches the control's exact `ClassName` property.
*   `AutomationId` (`str`, optional): Matches the control's exact `AutomationId` property (highly recommended for stability).
*   `Depth` (`int`, optional): Matches controls at a *specific* relative depth from `searchFromControl`. Also sets `searchDepth` to this value.
*   `Compare` (`Callable[[Control, int], bool]`, optional): A custom function that takes the `Control` and its `depth` as arguments, returning `True` for a match.
*   `**searchProperties`: Additional UIA properties (e.g., `IsKeyboardFocusable=True`) can be passed as keyword arguments for searching.

### Key Properties

These properties provide information about the found UI element. Accessing them might trigger a search if the control hasn't been found yet.

*   `control.Name` (`str`): The display name of the element.
*   `control.ClassName` (`str`): The Win32 window class name of the element.
*   `control.AutomationId` (`str`): The unique automation identifier.
*   `control.ControlType` (`int`): The UI Automation control type ID (e.g., `ControlType.ButtonControl`).
*   `control.ControlTypeName` (`str`): The string representation of `ControlType`.
*   `control.BoundingRectangle` (`Rect`): The screen coordinates and size of the element.
*   `control.NativeWindowHandle` (`int`): The underlying Win32 window handle (`HWND`), if applicable.
*   `control.ProcessId` (`int`): The ID of the process that owns the element.
*   `control.IsEnabled` (`bool`): `True` if the element is enabled, `False` otherwise.
*   `control.IsOffscreen` (`bool`): `True` if the element is not currently visible on screen.
*   `control.HasKeyboardFocus` (`bool`): `True` if the element has keyboard focus.
*   `control.IsPassword` (`bool`): `True` if the element is a password input field.
*   `control.FrameworkId` (`str`): The UI framework that provides the element (e.g., "Win32", "WPF").
*   `control.HelpText` (`str`): The help text for the element.
*   `control.Element`: The raw `IUIAutomationElement` COM object (for advanced use).

### Key Methods

*   `control.Exists(maxSearchSeconds: float = 5, searchIntervalSeconds: float = 0.5, printIfNotExist: bool = False) -> bool`
    *   Explicitly searches for the control. Returns `True` if found within `maxSearchSeconds`, `False` otherwise. Does not raise an exception on failure.
*   `control.Disappears(maxSearchSeconds: float = 5, searchIntervalSeconds: float = 0.5, printIfNotDisappear: bool = False) -> bool`
    *   Waits for the control to disappear. Returns `True` if it disappears within `maxSearchSeconds`, `False` otherwise.
*   `control.Refind(maxSearchSeconds: float = 10, searchIntervalSeconds: float = 0.5, raiseException: bool = True) -> bool`
    *   Re-searches for the control. If `raiseException` is `True`, a `LookupError` is raised on timeout.
*   `control.AddSearchProperties(**searchProperties) -> None`
    *   Adds or updates search criteria for future searches of this control object.
*   `control.RemoveSearchProperties(**searchProperties) -> None`
    *   Removes search criteria from this control object.
*   `control.GetParentControl() -> Optional[Control]`
    *   Returns the immediate parent `Control` in the UI Automation tree.
*   `control.GetFirstChildControl() -> Optional[Control]`
    *   Returns the first child `Control` in the UI Automation tree.
*   `control.GetNextSiblingControl() -> Optional[Control]`
    *   Returns the next sibling `Control` in the UI Automation tree.
*   `control.GetChildren() -> List[Control]`
    *   Returns a list of all immediate child controls.
*   `control.MoveCursorToInnerPos(x: Optional[int] = None, y: Optional[int] = None, ratioX: float = 0.5, ratioY: float = 0.5, simulateMove: bool = True) -> Optional[Tuple[int, int]]`
    *   Moves the mouse cursor to a position relative to the control's bounding rectangle.
        *   `x`, `y`: Absolute pixel offset from top-left (or right/bottom if negative).
        *   `ratioX`, `ratioY`: Relative position (0.0 to 1.0) if `x`/`y` are `None`.
    *   Returns `(screen_x, screen_y)` or `None`.
*   `control.Click(...)`, `control.RightClick(...)`, `control.DoubleClick(...)`
    *   These methods use `MoveCursorToInnerPos` then simulate clicks at the specified position within the control. Parameters are identical to `MoveCursorToInnerPos` plus `waitTime`.
*   `control.SetFocus() -> bool`
    *   Attempts to set keyboard focus on the control.
*   `control.SendKey(key: int, waitTime: float = 0.5) -> None`
    *   Sets focus on the control, then sends a single key press.
*   `control.SendKeys(text: str, interval: float = 0.01, waitTime: float = 0.5, charMode: bool = True) -> None`
    *   Sets focus on the control, then sends a string of keys.
*   `control.GetPattern(patternId: int)`
    *   The generic method to retrieve a control pattern. `patternId` is from `uiautomation.PatternId`. Returns a pattern-specific object (e.g., `InvokePattern`), or `None` if the pattern is not supported.
*   `control.ToBitmap(x: int = 0, y: int = 0, width: int = 0, height: int = 0, captureCursor: bool = False) -> Optional[Bitmap]`
    *   Captures a screenshot of the control (or a part of it) into a `Bitmap` object.
*   `control.CaptureToImage(savePath: str, x: int = 0, y: int = 0, width: int = 0, height: int = 0, captureCursor: bool = False) -> bool`
    *   Captures a screenshot of the control (or a part of it) and saves it to a file.

### Control Factory Methods (on `Control` instances)

Every `Control` object also acts as a factory for its child controls. This makes scoped searches very natural.

```python
# Assuming 'notepad_window' is already a found WindowControl instance
ok_button = notepad_window.ButtonControl(Name='OK')

# This is equivalent to:
# ok_button = uiautomation.ButtonControl(Name='OK', searchFromControl=notepad_window)
```

Each specific control type (e.g., `ButtonControl`, `EditControl`) has a corresponding method on `Control` (and its subclasses) that accepts the same search parameters as the constructor:

*   `control.ButtonControl(...) -> ButtonControl`
*   `control.EditControl(...) -> EditControl`
*   `control.WindowControl(...) -> WindowControl`
*   ... and so on for all `ControlType`s.

---

## III. Specific Control Classes

These classes inherit from `Control` and are associated with a specific `ControlType`. Their constructors implicitly set the `ControlType` parameter. They often include convenience methods for common patterns they support.

**Example: `WindowControl`**

```python
class WindowControl(Control, TopLevel):
    def __init__(self, searchFromControl: Optional[Control] = None, ..., **searchProperties):
        super().__init__(searchFromControl, ..., ControlType=ControlType.WindowControl, ..., **searchProperties)

    # Specific pattern getters for WindowControl (Mandatory patterns)
    def GetTransformPattern(self) -> TransformPattern: ...
    def GetWindowPattern(self) -> WindowPattern: ...

    # Specific window management methods (from TopLevel mixin)
    def SetTopmost(self, isTopmost: bool = True, waitTime: float = 0.5) -> bool: ...
    def Maximize(self, waitTime: float = 0.5) -> bool: ...
    def Minimize(self, waitTime: float = 0.5) -> bool: ...
    def Restore(self, waitTime: float = 0.5) -> bool: ...
    def SetActive(self, waitTime: float = 0.5) -> bool: ...
    def Close(self, waitTime: float = 0.5) -> bool: # Also available via GetWindowPattern().Close()
        """Closes the window using WindowPattern if supported, otherwise tries native APIs."""
        wp = self.GetWindowPattern()
        if wp:
            return wp.Close(waitTime)
        # Fallback to native window handle if WindowPattern not available/working
        handle = self.NativeWindowHandle
        if handle:
            return uiautomation.PostMessage(handle, 0x0010, 0, 0) # WM_CLOSE
        return False
```

**Common Specialized Control Classes and their Pattern Getters:**

*   **`ButtonControl`**:
    *   `button.GetInvokePattern() -> InvokePattern` (For clicking)
    *   `button.GetTogglePattern() -> TogglePattern` (For checkboxes/radio buttons styled as buttons)
*   **`EditControl`**:
    *   `edit.GetValuePattern() -> ValuePattern` (For getting/setting text)
    *   `edit.GetTextPattern() -> TextPattern` (For rich text manipulation)
*   **`CheckBoxControl`**:
    *   `checkbox.GetTogglePattern() -> TogglePattern` (For checking/unchecking)
    *   `checkbox.SetChecked(checked: bool) -> bool` (Convenience method)
*   **`ComboBoxControl`**:
    *   `combo.GetExpandCollapsePattern() -> ExpandCollapsePattern` (For opening/closing dropdown)
    *   `combo.GetValuePattern() -> ValuePattern` (For getting/setting current value)
    *   `combo.Select(itemName: str = '', condition: Optional[Callable[[str], bool]] = None, ...) -> bool` (Convenience method for selecting item)
*   **`ListItemControl`**:
    *   `item.GetSelectionItemPattern() -> SelectionItemPattern` (For selecting items in a list/tree)
    *   `item.GetInvokePattern() -> InvokePattern` (For activating the item)
    *   `item.GetExpandCollapsePattern() -> ExpandCollapsePattern` (For tree view items)

---

## IV. Control Pattern Classes

These classes wrap the `IUIAutomation...Pattern` COM interfaces. They are obtained via `control.GetPattern(PatternId.<PATTERN_ID>)` or specific `control.Get...Pattern()` methods.

**Example: `InvokePattern`**

```python
class InvokePattern:
    def __init__(self, pattern=None): # Internal COM object
        self.pattern = pattern

    def Invoke(self, waitTime: float = 0.5) -> bool:
        """
        Calls IUIAutomationInvokePattern::Invoke to activate the element.
        Returns True if successful, False otherwise.
        """
        # ... COM call ...
```

**Other Key Pattern Classes:**

*   **`ValuePattern`**:
    *   `vp.Value` (`str`): Gets the text value.
    *   `vp.IsReadOnly` (`bool`): Checks if the value is read-only.
    *   `vp.SetValue(value: str, waitTime: float = 0.5) -> bool`: Sets the text value.
*   **`TogglePattern`**:
    *   `tp.ToggleState` (`int`): Gets the current state (`ToggleState.Off`, `ToggleState.On`, `ToggleState.Indeterminate`).
    *   `tp.Toggle(waitTime: float = 0.5) -> bool`: Cycles through the toggle states.
    *   `tp.SetToggleState(toggleState: int, waitTime: float = 0.5) -> bool`: Sets the state to a specific `ToggleState`.
*   **`ExpandCollapsePattern`**:
    *   `ecp.ExpandCollapseState` (`int`): Gets the current state (`ExpandCollapseState.Expanded`, `Collapsed`, `PartiallyExpanded`, `LeafNode`).
    *   `ecp.Expand(waitTime: float = 0.5) -> bool`: Expands the element.
    *   `ecp.Collapse(waitTime: float = 0.5) -> bool`: Collapses the element.
*   **`WindowPattern`**:
    *   `wp.WindowVisualState` (`int`): Gets the current visual state (`WindowVisualState.Normal`, `Maximized`, `Minimized`).
    *   `wp.SetWindowVisualState(state: int, waitTime: float = 0.5) -> bool`: Sets the visual state.
    *   `wp.Close(waitTime: float = 0.5) -> bool`: Closes the window.
    *   `wp.WaitForInputIdle(milliseconds: int) -> bool`: Waits for the window to become idle.
*   **`ScrollPattern`**:
    *   `sp.HorizontalScrollPercent`, `sp.VerticalScrollPercent` (`float`): Current scroll positions (0-100).
    *   `sp.HorizontallyScrollable`, `sp.VerticallyScrollable` (`bool`): Whether scrolling is possible.
    *   `sp.Scroll(horizontalAmount: int, verticalAmount: int, waitTime: float = 0.5) -> bool`: Scrolls by a given amount (`ScrollAmount.LargeIncrement`, `SmallDecrement`, etc.).
    *   `sp.SetScrollPercent(horizontalPercent: float, verticalPercent: float, waitTime: float = 0.5) -> bool`: Sets scroll position by percentage.
*   **`SelectionItemPattern`**:
    *   `sip.IsSelected` (`bool`): Checks if the item is selected.
    *   `sip.Select(waitTime: float = 0.5) -> bool`: Selects the item (and deselects others in single-selection containers).
    *   `sip.AddToSelection(waitTime: float = 0.5) -> bool`: Adds the item to selection (in multi-selection containers).
    *   `sip.RemoveFromSelection(waitTime: float = 0.5) -> bool`: Removes the item from selection.
*   **`TextPattern`**:
    *   `tp.DocumentRange` (`TextRange`): The full text range of the document.
    *   `tp.GetSelection() -> List[TextRange]`: Returns a list of selected text ranges.
    *   `tp.RangeFromPoint(x: int, y: int) -> Optional[TextRange]`: Gets a text range at a specific point.
*   **`TextRange`**:
    *   `tr.GetText(maxLength: int = -1) -> str`: Retrieves text from the range.
    *   `tr.Select(waitTime: float = 0.5) -> bool`: Selects the text within the range.
    *   `tr.Move(unit: int, count: int, waitTime: float = 0.5) -> int`: Moves the text range by units (`TextUnit.Character`, `Word`, `Line`, etc.).

---

## V. Utility Classes & Enums

Constants and helper classes for various functionalities.

### Enums for UI Automation

*   `uiautomation.ControlType`: IDs for different UI element types (e.g., `ButtonControl`, `EditControl`, `WindowControl`).
*   `uiautomation.PatternId`: IDs for control patterns (e.g., `InvokePattern`, `ValuePattern`, `WindowPattern`).
*   `uiautomation.PropertyId`: IDs for UI Automation element properties (e.g., `NameProperty`, `AutomationIdProperty`, `BoundingRectangleProperty`).
*   `uiautomation.ToggleState`: States for `TogglePattern` (`Off`, `On`, `Indeterminate`).
*   `uiautomation.ExpandCollapseState`: States for `ExpandCollapsePattern` (`Expanded`, `Collapsed`).
*   `uiautomation.WindowVisualState`: Visual states for `WindowPattern` (`Normal`, `Maximized`, `Minimized`).
*   `uiautomation.TextUnit`: Units for `TextPattern` operations (`Character`, `Word`, `Line`, `Paragraph`, `Document`).
*   `uiautomation.AccessibleRole`: Roles for `LegacyIAccessiblePattern` (e.g., `PushButton`, `Window`).
*   `uiautomation.AccessibleState`: States for `LegacyIAccessiblePattern` (e.g., `Selected`, `Focused`, `Checked`).

### Enums for Win32 API

*   `uiautomation.Keys`: Virtual key codes for keyboard events (e.g., `VK_ENTER`, `VK_SHIFT`, `VK_A`).
*   `uiautomation.ModifierKey`: Modifier key flags for hotkeys (e.g., `Alt`, `Control`, `Shift`, `Win`).
*   `uiautomation.SW`: ShowWindow commands for window management (e.g., `ShowNormal`, `Maximize`, `Hide`).
*   `uiautomation.ConsoleColor`: Color codes for console output.

### `Rect` Class

Represents a rectangle, typically a bounding box of a UI element.

*   `Rect(left: int, top: int, right: int, bottom: int)`: Constructor.
*   `rect.width() -> int`: Width of the rectangle.
*   `rect.height() -> int`: Height of the rectangle.
*   `rect.xcenter() -> int`: X-coordinate of the center.
*   `rect.ycenter() -> int`: Y-coordinate of the center.
*   `rect.contains(x: int, y: int) -> bool`: Checks if a point `(x, y)` is within the rectangle.

### `Bitmap` Class

A simple image manipulation class, wrapping GDI+ `Gdiplus::Bitmap`.

*   `Bitmap(width: int = 0, height: int = 0)`: Creates a new transparent bitmap.
*   `Bitmap.FromControl(control: Control, ...) -> Optional['Bitmap']`: Captures a control's image.
*   `Bitmap.FromFile(filePath: str) -> Optional['Bitmap']`: Loads an image from a file.
*   `Bitmap.FromBytes(data: Union[bytes, bytearray], format: str = None, width: int = None, height: int = None) -> Optional['Bitmap']`: Creates bitmap from raw pixels or image data.
*   `bitmap.ToFile(savePath: str, quality: int = None) -> bool`: Saves the bitmap to a file.
*   `bitmap.ToBytes(format: str, quality: int = None) -> bytearray`: Converts the bitmap to bytes in a specified format.
*   `bitmap.ToPILImage() -> PIL.Image.Image`: Converts to a PIL Image object.
*   `bitmap.ToNDArray() -> numpy.ndarray`: Converts to a NumPy array (BGRA).
*   `bitmap.Width`, `bitmap.Height` (`int`): Dimensions of the bitmap.
*   `bitmap.GetPixelColor(x: int, y: int) -> int`: Gets ARGB color of a pixel (0xAARRGGBB).
*   `bitmap.SetPixelColor(x: int, y: int, argb: int) -> bool`: Sets ARGB color of a pixel.
*   `bitmap.Copy(...) -> MemoryBMP`: Creates a new bitmap from a portion of the current one.
*   `bitmap.Resize(width: int, height: int) -> MemoryBMP`: Returns a resized copy.

### `Logger` Class

Provides logging and colored console output.

*   `Logger.FilePath` (`str`): Path to the log file (default: `@AutomationLog.txt`).
*   `Logger.SetLogFile(logFile: Union[TextIOWrapper, str]) -> None`: Sets the log file.
*   `Logger.Write(log: Any, consoleColor: int = -1, writeToFile: bool = True, printToStdout: bool = True, logFile: Optional[str] = None, printTruncateLen: int = 0) -> None`: Writes a log entry.
*   `Logger.WriteLine(...)`, `Logger.ColorfullyWrite(...)`, `Logger.ColorfullyWriteLine(...)`, `Logger.Log(...)`, `Logger.ColorfullyLog(...)`: Convenience methods for logging.

---