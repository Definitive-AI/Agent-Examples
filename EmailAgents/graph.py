import os
from typing import TypedDict, Annotated, List, Union
from langchain.agents import AgentType, create_react_agent, create_tool_calling_agent
from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor
from tools import EmailMonitoringTool, EmailFlaggingTool, HumanReviewTool, SecureCredentialStorage, WebBrowserAutomation, HumanOperatorNotification, ScreenshotCaptureTool, OCRTool, SecureStorageSystemAPI, RetryMechanismTool, ReportingTool
from context import process_docs_search, exception_handling_retriever
from prompts import agent1_prompt, agent2_prompt, agent3_prompt, agent4_prompt
from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

load_dotenv()

class EncryptedEmailProcessingState(TypedDict):
    input: str
    email_detector_output: dict
    authenticator_output: dict
    screenshotter_output: dict
    extractor_output: dict

def create_email_detector_agent(llm):
    agent1_tools = [EmailMonitoringTool(), EmailFlaggingTool(), HumanReviewTool(), process_docs_search]
    return create_react_agent(llm, agent1_tools, agent1_prompt)

def create_authenticator_agent(llm):
    agent2_tools = [SecureCredentialStorage(), WebBrowserAutomation(), HumanOperatorNotification(), exception_handling_retriever]
    return create_react_agent(llm, agent2_tools, agent2_prompt)

def create_screenshotter_agent(llm):
    agent3_tools = [ScreenshotCaptureTool(), process_docs_search]
    return create_tool_calling_agent(llm, agent3_tools, agent3_prompt)

def create_extractor_agent(llm):
    agent4_tools = [OCRTool(), SecureStorageSystemAPI(), RetryMechanismTool(), HumanReviewTool(), ReportingTool(), process_docs_search]
    return create_react_agent(llm, agent4_tools, agent4_prompt)

anth_api_key = os.environ['anth_apikey']
llm = ChatAnthropic(temperature=0.3, anthropic_api_key=anth_api_key, model='claude-3-opus-20240229')

agent_email_detector = create_email_detector_agent(llm)
agent1_executor = AgentExecutor(agent=agent_email_detector, tools=agent_email_detector.tools, verbose=True, handle_parsing_errors=True)

agent_authenticator = create_authenticator_agent(llm)
agent2_executor = AgentExecutor(agent=agent_authenticator, tools=agent_authenticator.tools, verbose=True, handle_parsing_errors=True)

agent_screenshotter = create_screenshotter_agent(llm)
agent3_executor = AgentExecutor(agent=agent_screenshotter, tools=agent_screenshotter.tools, verbose=True, handle_parsing_errors=True)

agent_extractor = create_extractor_agent(llm)
agent4_executor = AgentExecutor(agent=agent_extractor, tools=agent_extractor.tools, verbose=True, handle_parsing_errors=True)

def email_detector_node(state):
    output = agent1_executor.invoke({"input": state["input"]})
    return {**state, "email_detector_output": output}

def authenticator_node(state):
    output = agent2_executor.invoke({"input": state["email_detector_output"]["output"]})
    return {**state, "authenticator_output": output}

def screenshotter_node(state):
    output = agent3_executor.invoke({"input": state["authenticator_output"]["output"]})
    return {**state, "screenshotter_output": output}

def extractor_node(state):
    output = agent4_executor.invoke({"input": state["screenshotter_output"]["output"]})
    return {**state, "extractor_output": output}

def should_continue(state):
    if "Extraction successful" in state["extractor_output"]["output"]:
        return "end"
    else:
        return "continue"

workflow = StateGraph(EncryptedEmailProcessingState)
workflow.add_node("email_detector", email_detector_node)
workflow.add_node("authenticator", authenticator_node)
workflow.add_node("screenshotter", screenshotter_node)
workflow.add_node("extractor", extractor_node)

workflow.set_entry_point("email_detector")
workflow.add_edge("email_detector", "authenticator")
workflow.add_edge("authenticator", "screenshotter")
workflow.add_edge("screenshotter", "extractor")

workflow.add_conditional_edges(
    "extractor",
    should_continue,
    {
        "continue": "email_detector",
        "end": END,
    },
)

app = workflow.compile()

user_input = "New email received"
inputs = {"input": user_input}

for s in app.stream(inputs):
    print(s)
