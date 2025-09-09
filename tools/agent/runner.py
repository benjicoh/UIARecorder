from tools.agent.main import create_agent
from langchain_core.messages import HumanMessage, AIMessage

def run_agent(initial_prompt: str):
    """Runs the agent and manages the chat history."""

    agent_executor = create_agent()

    chat_history = []

    response = agent_executor.invoke({
        "input": initial_prompt,
        "chat_history": chat_history
    })

    chat_history.append(HumanMessage(content=initial_prompt))
    chat_history.append(AIMessage(content=response['output']))

    print(response['output'])

if __name__ == "__main__":
    run_agent("Start by generating a script from the recording at 'tools/recorder/output'.")
