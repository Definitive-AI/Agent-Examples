import os

import pysqlite3
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import streamlit as st
import sqlite3

import os
from langchain.agents import create_react_agent, create_tool_calling_agent, create_structured_chat_agent, AgentExecutor
from langchain_anthropic import ChatAnthropic
from tools import google_trends, seo_keyword_check
from context import seo_best_practices_retriever, universal_orchestrator_retriever, wonderbotz_articles_retriever, rpa_cloud_migration_retriever, chatgpt_automation_retriever
from prompts import agent1_prompt, agent2_prompt, agent3_prompt, agent4_prompt
from dotenv import load_dotenv
from typing import Dict
from reflection import create_reflection_agent
from StreamlitTools import StreamlitInput, StreamlitHandler
import time

load_dotenv()

with st.sidebar:
    anth_api_key = st.text_input("Anthropic API Key", key="anth_api_key", type="password")
    serp_api_key = st.text_input("SERP API Key", key="serp_api_key", type="password")
    
st.sidebar.title("Controls")
stop = st.sidebar.button("Stop")

def stop_processing():
    st.session_state.clear()

if stop:
    stop_processing()
    st.write("Stopped process")
    
llm = ChatAnthropic(temperature=0.3, model='claude-3-opus-20240229', anthropic_api_key=anth_api_key, max_tokens_to_sample= 4096, callbacks=[StreamlitHandler()])

streamlit_tool = StreamlitInput()

def create_agent1() -> AgentExecutor:
    """Create and return the first agent (Keyphrase Researcher)."""
    tools = [google_trends, streamlit_tool, seo_best_practices_retriever]
    agent = create_react_agent(llm=llm, tools=tools, prompt=agent1_prompt)
    return AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

def create_agent2() -> AgentExecutor:
    """Create and return the second agent (Content Outliner)."""
    tools = [google_trends, seo_keyword_check, streamlit_tool, seo_best_practices_retriever, universal_orchestrator_retriever, wonderbotz_articles_retriever, rpa_cloud_migration_retriever, chatgpt_automation_retriever]
    agent = create_tool_calling_agent(llm, tools, agent2_prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
    
def create_agent3() -> AgentExecutor:
    """Create and return the third agent (Content Generator)."""
    agent = create_reflection_agent(llm=llm, prompt=agent3_prompt, num_reflections=3)
    return agent 

def create_agent4() -> AgentExecutor:
    """Create and return the fourth agent (Article Optimizer)."""
    tools = [streamlit_tool, rpa_cloud_migration_retriever, universal_orchestrator_retriever]
    agent = create_react_agent(llm, tools, agent4_prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

def run_agent_chain(user_input) -> Dict[str, str]:
    """Run the agent chain and return the optimized article."""
    agent1_executor = create_agent1()
    agent2_executor = create_agent2()
    agent3_executor = create_agent3()
    agent4_executor = create_agent4()



    # Example input for the first agent
    user_input = t1 #input("Enter the topic and key ideas to include: ")
    input_keyphrase_research = {"input": user_input}

    # Execute the first agent
    output_keyphrase = agent1_executor.invoke(input_keyphrase_research)

    # Use the output of the first agent as input for the second agent
    input_content_outline = {
        "keyphrase": output_keyphrase["output"],
        "topic": user_input,
        "key_ideas": user_input,
        "seo_guidelines": output_keyphrase["output"]
    }

    # Execute the second agent with the output of the first agent as its input
    output_outline = agent2_executor.invoke(input_content_outline)

    # Use the output of the second agent as input for the third agent
    input_content_generator = {"input": output_outline["output"]}

    # Execute the third agent with the output of the second agent as its input
    output_content_generator = agent3_executor.invoke(input_content_generator)

    # Use the output of the third agent as input for the fourth agent
    input_article_optimizer = {"input": output_content_generator["output"]}

    # Execute the fourth agent with the output of the third agent as its input
    optimized_article = agent4_executor.invoke(input_article_optimizer)

    return optimized_article


if __name__ == "__main__":
    try:
        widget_update_func = st.empty().code
        streamlit_tool.add_ai_message("Enter topic, key ideas, products, potential key phrases, and example articles")

        while streamlit_tool.user_input == None:    
            time.sleep(2) 
               
        st.chat_message("user").write(streamlit_tool.user_input)        
        optimized_article = run_agent_chain(streamlit_tool.user_input)
        print(f"Optimized article: {optimized_article['output']}")
    except KeyError as e:
        print(f"Error: Missing required environment variable - {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
