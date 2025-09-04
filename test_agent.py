import logging
from agent.main_agent import LangChainAgent

if __name__ == "__main__":
    # Basic logging setup
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    agent = LangChainAgent("dummy_recording", logger)
    agent.run()
