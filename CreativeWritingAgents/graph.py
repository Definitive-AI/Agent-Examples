import os

import pysqlite3
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import streamlit as st
import sqlite3

from langchain.agents import create_react_agent, create_tool_calling_agent, create_structured_chat_agent, AgentExecutor
from langchain_anthropic import ChatAnthropic
from tools import seo_keyword_check, human_tool #google_trends, 
from context import seo_best_practices_retriever, universal_orchestrator_retriever, wonderbotz_articles_retriever, rpa_cloud_migration_retriever, chatgpt_automation_retriever
from prompts import agent1_prompt, agent2_prompt, agent3_prompt, agent4_prompt
from dotenv import load_dotenv
from typing import Dict, Any, TypedDict, Annotated, List, Union
from langgraph.graph import END, StateGraph
from StreamlitTools import StreamlitInput, StreamlitHandler


load_dotenv()
with st.sidebar:
    anth_api_key = st.text_input("Anthropic API Key", key="anth_api_key", type="password")
    serp_api_key = st.text_input("SERP API Key", key="serp_api_key", type="password")

streamlit_tool = StreamlitInput()

llm = ChatAnthropic(temperature=0.3, model='claude-3-opus-20240229', anthropic_api_key=anth_api_key,callbacks=[StreamlitHandler()])

class ArticleWritingState(TypedDict):
    input: str
    keyphrase_research_output: Dict[str, Any]
    content_outline_output: Dict[str, Any]
    content_generator_output: Dict[str, Any]
    optimized_article: Dict[str, Any]

def create_agent1() -> AgentExecutor:
    tools = [streamlit_tool] #google_trends
    agent = create_react_agent(llm=llm, tools=tools, prompt=agent1_prompt)
    return AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

def create_agent2() -> AgentExecutor:
    tools = [streamlit_tool, seo_best_practices_retriever, universal_orchestrator_retriever, wonderbotz_articles_retriever]
    agent = create_tool_calling_agent(llm, tools, agent2_prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

def create_agent3() -> AgentExecutor:
    tools = [seo_keyword_check,rpa_cloud_migration_retriever, chatgpt_automation_retriever]
    agent = create_react_agent(llm=llm, tools=tools, prompt=agent3_prompt)
    return AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

def create_agent4() -> AgentExecutor:
    tools = [streamlit_tool, seo_best_practices_retriever, wonderbotz_articles_retriever]
    agent = create_structured_chat_agent(llm, tools, agent4_prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

agent1_executor = create_agent1()
agent2_executor = create_agent2()
agent3_executor = create_agent3()
agent4_executor = create_agent4()

def keyphrase_researcher_node(state: ArticleWritingState) -> ArticleWritingState:
    st.write("keyphrase_researcher_node")
    input_keyphrase_research = {"input": state["input"]}
    output_keyphrase = agent1_executor.invoke(input_keyphrase_research)
    return {**state, "keyphrase_research_output": output_keyphrase}

def content_outliner_node(state: ArticleWritingState) -> ArticleWritingState:
    input_content_outline = {
        "keyphrase": state["keyphrase_research_output"]["output"],
        "topic": state["input"],
        "key_ideas": state["input"],
        "seo_guidelines": state["keyphrase_research_output"]["output"]
    }
    output_outline = agent2_executor.invoke({"input": state["keyphrase_research_output"]["output"]})
    return {**state, "content_outline_output": output_outline}

def content_generator_node(state: ArticleWritingState) -> ArticleWritingState:
    input_content_generator = {"input": state["content_outline_output"]["output"]}
    output_content_generator = agent3_executor.invoke(input_content_generator)
    return {**state, "content_generator_output": output_content_generator}

def article_optimizer_node(state: ArticleWritingState) -> ArticleWritingState:
    input_article_optimizer = {"input": state["content_generator_output"]["output"]}
    optimized_article = agent4_executor.invoke(input_article_optimizer)
    return {**state, "optimized_article": optimized_article}

workflow = StateGraph(ArticleWritingState)
workflow.add_node("keyphrase_researcher", keyphrase_researcher_node)
workflow.add_node("content_outliner", content_outliner_node)
workflow.add_node("content_generator", content_generator_node)
workflow.add_node("article_optimizer", article_optimizer_node)

workflow.set_entry_point("keyphrase_researcher")
workflow.add_edge("keyphrase_researcher", "content_outliner")
workflow.add_edge("content_outliner", "content_generator")
workflow.add_edge("content_generator", "article_optimizer")
workflow.add_edge("article_optimizer", END)


# app = workflow.compile()
# import time
# if __name__ == "__main__":
#     try:

#         #user_input = st.text_input("Enter topic, key ideas, products, potential key phrases, and example articles:")
#         #streamlit_tool.add_ai_message("Enter topic, key ideas, products, potential key phrases, and example articles:")
#         #input1 = streamlit_tool._run("Enter topic, key ideas, products, potential key phrases, and example articles:")

#         widget_update_func = st.empty().code
#         streamlit_tool.add_ai_message("Enter topic, key ideas, products, potential key phrases, and example articles")

#         while streamlit_tool.user_input == None:     
#             st.write("waiting")
#             time.sleep(2)       
#         st.chat_message("user").write(streamlit_tool.user_input)
        
#         input_data = {"input": streamlit_tool.user_input}

#         progress_bar = st.progress(0)
        
#         for i, s in enumerate(app.stream(input_data)):
#             print(s)
#             agent_name = list(s.keys())[-1]
#             st.write(f"Agent: {agent_name}")
#             st.write(f"Results/Outputs:")
#             st.write(s[agent_name])
#             progress_bar.progress((i + 1) / 4)    

#     except KeyError as e:
#         print(f"Error: Missing required environment variable - {str(e)}")
#     except Exception as e:
#         print(f"An error occurred: {str(e)}")
