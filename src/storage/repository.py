"""
Repository layer for database operations.
"""
from typing import Optional
from sqlalchemy import create_engine, select, cast
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, ExchangeMessage, ExchangeThread, ThreadMemory
from .enums import MemoryStrategyEnums, MemoryActionType
from src.config.settings import settings


class Repository:
    """Synchronous repository for database operations."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.DATABASE_URL
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
        
    def create_tables(self):
        """Create all tables."""
        Base.metadata.create_all(self.engine)
    
    def get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()
    
    def get_thread_messages(self, thread_id: str, is_summarized: Optional[bool] = None, limit: Optional[int] = None):
        """Retrieve messages for a given thread."""
        with self.get_session() as session:
            query = session.query(ExchangeMessage).filter(ExchangeMessage.thread_id == thread_id).order_by(ExchangeMessage.created_at)
            if is_summarized is not None:
                query = query.filter(ExchangeMessage.is_summarized == is_summarized)
            if limit:
                query = query.limit(limit)
            return query.all()
    
    def get_recent_thread_messages(self, thread_id: str, limit: Optional[int] = None):
        """Retrieve messages for a given thread."""
        with self.get_session() as session:
            stmt = (
                select(ExchangeMessage)
                .where(ExchangeMessage.thread_id == thread_id)
                .order_by(
                    ExchangeMessage.created_at.desc(),
                    ExchangeMessage.id.desc(),
                )
                .limit(limit)
            )

            messages = session.execute(stmt).scalars().all()
            return list(reversed(messages))
    
    def save_message(self, thread_id: str, role: str, content: str, metadata: Optional[dict] = None):
        """Save a message to the database."""
        with self.get_session() as session:
            self.create_or_get_thread(thread_id)
            message = ExchangeMessage(
                thread_id=thread_id,
                role=role,
                content=content,
                metadata=metadata
            )
            session.add(message)
            session.commit()
    
    def get_thread(self, thread_id: str):
        """Get a thread by ID."""
        with self.get_session() as session:
            exchange_thread = session.query(ExchangeThread).filter(ExchangeThread.id == thread_id).first()
            return exchange_thread
        
    def create_or_get_thread(self, thread_id: str):
        """Create or get a thread by ID."""
        with self.get_session() as session:
            exchange_thread = session.query(ExchangeThread).filter(ExchangeThread.id == thread_id).first()
            if not exchange_thread:
                exchange_thread = ExchangeThread(id=thread_id)
                session.add(exchange_thread)
                session.commit()
            return exchange_thread
    
    def save_memory(
        self,
        user_id: str,
        thread_id: str,
        strategy: str,
        action: str,
        content: str,
        memory_id: Optional[int] = None,
        embedding: Optional[list] = None,
        metadata: Optional[dict] = None
    ):
        """Save a memory to the database."""
        with self.get_session() as session:
            namespace = f'/strategies/{strategy}/users/{user_id}'
            if strategy == MemoryStrategyEnums.SUMMARY.value:
                namespace += f'/threads/{thread_id}'
            if action == MemoryActionType.add.value:
                memory = ThreadMemory(
                    userId=user_id,
                    threadId=thread_id,
                    strategy=strategy,
                    namespace=namespace,
                    content=content,
                    embedding=embedding,
                    thread_memory_metadata=metadata
                )
                session.add(memory)
                session.commit()
            elif action == MemoryActionType.update.value and memory_id is not None:
                memory = session.query(ThreadMemory).filter(ThreadMemory.id == memory_id).first()
                if memory:
                    memory.content = content
                    memory.embedding = embedding
                    memory.thread_memory_metadata = metadata
                    session.commit()
    
    def get_memories(
        self,
        user_id: str,
        strategy_id: MemoryStrategyEnums,
        similarity_threshold: float = 0.1,
        query_embedding: Optional[list] = None,
        thread_id: Optional[str] = None,
        limit: Optional[int] = None
    ):
        """Retrieve memories based on criteria."""
        print(f"Retrieving memories for {strategy_id.value} with similarity threshold {similarity_threshold}")
        with self.get_session() as session:
            if query_embedding:
                # Calculate similarity score
                similarity = (1 - ThreadMemory.embedding.cosine_distance(query_embedding)).label('similarity')
                
                # Build query with similarity
                query = (
                    session.query(ThreadMemory, similarity)
                    .filter(
                        cast(ThreadMemory.userId, UUID) == user_id,
                        ThreadMemory.strategy == strategy_id,
                        similarity >= similarity_threshold
                    )
                )
                
                if thread_id and len(thread_id) > 0:
                    query = query.filter(cast(ThreadMemory.threadId, UUID) == thread_id)
                # Order by similarity (most similar first)
                query = query.order_by(similarity.desc())
                
                if limit:
                    query = query.limit(limit)
                
                # Return tuples of (memory, score)
                results = query.all()
                return [(row[0], float(row[1])) for row in results]
            
            else:
                # No embedding query - standard retrieval
                query = session.query(ThreadMemory).filter(
                    cast(ThreadMemory.userId, UUID) == user_id,
                    ThreadMemory.strategy == strategy_id
                )
                
                if thread_id:
                    query = query.filter(cast(ThreadMemory.threadId, UUID) == thread_id)
                
                if limit:
                    query = query.limit(limit)
                
                return query.all()
    
    def mark_messages_as_summarized(self, message_ids: list):
        """Mark messages as summarized."""
        with self.get_session() as session:
            session.query(ExchangeMessage).filter(ExchangeMessage.id.in_(message_ids)).update(
                {ExchangeMessage.is_summarized: True},
                synchronize_session=False
            )
            session.commit()