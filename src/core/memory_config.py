"""
AgentCore Memory Configuration.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class AgentCoreMemoryConfig(BaseModel):
    """Configuration for AgentCore Memory system."""
    
    memory_strategies: Optional[List[str]] = Field(..., description="Memory strategy identifier")
    thread_id: str = Field(..., description="Thread/conversation identifier")
    user_id: str = Field(..., description="User identifier")
    token_limit: int = Field(default=8000, description="Token limit for memory context")
    max_memories: int = Field(default=5, description="Maximum number of memories to retrieve")
    no_of_exchanges_to_llm: int | str = Field(default=2, description="Number of recent exchanges to consider for LLM context")
    model: str = Field(..., description="Model name for LLM interactions")
    summarization_model: str = Field(..., description="Model name for summarization tasks")
    embedding_model: str = Field(..., description="Model name for embedding generation")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API Key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API Key")
    summary_score: float = Field(default=0.3, description="Threshold score for summary relevance")
    semantic_score: float = Field(default=0.2, description="Threshold score for semantic relevance")
    user_preference_score: float = Field(default=0.1, description="Threshold score for user preference relevance")
    
    class Config:
        frozen = True