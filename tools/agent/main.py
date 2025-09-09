import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

import subprocess
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool

# --- Tools ---

from tools.uia_dumper import dump_uia_tree
from tools.gemini_chat import new_chat_session, upload_folder_to_gemini, send_message_to_gemini

@tool
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

@tool
def dump_ui(window_title: str, output_file: str, screenshots: bool = False):
    """Dumps the UI tree of a window to a JSON file."""
    return dump_uia_tree(
        window_title=window_title,
        output_file=output_file,
        screenshots=screenshots
    )

# --- Agent ---

@tool
def start_new_gemini_chat_session():
    """Starts a new Gemini chat session."""
    return new_chat_session()

@tool
def upload_to_gemini(folder_path: str, allowed_extensions: list[str]):
    """Uploads files to Gemini."""
    return upload_folder_to_gemini(folder_path, allowed_extensions)

import json

@tool
def send_gemini_message(message: str):
    """
    Sends a message to Gemini and returns the generated code.
    The response from Gemini is expected to be a JSON string with a 'code' field.
    """
    response_text = send_message_to_gemini(message)
    try:
        response_json = json.loads(response_text)
        return response_json.get("code", "")
    except json.JSONDecodeError:
        return f"Error: Could not decode Gemini's response: {response_text}"

@tool
def write_file(file_path: str, content: str):
    """Writes content to a file."""
    with open(file_path, "w") as f:
        f.write(content)
    return f"File '{file_path}' written successfully."

# --- Agent ---

def create_agent():
    """Creates the ReAct agent."""

    # --- LLM ---
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro")

    # --- Tools ---
    tools = [
        run_python_script,
        dump_ui,
        start_new_gemini_chat_session,
        upload_to_gemini,
        send_gemini_message,
        write_file
    ]

    # --- Prompt ---
    prompt_template = """
    # Instructions
    You are an agent that automates UI interaction based on user recordings.
    Your goal is to generate a python script, run it, and refine it until it runs successfully.

    Here is the workflow you should follow:
    1.  Start a new Gemini chat session.
    2.  Upload the user's recording to Gemini. The user will provide the path to the recording folder.
    3.  Ask Gemini to generate a python script based on the recording.
    4.  Write the generated script to a file.
    5.  Run the script.
    6.  If the script runs successfully, you are done.
    7.  If the script fails, dump the UI of the application, and send the UI dump, the error log, and a screenshot to Gemini to get a refined script.
    8.  Repeat from step 4 until the script runs successfully.

    You have access to the following tools:
    {tools}

    You have access to the following tool names:
    {tool_names}

    # Conversation
    ## The following is the conversation history. Use it to help you respond.
    {chat_history}

    # User question
    ## This is the user's question. Use it to determine which tool to use.
    {input}

    # Thought process
    ## This is your thought process. Write down your thoughts, then use a tool to help you respond.
    {agent_scratchpad}
    """

    prompt = PromptTemplate.from_template(prompt_template)

    # --- Agent ---
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )

    return AgentExecutor(agent=agent, tools=tools, verbose=True)
