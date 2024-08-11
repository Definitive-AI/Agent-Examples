import os
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from langchain.agents import AgentType, create_react_agent, initialize_agent
from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, END

# Import tools and contexts (assuming these are defined in separate modules)
from tools import (
    office_automation_tool, pdf_tool, data_verification_interface, word_doc_analyzer,
    word_document_handler, ms_office_integration_tool, file_system_manager,
    human_review_interface, court_procedure_db
)
from context import (
    template_documents, excel_data_structure_guide, file_naming_conventions,
    guardianship_renewal_requirements, attorney_fee_guidelines,
    financial_medical_guidelines, court_specific_guidelines
)
from prompts import agent1_prompt, agent2_prompt, agent3_prompt, agent4_prompt

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    raise ValueError("Anthropic API key not found in environment variables")

ANTHROPIC_MODEL = 'claude-3-opus-20240229'

class DocumentProcessingState(TypedDict):
    user_input: str
    initial_data: Optional[Dict[str, Any]]
    document_requirements: Optional[Dict[str, Any]]
    prepared_documents: Optional[Dict[str, Any]]
    processing_status: Optional[str]
    exceptions: Optional[List[str]]
    analysis_results: Optional[Dict[str, Any]]
    detected_errors: Optional[List[str]]
    quality_assurance_report: Optional[Dict[str, Any]]
    generated_content: Optional[Dict[str, Any]]
    human_review_results: Optional[Dict[str, Any]]
    final_document_package: Optional[Dict[str, Any]]
    process_completion_status: Optional[str]

def initialize_llm() -> ChatAnthropic:
    return ChatAnthropic(temperature=0.3, anthropic_api_key=ANTHROPIC_API_KEY, model=ANTHROPIC_MODEL)

def create_agent_executor(llm: ChatAnthropic, prompt: PromptTemplate, tools: list, agent_type: AgentType = AgentType.REACT) -> AgentExecutor:
    if agent_type == AgentType.REACT:
        agent = create_react_agent(llm, tools, prompt)
    else:
        agent = initialize_agent(tools, llm, agent=agent_type, prompt=prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

llm = initialize_llm()

agent1_executor = create_agent_executor(llm, agent1_prompt, [office_automation_tool, pdf_tool, data_verification_interface, template_documents, excel_data_structure_guide, file_naming_conventions])
agent2_executor = create_agent_executor(llm, agent2_prompt, [word_doc_analyzer, template_documents, guardianship_renewal_requirements])
agent3_executor = create_agent_executor(llm, agent3_prompt, [word_document_handler, guardianship_renewal_requirements, attorney_fee_guidelines, financial_medical_guidelines])
agent4_executor = create_agent_executor(llm, agent4_prompt, [ms_office_integration_tool, file_system_manager, human_review_interface, court_procedure_db, court_specific_guidelines, guardianship_renewal_requirements, file_naming_conventions], AgentType.REACT)

def agent1_node(state: DocumentProcessingState) -> DocumentProcessingState:
    logger.info("Starting document processing")
    try:
        result = agent1_executor.invoke({"input": state.get("initial_data", {})})
        state["prepared_documents"] = result["output"].get("prepared_documents", {})
        state["processing_status"] = result["output"].get("processing_status", "Processing completed")
        state["exceptions"] = result["output"].get("exceptions", [])
    except Exception as e:
        logger.error(f"Error in agent1_node: {str(e)}")
        state["exceptions"] = state.get("exceptions", []) + [str(e)]
    logger.info("Document processing completed")
    return state

def agent2_node(state: DocumentProcessingState) -> DocumentProcessingState:
    logger.info("Starting content analysis and error detection")
    try:
        result = agent2_executor.invoke({"input": state.get("prepared_documents", {})})
        state["analysis_results"] = result["output"].get("analysis_results", {})
        state["detected_errors"] = result["output"].get("detected_errors", [])
        state["quality_assurance_report"] = result["output"].get("quality_assurance_report", {})
    except Exception as e:
        logger.error(f"Error in agent2_node: {str(e)}")
        state["exceptions"] = state.get("exceptions", []) + [str(e)]
    logger.info("Content analysis and error detection completed")
    return state

def agent3_node(state: DocumentProcessingState) -> DocumentProcessingState:
    logger.info("Starting content generation and review")
    try:
        input_data = {
            "analysis_results": state.get("analysis_results", {}),
            "detected_errors": state.get("detected_errors", [])
        }
        result = agent3_executor.invoke({"input": input_data})
        state["generated_content"] = result["output"].get("generated_content", {})
        state["human_review_results"] = result["output"].get("human_review_results", {})
    except Exception as e:
        logger.error(f"Error in agent3_node: {str(e)}")
        state["exceptions"] = state.get("exceptions", []) + [str(e)]
    logger.info("Content generation and review completed")
    return state

def agent4_node(state: DocumentProcessingState) -> DocumentProcessingState:
    logger.info("Starting workflow and exception management")
    try:
        input_data = {
            "user_input": state["user_input"],
            "processing_status": state.get("processing_status", ""),
            "exceptions": state.get("exceptions", []),
            "quality_assurance_report": state.get("quality_assurance_report", {}),
            "generated_content": state.get("generated_content", {}),
            "human_review_results": state.get("human_review_results", {})
        }
        result = agent4_executor.invoke({"input": input_data})
        state["initial_data"] = result["output"].get("initial_data", {})
        state["document_requirements"] = result["output"].get("document_requirements", {})
        state["final_document_package"] = result["output"].get("final_document_package", {})
        state["process_completion_status"] = result["output"].get("process_completion_status", "")
    except Exception as e:
        logger.error(f"Error in agent4_node: {str(e)}")
        state["exceptions"] = state.get("exceptions", []) + [str(e)]
    logger.info("Workflow and exception management completed")
    return state

def agent4_decision(state: DocumentProcessingState) -> str:
    if state.get("exceptions"):
        return "agent1"
    elif state.get("detected_errors"):
        return "generate_content"
    elif state.get("generated_content"):
        return "finalize"
    else:
        return "agent1"

def agent2_decision(state: DocumentProcessingState) -> str:
    if state.get("analysis_results", {}).get("needs_specialized_content", False):
        return "generate_specialized_content"
    else:
        return "continue"

workflow = StateGraph(DocumentProcessingState)

workflow.add_node("agent1", agent1_node)
workflow.add_node("agent2", agent2_node)
workflow.add_node("agent3", agent3_node)
workflow.add_node("agent4", agent4_node)

workflow.set_entry_point("agent4")

workflow.add_edge("agent4", "agent1")
workflow.add_edge("agent1", "agent2")
workflow.add_edge("agent3", "agent4")

workflow.add_conditional_edges(
    "agent4",
    agent4_decision,
    {
        "agent1": "agent1",
        "generate_content": "agent3",
        "finalize": END,
    }
)

workflow.add_conditional_edges(
    "agent2",
    agent2_decision,
    {
        "generate_specialized_content": "agent3",
        "continue": "agent4"
    }
)

graph = workflow.compile()

async def main():
    user_input = "Process guardianship renewal documents for case ID 12345"
    try:
        initial_state = DocumentProcessingState(user_input=user_input)
        final_state = await graph.arun(initial_state)
        print("Final Output:", final_state["final_document_package"])
        print("Process Completion Status:", final_state["process_completion_status"])
    except Exception as e:
        logger.error(f"An error occurred in the main execution: {str(e)}")
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
