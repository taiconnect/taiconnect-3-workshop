from __future__ import annotations
import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import (
    DateTime,
    String,
    Text,
    Boolean,
    Double,
    Integer,
    ForeignKey,
    Index,
    Enum,
    TIMESTAMP,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from .enums import MemoryStrategyEnums

class Base(DeclarativeBase):
    pass

StepTypeEnum = Enum(
    "assistant_message",
    "embedding",
    "llm",
    "retrieval",
    "rerank",
    "run",
    "system_message",
    "tool",
    "undefined",
    "user_message",
    name="StepType",
)

MemoryStrategyEnum = Enum(
    MemoryStrategyEnums,
    name="MemoryStrategy",
)

class User(Base):
    __tablename__ = "User"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=uuid.uuid4,
    )
    createdAt: Mapped[datetime] = mapped_column(
        TIMESTAMP(3), server_default=func.now(), nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        TIMESTAMP(3), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user_metadata: Mapped[dict] = mapped_column(
        "metadata", 
        JSONB,
        nullable=False,
    )
    
    identifier: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    threads: Mapped[List["Thread"]] = relationship(
        back_populates="user",
        cascade="all, delete",
    )

    __table_args__ = (
        Index("User_identifier_idx", "identifier"),
    )

class Thread(Base):
    __tablename__ = "Thread"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=uuid.uuid4,
    )
    createdAt: Mapped[datetime] = mapped_column(
        TIMESTAMP(3), server_default=func.now(), nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        TIMESTAMP(3), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deletedAt: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(3))

    name: Mapped[Optional[str]] = mapped_column(String)

    thread_metadata: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
    )

    userId: Mapped[Optional[str]] = mapped_column(
        ForeignKey("User.id", ondelete="SET NULL", onupdate="CASCADE")
    )

    user: Mapped[Optional["User"]] = relationship(back_populates="threads")
    steps: Mapped[List["Step"]] = relationship(
        back_populates="thread",
        cascade="all, delete",
    )
    elements: Mapped[List["Element"]] = relationship(
        back_populates="thread",
        cascade="all, delete",
    )

    __table_args__ = (
        Index("Thread_createdAt_idx", "createdAt"),
        Index("Thread_name_idx", "name"),
    )

