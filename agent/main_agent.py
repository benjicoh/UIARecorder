import os
import json
import subprocess
from langchain_google.genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain.tools import Tool
from langchain_experimental.plan_and_execute import PlanAndExecute, load_agent_executor, load_chat_planner

class LangChainAgent:
    def __init__(self, recording_path, logger):
        self.recording_path = recording_path
        self.logger = logger
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro")

    def run(self):
        self.logger.info(f"Running LangChain agent with recording path: {self.recording_path}")

        # Load the recording data
        prompt = self._load_prompt()
        json_data = self._load_json_data()

        # Create the agent
        agent = self._create_plan_and_execute_agent()

        # Run the agent
        agent.invoke({
            "input": f"Here is the prompt:\n{prompt}\n\nHere is the JSON data:\n{json.dumps(json_data)}\n\nHere is the path to the recording folder:\n{self.recording_path}"
        })

    def _load_prompt(self):
        prompt_path = os.path.join(self.recording_path, "prompt.md")
        # Check if a custom prompt exists in the recording folder, otherwise use the default
        if not os.path.exists(prompt_path):
            self.logger.info("No custom prompt.md found in recording folder, using default prompt.")
            prompt_path = "prompt.md"

        with open(prompt_path, "r") as f:
            return f.read()

    def _load_json_data(self):
        json_path = os.path.join(self.recording_path, "annotations.json")
        with open(json_path, "r") as f:
            return json.load(f)

    def _create_executor(self) -> AgentExecutor:
        # Define tools
        tools = [
            Tool(
                name="run_python",
                func=self._run_python,
                description="Executes a python script and returns the output. The script has access to the recording data.",
            ),
            Tool(
                name="edit_code",
                func=self._edit_code,
                description="""
        Edits a code file at a given path.
        The input must be a JSON string with two keys: 'file_path' and 'new_content'.
        Example: '{"file_path": "path/to/your/file.py", "new_content": "print(\'Hello, World!\')"}'
        """,
            ),
            Tool(
                name="dump_uia_tree",
                func=self._dump_uia_tree,
                description="""
        Dumps the UI automation tree to a file. The input is the desired output path for the dump file.
        Example: 'path/to/your/dump.txt'
        """,
            ),
        ]

        # Create the react agent
        template = """
You are a helpful assistant that generates a python script for windows desktop automation using the uiautomation package.
You will be given a prompt, a json file with UIA properties of the clicked and focused elements, and a path to a folder with a video and screenshots.
Your task is to generate a python script that automates the recorded scenario.
You have access to the following tools:

{tools}

Use the following format:

Question: the user's request to generate the automation script
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I am now ready to generate the final python script
Final Answer: the final python script that automates the scenario

Begin!

Question: {input}
Thought:
"""
        prompt_template = PromptTemplate.from_template(template)
        react_agent = create_react_agent(self.llm, tools, prompt_template)
        return AgentExecutor(agent=react_agent, tools=tools, verbose=True)

    def _create_plan_and_execute_agent(self):
        planner = load_chat_planner(self.llm)
        executor = self._create_executor()

        agent = PlanAndExecute(planner=planner, executor=executor, verbose=True)
        return agent

    def _run_python(self, script):
        self.logger.info(f"Executing python script:\n{script}")
        try:
            # Create a temporary file to save the script
            script_path = os.path.join(self.recording_path, "temp_script.py")
            with open(script_path, "w") as f:
                f.write(script)

            # Execute the script as a separate process
            process = subprocess.Popen(
                ["python", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = process.communicate()

            # Clean up the temporary file
            os.remove(script_path)

            if process.returncode == 0:
                self.logger.info(f"Python script executed successfully. Output:\n{stdout}")
                return stdout
            else:
                self.logger.error(f"Python script failed with error:\n{stderr}")
                return f"Error: {stderr}"
        except Exception as e:
            self.logger.error(f"Failed to execute python script: {e}")
            return f"Error: {e}"

    def _edit_code(self, input_str: str) -> str:
        """
        Edits a code file at a given path.
        The input must be a JSON string with two keys: 'file_path' and 'new_content'.
        Example: '{"file_path": "path/to/your/file.py", "new_content": "print(\'Hello, World!\')"}'
        """
        try:
            data = json.loads(input_str)
            file_path = data['file_path']
            new_content = data['new_content']

            self.logger.info(f"Editing code at path: {file_path}")
            with open(file_path, "w") as f:
                f.write(new_content)
            self.logger.info(f"Code at {file_path} edited successfully.")
            return f"Code at {file_path} edited successfully."
        except Exception as e:
            self.logger.error(f"Failed to edit code: {e}")
            return f"Error during code edit: {e}. Input must be a valid JSON string with 'file_path' and 'new_content' keys."

    def _dump_uia_tree(self, output_path: str) -> str:
        """
        Dumps the UI automation tree to a file. The input is the desired output path for the dump file.
        Example: 'path/to/your/dump.txt'
        """
        self.logger.info(f"Dumping UIA tree to: {output_path}")
        try:
            # Execute the uia_dumper.py script as a separate process
            process = subprocess.Popen(
                ["python", "uia_dumper.py", "--output", output_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                self.logger.info(f"UIA tree dumped successfully to {output_path}.")
                return f"UIA tree dumped successfully to {output_path}."
            else:
                self.logger.error(f"Failed to dump UIA tree: {stderr}")
                return f"Error: {stderr}"
        except Exception as e:
            self.logger.error(f"Failed to dump UIA tree: {e}")
            return f"Error: {e}"
