## Goal
- Generate a robust windows desktop automation script using python [uiautomation package](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows).


## Inputs

### Recording Directory
- A video file with narration of the test scenario.
- A json file with the UIA properties of the clicked and focused elements.
- A series of screenshots for each user interaction, with annotations.
### Failed Run Artifacts (Optional)
- Log file from a previous execution of the generated script, containing errors or failures.
- A full json snapshot of the application's UI tree from a previous run, useful for refining element selectors.
- Screenshots from the previous run, useful for visual reference.

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
- Provide detailed logging of your actions and any errors encountered.
- Listen to the video's audio, there might be additional context or information that can help with element identification.
- It is useful to identify the main window of the application, and activate it at the start of the script.

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
If you are provided with a log file from a previous execution and / or a full UI dump, use them to refine the script.
- **Logs**: This file contains the output of a previous run of the generated script. Analyze any errors or failures in the log to identify the root cause. Modify the script to fix these issues. For example, if an element was not found, you may need to adjust the selectors or add a wait condition.
- **UI Dump**: This file contains a full snapshot of the application's UI tree. Use this as a reference to find more robust selectors for elements that were problematic in the previous run. It can also help you understand the overall structure of the application and discover alternative ways to automate a task.
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