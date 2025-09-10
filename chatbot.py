import os
from typing import Annotated, TypedDict, Literal
from langchain_core.messages import AnyMessage, HumanMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages


if os.getenv("GEMINI_API_KEY") is None:
    print("Please set the GEMINI_API_KEY environment variable to run this script.")
    print("You can do this by running the following command in your terminal:")
    print("export GEMINI_API_KEY='your_api_key'")
    exit()

@tool
def multiply(first_number: int, second_number: int):
    """Multiplies two numbers."""
    return first_number * second_number

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

graph_builder = StateGraph(State)

llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest")

tools = [multiply]
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)

def tool_node(state: State):
    tool_calls = state["messages"][-1].tool_calls

    tool_outputs = []
    for tool_call in tool_calls:
        tool_output = multiply.invoke(tool_call["args"])
        tool_outputs.append(
            ToolMessage(
                content=str(tool_output),
                tool_call_id=tool_call["id"],
            )
        )

    return {"messages": tool_outputs}

graph_builder.add_node("tools", tool_node)

def router(state: State) -> Literal["tools", "__end__"]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return "__end__"

graph_builder.add_conditional_edges("chatbot", router)
graph_builder.add_edge("tools", "chatbot")

graph_builder.set_entry_point("chatbot")

graph = graph_builder.compile()

while True:
    user_input = input("User: ")
    if user_input.lower() in ["quit", "exit", "q"]:
        print("Goodbye!")
        break
    for event in graph.stream({"messages": [HumanMessage(content=user_input)]}):
        for value in event.values():
            if value["messages"][-1].content:
                print("Assistant:", value["messages"][-1].content)