class Step(Base):
    __tablename__ = "Step"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=uuid.uuid4,
    )
    createdAt: Mapped[datetime] = mapped_column(
        TIMESTAMP(3), server_default=func.now(), nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        TIMESTAMP(3), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    parentId: Mapped[Optional[str]] = mapped_column(
        ForeignKey("Step.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    threadId: Mapped[Optional[str]] = mapped_column(
        ForeignKey("Thread.id", ondelete="CASCADE", onupdate="CASCADE")
    )

    input: Mapped[Optional[str]] = mapped_column(Text)
    output: Mapped[Optional[str]] = mapped_column(Text)
    
    step_metadata: Mapped[dict] = mapped_column(
        "metadata", 
        JSONB,
        nullable=False,
    )

    name: Mapped[Optional[str]] = mapped_column(String)
    type: Mapped[str] = mapped_column(StepTypeEnum, nullable=False)

    showInput: Mapped[str] = mapped_column(String, server_default="json")
    isError: Mapped[bool] = mapped_column(Boolean, server_default="false")

    startTime: Mapped[datetime] = mapped_column(TIMESTAMP(3), nullable=False)
    endTime: Mapped[datetime] = mapped_column(TIMESTAMP(3), nullable=False)

    parent: Mapped[Optional["Step"]] = relationship(
        remote_side=[id],
        back_populates="children",
    )
    children: Mapped[List["Step"]] = relationship(
        back_populates="parent",
        cascade="all, delete",
    )

    thread: Mapped[Optional["Thread"]] = relationship(back_populates="steps")
    elements: Mapped[List["Element"]] = relationship(
        back_populates="step",
        cascade="all, delete",
    )
    feedbacks: Mapped[List["Feedback"]] = relationship(
        back_populates="step",
        cascade="all, delete",
    )

    __table_args__ = (
        Index("Step_createdAt_idx", "createdAt"),
        Index("Step_startTime_idx", "startTime"),
        Index("Step_endTime_idx", "endTime"),
        Index("Step_parentId_idx", "parentId"),
        Index("Step_threadId_idx", "threadId"),
        Index("Step_type_idx", "type"),
        Index("Step_name_idx", "name"),
        Index("Step_threadId_startTime_endTime_idx", "threadId", "startTime", "endTime"),
    )

class Element(Base):
    __tablename__ = "Element"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=uuid.uuid4,
    )
    createdAt: Mapped[datetime] = mapped_column(
        TIMESTAMP(3), server_default=func.now(), nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        TIMESTAMP(3), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    threadId: Mapped[Optional[str]] = mapped_column(
        ForeignKey("Thread.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    stepId: Mapped[str] = mapped_column(
        ForeignKey("Step.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )

    element_metadata: Mapped[dict] = mapped_column(
        "metadata", 
        JSONB,
        nullable=False,
    )
    
    mime: Mapped[Optional[str]] = mapped_column(String)
    name: Mapped[str] = mapped_column(String, nullable=False)
    objectKey: Mapped[Optional[str]] = mapped_column(String)
    url: Mapped[Optional[str]] = mapped_column(String)
    chainlitKey: Mapped[Optional[str]] = mapped_column(String)
    display: Mapped[Optional[str]] = mapped_column(String)
    size: Mapped[Optional[str]] = mapped_column(String)
    language: Mapped[Optional[str]] = mapped_column(String)
    page: Mapped[Optional[int]] = mapped_column(Integer)
    props: Mapped[Optional[dict]] = mapped_column(JSONB)

    step: Mapped["Step"] = relationship(back_populates="elements")
    thread: Mapped[Optional["Thread"]] = relationship(back_populates="elements")

    __table_args__ = (
        Index("Element_stepId_idx", "stepId"),
        Index("Element_threadId_idx", "threadId"),
    )

class Feedback(Base):
    __tablename__ = "Feedback"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=uuid.uuid4,
    )
    createdAt: Mapped[datetime] = mapped_column(
        TIMESTAMP(3), server_default=func.now(), nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        TIMESTAMP(3), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    stepId: Mapped[Optional[str]] = mapped_column(
        ForeignKey("Step.id", ondelete="SET NULL", onupdate="CASCADE")
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float] = mapped_column(Double, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text)

    step: Mapped[Optional["Step"]] = relationship(back_populates="feedbacks")

    __table_args__ = (
        Index("Feedback_createdAt_idx", "createdAt"),
        Index("Feedback_name_idx", "name"),
        Index("Feedback_stepId_idx", "stepId"),
        Index("Feedback_value_idx", "value"),
        Index("Feedback_name_value_idx", "name", "value"),
    )

class ThreadMemory(Base):
    __tablename__ = "ThreadMemory"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    userId: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("User.id"),
        nullable=True,
    )

    threadId: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("Thread.id"),
        nullable=True,
    )

    strategy: Mapped[str] = mapped_column(
        MemoryStrategyEnum,
        nullable=False,
    )

    namespace: Mapped[Optional[str]] = mapped_column(nullable=True)

    embedding: Mapped[Optional[list[float]]] = mapped_column(
        Vector(3072),
        nullable=True,
    )

    content: Mapped[str] = mapped_column(nullable=False)

    thread_memory_metadata: Mapped[dict] = mapped_column(
        "metadata", 
        JSONB,
        nullable=False,
    )

    createdAt: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
    )

    updatedAt: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Optional relationships (recommended)
    user: Mapped[Optional["User"]] = relationship()
    thread: Mapped[Optional["Thread"]] = relationship()

    __table_args__ = (
        Index("idx_strategy", "strategy"),
        Index("idx_userId", "userId"),
        Index("idx_threadId", "threadId"),
        Index("idx_namespace", "namespace"),
    )

class ExchangeThread(Base):
    __tablename__ = "ExchangeThread"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now()
    )

    messages = relationship("ExchangeMessage", back_populates="thread")


class ExchangeMessage(Base):
    __tablename__ = "ExchangeMessage"

    id: Mapped[int] = mapped_column(primary_key=True)
    thread_id: Mapped[str] = mapped_column(
        ForeignKey("ExchangeThread.id"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    is_summarized: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now()
    )

    thread = relationship("ExchangeThread", back_populates="messages")