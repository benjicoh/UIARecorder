import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from tools.agent.main import create_graph
from langchain_core.messages import HumanMessage

def run_agent(initial_prompt: str):
    """Runs the agent graph."""

    graph = create_graph()

    events = graph.stream(
        {"messages": [HumanMessage(content=initial_prompt)]},
    )
    for event in events:
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)

if __name__ == "__main__":
    run_agent("Start by generating a script from the recording at 'tools/recorder/output'.")
