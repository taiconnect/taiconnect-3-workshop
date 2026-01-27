import os, asyncio
import chainlit as cl

from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

from sqlalchemy import create_engine

from chainlit.types import ThreadDict
from chainlit.input_widget import Select, Switch, MultiSelect, Slider

from llama_index.core import Settings
from llama_index.core.tools import FunctionTool
from llama_index.core.tools import FunctionTool

from src.config.settings import settings as config_settings
from src.storage.models import MemoryStrategyEnums
from src.core.memory_config import AgentCoreMemoryConfig
from src.core.session_manager import AgentCoreMemorySessionManager
from src.core.agent import Agent
from src.tools import create_memory_tool
from src.prompts.agent import AGENT_SYSTEM_PROMPT
from src.prompts.memory_retrieval import MEMORY_SYSTEM_PROMPT

load_dotenv()

POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
engine = create_engine(f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
@cl.on_message
async def on_message(message: cl.Message):
    cl_settings = cl.user_session.get("settings")
    username = cl.user_session.get("username")
    thread_id = cl.user_session.get("thread_id")
    user_id = cl.user_session.get("user_id")
    current_time = datetime.now().isoformat()
    
    agent_core_memory_config = get_agent_memory_config()
    agent_core_session_manager = AgentCoreMemorySessionManager(
        agent_core_memory_config=agent_core_memory_config
    )
    retrieve_memory_context_tool = FunctionTool.from_defaults(
        name="retrieve_memory_context",
        description="Retrieve relevant memories from the conversation history to provide context for the current conversation.",
        fn=create_memory_tool(agent_core_session_manager)
    )
    
    # Build_system_prompt - base prompt always included
    system_prompt = AGENT_SYSTEM_PROMPT.format(
        username=username,
        user_id=user_id,
        thread_id=thread_id,
        current_time=current_time
    )
    
    # Add memory retrieval prompt only if memory strategies are enabled
    tools = []
    is_strategy_enabled = len(cl_settings["memory_strategies"]) > 0
    if is_strategy_enabled:
        memory_retrieval_system_prompt = MEMORY_SYSTEM_PROMPT.format(thread_id=thread_id)
        system_prompt += "\n\n" + memory_retrieval_system_prompt
        tools.append(retrieve_memory_context_tool)
    
    agent = Agent(
        system_prompt=system_prompt, 
        session_manager=agent_core_session_manager, 
        tools=tools,
        max_iterations=5,
        streaming=True,
        verbose=True,
    ) 
    await agent.invoke(message.content)

@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    chat_history = build_chat_history(thread)
    await set_chat_settings(chat_history=chat_history, thread_id=thread.get("id"))

@cl.on_chat_end
async def end():
    cl_settings = cl.user_session.get("settings")
    if not cl_settings or cl.user_session.get("thread_id") is None or len(cl_settings["memory_strategies"]) == 0:
        return
    agent_core_memory_config = get_agent_memory_config()
    session_manager = AgentCoreMemorySessionManager(
        agent_core_memory_config=agent_core_memory_config
    )
    asyncio.create_task(
        session_manager.process_conversation_for_memory(
            is_process_next_messages=True
        )
    )

@cl.on_chat_start
async def start():
    await set_chat_settings(thread_id=cl.context.session.thread_id)

def get_agent_memory_config():
    cl_settings = cl.user_session.get("settings")
    no_exchanges_to_llm = cl_settings["no_exchanges_to_llm"] if cl_settings["no_exchanges_to_llm"] == 'All' else int(cl_settings["no_exchanges_to_llm"])
    user_env = cl.user_session.get("env")
    return AgentCoreMemoryConfig(
        memory_strategies=cl_settings["memory_strategies"], 
        thread_id=cl.user_session.get("thread_id"), 
        user_id=cl.user_session.get("user_id") ,
        no_of_exchanges_to_llm=no_exchanges_to_llm, 
        model=cl_settings["model"],
        summarization_model=cl_settings["summarization_model"],
        embedding_model=config_settings.DEFAULT_EMBEDDING_MODEL,
        openai_api_key=user_env['OPENAI_API_KEY'],
        anthropic_api_key=user_env['ANTHROPIC_API_KEY'],
        summary_score=cl_settings["summary_score"],
        semantic_score=cl_settings["semantic_score"],
        user_preference_score=cl_settings["user_preference_score"],
    )

async def set_chat_settings(chat_history: Optional[list] = None, thread_id: Optional[str] = None):
    cl_settings = await cl.ChatSettings(
        [
            Select(
                id="model",
                label="Models",
                items=config_settings.PROVIDER_MODELS_KEYS,
                initial_value=config_settings.DEFAULT_LLM_MODEL,
            ),
            Select(
                id="summarization_model",
                label="Summarization Models",
                items=config_settings.PROVIDER_MODELS_KEYS,
                initial_value=config_settings.DEFAULT_SUMMARIZATION_MODEL,
            ),
            Select(
                id="no_exchanges_to_llm",
                label="Number of Exchanges to LLM",
                values=config_settings.EXCHANGE_OPTIONS,
                initial_value=config_settings.DEFAULT_NO_EXCHANGES_TO_LLM,
            ),
            MultiSelect(
                id="memory_strategies",
                label="Memory Strategies to Enable",
                values=[
                    MemoryStrategyEnums.SUMMARY.value,
                    MemoryStrategyEnums.SEMANTIC.value,
                    MemoryStrategyEnums.USER_PREFERENCE.value
                ],
                initial=[
                    MemoryStrategyEnums.SUMMARY.value,
                    MemoryStrategyEnums.SEMANTIC.value,
                    MemoryStrategyEnums.USER_PREFERENCE.value
                ],
            ),
            Slider(
                id="summary_score",
                label="Summary Score",
                initial=config_settings.DEFAULT_SUMMARY_SCORE,
                min=0,
                max=1,
                step=0.01,
            ),
            Slider(
                id="semantic_score",
                label="Semantic Score",
                initial=config_settings.DEFAULT_SEMANTIC_SCORE,
                min=0,
                max=1,
                step=0.01,
            ),
            Slider(
                id="user_preference_score",
                label="User Preference Score",
                initial=config_settings.DEFAULT_USER_PREFERENCE_SCORE,
                min=0,
                max=1,
                step=0.01,
            ),
        ]
    ).send()
    cl.user_session.set("settings", cl_settings)
    cl.user_session.set("user_id", cl.context.session.user.id)
    cl.user_session.set("username", cl.context.session.user.identifier)
    if thread_id:
        cl.user_session.set("thread_id", thread_id)
    if chat_history is not None:
        cl.user_session.set("chat_history", chat_history)
    
def get_engine():
    """
    Establish SQLAlchemy-based data layer for persisting chat history into PostgreSQL.
    """
    conninfo = config_settings.DATABASE_URL
    engine = create_engine(conninfo)
    return engine


@cl.password_auth_callback
async def auth_callback(username: str, password: str):
    """
    Simple authentication that accepts any username/password.
    This enables thread persistence.
    """
    # Accept any credentials for demo purposes
    return cl.User(identifier=username, metadata={"name": username})


@cl.on_settings_update
async def setup_agent(cl_settings):
    cl.user_session.set("settings", cl_settings)

def build_chat_history(thread: ThreadDict):
    chat_history = []
    for message in thread["steps"]:
        if message["type"] == "user_message":
            chat_history.append({"role": "user", "content": message["output"]})
        elif message["type"] == "assistant_message":
            chat_history.append({"role": "assistant", "content": message["output"]})
    return chat_history
