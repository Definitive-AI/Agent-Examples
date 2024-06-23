import streamlit as st
from  typing import Union, Any, Dict
from streamlit.logger import get_logger
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.callbacks import CallbackManagerForToolRun
from typing import Callable, Optional
from streamlit.delta_generator import DeltaGenerator
from langchain_core.pydantic_v1 import Field
from langchain_core.tools import BaseTool
import time

class StreamlitHandler(BaseCallbackHandler):
    """Base callback handler that can be used to handle callbacks from langchain."""

    def __init__(self):
        super().__init__()
        self.widget_update_func = st.empty().code

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> Any:
        """Run when chain starts running."""
        print(inputs)
        self.widget_update_func(str(inputs))

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> Any:
        """Run when chain ends running."""
        print(outputs)
        self.widget_update_func(str(outputs))

    def on_chain_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> Any:
        """Run when chain errors."""
        print(error)
        self.widget_update_func(str(error))

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> Any:
        """Run when tool starts running."""
        print(input_str)
        self.widget_update_func(str(input_str))

    def on_tool_end(self, output: Any, **kwargs: Any) -> Any:
        """Run when tool ends running."""
        print(output)      
        self.widget_update_func(str(output))  

    def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> Any:
        """Run when tool errors."""
        print(error)
        self.widget_update_func(str(error))

    def on_text(self, text: str, **kwargs: Any) -> Any:
        """Run on arbitrary text."""
        print(text)
        self.widget_update_func(str(text))

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        """Run on agent action."""
        print(action)
        self.widget_update_func(str(action))

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        """Run on agent end."""
        print(finish)
        self.widget_update_func(str(finish))



class StreamlitInput(BaseTool):
    name: str = "human"
    description: str = (
        "You can ask a human for guidance when you think you "
        "got stuck or you are not sure what to do next. "
        "The input should be a question for the human."
    )

    messages =  [] 
    ai_message: DeltaGenerator = None
    user_message: DeltaGenerator = None
    st.session_state['user_text'] = None
    st.session_state.messages = []
    user_input: str = None

    def __init__(self):
        super().__init__()
        st.session_state.messages = []
        st.session_state['user_text'] = None
        self.messages =  st.session_state.messages
        self.ai_message: DeltaGenerator = None
        self.user_message: DeltaGenerator = None    
        self.user_input: str = st.chat_input('Enter text here:', key='widget', on_submit=self.clear_text)


    def display_messages(self):
        for msg in self.messages:
            st.chat_message(msg["role"]).write(msg["content"])

    def clear_text(self):
        st.session_state.user_text = st.session_state.widget
        self.user_input = st.session_state.widget

    def get_user_input(self):
        return self.user_input

    def get_text(self):
        input_text = self.user_input
        
        while input_text == None:        
            input_text = self.get_user_input()
            time.sleep(1)        
        
        if self.user_input:
            self.messages.append({"role": "user", "content": self.user_input})
            if self.user_message == None:
                self.user_message = st.chat_message("user")
            self.user_message.write(self.user_input)
            return self.user_input

    def prompt_func(self, input):
        if input:
            st.session_state.user_text = None
            self.user_input = None
            if self.ai_message == None:
                self.ai_message = st.chat_message("assistant")
            self.ai_message.write(input)
            self.messages.append({"role": "assistant", "content": input})

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        self.prompt_func(query)
        self.display_messages()        
        user_input = self.get_text()
        if user_input:
            if user_input == "q":
                st.stop()
            return user_input

