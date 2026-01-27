"""
AgentCore Memory Session Manager.
"""
import asyncio
import chainlit as cl
from typing import List, Dict, Optional
from .memory_config import AgentCoreMemoryConfig
from src.storage.repository import Repository
from src.storage.models import ExchangeMessage
from src.strategies.base import MemoryStrategy
from src.strategies.summary import SummaryMemoryStrategy
from src.strategies.user_preference import UserPreferenceMemoryStrategy
from src.strategies.semantic import SemanticMemoryStrategy
from src.storage.enums import MemoryStrategyEnums
from llama_index.embeddings.openai import OpenAIEmbedding


class AgentCoreMemorySessionManager:
    """Manages memory sessions for AgentCore."""
    
    def __init__(
        self,
        agent_core_memory_config: AgentCoreMemoryConfig,
    ):
        """
        Initialize session manager.
        
        Args:
            agentcore_memory_config: Memory configuration
            strategies: List of strategy IDs to use (default: all)
        """
        self.config = agent_core_memory_config
        self.repository = Repository()
        
        # Initialize strategies
        self.strategies: Dict[str, MemoryStrategy] = {}
        strategy_ids = self.config.memory_strategies
        
        for strategy_id in strategy_ids:
            if strategy_id == MemoryStrategyEnums.SUMMARY.value:
                self.strategies[strategy_id] = SummaryMemoryStrategy(config=agent_core_memory_config)
            elif strategy_id == MemoryStrategyEnums.USER_PREFERENCE.value:
                self.strategies[strategy_id] = UserPreferenceMemoryStrategy(config=agent_core_memory_config)
            elif strategy_id == MemoryStrategyEnums.SEMANTIC.value:
                self.strategies[strategy_id] = SemanticMemoryStrategy(config=agent_core_memory_config)
        
    
    def get_chat_history(
        self, 
        is_summarized: Optional[bool] = None, 
        limit: Optional[int] = None
    ) -> List[ExchangeMessage]:
        """
        Retrieve chat history from database.
        
        Args:
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of message dictionaries
        """
        return self.repository.get_thread_messages(
            thread_id=self.config.thread_id,
            is_summarized=is_summarized,
            limit=limit
        )
    
    def format_messages_for_llm(self, messages: List[ExchangeMessage]) -> List[Dict[str, str]]:
        """
        Format messages for LLM consumption.
        
        Args:
            messages: List of ExchangeMessage objects
        Returns:
            List of formatted message dictionaries
        """ 
        return [
            {"role": msg.role, "content": msg.content, "created_at": msg.created_at.isoformat()}
            for msg in messages
        ]
    
    def get_exchange_message_ids(self, messages: List[ExchangeMessage]) -> List[int]:
        """
        Get list of message IDs from ExchangeMessage objects.
        
        Args:
            messages: List of ExchangeMessage objects
        Returns:
            List of message IDs
        """
        return [msg.id for msg in messages]
    
    def get_recent_chat_history(self, limit: Optional[int] = None):
        """
        Retrieve chat history from database.
        
        Args:
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of message dictionaries
        """
        return self.repository.get_recent_thread_messages(
            thread_id=self.config.thread_id,
            limit=limit
        )
            
    def save_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Save a message to the database.
        
        Args:
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
        """
        self.repository.save_message(
            thread_id=self.config.thread_id,
            role=role,
            content=content,
            metadata=metadata
        )
    
    async def retrieve_memory_context(self, query: str, thread_id: Optional[str] = None) -> str:
        """
        Retrieve relevant memories and format for LLM context.
        
        Args:
            query: Query for semantic search (required)
            thread_id: Optional thread_id to retrieve memories from.
                    If provided: retrieves memories from that specific thread (current conversation)
                    If None: searches across ALL conversations (omits thread_id filter)
            
        Returns:
            Formatted memory context string
        """
        all_memories = []
        retrieval_tasks = [
            self.retrieve_and_format_memories(
                strategy_id=strategy_id, 
                strategy=strategy,
                query=query,
                thread_id=thread_id
            )
            for strategy_id, strategy in self.strategies.items()
        ]
        
        results = await asyncio.gather(*retrieval_tasks)
        
        all_memories = [result for result in results if result is not None]
        
        if not all_memories:
            print("No relevant memories found.")
            return ""
        print("Relevant memories retrieved for context.")
        return "\n\n".join([
            "## RELEVANT MEMORIES",
            "The following information has been remembered from previous conversations:",
            "",
            *all_memories
        ])
    
    async def retrieve_and_format_memories(
        self, 
        strategy_id: str, 
        strategy: MemoryStrategy,
        query: str,
        thread_id: Optional[str] = None
    ):
        """Retrieve memories for a strategy and format them."""
        memories = await strategy.retrieve_memories(
            user_id=self.config.user_id,
            thread_id=thread_id,
            query=query,
            limit=self.config.max_memories
        )
        if memories:
            formatted = strategy.format_memories_for_context(memories)
            if formatted:
                return f"### {strategy_id.upper()} MEMORIES\n{formatted}"
        return None
        
    async def process_conversation_for_memory(
        self,
        is_process_next_messages: bool = False,
    ):
        """
        Process conversation and store memories (runs in background).
        
        Args:
            chat_history: Full chat history
            latest_message: Latest user message
            latest_response: Latest assistant response
        """
        unsummarized_chat_history = self.get_chat_history(is_summarized=False)
        messages_to_process = self.get_messages_for_llm_processing(
            chat_history=unsummarized_chat_history, 
            is_process_next_messages=is_process_next_messages
        )
        exchange_message_ids = self.get_exchange_message_ids(messages_to_process)
        formatted_messages = self.format_messages_for_llm(messages_to_process)
        if len(formatted_messages) == 0:
            return
        try:
            strategy_extraction_tasks = [
                self.process_and_save_memory(
                    strategy_id=strategy_id, 
                    strategy=strategy, 
                    formatted_messages=formatted_messages
                )
                for strategy_id, strategy in self.strategies.items()
            ]
            
            await asyncio.gather(*strategy_extraction_tasks)
            
            self.repository.mark_messages_as_summarized(
                message_ids=exchange_message_ids
            )
        except Exception as e:
            print(f"Error processing memories: {e}")
    
    async def process_and_save_memory(
        self, 
        strategy_id: str, 
        strategy: MemoryStrategy, 
        formatted_messages: List[Dict[str, str]]
    ):
        """Process conversation for a strategy and save its memories."""
        # Extract memories using strategy
        memories = await strategy.process_conversation(
            user_id=self.config.user_id,
            thread_id=self.config.thread_id,
            model=self.config.summarization_model,
            chat_history=formatted_messages,
        )
        all_memories = ''
        # Store memories
        for memory in memories:
            all_memories += f"{memory['content']}\n"
            self.repository.save_memory(
                user_id=self.config.user_id,
                thread_id=self.config.thread_id,
                strategy=strategy_id,
                memory_id=memory.get("memory_id"),
                action=memory.get("action"),
                content=memory["content"],
                embedding=memory.get("embedding"),
                metadata=memory.get("metadata", {})
            )
            
        strategy_title = " ".join(word.capitalize() for word in strategy_id.split("_"))
        extraction_step = cl.Step(
            name=f"{strategy_title} strategy", 
            type="tool",
            show_input=True,
        )
        extraction_step.input = f"Input:\nExtracting {strategy_title} memories..."
        extraction_step.output = f"Output:\n{strategy_id.capitalize()} memories saved.\n{all_memories}"
        await extraction_step.send()
                
    def get_messages_for_llm_processing(
        self, 
        chat_history: List[ExchangeMessage],
        is_process_next_messages: bool = False
    ) -> list | None:
        pair_messages = self._insert_missing_assistant_message(chat_history)
        chat_length = len(pair_messages)
        no_of_messages_to_process = self.config.no_of_exchanges_to_llm
        
        if is_process_next_messages:
            end = chat_length
            start = 0
            messages_to_process = pair_messages[start:end]
            filtered_messages = self._filter_none_messages(messages_to_process)
            return filtered_messages
        
        if chat_length % no_of_messages_to_process != 0:
            return []
        
        if (chat_length <= no_of_messages_to_process):
            return []
        
        end = chat_length - no_of_messages_to_process
        start = 0
        messages_to_process = pair_messages[start:end]
        filtered_messages = self._filter_none_messages(messages_to_process)
        return filtered_messages

    def _filter_none_messages(self, messages: List[ExchangeMessage]):
        """Filter out None messages from the list.

        Args:
            messages (list): List of message dictionaries with "role" and "content".

        Returns:
            list: List of messages with None filtered out.
        """
        return [msg for msg in messages if msg is not None]

    def _insert_missing_assistant_message(self, messages: List[ExchangeMessage]):
        """Insert None in place of missing assistant messages after user messages.

        Args:
            messages (list): List of message dictionaries with "role" and "content".

        Returns:
            list: List of messages with None inserted for missing assistant messages.
        """
        result = []

        for i, msg in enumerate(messages):
            result.append(msg)

            if msg.role == "user":
                next_msg = messages[i + 1] if i + 1 < len(messages) else None

                if not next_msg or next_msg.role != "assistant":
                    result.append(None)

        return result