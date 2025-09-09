import sys
import os
import subprocess
import json
import base64
import mimetypes
from typing import Annotated, TypedDict, List

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from tools.uia_dumper import dump_uia_tree

# --- Tools ---

def run_python_script(script_path: str):
    """Runs a python script and returns the output."""
    if not os.path.exists(script_path):
        return f"Error: Script not found at {script_path}"

    try:
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error running script:\n{e.stderr}"

def dump_ui(window_title: str, output_file: str, screenshots: bool = False):
    """Dumps the UI tree of a window to a JSON file."""
    return dump_uia_tree(
        window_title=window_title,
        output_file=output_file,
        screenshots=screenshots
    )

def write_file(file_path: str, content: str):
    """Writes content to a file."""
    with open(file_path, "w") as f:
        f.write(content)
    return f"File '{file_path}' written successfully."

def prepare_multimodal_prompt_from_folder(folder_path: str, allowed_extensions: List[str], state: "State"):
    """Reads files from a folder, base64 encodes them, and prepares them for a multimodal prompt."""
    if not os.path.isdir(folder_path):
        return f"Folder not found: {folder_path}"

    prompt_parts = []
    for root, _, files in os.walk(folder_path):
        for filename in files:
            if any(filename.endswith(ext) for ext in allowed_extensions):
                file_path = os.path.join(root, filename)
                mime_type, _ = mimetypes.guess_type(file_path)
                if mime_type:
                    with open(file_path, "rb") as f:
                        encoded_content = base64.b64encode(f.read()).decode("utf-8")
                    prompt_parts.append({
                        "type": "media",
                        "data": encoded_content,
                        "mime_type": mime_type,
                    })

    state["multimodal_prompt_parts"] = prompt_parts
    return f"Prepared {len(prompt_parts)} files for multimodal prompt."


# --- Graph ---

class State(TypedDict):
    messages: Annotated[list, add_messages]
    multimodal_prompt_parts: list

def create_graph():
    """Creates the agent graph."""

    # --- LLM ---
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", google_api_key=os.getenv("GEMINI_API_KEY"))

    # --- Tools ---
    tools = [
        run_python_script,
        dump_ui,
        write_file,
        prepare_multimodal_prompt_from_folder
    ]
    llm_with_tools = llm.bind_tools(tools)

    # --- Prompt ---
    prompt = """
    # Instructions
    You are an agent that automates UI interaction based on user recordings.
    Your goal is to generate a python script, run it, and refine it until it runs successfully.

    Here is the workflow you should follow:
    1.  The user will provide a path to a folder containing a screen recording (e.g., .mp4) and a log of UI events (e.g., .json).
    2.  Use the `prepare_multimodal_prompt_from_folder` tool to prepare these files.
    3.  Generate a python script based on the recording.
    4.  Write the generated script to a file.
    5.  Run the script.
    6.  If the script runs successfully, you are done.
    7.  If the script fails, dump the UI of the application, and send the UI dump, the error log, and a screenshot to get a refined script.
    8.  Repeat from step 4 until the script runs successfully.
    """

    # --- Graph ---
    graph_builder = StateGraph(State)

    def chatbot(state: State):
        messages = state["messages"]
        if state.get("multimodal_prompt_parts"):
            # We have multimodal content to add to the prompt
            last_message = messages[-1]
            content = [
                {"type": "text", "text": last_message.content}
            ] + state["multimodal_prompt_parts"]
            messages[-1] = HumanMessage(content=content)
            state["multimodal_prompt_parts"] = []

        messages_with_prompt = [SystemMessage(content=prompt)] + messages
        response = llm_with_tools.invoke(messages_with_prompt)
        return {"messages": [response]}

    graph_builder.add_node("chatbot", chatbot)

    def tool_node_with_state(state: State):
        tool_node = ToolNode(tools=tools)
        # Manually handle tool calls to pass state
        messages = state["messages"]
        last_message = messages[-1]
        tool_outputs = []
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            selected_tool = next((tool for tool in tools if tool.__name__ == tool_name), None)
            if selected_tool:
                if tool_name == "prepare_multimodal_prompt_from_folder":
                    tool_args["state"] = state
                output = selected_tool(**tool_args)
                tool_outputs.append(ToolMessage(content=str(output), tool_call_id=tool_call["id"]))
        return {"messages": tool_outputs}


    graph_builder.add_node("tools", tool_node_with_state)

    graph_builder.add_conditional_edges(
        "chatbot",
        tools_condition,
    )
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge(START, "chatbot")

    return graph_builder.compile()
