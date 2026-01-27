"""
Semantic memory strategy for factual knowledge extraction.
"""

from typing import List, Dict, Any, Optional
from llama_index.llms.openai import OpenAI
from llama_index.llms.anthropic import Anthropic
from llama_index.core.llms import ChatMessage
from pydantic import BaseModel, Field

from .base import MemoryStrategy
from src.storage.repository import Repository
from src.storage.enums import MemoryActionType, MemoryStrategyEnums
from src.config.settings import settings
from src.storage.models import ThreadMemory
from src.prompts.semantic import SEMANTIC_SYSTEM_PROMPT
from src.core.memory_config import AgentCoreMemoryConfig


class SemanticAction(BaseModel):
    action: MemoryActionType = Field(
        description="Action to perform on memory: add a new semantic memory or update an existing one"
    )

    target_semantic_id: Optional[str] = Field(
        default=None, description="Required if action is 'update'; omitted for 'add'"
    )

    title: str = Field(
        description="Title or brief description of the semantic fact"
    )
    
    memory_type: str = Field(
        description="Type of semantic memory (fact, definition, explanation, procedure, example, comparison, reference)"
    )

    description: str = Field(
        description="This is a standalone personal fact about the user, stated in a simple sentence.\\nIt should represent a piece of personal information, such as life events, personal experience, and preferences related to the user.\\nMake sure you include relevant details such as specific numbers, locations, or dates, if presented.\\nMinimize the coreference across the facts, e.g., replace pronouns with actual entities."
    )

    description_word_count: int = Field(
        description="Word count of the description"
    )


class SemanticUpdateResult(BaseModel):
    memories: List[SemanticAction] = Field(
        description="List of semantic memory add/update actions"
    )


class SemanticMemoryStrategy(MemoryStrategy):
    """Strategy that maintains factual semantic knowledge."""

    def __init__(
        self, strategy_id: MemoryStrategyEnums = MemoryStrategyEnums.SEMANTIC, config: Optional[AgentCoreMemoryConfig] = None
    ):
        super().__init__(strategy_id, config)
        self.repository = Repository()

    def _initialize_llm(self, model: str):
        """Initialize LLM for semantic extraction."""
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
        """Process conversation and extract semantic knowledge."""
        memories = []
        self.llm = self._initialize_llm(model)
        
        # Check if we have messages to process
        message_count = len(chat_history)
        if message_count < 1:
            return memories
        
        # Retrieve existing semantic memories
        semantic_memories = await self.retrieve_memories(
            user_id=user_id, limit=5
        )
        
        # Generate semantic actions
        semantic_actions = await self._extract_semantic_knowledge(
            semantic_memories=semantic_memories,
            exchanges=chat_history
        )
        
        if semantic_actions is None or len(semantic_actions) == 0:
            return memories
        
        # Process each semantic action
        for action in semantic_actions:
            content = f"Title: {action.title}\nType: {action.memory_type}\nDescription: {action.description}\n"
            embedding = await self.generate_embedding(text=content)
            
            memory_dict = {
                "memory_id": action.target_semantic_id or None,
                "action": action.action,
                "content": content,
                "embedding": embedding,
                "metadata": {
                    "memory_type": action.memory_type,
                    "title": action.title,
                    "description": action.description,
                    "description_word_count": action.description_word_count,
                },
            }
            memories.append(memory_dict)
        
        return memories

    async def _extract_semantic_knowledge(
        self, exchanges: List[Dict[str, str]], semantic_memories: List[ThreadMemory] = []
    ) -> Optional[List[SemanticAction]]:
        """Extract semantic knowledge from conversation exchanges."""
        conversation_text = ",\n".join(
            f"""{{
                "role": "{msg['role'].upper()}",
                "content": "{msg['content']}",
                "created_at": "{msg['created_at']}"
            }}"""
            for msg in exchanges
        )

        existing_semantic_memories = (
            ",\n".join(
                f"""{{
                    "semantic_id": "{memory.id}",
                    "title": "{memory.thread_memory_metadata.get('title', '')}",
                    "memory_type": "{memory.thread_memory_metadata.get('memory_type', '')}",
                    "description": "{memory.thread_memory_metadata.get('description', '')}",
                    "created_at": "{memory.createdAt.isoformat()}",
                    "updated_at": "{memory.updatedAt.isoformat()}"
                }}""" 
                for memory in semantic_memories
            )
            if semantic_memories else "None"
        )

        prompt = SEMANTIC_SYSTEM_PROMPT.format(
            conversation_text=conversation_text, 
            existing_semantic_memories=existing_semantic_memories,
            MemoryActionType=MemoryActionType
        )
        
        try:
            sllm = self.llm.as_structured_llm(output_cls=SemanticUpdateResult)
            input_msg = ChatMessage.from_str(prompt)
            response = await sllm.achat([input_msg])
            semantic_actions: List[SemanticAction] = [
                SemanticAction.model_validate(s)
                for s in getattr(response.raw, "memories", [])
            ]
            return semantic_actions
        except Exception as e:
            print(f"Error extracting semantic knowledge: {e}")
            return []

    async def retrieve_memories(
        self, user_id: str, thread_id: Optional[str] = None, query: Optional[str] = None, limit: int = 10
    ):
        """Retrieve semantic memories."""   
        query_embedding = None
        if query:
            query_embedding = await self.generate_embedding(text=query)     
        return self.repository.get_memories(
            user_id=user_id,
            thread_id=thread_id,
            strategy_id=self.strategy_id,
            limit=limit,
            query_embedding=query_embedding,
            similarity_threshold=self.config.semantic_score,
        )

    def format_memories_for_context(self, memories) -> str:
        """Format semantic memories for LLM context."""
        if not memories:
            return ""
        
        context_parts = []
        context_parts.append("## Semantic Knowledge Base")
        
        # Group by memory type
        for i, item in enumerate(memories, 1):
            # Handle both tuple (memory, score) and memory object
            if isinstance(item, tuple):
                memory, score = item
                context_parts.append(f"### Semantic Memory {i} [Score: {score:.4f}]. {memory.content}")
            else:
                memory = item
                context_parts.append(f"### Semantic Memory {i}. {memory.content}")
        
        return "\n".join(context_parts)
