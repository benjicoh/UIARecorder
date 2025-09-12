import sys
import os

import abc
import logging

class BaseTestCase(abc.ABC):
    """
    The base class for all test cases.
    """
    def __init__(self, logger: logging.Logger, variables: dict):
        """
        Initializes the test case.

        Args:
            logger: The logger instance to use for logging.
            variables: A dictionary of variables for the test case.
        """
        self.logger = logger
        self.variables = variables

    def setup(self):
        """
        (Optional) Executed before the test runs.
        Use this for any initial setup, like launching an application.
        """
        pass

    @abc.abstractmethod
    def run(self):
        """
        (Required) The main body of the test case.
        This method contains the sequence of actions to be performed.
        """
        raise NotImplementedError

    def teardown(self):
        """
        (Optional) Executed after the test completes, regardless of success or failure.
        Use this for cleanup, like closing applications.
        """
        pass
