import os
import logging
from langchain.agents import create_react_agent, AgentExecutor
from langchain_anthropic import ChatAnthropic
from tools import linkedin_browser, linkedin_post_filter, human_approval, schedule_posts, monitor_linkedin_post, alert_post_changes
from context import redstone_security_sources_retriever
from prompts import agent1_prompt, agent2_prompt, agent3_prompt, agent4_prompt
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_agent(llm, tools, prompt):
    """
    Create an agent using the provided LLM, tools, and prompt.
    """
    return create_react_agent(llm=llm, tools=tools, prompt=prompt)

def execute_agent(agent, tools, input_data):
    """
    Execute an agent with the provided tools and input data.
    """
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
    try:
        result = executor.invoke(input_data["input"])
        return result["output"] if "output" in result else None
    except Exception as e:
        logger.error(f"Error executing agent: {str(e)}")
        return None

def get_user_input(prompt):
    """
    Get user input with error handling.
    """
    try:
        user_input = input(prompt)
        return user_input
    except KeyboardInterrupt:
        logger.info("User interrupted the input process.")
        return None

def main():
    anth_api_key = os.environ.get('anth_apikey')
    if not anth_api_key:
        logger.error("Anthropic API key not found in environment variables.")
        return

    llm = ChatAnthropic(temperature=0.3, anthropic_api_key=anth_api_key, model='claude-3-opus-20240229')

    agent1_tools = [linkedin_browser, linkedin_post_filter, human_approval, redstone_security_sources_retriever]
    agent2_tools = [linkedin_browser, human_approval, redstone_security_sources_retriever]
    agent3_tools = [linkedin_browser, human_approval]
    agent4_tools = [linkedin_browser, schedule_posts, monitor_linkedin_post, human_approval, redstone_security_sources_retriever]

    agent_linkedin_post_finder = create_agent(llm, agent1_tools, agent1_prompt)
    agent_comment_analyzer = create_agent(llm, agent2_tools, agent2_prompt)
    agent_linkedin_drafter = create_agent(llm, agent3_tools, agent3_prompt)
    agent_scheduler = create_agent(llm, agent4_tools, agent4_prompt)

    # Example input for the LinkedIn Post Finder agent
    input_data_linkedin = {"input": "Find relevant LinkedIn posts for Redstone Security"}

    # Execute the LinkedIn Post Finder agent and store the output
    output_linkedin = execute_agent(agent_linkedin_post_finder, agent1_tools, input_data_linkedin)

    if output_linkedin:
        # Use the output of the LinkedIn Post Finder agent as input for the LinkedIn Comment Analyzer agent
        input_data_comment_analyzer = {"input": output_linkedin}
        output_comment_analyzer = execute_agent(agent_comment_analyzer, agent2_tools, input_data_comment_analyzer)
    else:
        logger.warning("LinkedIn Post Finder agent did not produce an output.")

    # Example input for the LinkedIn Comment Drafter agent
    approved_comments = get_user_input("Enter approved comments for engagement: ")
    if approved_comments:
        input_data_drafter = {"input": approved_comments}
        output_drafter = execute_agent(agent_linkedin_drafter, agent3_tools, input_data_drafter)
    else:
        logger.warning("User did not provide approved comments.")

    # Example input for the LinkedIn Content Scheduler agent
    approved_content = get_user_input("Enter approved comments and replies for publishing: ")
    if approved_content:
        input_data_scheduler = {"input": approved_content}
        output_scheduler = execute_agent(agent_scheduler, agent4_tools, input_data_scheduler)
        if output_scheduler:
            logger.info(f"Performance metrics of published content: {output_scheduler}")
    else:
        logger.warning("User did not provide approved content.")

if __name__ == "__main__":
    main()
