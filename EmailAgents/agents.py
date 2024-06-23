import os
from langchain.agents import AgentType, create_react_agent, create_tool_calling_agent
from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor
from tools import EmailMonitoringTool, EmailFlaggingTool, HumanReviewTool, SecureCredentialStorage, WebBrowserAutomation, HumanOperatorNotification, ScreenshotCaptureTool, OCRTool, SecureStorageSystemAPI, RetryMechanismTool, ReportingTool
from context import process_docs_search, exception_handling_retriever
from prompts import agent1_prompt, agent2_prompt, agent3_prompt, agent4_prompt
from dotenv import load_dotenv

load_dotenv()

def create_email_detector_agent(llm):
    """
    Creates an agent for detecting flagged encrypted or protected email details.
    
    Args:
        llm: The language model to be used by the agent.
        
    Returns:
        The created email detector agent.
    """
    agent1_tools = [EmailMonitoringTool(), EmailFlaggingTool(), HumanReviewTool(), process_docs_search]
    return create_react_agent(llm, agent1_tools, agent1_prompt)

def create_authenticator_agent(llm):
    """
    Creates an agent for authenticating and accessing encrypted emails.
    
    Args:
        llm: The language model to be used by the agent.
        
    Returns:
        The created authenticator agent.
    """
    agent2_tools = [SecureCredentialStorage(), WebBrowserAutomation(), HumanOperatorNotification(), exception_handling_retriever]
    return create_react_agent(llm, agent2_tools, agent2_prompt)

def create_screenshotter_agent(llm):
    """
    Creates an agent for capturing screenshots of encrypted email navigation.
    
    Args:
        llm: The language model to be used by the agent.
        
    Returns:
        The created screenshotter agent.
    """
    agent3_tools = [ScreenshotCaptureTool(), process_docs_search]
    return create_tool_calling_agent(llm, agent3_tools, agent3_prompt)

def create_extractor_agent(llm):
    """
    Creates an agent for extracting information from encrypted email screenshots.
    
    Args:
        llm: The language model to be used by the agent.
        
    Returns:
        The created extractor agent.
    """
    agent4_tools = [OCRTool(), SecureStorageSystemAPI(), RetryMechanismTool(), HumanReviewTool(), ReportingTool(), process_docs_search]
    return create_react_agent(llm, agent4_tools, agent4_prompt)

def main():
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

    new_email_received = True

    while new_email_received:
        try:
            input_data_agent1 = {"input": "New email received"}
            output_email_detector = agent1_executor.invoke(input_data_agent1)
            print(f"Email Detector Output: {output_email_detector}")
            
            if "Flagged encrypted or protected email details" in output_email_detector:
                input_data_agent2 = {"input": output_email_detector}
                output_authenticator = agent2_executor.invoke(input_data_agent2)
                print(f"Authenticator Output: {output_authenticator}")
                
                input_data_screenshotter = {"input": output_authenticator}
                output_screenshotter = agent3_executor.invoke(input_data_screenshotter["input"])
                print(f"Screenshotter Output: {output_screenshotter}")
                
                encrypted_email_screenshot = output_screenshotter
                input_data_extractor = {"input": encrypted_email_screenshot}
                output_extractor = agent4_executor.invoke(input_data_extractor["input"])
                print(f"Extractor Output: {output_extractor}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        
        new_email_received = EmailMonitoringTool().check_for_new_emails()

if __name__ == "__main__":
    main()
