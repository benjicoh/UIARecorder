import time
from player.test_case import BaseTestCase

class TestCase(BaseTestCase):
    def setup(self):
        self.logger.info("Setting up the example test case.")
        self.logger.info(f"Received variables: {self.variables}")

    def run(self):
        self.logger.info("Running the example test case.")

        username = self.variables.get("username", "default_user")
        delay = self.variables.get("delay", 1)

        self.logger.info(f"Simulating login for user: {username}")
        time.sleep(delay)

        self.logger.info("Simulating some action.")
        time.sleep(delay)

        self.logger.info("Example test case finished.")

    def teardown(self):
        self.logger.info("Tearing down the example test case.")
