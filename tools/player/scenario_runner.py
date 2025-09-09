import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

import json
from datetime import datetime
import logging
import pyautogui
import uiautomation as auto

from tools.player.main_player import Player
from tools.player.logger import get_logger
from tools.uia_dumper import traverse_element_tree


class ScenarioRunner:
    def __init__(self, scenario_path: str, output_folder: str, logger: logging.Logger = None, indent_level: int = 0):
        self.scenario_path = scenario_path
        self.output_folder = self._get_output_folder(output_folder) if not logger else output_folder
        self.indent_level = indent_level
        self.logger = logger or self._setup_logger()

    def _get_output_folder(self, base_folder):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(self.scenario_path, 'r') as f:
            scenario_data = json.load(f)
        scenario_name = scenario_data.get("name", "scenario").replace(" ", "_")
        folder_name = f"{scenario_name}_{timestamp}"
        full_path = os.path.join(base_folder, folder_name)
        os.makedirs(full_path, exist_ok=True)
        return full_path

    def _setup_logger(self):
        log_file = os.path.join(self.output_folder, "scenario_run.log")
        logger = get_logger("ScenarioRunner", log_file=log_file, indent_level=self.indent_level)
        return logger

    def run(self):
        self.logger.info(f"Starting scenario from: {self.scenario_path}")
        self.logger.info(f"Output will be saved in: {self.output_folder}")

        with open(self.scenario_path, 'r') as f:
            scenario_data = json.load(f)

        csv_file = scenario_data.get("csv_data")
        if csv_file:
            self._run_with_csv_data(scenario_data, csv_file)
        else:
            self._run_scenario_once(scenario_data)

    def _run_with_csv_data(self, scenario_data, csv_file):
        import csv

        csv_path = os.path.join(os.path.dirname(self.scenario_path), csv_file)
        if not os.path.exists(csv_path):
            self.logger.error(f"CSV file not found at: {csv_path}")
            return

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                self.logger.info(f"--- Running Scenario Iteration {i+1} with data: {row} ---")
                self._run_scenario_once(scenario_data, row)

    def _substitute_variables(self, variables, csv_row):
        new_vars = {}
        for key, value in variables.items():
            if isinstance(value, str) and value.startswith("$"):
                var_name = value[1:]
                if var_name in csv_row:
                    new_vars[key] = csv_row[var_name]
                else:
                    self.logger.warning(f"Variable '{var_name}' not found in CSV row.")
                    new_vars[key] = value
            else:
                new_vars[key] = value
        return new_vars

    def _run_scenario_once(self, scenario_data, csv_row=None):
        # Handle nested scenarios
        nested_scenarios = scenario_data.get("scenarios", [])
        for i, sub_scenario_def in enumerate(nested_scenarios):
            sub_scenario_path = sub_scenario_def.get("scenario")
            if not sub_scenario_path:
                self.logger.warning(f"Skipping sub-scenario {i+1} because no path was provided.")
                continue

            self.logger.info(f"--- Running Sub-Scenario: {sub_scenario_path} ---")
            sub_runner = ScenarioRunner(
                scenario_path=sub_scenario_path,
                output_folder=self.output_folder,
                logger=self.logger,
                indent_level=self.indent_level + 1
            )
            sub_runner.run()
            self.logger.info(f"--- Finished Sub-Scenario: {sub_scenario_path} ---")

        # Handle test cases
        test_cases = scenario_data.get("test_cases", [])
        for i, test_case_def in enumerate(test_cases):
            test_name = test_case_def.get("name", f"test_{i+1}")
            script_path = test_case_def.get("script")
            variables = test_case_def.get("variables", {})

            if csv_row:
                variables = self._substitute_variables(variables, csv_row)

            if not script_path:
                self.logger.warning(f"Skipping test case '{test_name}' because no script was provided.")
                continue

            self.logger.info(f"--- Running Test Case: {test_name} ---")
            test_output_folder = os.path.join(self.output_folder, f"test_{i+1}_{test_name.replace(' ', '_')}")

            try:
                record_video = test_case_def.get("record_video", True)
                player = Player(
                    script_path=script_path,
                    output_folder=test_output_folder,
                    variables=variables,
                    record_video=record_video,
                    logger=self.logger
                )
                player.run()
                self.logger.info(f"--- Finished Test Case: {test_name} ---")
            except Exception as e:
                self.logger.error(f"--- Test Case Failed: {test_name} ---")
                self.logger.error(f"Error: {e}")
                on_failure_config = scenario_data.get("on_failure")
                if on_failure_config:
                    self._take_failure_snapshots(on_failure_config, test_output_folder)

        self.logger.info("Scenario run finished.")

    def _take_failure_snapshots(self, config, output_folder):
        self.logger.info("Taking failure snapshots...")
        if config.get("screenshot", True):
            try:
                screenshot_path = os.path.join(output_folder, "failure_screenshot.png")
                pyautogui.screenshot(screenshot_path)
                self.logger.info(f"Screenshot saved to {screenshot_path}")
            except Exception as e:
                self.logger.error(f"Failed to take screenshot: {e}")

        processes = config.get("processes_to_dump")
        if processes:
            self.logger.info(f"Dumping UI tree for processes: {processes}")
            try:
                dump_path = os.path.join(output_folder, "failure_uia_dump.json")
                root_control = auto.GetRootControl()
                trees = []
                for w in root_control.GetChildren():
                    try:
                        if w.ProcessId and auto.ProcessName(w.ProcessId).lower() in [p.lower() for p in processes]:
                            trees.append(traverse_element_tree(w))
                    except Exception:
                        continue
                with open(dump_path, 'w', encoding='utf-8') as f:
                    json.dump(trees, f, ensure_ascii=False, indent=2)
                self.logger.info(f"UI dump saved to {dump_path}")
            except Exception as e:
                self.logger.error(f"Failed to dump UI tree: {e}")
