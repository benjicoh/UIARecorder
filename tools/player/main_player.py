import importlib.util
import os
import sys
import traceback
from datetime import datetime
import logging

from player.exceptions import TestCaseNotFound, InvalidTestCase
from player.logger import get_logger
from player.test_case import BaseTestCase

class Player:
    def __init__(self, script_path: str, output_folder: str, variables: dict = None, record_video: bool = True, logger: logging.Logger = None):
        self.script_path = script_path
        self.output_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)
        self.variables = variables or {}
        self.logger = logger or self._setup_logger()
        self.record_video = record_video
        self.video_recorder = None
        if self.record_video:
            from recorder.media import MediaRecorder
            self.video_recorder = MediaRecorder(self.output_folder, record_audio=False)

    def _setup_logger(self):
        log_file = os.path.join(self.output_folder, "test_run.log")
        logger = get_logger("TestPlayer", log_file=log_file)
        return logger

    def run(self):
        self.logger.info(f"Starting test from script: {self.script_path}")
        self.logger.info(f"Output will be saved in: {self.output_folder}")

        try:
            if self.video_recorder:
                self.video_recorder.start()
            test_case_instance = self._load_test_case()
            self._execute_test_case(test_case_instance)
            self.logger.info("Test case finished successfully.")
        except Exception as e:
            self.logger.error(f"Test case failed: {e}")
            self.logger.error(traceback.format_exc())
        finally:
            if self.video_recorder:
                self.video_recorder.stop()
            self.logger.info("Test run finished.")

    def _load_test_case(self) -> BaseTestCase:
        self.logger.info(f"Loading test case from {self.script_path}")
        if not os.path.exists(self.script_path):
            raise FileNotFoundError(f"Test script not found at {self.script_path}")

        # Add the script's directory to the python path to handle relative imports
        script_dir = os.path.dirname(os.path.abspath(self.script_path))
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        module_name = os.path.splitext(os.path.basename(self.script_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, self.script_path)
        test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_module)

        if not hasattr(test_module, "TestCase"):
            raise TestCaseNotFound("Class 'TestCase' not found in the script.")

        test_case_class = getattr(test_module, "TestCase")
        if not issubclass(test_case_class, BaseTestCase):
            raise InvalidTestCase("Class 'TestCase' must inherit from 'BaseTestCase'.")

        return test_case_class(logger=self.logger, variables=self.variables)

    def _execute_test_case(self, test_case_instance: BaseTestCase):
        start_time = datetime.now()
        try:
            self.logger.info("Executing setup()")
            test_case_instance.setup()
            self.logger.info("Executing run()")
            test_case_instance.run()
        finally:
            self.logger.info("Executing teardown()")
            test_case_instance.teardown()
            end_time = datetime.now()
            duration = end_time - start_time
            self.logger.info(f"Test case execution time: {duration}")
