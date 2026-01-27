"""
Summary-based memory strategy.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from llama_index.llms.openai import OpenAI
from llama_index.llms.anthropic import Anthropic
from llama_index.core.llms import ChatMessage

from src.strategies.base import MemoryStrategy
from src.storage.repository import Repository
from src.storage.enums import MemoryActionType, MemoryStrategyEnums
from src.config.settings import settings
from src.storage.models import ThreadMemory
from src.prompts.summary import SUMMARY_SYSTEM_PROMPT
from src.core.memory_config import AgentCoreMemoryConfig


class MemoryAction(BaseModel):
    action: MemoryActionType = Field(
        description="Action to perform on memory: add a new chunk or update an existing one"
    )

    target_chunk_id: Optional[str] = Field(
        default=None, description="Required if action is 'update'; omitted for 'add'"
    )

    topic_name: str = Field(description="Name of the topic for the memory chunk")

    global_summary: str = Field(
        description="Concise global summary for the memory chunk"
    )

    detailed_summary: str = Field(
        description="Detailed delta summary for the memory chunk in XML format"
    )

    global_summary_word_count: int = Field(
        description="Word count of the global summary"
    )

    detailed_summary_word_count: int = Field(
        description="Word count of the detailed summary"
    )


class MemoryUpdateResult(BaseModel):
    memories: List[MemoryAction] = Field(
        description="List of memory add/update actions"
    )


class SummaryMemoryStrategy(MemoryStrategy):
    """Strategy that maintains conversation summaries."""

    def __init__(
        self, strategy_id: MemoryStrategyEnums = MemoryStrategyEnums.SUMMARY, config: Optional[AgentCoreMemoryConfig] = None
    ):
        super().__init__(strategy_id, config)
        self.repository = Repository()

    def _initialize_llm(self, model: str):
        """Initialize LLM for summarization."""
        provider = settings.PROVIDER_MODELS.get(model, {}).get("provider", "OpenAI")
        max_tokens = settings.PROVIDER_MODELS.get(model, {}).get("max_tokens", 16384)
        if provider == "Anthropic":
            return Anthropic(model=model, api_key=self.config.anthropic_api_key, max_tokens=max_tokens)
        else:
            return OpenAI(model=model, api_key=self.config.openai_api_key, max_tokens=max_tokens)
    async def process_conversation(
        self,
        user_id: str,
        thread_id: str,
        chat_history: List[Dict[str, str]],
        model: str,
    ) -> List[Dict[str, Any]]:
        """Process conversation and create summaries."""
        new_summary_memories = []
        self.llm = self._initialize_llm(model)
        # Check if we should create a summary
        message_count = len(chat_history)
        if message_count < 1:
            return new_summary_memories
        existing_summary_memories = await self.retrieve_memories(
            user_id=user_id, thread_id=thread_id, limit=50
        )
        summary_memory_actions = await self._generate_summary(
            summary_memories=existing_summary_memories,
            exchanges=chat_history
        )
        if summary_memory_actions is None or len(summary_memory_actions) == 0:
            return new_summary_memories
        for action in summary_memory_actions:
            content = f"Topic: {action.topic_name}\nGlobal Summary: {action.global_summary}\nDetailed Summary: {action.detailed_summary}"
            summary_embedding = await self.generate_embedding(text=content)
            memory_dict = {
                "memory_id": action.target_chunk_id or None,
                "action": action.action,
                "content": content,
                "embedding": summary_embedding,
                "metadata": {
                    "topic_name": action.topic_name,
                    "global_summary": action.global_summary,
                    "detailed_summary": action.detailed_summary,
                    "global_summary_word_count": action.global_summary_word_count,
                    "detailed_summary_word_count": action.detailed_summary_word_count,
                },
            }
            new_summary_memories.append(memory_dict)
        return new_summary_memories

    async def _generate_summary(
        self, exchanges: List[Dict[str, str]], summary_memories: List[ThreadMemory] = []
    ) -> Optional[List[MemoryAction]]:
        """Generate summary of conversation exchanges."""
        conversation_text = ",\n".join(
            f"""{{
                "role": "{msg['role'].upper()}",
                "content": "{msg['content']}",
                "created_at": "{msg['created_at']}"
            }}"""
            for msg in exchanges
        )

        existing_chunks = (
            ",\n".join(
                f"""{{
                    "chunk_id": "{chunk.id}",
                    "topic_name": "{chunk.thread_memory_metadata['topic_name']}",
                    "global_summary": "{chunk.thread_memory_metadata['global_summary']}",
                    "detailed_summary": "{chunk.thread_memory_metadata['detailed_summary']}",
                    "created_at": "{chunk.createdAt.isoformat()}",
                    "updated_at": "{chunk.updatedAt.isoformat()}"
                }}""" 
                for chunk in summary_memories
            )
            if summary_memories else "None"
        )

        prompt = SUMMARY_SYSTEM_PROMPT.format(
            conversation_text=conversation_text, 
            existing_chunks=existing_chunks,
            MemoryActionType=MemoryActionType
        )
        try:
            input_msg = ChatMessage.from_str(prompt)
            sllm = self.llm.as_structured_llm(output_cls=MemoryUpdateResult)
            extracted_summary_memory = await sllm.achat([input_msg])
            memory_actions: List[MemoryAction] = [
                MemoryAction.model_validate(m)
                for m in getattr(extracted_summary_memory.raw, "memories", [])
            ]
            return memory_actions
        except Exception as e:
            print(f"Error generating summary: {e}")
            return []

    async def retrieve_memories(
        self, user_id: str, thread_id: Optional[str] = None, query: Optional[str] = None, limit: int = 5
    ):
        """Retrieve summaries and facts."""
        summary_query_embedding = None
        if query:
            summary_query_embedding = await self.generate_embedding(text=query)
        return self.repository.get_memories(
            user_id=user_id,
            thread_id=thread_id,
            strategy_id=self.strategy_id,
            limit=limit,
            query_embedding=summary_query_embedding,
            similarity_threshold=self.config.summary_score,
        )

    def format_memories_for_context(self, memories) -> str:
        """Format memories for LLM context."""
        if not memories:
            return ""
        summary_context_parts = []

        summary_context_parts.append("## Conversation Summaries")
        for i, item in enumerate(memories, 1):
            # Handle both tuple (memory, score) and memory object
            if isinstance(item, tuple):
                summary, score = item
                summary_context_parts.append(f"### Summary Memory {i} [Score: {score:.4f}]. {summary.content}")
            else:
                summary = item
                summary_context_parts.append(f"### Summary Memory {i}. {summary.content}")

        return "\n".join(summary_context_parts)
