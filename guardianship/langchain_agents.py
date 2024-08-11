import os
import logging
from typing import Dict, Tuple, Any
from dotenv import load_dotenv
from langchain.agents import AgentType, create_react_agent, initialize_agent
from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor
from langchain.prompts import PromptTemplate

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
ANTHROPIC_MODEL = 'claude-3-opus-20240229'

class AgentChain:
    def __init__(self):
        self.llm = self._initialize_llm()
        self.agent1_executor = self._create_agent_executor(agent1_prompt, self._get_agent1_tools())
        self.agent2_executor = self._create_agent_executor(agent2_prompt, self._get_agent2_tools())
        self.agent3_executor = self._create_agent_executor(agent3_prompt, self._get_agent3_tools())
        self.agent4_executor = self._create_agent_executor(agent4_prompt, self._get_agent4_tools(), agent_type=AgentType.REACT)

    @staticmethod
    def _initialize_llm() -> ChatAnthropic:
        if not ANTHROPIC_API_KEY:
            raise ValueError("Anthropic API key not found in environment variables")
        return ChatAnthropic(temperature=0.3, anthropic_api_key=ANTHROPIC_API_KEY, model=ANTHROPIC_MODEL)

    def _create_agent_executor(self, prompt: PromptTemplate, tools: list, agent_type: AgentType = AgentType.REACT) -> AgentExecutor:
        if agent_type == AgentType.REACT:
            agent = create_react_agent(self.llm, tools, prompt)
        else:
            agent = initialize_agent(tools, self.llm, agent=agent_type, prompt=prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    @staticmethod
    def _get_agent1_tools() -> list:
        return [office_automation_tool, pdf_tool, data_verification_interface, template_documents, excel_data_structure_guide, file_naming_conventions]

    @staticmethod
    def _get_agent2_tools() -> list:
        return [word_doc_analyzer, template_documents, guardianship_renewal_requirements]

    @staticmethod
    def _get_agent3_tools() -> list:
        return [word_document_handler, guardianship_renewal_requirements, attorney_fee_guidelines, financial_medical_guidelines]

    @staticmethod
    def _get_agent4_tools() -> list:
        return [ms_office_integration_tool, file_system_manager, human_review_interface, court_procedure_db, court_specific_guidelines, guardianship_renewal_requirements, file_naming_conventions]

    async def process_documents(self, input_data: str) -> Tuple[str, str]:
        try:
            logger.info("Starting document processing")
            result = await self.agent1_executor.ainvoke({"input": input_data})
            prepared_documents = result.get("output", "No documents prepared")
            processing_status = result.get("status", "Processing completed with no specific status")
            logger.info("Document processing completed")
            return prepared_documents, processing_status
        except Exception as e:
            logger.error(f"Error in process_documents: {str(e)}")
            raise

    async def content_analysis_and_error_detection(self, prepared_documents: str) -> str:
        try:
            logger.info("Starting content analysis and error detection")
            input_data = {"input": prepared_documents}
            output = await self.agent2_executor.ainvoke(input_data)
            analysis_results = output.get("output", {}).get("analysis_results", "No analysis results available.")
            detected_errors = output.get("output", {}).get("detected_errors", "No errors detected.")
            quality_assurance_report = output.get("output", {}).get("quality_assurance_report", "No quality assurance report available.")
            output_agent3 = f"Analysis Results and Detected Errors:\n{analysis_results}\n{detected_errors}"
            output_agent4 = f"Quality Assurance Report:\n{quality_assurance_report}"
            logger.info("Content analysis and error detection completed")
            return f"Output for Agent 3:\n{output_agent3}\n\nOutput for Agent 4:\n{output_agent4}"
        except Exception as e:
            logger.error(f"Error in content_analysis_and_error_detection: {str(e)}")
            raise

    async def content_generation_and_review_agent(self, input_data: str) -> str:
        try:
            logger.info("Starting content generation and review")
            agent_input = {"input": input_data}
            output = await self.agent3_executor.ainvoke(agent_input)
            logger.info("Content generation and review completed")
            return output["output"]
        except Exception as e:
            logger.error(f"Error in content_generation_and_review_agent: {str(e)}")
            raise

    async def workflow_and_exception_management_agent(self, user_input: str, agent1_output: str, agent2_output: str, agent3_output: str) -> Dict[str, str]:
        try:
            logger.info("Starting workflow and exception management")
            input_data = f"""
            User Input: {user_input}
            Agent 1 Output: {agent1_output}
            Agent 2 Output: {agent2_output}
            Agent 3 Output: {agent3_output}
            
            Based on the above inputs, manage the workflow and handle any exceptions. Provide instructions for Agent 1 and prepare the final output for the user.
            """
            output = await self.agent4_executor.ainvoke({"input": input_data})
            agent1_instructions = ""
            user_output = ""
            for line in output["output"].split('\n'):
                if line.startswith("Instructions for Agent 1:"):
                    agent1_instructions = line.split(":", 1)[1].strip()
                elif line.startswith("Output for User:"):
                    user_output = line.split(":", 1)[1].strip()
            logger.info("Workflow and exception management completed")
            return {
                "agent1_instructions": agent1_instructions,
                "user_output": user_output
            }
        except Exception as e:
            logger.error(f"Error in workflow_and_exception_management_agent: {str(e)}")
            raise

    async def run_agent_chain(self, user_input: str) -> str:
        try:
            logger.info("Starting agent chain")
            
            # Agent 4: Initial workflow management
            initial_workflow = await self.workflow_and_exception_management_agent(user_input, "", "", "")
            logger.info("Completed initial workflow management")
            
            # Agent 1: Process documents
            prepared_docs, status = await self.process_documents(initial_workflow["agent1_instructions"])
            logger.info("Completed document processing")
            
            # Agent 2: Content analysis and error detection
            analysis_result = await self.content_analysis_and_error_detection(prepared_docs)
            logger.info("Completed content analysis and error detection")
            
            # Agent 3: Content generation and review
            generated_content = await self.content_generation_and_review_agent(analysis_result)
            logger.info("Completed content generation and review")
            
            # Agent 4: Final workflow management and output preparation
            final_result = await self.workflow_and_exception_management_agent(user_input, status, analysis_result, generated_content)
            logger.info("Completed final workflow management")
            
            return final_result["user_output"]
        except Exception as e:
            logger.error(f"Error in run_agent_chain: {str(e)}")
            raise

async def main():
    agent_chain = AgentChain()
    user_input = "Process guardianship renewal documents for case ID 12345"
    try:
        final_output = await agent_chain.run_agent_chain(user_input)
        print("Final Output:", final_output)
    except Exception as e:
        logger.error(f"An error occurred in the main execution: {str(e)}")
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
