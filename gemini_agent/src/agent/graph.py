import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

import subprocess
import mimetypes
import shutil
import time
from typing import Annotated, TypedDict, List

import google.genai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from src.uia_dumper import dump_uia_tree


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

def prepare_files_for_prompt(folder_path: str, allowed_extensions: List[str], state: "State"):
    """Reads files from a folder, uploads them using the File API, and prepares them for a multimodal prompt."""
    if not os.path.isdir(folder_path):
        return f"Folder not found: {folder_path}"

    uploaded_files = []
    for root, _, files in os.walk(folder_path):
        for filename in files:
            if any(filename.endswith(ext) for ext in allowed_extensions):
                file_path = os.path.join(root, filename)

                # Rename .json to .txt
                if filename.endswith(".json"):
                    new_filename = filename.replace(".json", ".txt")
                    new_file_path = os.path.join(root, new_filename)
                    shutil.copy(file_path, new_file_path)
                    file_path = new_file_path

                # Upload the file
                uploaded_file = llm.client.files.upload(file=file_path)
                # wait for it's processing to finish
                while uploaded_file.status.name == "PROCESSING":
                    time.sleep(1)
                    uploaded_file = llm.client.files.get(uploaded_file.name)
                uploaded_files.append(uploaded_file)

    state["uploaded_files"] = uploaded_files
    return f"Prepared {len(uploaded_files)} files for prompt."


# --- Graph ---

class State(TypedDict):
    messages: Annotated[list, add_messages]
    uploaded_files: list

# --- LLM ---
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GEMINI_API_KEY"))

# --- Tools ---
tools = [
    run_python_script,
    dump_ui,
    write_file,
    prepare_files_for_prompt
]
llm_with_tools = llm.bind_tools(tools)

# --- Prompt ---
# read it from file
with open(os.path.join(os.path.dirname(__file__), 'recording_to_script.md'), 'r', encoding='utf-8') as f:
    prompt = f.read()

# --- Graph ---
graph_builder = StateGraph(State)

def chatbot(state: State):
    messages = state["messages"]
    if state.get("uploaded_files"):
        # We have multimodal content to add to the prompt
        last_message = messages[-1]
        content = [last_message.content] + state["uploaded_files"]
        messages[-1] = HumanMessage(content=content)
        state["uploaded_files"] = []

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
            if tool_name == "prepare_files_for_prompt":
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

graph = graph_builder.compile()
