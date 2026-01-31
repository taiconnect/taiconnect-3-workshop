"""
Configuration settings for AgentCore Memory system.
"""
from typing import Dict, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration settings."""
    DATABASE_URL: str = Field(..., description="Database connection URL")
    POSTGRES_DB: str = Field(..., description="PostgreSQL database name")
    POSTGRES_USER: str = Field(..., description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(..., description="PostgreSQL password")
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")

    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    PROVIDER_MODELS: Dict[str, Dict[str, str | int]] = {
        "claude-sonnet-4-5-20250929": {
            "provider": "Anthropic",
            "display": "Anthropic - Sonnet 4.5",
            "max_tokens": 1000,
        },
        "claude-haiku-4-5-20251001": {
            "provider": "Anthropic",
            "display": "Anthropic - Haiku 4.5",
            "max_tokens": 1000,
        },
        "claude-4-sonnet-20250514": {
            "provider": "Anthropic",
            "display": "Anthropic - Claude 4 Sonnet",
            "max_tokens": 1000,
        },
        "gpt-4.1": {
            "provider": "OpenAI", 
            "display": "OpenAI - GPT-4.1", 
            "max_tokens": 1000
        },
        "gpt-4.1-mini": {
            "provider": "OpenAI", 
            "display": "OpenAI - GPT-4.1 Mini", 
            "max_tokens": 1000
        },
        "gpt-4o": {
            "provider": "OpenAI", 
            "display": "OpenAI - GPT-4o", 
            "max_tokens": 1000
        },
        "gpt-4o-mini": {
            "provider": "OpenAI", 
            "display": "OpenAI - GPT-4o Mini", 
            "max_tokens": 1000
        },
    }

    EMBEDDING_MODELS: Dict[str, Dict[str, str | int]] = {
        "text-embedding-3-large": {
            "provider": "OpenAI",
            "display": "OpenAI - Text Embedding 3 Large",
        },  
        "gemini-embedding-001": {
            "provider": "Google",
            "display": "Google - Gemini Embedding 001",
        },
    }
    
    DEFAULT_EMBEDDING_MODEL: str = "gemini-embedding-001"
    DEFAULT_LLM_MODEL: str = "gpt-4.1"
    DEFAULT_SUMMARIZATION_MODEL: str = "gpt-4.1-mini"

    EXCHANGE_OPTIONS: List[str] = ["2", "10", "20", "30", "All"]
    DEFAULT_NO_EXCHANGES_TO_LLM: str = "2"
    DEFAULT_SUMMARY_SCORE: float = 0.001
    DEFAULT_SEMANTIC_SCORE: float = 0.001
    DEFAULT_USER_PREFERENCE_SCORE: float = 0.001

    @property
    def PROVIDER_MODELS_KEYS(self) -> Dict[str, str]:
        return {v["display"]: k for k, v in self.PROVIDER_MODELS.items()}
    
    @property
    def EMBEDDING_MODELS_KEYS(self) -> Dict[str, str]:
        return {v["display"]: k for k, v in self.EMBEDDING_MODELS.items()}

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

settings = Settings()
