import os
import logging
from typing import TypedDict, Annotated, List, Union
from langchain.agents import create_react_agent, AgentExecutor
from langchain_anthropic import ChatAnthropic
from tools import linkedin_browser, linkedin_post_filter, human_approval, schedule_posts, monitor_linkedin_post, alert_post_changes
from context import redstone_security_sources_retriever
from prompts import agent1_prompt, agent2_prompt, agent3_prompt, agent4_prompt
from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocialMediaMonitoringState(TypedDict):
    input: str
    linkedin_posts: dict
    analyzed_comments: dict
    drafted_comments: dict
    performance_metrics: dict

def create_agent(llm, tools, prompt):
    return create_react_agent(llm=llm, tools=tools, prompt=prompt)

def execute_agent(agent, tools, input_data):
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
    try:
        result = executor.invoke(input_data)
        return result
    except Exception as e:
        logger.error(f"Error executing agent: {str(e)}")
        return None

anth_api_key = os.environ.get('anth_apikey')
if not anth_api_key:
    logger.error("Anthropic API key not found in environment variables.")
    raise ValueError("Anthropic API key not found.")

llm = ChatAnthropic(temperature=0.3, anthropic_api_key=anth_api_key, model='claude-3-opus-20240229')

agent1_tools = [linkedin_browser, linkedin_post_filter, human_approval, redstone_security_sources_retriever]
agent2_tools = [linkedin_browser, human_approval, redstone_security_sources_retriever]
agent3_tools = [linkedin_browser, human_approval]
agent4_tools = [linkedin_browser, schedule_posts, monitor_linkedin_post, human_approval, redstone_security_sources_retriever]

agent_linkedin_post_finder = create_agent(llm, agent1_tools, agent1_prompt)
agent_comment_analyzer = create_agent(llm, agent2_tools, agent2_prompt)
agent_linkedin_drafter = create_agent(llm, agent3_tools, agent3_prompt)
agent_scheduler = create_agent(llm, agent4_tools, agent4_prompt)

def linkedin_post_finder_node(state):
    output = execute_agent(agent_linkedin_post_finder, agent1_tools, {"input": state["input"]})
    if output is None:
        raise ValueError("LinkedIn Post Finder agent failed to produce an output.")
    return {**state, "linkedin_posts": output}

def comment_analyzer_node(state):
    output = execute_agent(agent_comment_analyzer, agent2_tools, {"input": state["linkedin_posts"]["output"]})
    if output is None:
        raise ValueError("Comment Analyzer agent failed to produce an output.")
    return {**state, "analyzed_comments": output}

def comment_drafter_node(state):
    output = execute_agent(agent_linkedin_drafter, agent3_tools, {"input": state["analyzed_comments"]["output"]})
    if output is None:
        raise ValueError("Comment Drafter agent failed to produce an output.")
    return {**state, "drafted_comments": output}

def content_scheduler_node(state):
    output = execute_agent(agent_scheduler, agent4_tools, {"input": state["drafted_comments"]["output"]})
    if output is None:
        raise ValueError("Content Scheduler agent failed to produce an output.")
    return {**state, "performance_metrics": output}

workflow = StateGraph(SocialMediaMonitoringState)
workflow.add_node("linkedin_post_finder", linkedin_post_finder_node)
workflow.add_node("comment_analyzer", comment_analyzer_node)
workflow.add_node("comment_drafter", comment_drafter_node)
workflow.add_node("content_scheduler", content_scheduler_node)

workflow.set_entry_point("linkedin_post_finder")
workflow.add_edge("linkedin_post_finder", "comment_analyzer")
workflow.add_edge("comment_analyzer", "comment_drafter")
workflow.add_edge("comment_drafter", "content_scheduler")
workflow.add_edge("content_scheduler", END)

app = workflow.compile()

user_input = input("Enter input for LinkedIn Post Finder: ")
input_data = {"input": user_input}

for s in app.stream(input_data):
    print(s)
