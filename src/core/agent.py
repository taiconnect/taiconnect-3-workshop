"""
AgentCore Memory-enabled Agent.
"""
import asyncio
import chainlit as cl

from typing import List, Optional

from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.agent import FunctionAgent
from llama_index.core.agent.workflow import AgentStream, ToolCallResult
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.workflow import Context
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from llama_index.llms.anthropic import Anthropic

from src.storage.models import ExchangeMessage
from src.core.session_manager import AgentCoreMemorySessionManager
from src.config.settings import settings as config_settings

class Agent:
    """Memory-enhanced agent with AgentCore capabilities."""
    
    def __init__(
        self,
        system_prompt: str,
        session_manager: AgentCoreMemorySessionManager,
        tools: Optional[List[FunctionTool]] = None,
        max_iterations: int = 5,
        streaming: bool = True,
        verbose: bool = True
    ):
        """
        Initialize memory-enhanced agent.
        
        Args:
            system_prompt: System prompt for the agent
            session_manager: AgentCore memory session manager
            no_of_exchanges_to_llm: Number of exchanges to consider for LLM
            llm: Language model instance
            tools: Optional list of tools
            max_iterations: Maximum agent iterations
            streaming: Enable streaming responses
            verbose: Enable verbose logging
        """
        self.system_prompt = system_prompt
        self.session_manager = session_manager
        self.tools = tools or []
        self.max_iterations = max_iterations
        self.streaming = streaming
        self.verbose = verbose
        
        # Initialize memory
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=40000)
        self.llm = self._get_llm()
        # Initialize agent
        agent_kwargs = {
            "tools": self.tools,
            "llm": self.llm,
            "streaming": self.streaming,
            "verbose": self.verbose,
            "system_prompt": self.system_prompt,
        }
        if self.is_openai_model():
            agent_kwargs["initial_tool_choice"] = "retrieve_memory_context"
        
        self._agent = FunctionAgent(**agent_kwargs)
    
    async def invoke(self, user_message: str) -> str:
        """
        Invoke the agent with memory enhancement.
        
        Args:
            user_message: User's message
            
        Returns:
            Agent's response
        """
        thread_messages = self.session_manager.get_chat_history()
        formatted_messages = self.session_manager.format_messages_for_llm(thread_messages)
        chat_history: list = cl.user_session.get("chat_history", formatted_messages)
        
        is_all_exchanges_selected = self.session_manager.config.no_of_exchanges_to_llm == 'All'
        if is_all_exchanges_selected:
            messages_to_send = thread_messages
        else:
            recent_chat_messages = self.session_manager.get_recent_chat_history(
                limit=self.session_manager.config.no_of_exchanges_to_llm * 2
            )
            messages_to_send = recent_chat_messages
        
        recent_chat_history = self._prepare_messages(messages=messages_to_send)
        ctx = Context(self._agent)
        agent_handler = self._agent.run(
            user_msg=user_message,
            chat_history=recent_chat_history,
            memory=self.memory,
            ctx=ctx,
            max_iterations=self.max_iterations
        )
        
        final_assistant_response = ""
        msg = cl.Message(content="", author="Assistant")
        agent_event_stream = agent_handler.stream_events()
        async for event in agent_event_stream:
            if isinstance(event, ToolCallResult):
                tool_step = cl.Step(
                    name=f"{event.tool_name} tool", 
                    type="tool",
                    show_input="json",
                )
                tool_step.input = str(event.tool_kwargs)
                tool_step.output = str(event.tool_output)
                await tool_step.send()
            if isinstance(event, AgentStream):
                if event.delta:
                    await msg.stream_token(event.delta)
                    final_assistant_response += event.delta
        
        self.session_manager.save_message("user", user_message)
        self.session_manager.save_message("assistant", final_assistant_response)
        
        await msg.send()
        chat_history.append({"role": "user", "content": user_message})
        chat_history.append({"role": "assistant", "content": final_assistant_response})
        cl.user_session.set("chat_history", chat_history)
        is_extraction_enabled = self.session_manager.config.memory_strategies and len(self.session_manager.config.memory_strategies) > 0
        if is_extraction_enabled:
            asyncio.create_task(
                self.session_manager.process_conversation_for_memory()
            )
        return final_assistant_response

    def _prepare_messages(self, messages: List[ExchangeMessage]) -> List[ChatMessage]:
        """Prepare messages with system prompt and memory context."""
        processed_messages = []    
        
        # Add chat history
        for msg in messages:
            role = MessageRole.USER if msg.role == "user" else MessageRole.ASSISTANT
            processed_messages.append(ChatMessage(role=role, content=msg.content))
        return processed_messages
    
    def _get_llm(self):
        model_config = config_settings.PROVIDER_MODELS.get(self.session_manager.config.model)
        provider = model_config["provider"]
        max_tokens = model_config.get("max_tokens", 16384)
        llm_creators = {
            "Anthropic": Anthropic(
                model=self.session_manager.config.model,
                api_key=self.session_manager.config.anthropic_api_key,
                max_tokens=max_tokens,
            ),
            "OpenAI": OpenAI(
                model=self.session_manager.config.model,
                api_key=self.session_manager.config.openai_api_key,
                max_tokens=max_tokens,
                context_window=0
            ),
        }
        return llm_creators.get(provider)
    
    def is_openai_model(self) -> bool:
        """Check if the LLM is OpenAI."""
        model_config = config_settings.PROVIDER_MODELS.get(self.session_manager.config.model)
        provider = model_config["provider"]
        return provider == "OpenAI"