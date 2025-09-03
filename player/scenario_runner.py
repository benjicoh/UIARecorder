import json
import os
from datetime import datetime

from player.main_player import Player
from player.logger import get_logger

class ScenarioRunner:
    def __init__(self, scenario_path: str, output_folder: str):
        self.scenario_path = scenario_path
        self.output_folder = self._get_output_folder(output_folder)
        self.logger = self._setup_logger()

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
        logger = get_logger("ScenarioRunner", log_file=log_file)
        return logger

    def run(self):
        self.logger.info(f"Starting scenario from: {self.scenario_path}")
        self.logger.info(f"Output will be saved in: {self.output_folder}")

        with open(self.scenario_path, 'r') as f:
            scenario_data = json.load(f)

        test_cases = scenario_data.get("test_cases", [])
        for i, test_case_def in enumerate(test_cases):
            test_name = test_case_def.get("name", f"test_{i+1}")
            script_path = test_case_def.get("script")
            variables = test_case_def.get("variables", {})

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
                    record_video=record_video
                )
                player.run()
                self.logger.info(f"--- Finished Test Case: {test_name} ---")
            except Exception as e:
                self.logger.error(f"--- Test Case Failed: {test_name} ---")
                self.logger.error(f"Error: {e}")

        self.logger.info("Scenario run finished.")
