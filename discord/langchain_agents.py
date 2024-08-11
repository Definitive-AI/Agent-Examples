import os
import asyncio
import logging
from typing import Tuple, Dict, Any
from functools import lru_cache

from langchain.agents import AgentType, create_react_agent
from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

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

async def process_discord_event(event: Dict[str, Any]) -> Tuple[str, str, str]:
    try:
        input_data = f"Process this Discord event: {event}"
        output = await agent1_executor.ainvoke({"input": input_data})
        output_text = output['output']
        parts = output_text.split('|')
        categorized_question = parts[0] if len(parts) > 0 else ""
        triage_info = parts[1] if len(parts) > 1 else ""
        discord_action = parts[2] if len(parts) > 2 else ""
        return categorized_question.strip(), triage_info.strip(), discord_action.strip()
    except Exception as e:
        logger.error(f"Error in process_discord_event: {e}")
        return "", "", ""

@lru_cache(maxsize=CACHE_SIZE)
async def knowledge_base_and_faq_management_agent(input_data: str) -> str:
    try:
        result = await agent2_executor.ainvoke({"input": input_data})
        return result["output"]
    except Exception as e:
        logger.error(f"Error in knowledge_base_and_faq_management_agent: {e}")
        return ""

async def answer_generation_nlp_agent(input_data: str) -> str:
    try:
        agent_input = {
            "input": input_data,
            "context": "Knowledge Base and FAQs, Official Documentation, Response Templates or Guidelines"
        }
        output = await agent3_executor.ainvoke(agent_input)
        return output["output"]
    except Exception as e:
        logger.error(f"Error in answer_generation_nlp_agent: {e}")
        return ""

async def quality_assurance_sentiment_analysis_agent(input_data: str, user_feedback: str = None) -> Tuple[str, str]:
    try:
        agent_input = {
            "input": input_data,
            "user_feedback": user_feedback if user_feedback else "No user feedback provided.",
            "task": "Perform quality assurance and sentiment analysis on the given input. If user feedback is provided, incorporate it into your analysis."
        }
        output = await agent4_executor.ainvoke(agent_input)
        refined_answer = output.get("output", "").split("Refined Answer: ")[-1].split("Feedback for Knowledge Base:")[0].strip()
        feedback_for_knowledge_base = output.get("output", "").split("Feedback for Knowledge Base:")[-1].strip()
        return refined_answer, feedback_for_knowledge_base
    except Exception as e:
        logger.error(f"Error in quality_assurance_sentiment_analysis_agent: {e}")
        return "", ""

async def response_management_and_feedback_agent(input_data: str) -> str:
    try:
        result = await agent5_executor.ainvoke({"input": input_data})
        return result['output']
    except Exception as e:
        logger.error(f"Error in response_management_and_feedback_agent: {e}")
        return ""

async def process_discord_chain(event: Dict[str, Any]) -> str:
    categorized_question, triage_info, discord_action = await process_discord_event(event)
    kb_faq_info = await knowledge_base_and_faq_management_agent(f"{categorized_question}\n{triage_info}")
    generated_answer = await answer_generation_nlp_agent(kb_faq_info)
    refined_answer, feedback = await quality_assurance_sentiment_analysis_agent(generated_answer)
    final_response = await response_management_and_feedback_agent(f"Refined answer: {refined_answer}\nDiscord action: {discord_action}")
    return final_response

async def monitor_discord():
    try:
        while True:
            new_events = await discord_api_tool.aget_new_events()
            for event in new_events:
                final_response = await process_discord_chain(event)
                logger.info(f"Final response for event: {final_response}")
            await asyncio.sleep(1)  # Add a small delay to prevent excessive CPU usage
    except asyncio.CancelledError:
        logger.info("Discord monitor shutting down gracefully")

async def main():
    monitor_task = asyncio.create_task(monitor_discord())
    try:
        await monitor_task
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        monitor_task.cancel()
        await monitor_task

if __name__ == "__main__":
    asyncio.run(main())
ANTHROPIC_API_KEY = "your_anthropic_api_key_here"
LOG_LEVEL = logging.INFO  # or any other log level you prefer
CACHE_SIZE = 100  # or any other size you prefer for the LRU cache
