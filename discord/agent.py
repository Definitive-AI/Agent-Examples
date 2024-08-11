import os
import asyncio
import logging
from typing import Dict, Any, TypedDict, Annotated, NotRequired
from functools import lru_cache

from langchain.agents import AgentType, create_react_agent
from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from tools import discord_api_tool, kbms_api_tool, web_browser_tool, translation_api_tool, human_feedback_interface, sentiment_analysis_api, discord_integration_tool, ticket_management_tool, analytics_reporting_tool
from context import server_guidelines, response_guidelines, knowledge_base, official_docs, trusted_websites
from prompts import agent1_prompt, agent2_prompt, agent3_prompt, agent4_prompt, agent5_prompt
from config import ANTHROPIC_API_KEY, LOG_LEVEL, CACHE_SIZE

# Setup logging
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize the language model
llm = ChatAnthropic(temperature=0.3, anthropic_api_key=ANTHROPIC_API_KEY, model='claude-3-opus-20240229')

# Define tools for each agent
agent1_tools = [discord_api_tool, server_guidelines, response_guidelines]
agent2_tools = [kbms_api_tool, web_browser_tool, translation_api_tool, knowledge_base, official_docs, trusted_websites]
agent3_tools = [knowledge_base, official_docs, response_guidelines]
agent4_tools = [human_feedback_interface, sentiment_analysis_api, server_guidelines, response_guidelines]
agent5_tools = [discord_integration_tool, ticket_management_tool, analytics_reporting_tool, response_guidelines, server_guidelines]

# Create ReAct agents
agent1 = create_react_agent(llm, agent1_tools, agent1_prompt)
agent2 = create_react_agent(llm, agent2_tools, agent2_prompt)
agent3 = create_react_agent(llm, agent3_tools, agent3_prompt)
agent4 = create_react_agent(llm, agent4_tools, agent4_prompt)
agent5 = create_react_agent(llm, agent5_tools, agent5_prompt)

# Create agent executors
agent1_executor = AgentExecutor(agent=agent1, tools=agent1_tools, verbose=True, handle_parsing_errors=True)
agent2_executor = AgentExecutor(agent=agent2, tools=agent2_tools, verbose=True, handle_parsing_errors=True)
agent3_executor = AgentExecutor(agent=agent3, tools=agent3_tools, verbose=True, handle_parsing_errors=True)
agent4_executor = AgentExecutor(agent=agent4, tools=agent4_tools, verbose=True, handle_parsing_errors=True)
agent5_executor = AgentExecutor(agent=agent5, tools=agent5_tools, verbose=True, handle_parsing_errors=True)

class DiscordBotState(TypedDict):
    input: NotRequired[Dict[str, Any]]
    categorized_question: str
    triage_info: str
    discord_action: str
    kb_faq_info: str
    generated_answer: str
    refined_answer: str
    feedback: str
    final_response: str

def monitoring_node(state: DiscordBotState) -> DiscordBotState:
    try:
        output = agent1_executor.invoke({"input": f"Process this Discord event: {state['input']}"})
        output_text = output['output']
        parts = output_text.split('|')
        state["categorized_question"] = parts[0].strip() if len(parts) > 0 else ""
        state["triage_info"] = parts[1].strip() if len(parts) > 1 else ""
        state["discord_action"] = parts[2].strip() if len(parts) > 2 else ""
    except Exception as e:
        logger.error(f"Error in monitoring_node: {e}")
        state["categorized_question"] = ""
        state["triage_info"] = ""
        state["discord_action"] = ""
    return state

def knowledge_base_node(state: DiscordBotState) -> DiscordBotState:
    input_data = f"{state['categorized_question']}\n{state['triage_info']}"
    result = agent2_executor.invoke({"input": input_data})
    state["kb_faq_info"] = result["output"]
    return state

def answer_generation_node(state: DiscordBotState) -> DiscordBotState:
    agent_input = {
        "input": state["kb_faq_info"],
        "context": "Knowledge Base and FAQs, Official Documentation, Response Templates or Guidelines"
    }
    output = agent3_executor.invoke(agent_input)
    state["generated_answer"] = output["output"]
    return state

def quality_assurance_node(state: DiscordBotState) -> DiscordBotState:
    agent_input = {
        "input": state["generated_answer"],
        "user_feedback": "No user feedback provided.",
        "task": "Perform quality assurance and sentiment analysis on the given input."
    }
    output = agent4_executor.invoke(agent_input)
    output_text = output["output"]
    state["refined_answer"] = output_text.split("Refined Answer: ")[-1].split("Feedback for Knowledge Base:")[0].strip()
    state["feedback"] = output_text.split("Feedback for Knowledge Base:")[-1].strip()
    return state

def response_management_node(state: DiscordBotState) -> DiscordBotState:
    input_data = f"Refined answer: {state['refined_answer']}\nDiscord action: {state['discord_action']}"
    result = agent5_executor.invoke({"input": input_data})
    state["final_response"] = result['output']
    return state

def should_use_kb(state: DiscordBotState) -> str:
    if "simple_question" in state["categorized_question"]:
        return "answer_generation"
    return "knowledge_base"

# Create the graph
workflow = StateGraph(DiscordBotState)

workflow.add_node("monitoring", monitoring_node)
workflow.add_node("knowledge_base", knowledge_base_node)
workflow.add_node("answer_generation", answer_generation_node)
workflow.add_node("quality_assurance", quality_assurance_node)
workflow.add_node("response_management", response_management_node)

workflow.set_entry_point("monitoring")

workflow.add_conditional_edges(
    "monitoring",
    should_use_kb,
    {
        "knowledge_base": "knowledge_base",
        "answer_generation": "answer_generation"
    }
)

workflow.add_edge("knowledge_base", "answer_generation")
workflow.add_edge("answer_generation", "quality_assurance")
workflow.add_edge("quality_assurance", "response_management")
workflow.add_edge("response_management", END)

# Compile the graph
graph = workflow.compile()

async def process_discord_event(event: Dict[str, Any]) -> str:
    initial_state = DiscordBotState(
        input=event,
        categorized_question="",
        triage_info="",
        discord_action="",
        kb_faq_info="",
        generated_answer="",
        refined_answer="",
        feedback="",
        final_response=""
    )
    final_state = await graph.ainvoke(initial_state)
    return final_state["final_response"]

async def monitor_discord() -> None:
    try:
        while True:
            new_events = await discord_api_tool.aget_new_events()
            for event in new_events:
                final_response = await process_discord_event(event)
                logger.info(f"Final response for event: {final_response}")
            await asyncio.sleep(1)  # Add a small delay to prevent excessive CPU usage
    except asyncio.CancelledError:
        logger.info("Discord monitor shutting down gracefully")

async def main() -> None:
    monitor_task = asyncio.create_task(monitor_discord())
    try:
        await monitor_task
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        monitor_task.cancel()
        await monitor_task

if __name__ == "__main__":
    asyncio.run(main())
