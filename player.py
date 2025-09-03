import argparse
import os
from datetime import datetime

from player.main_player import Player
from player.scenario_runner import ScenarioRunner

def main():
    parser = argparse.ArgumentParser(description="Run a test script or a scenario.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--script", help="Path to the test script to run.")
    group.add_argument("--scenario", help="Path to the scenario JSON to run.")
    parser.add_argument("--output", default="output", help="Path to the output folder.")
    parser.add_argument("--no-video", action="store_true", help="Disable video recording.")

    args = parser.parse_args()

    if args.script:
        # Create a unique output folder for the test run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        script_name = os.path.splitext(os.path.basename(args.script))[0]
        output_folder = os.path.join(args.output, f"{script_name}_{timestamp}")

        player = Player(
            script_path=args.script,
            output_folder=output_folder,
            record_video=not args.no_video
        )
        player.run()
    elif args.scenario:
        runner = ScenarioRunner(
            scenario_path=args.scenario,
            output_folder=args.output
        )
        runner.run()

if __name__ == "__main__":
    main()
