# Player

This document explains how to build a scenario and test cases for the player.

## Test Case Structure

Each test script must contain a class named `TestCase` that inherits from the `tools.player.test_case.BaseTestCase` class.

```python
from tools.player.test_case import BaseTestCase

class TestCase(BaseTestCase):
    def setup(self):
        """
        (Optional) Executed before the test runs.
        Use this for any initial setup, like launching an application.
        """
        pass

    def run(self):
        """
        (Required) The main body of the test case.
        This method contains the sequence of actions to be performed.
        """
        # Test logic goes here
        pass

    def teardown(self):
        """
        (Optional) Executed after the test completes, regardless of success or failure.
        Use this for cleanup, like closing applications.
        """
        pass
```

### Methods

- **`setup(self)`**: This method is called once before `run()`. It should be used for any setup that is required for the test, such as starting an application or loading data.
- **`run(self)`**: This is the main method of the test case. It should contain the core logic of the test, including all UI interactions and assertions.
- **`teardown(self)`**: This method is called once after `run()` has completed. It is always called, even if `setup()` or `run()` raise an exception. It should be used for cleanup, such as closing applications or deleting temporary files.

## Logging

The `BaseTestCase` class provides a logger instance at `self.logger`. This logger should be used for all logging within the test case. The logger is configured to output to both the console and a log file.

### Log Levels

- **`self.logger.info(message)`**: For general information about the test flow. This is the standard level for logging test steps.
- **`self.logger.warning(message)`**: For unexpected situations that do not block the test from continuing.
- **`self.logger.error(message)`**: For errors that cause the test to fail.
- **`self.logger.debug(message)`**: For detailed information that is useful for debugging.

## Passing and Failing Tests

- **Passing**: A test case is considered to have passed if the `run()` method completes without raising any exceptions.
- **Failing**: A test case is considered to have failed if any method (`setup`, `run`, or `teardown`) raises an exception. To fail a test, raise a standard Python exception. For example, `raise Exception("Element not found")`.

## Video Recording

The player will automatically record a video of the entire test run. The video will be saved in the output directory.

## Scenario Composition

The player can run a scenario composed of multiple test cases. A scenario is defined in a JSON file.

```json
{
  "name": "My Application Test Scenario",
  "test_cases": [
    {
      "name": "Example Test",
      "script": "path/to/your/test_script.py",
      "variables": {
        "username": "admin",
        "delay": "2"
      }
    }
  ]
}
```
The path to the script should be relative to the current working directory, or an absolute path.

### Variables

Variables can be passed to a test case from the scenario JSON file. These variables are accessible in the test case via `self.variables`.

```python
class TestCase(BaseTestCase):
    def run(self):
        username = self.variables.get("username")
        password = self.variables.get("password")
        # ...
```
