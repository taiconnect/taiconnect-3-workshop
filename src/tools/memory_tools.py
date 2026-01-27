"""Memory tools for retrieving context from conversation history."""

from typing import Optional
from src.core.session_manager import AgentCoreMemorySessionManager


class MemoryTools:
    """Tools for interacting with memory system."""
    
    def __init__(self, session_manager: AgentCoreMemorySessionManager):
        """
        Initialize memory tools with session manager.
        
        Args:
            session_manager: The AgentCoreMemorySessionManager instance
        """
        self.session_manager = session_manager
    
    async def retrieve_memory_context_tool(self, query: str, thread_id: Optional[str] = None) -> str:
        """
        Retrieve relevant memory context for LLM reasoning and response generation.

        This tool recalls and synthesizes information from:
        - The current conversation (when thread_id is provided)
        - Previous conversations (when thread_id is None)
        - Stored user preferences
        - User semantic and profile-level information

        It can return both general conversational context and targeted memories
        relevant to a specific query.

        Args:
            query: Query string used to retrieve targeted memories (required).
                Searches for semantically related memories (e.g., past discussions, 
                preferences, facts).
            thread_id: Optional thread_id to specify which conversation to search.
                When provided: searches ONLY the current conversation thread
                When None: searches across ALL conversations and stored memories

        Returns:
            str: A formatted memory context string containing relevant information
                recalled from:
                - Current conversation state (if thread_id provided)
                - Prior conversations (if thread_id is None)
                - User preferences
                - Long-term semantic memory

        Examples:
            - retrieve_memory_context(query="user preferences")  # Search all conversations
            - retrieve_memory_context(query="what we discussed", thread_id="current_thread_id")  # Current conversation only
            - retrieve_memory_context(query="dietary restrictions", thread_id=None)  # Search all

        """
        return await self.session_manager.retrieve_memory_context(query=query, thread_id=thread_id)


def create_memory_tool(session_manager: AgentCoreMemorySessionManager):
    """
    Create a memory retrieval tool function bound to a session manager.
    
    Args:
        session_manager: The AgentCoreMemorySessionManager instance
        
    Returns:
        Async function that can be used as a tool
    """
    memory_tools = MemoryTools(session_manager)
    
    async def _retrieve_memory_context(query: str, thread_id: Optional[str] = None) -> str:
        """
        Retrieve relevant memories and format for LLM context.
        
        Args:
            query: Query string to search for specific memories (required).
            thread_id: Optional thread_id to specify conversation scope.
                   If provided: searches ONLY that conversation thread (current conversation)
                   If None: searches across ALL conversations and memories
        
        Returns:
            str: Formatted memory context containing relevant information
        
        Usage:
            - retrieve_memory_context(query="what we discussed", thread_id="abc123")  # Current conversation only
            - retrieve_memory_context(query="preferences")  # Search all conversations
        """
        return await memory_tools.retrieve_memory_context_tool(query=query, thread_id=thread_id)
    
    return _retrieve_memory_context
