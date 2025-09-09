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

    initial_state = {
        "messages": [HumanMessage(content=initial_prompt)],
        "multimodal_prompt_parts": []
    }

    events = graph.stream(initial_state)

    for event in events:
        if "messages" in event:
            for message in event["messages"]:
                if hasattr(message, 'content') and message.content:
                    print("Assistant:", message.content)
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    print("Tool Calls:", message.tool_calls)


if __name__ == "__main__":
    initial_prompt = (
        "Please generate a python script based on the recording in 'tools/recorder/output'. "
        "The recording consists of a video file and a JSON file with UI events. "
        "Use the `prepare_multimodal_prompt_from_folder` tool with the folder path 'tools/recorder/output' and extensions ['.mp4', '.json']"
    )
    run_agent(initial_prompt)
