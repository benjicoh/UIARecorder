# Player Examples

This directory contains example files that demonstrate how to use the test player.

## `example_test.py`

This is an example of a basic test case script. It defines a `TestCase` class that inherits from `BaseTestCase` and implements the `setup`, `run`, and `teardown` methods. It shows how to use the logger and access variables passed from a scenario.

## `example_scenario.json`

This JSON file defines a simple scenario that runs the `example_test.py` script. It demonstrates how to define a test case within a scenario and how to pass variables to it.

## `new_features_scenario.json`

This is a more complex scenario that demonstrates two features:
1.  **Running multiple test cases**: It shows how to define and run more than one test case in a sequence.
2.  **Data-driven testing**: It shows how to link a scenario to a CSV file (`user_data.csv`) to run the same test case multiple times with different data.

## `user_data.csv`

This is an example of a data file for data-driven testing. It contains rows of data that can be used as variables in a test case, as demonstrated in `new_features_scenario.json`. Each column header in the CSV file can be used as a variable name in the scenario definition.
