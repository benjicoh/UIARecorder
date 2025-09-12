import sys
import os

import argparse
from datetime import datetime

from tools.player.main_player import Player
from tools.player.scenario_runner import ScenarioRunner

def run_script(script_path: str, output_folder: str = "output", no_video: bool = False, variables: dict = None):
    """
    Runs a single test script.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    script_name = os.path.splitext(os.path.basename(script_path))[0]
    output_folder = os.path.join(output_folder, f"{script_name}_{timestamp}")

    player = Player(
        script_path=script_path,
        output_folder=output_folder,
        record_video=not no_video,
        variables=variables
    )
    player.run()
    return f"Test script '{script_path}' executed. Output saved to '{output_folder}'"

def run_scenario(scenario_path: str, output_folder: str = "output"):
    """
    Runs a test scenario.
    """
    runner = ScenarioRunner(
        scenario_path=scenario_path,
        output_folder=output_folder
    )
    runner.run()
    return f"Scenario '{scenario_path}' executed. Output saved to '{runner.output_folder}'"

def main():
    parser = argparse.ArgumentParser(description="Run a test script or a scenario.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-s", "--script", help="Path to the test script to run.")
    group.add_argument("-sc", "--scenario", help="Path to the scenario JSON to run.")
    parser.add_argument("-o", "--output", default="output", help="Path to the output folder.")
    parser.add_argument("-nv", "--no-video", action="store_true", help="Disable video recording.")

    args = parser.parse_args()

    if args.script:
        run_script(args.script, args.output, args.no_video)
    elif args.scenario:
        run_scenario(args.scenario, args.output)

if __name__ == "__main__":
    main()
