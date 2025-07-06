# agent.py
import os
from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import ToolMessage
from dotenv import load_dotenv
load_dotenv()

os.environ["GOOGLE_API_KEY"] = os.getenv('GOOGLE-API-KEY')

from tools import check_calendar_availability, create_calendar_event
tools = [check_calendar_availability, create_calendar_event]
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0).bind_tools(tools)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

def should_continue(state: AgentState):
    last_message = state['messages'][-1]
    if not last_message.tool_calls:
        return "end"
    return "continue"

def call_model(state: AgentState):
    response = model.invoke(state['messages'])
    return {"messages": [response]}

def call_tool(state: AgentState):
    last_message = state['messages'][-1]    
    tool_messages = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call['name']
        selected_tool = next((t for t in tools if t.name == tool_name), None)
        if not selected_tool:
            raise ValueError(f"Tool '{tool_name}' not found.")
        tool_output = selected_tool.invoke(tool_call['args'])        
        tool_messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call['id']))
    return {"messages": tool_messages}

workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("action", call_tool)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "action",
        "end": END,
    },
)

workflow.add_edge("action", "agent")

app_runnable = workflow.compile()