"""
User preference-based memory strategy.
"""

from typing import List, Dict, Any, Optional
from llama_index.llms.openai import OpenAI
from llama_index.llms.anthropic import Anthropic
from llama_index.core.llms import ChatMessage
from pydantic import BaseModel, Field

from src.strategies.base import MemoryStrategy
from src.storage.repository import Repository
from src.storage.enums import MemoryActionType, MemoryStrategyEnums
from src.config.settings import settings
from src.storage.models import ThreadMemory
from src.prompts.user_preference import USER_PREFERENCE_SYSTEM_PROMPT
from src.core.memory_config import AgentCoreMemoryConfig


class PreferenceAction(BaseModel):
    action: MemoryActionType = Field(
        description="Action to perform on memory: add a new preference or update an existing one or skip if it's not relevant"
    )

    target_preference_id: Optional[str] = Field(
        default=None, description="Required if action is 'update'; omitted for 'add'"
    )

    context: str = Field(
        description="The background and reason why this preference is extracted"
    )

    preference: str = Field(
        description="The specific preference information"
    )

    categories: List[str] = Field(
        default_factory=list,
        description="A list of categories this preference belongs to (include topic categories like \"food\", \"entertainment\", \"travel\", etc.)"
    )


class PreferenceUpdateResult(BaseModel):
    preferences: List[PreferenceAction] = Field(
        description="List of preference add/update actions"
    )


class UserPreferenceMemoryStrategy(MemoryStrategy):
    """Strategy that maintains user preferences and characteristics."""

    def __init__(
        self, strategy_id: MemoryStrategyEnums = MemoryStrategyEnums.USER_PREFERENCE, config: Optional[AgentCoreMemoryConfig] = None
    ):
        super().__init__(strategy_id, config)
        self.repository = Repository()

    def _initialize_llm(self, model: str):
        """Initialize LLM for preference extraction."""
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
        """Process conversation and extract user preferences."""
        memories = []
        self.llm = self._initialize_llm(model)
        
        # Check if we have messages to process
        message_count = len(chat_history)
        if message_count < 1:
            return memories
        
        # Retrieve existing preferences
        preference_memories = await self.retrieve_memories(
            user_id=user_id, limit=5
        )
        
        # Generate preference actions
        preference_actions = await self._extract_preferences(
            preference_memories=preference_memories,
            exchanges=chat_history
        )
        
        if preference_actions is None or len(preference_actions) == 0:
            return memories
        
        # Process each preference action
        for action in preference_actions:
            content = f'Preference: {action.preference}\nContext: {action.context}\nCategories: {", ".join(action.categories)}'
            embedding = await self.generate_embedding(text=content)
            
            memory_dict = {
                "memory_id": action.target_preference_id or None,
                "action": action.action,
                "content": content,
                "embedding": embedding,
                "metadata": {
                    "context": action.context,
                    "preference": action.preference,
                    "categories": action.categories,
                },
            }
            memories.append(memory_dict)
        
        return memories

    async def _extract_preferences(
        self, exchanges: List[Dict[str, str]], preference_memories: List[ThreadMemory] = []
    ) -> Optional[List[PreferenceAction]]:
        """Extract user preferences from conversation exchanges."""
        conversation_text = ",\n".join(
            f"""{{
                "role": "{msg['role'].upper()}",
                "content": "{msg['content']}",
                "created_at": "{msg['created_at']}"
            }}"""
            for msg in exchanges
        )
        existing_preferences = (
            ",\n".join(
                f"""{{
                    "preference_id": "{chunk.id}",
                    "preference": "{chunk.thread_memory_metadata.get('preference', '')}",
                    "context": "{chunk.thread_memory_metadata.get('context', '')}",
                    "categories": "{chunk.thread_memory_metadata.get('categories', [])}",
                    "created_at": "{chunk.createdAt.isoformat()}",
                    "updated_at": "{chunk.updatedAt.isoformat()}"
                }}""" 
                for chunk in preference_memories
            )
            if preference_memories else "None"
        )
        prompt = USER_PREFERENCE_SYSTEM_PROMPT.format(
            conversation_text=conversation_text, 
            existing_preferences=existing_preferences,
            MemoryActionType=MemoryActionType
        )
        try:
            sllm = self.llm.as_structured_llm(output_cls=PreferenceUpdateResult)
            input_msg = ChatMessage.from_str(prompt)
            response = await sllm.achat([input_msg])
            preference_actions: List[PreferenceAction] = [
                PreferenceAction.model_validate(p)
                for p in getattr(response.raw, "preferences", [])
            ]
            return preference_actions
        except Exception as e:
            print(f"Error extracting preferences: {e}")
            return []

    async def retrieve_memories(
        self, user_id: str, thread_id: Optional[str] = None, query: Optional[str] = None, limit: int = 10
    ):
        """Retrieve user preferences."""
        query_embedding = None
        if query:
            query_embedding = await self.generate_embedding(text=query)
        return self.repository.get_memories(
            user_id=user_id,
            thread_id=thread_id,
            strategy_id=self.strategy_id,
            limit=limit,
            query_embedding=query_embedding,
            similarity_threshold=self.config.user_preference_score,
        )

    def format_memories_for_context(self, memories) -> str:
        """Format preferences for LLM context."""
        if not memories:
            return ""
        
        context_parts = []
        context_parts.append("## User Preferences")
        
        for i, item in enumerate(memories, 1):
            # Handle both tuple (memory, score) and memory object
            if isinstance(item, tuple):
                memory, score = item
                context_parts.append(f"### Preference {i} [Score: {score:.4f}]. {memory.content}")
            else:
                memory = item
                context_parts.append(f"### Preference {i}. {memory.content}")
        
        return "\n".join(context_parts)
