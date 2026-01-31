"""
Base memory strategy interface.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from llama_index.embeddings.openai import OpenAIEmbedding
from google.genai.types import EmbedContentConfig
from google import genai
from src.core.memory_config import AgentCoreMemoryConfig
from src.storage.models import ThreadMemory
from src.config.settings import settings as config_settings

class MemoryStrategy(ABC):
    """Base class for memory strategies."""
    
    def __init__(self, strategy_id: str, config: Optional[AgentCoreMemoryConfig] = None):
        self.strategy_id = strategy_id
        self.config = config or {}
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for given text.
        
        Args:
            text: Text string
        Returns:
            List of embedding vectors
        """
        model_config = config_settings.EMBEDDING_MODELS.get(self.config.embedding_model)
        if model_config["provider"] == "OpenAI":
            embedding = OpenAIEmbedding(model=self.config.embedding_model, api_key=self.config.openai_api_key).get_text_embedding(text)
            return embedding
        elif model_config["provider"] == "Google": 
            client = genai.Client(api_key=self.config.gemini_api_key)
            result = client.models.embed_content(
                        model=self.config.embedding_model,
                        contents=text,
                        config=EmbedContentConfig(
                            output_dimensionality=3072,
                        ),
                    )
            embedding = result.embeddings[0].values
            return embedding
    
    @abstractmethod
    async def process_conversation(
        self,
        user_id: str,
        thread_id: str,
        chat_history: List[Dict[str, str]],
        model: str,
    ) -> List[Dict[str, Any]]:
        """
        Process conversation and extract memories.
        
        Args:
            user_id: User identifier
            thread_id: Thread identifier
            chat_history: Full chat history
            
        Returns:
            List of memory dictionaries to be stored
        """
        pass
    
    @abstractmethod
    async def retrieve_memories(
        self,
        user_id: str,
        thread_id: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 10
    ) -> List[ThreadMemory]:
        """
        Retrieve relevant memories.
        
        Args:
            user_id: User identifier
            thread_id: Optional Thread identifier
            query: Optional[str] = None,
            limit: Maximum number of memories to retrieve
            
        Returns:
            List of relevant memories
        """
        pass
    
    @abstractmethod
    def format_memories_for_context(self, memories: List[ThreadMemory]) -> str:
        """
        Format memories for inclusion in LLM context.
        
        Args:
            memories: List of memory dictionaries
            
        Returns:
            Formatted string for LLM context
        """
        pass