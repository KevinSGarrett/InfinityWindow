from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Float,
    JSON,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # NEW: optional local filesystem root for this project
    local_root_path: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True
    )
    instruction_text: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    instruction_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    pinned_note_text: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="project", cascade="all, delete-orphan"
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="project", cascade="all, delete-orphan"
    )
    tasks: Mapped[List["Task"]] = relationship(
        "Task", back_populates="project", cascade="all, delete-orphan"
    )
    usage_records: Mapped[List["UsageRecord"]] = relationship(
        "UsageRecord", back_populates="project", cascade="all, delete-orphan"
    )
    decisions: Mapped[List["ProjectDecision"]] = relationship(
        "ProjectDecision",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    folders: Mapped[List["ConversationFolder"]] = relationship(
        "ConversationFolder",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    memory_items: Mapped[List["MemoryItem"]] = relationship(
        "MemoryItem",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    ingestion_jobs: Mapped[List["IngestionJob"]] = relationship(
        "IngestionJob",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    file_ingestion_states: Mapped[List["FileIngestionState"]] = relationship(
        "FileIngestionState",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    folder_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("conversation_folders.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    project: Mapped[Project] = relationship(
        "Project", back_populates="conversations"
    )
    folder: Mapped[Optional["ConversationFolder"]] = relationship(
        "ConversationFolder", back_populates="conversations"
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )
    usage_records: Mapped[List["UsageRecord"]] = relationship(
        "UsageRecord", back_populates="conversation", cascade="all, delete-orphan"
    )
    memory_items: Mapped[List["MemoryItem"]] = relationship(
        "MemoryItem",
        back_populates="source_conversation",
        cascade="all, delete-orphan",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id"), index=True
    )
    # "user" | "assistant" | "system"
    role: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    conversation: Mapped[Conversation] = relationship(
        "Conversation", back_populates="messages"
    )
    usage_records: Mapped[List["UsageRecord"]] = relationship(
        "UsageRecord", back_populates="message", cascade="all, delete-orphan"
    )
    memory_items: Mapped[List["MemoryItem"]] = relationship(
        "MemoryItem",
        back_populates="source_message",
        cascade="all, delete-orphan",
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    project: Mapped["Project"] = relationship(
        "Project", back_populates="documents"
    )
    sections: Mapped[List["DocumentSection"]] = relationship(
        "DocumentSection",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentSection(Base):
    __tablename__ = "document_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documents.id"), index=True
    )
    # Optional human-readable section title (e.g., "Chapter 3: Methods")
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Order of this section within the document
    index: Mapped[int] = mapped_column(Integer, default=0)
    # Optional path like "Chapter 1 > Section 2"
    path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    document: Mapped["Document"] = relationship(
        "Document", back_populates="sections"
    )
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="section",
        cascade="all, delete-orphan",
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documents.id"), index=True
    )
    section_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("document_sections.id"), nullable=True
    )
    # Order of this chunk within its section or document
    index: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text)

    document: Mapped["Document"] = relationship(
        "Document", back_populates="chunks"
    )
    section: Mapped[Optional["DocumentSection"]] = relationship(
        "DocumentSection", back_populates="chunks"
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), index=True
    )
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="open")
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    blocked_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    auto_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    project: Mapped["Project"] = relationship(
        "Project", back_populates="tasks"
    )


class TaskSuggestion(Base):
    __tablename__ = "task_suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), index=True
    )
    conversation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("conversations.id"), nullable=True, index=True
    )
    target_task_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("tasks.id"), nullable=True, index=True
    )
    action_type: Mapped[str] = mapped_column(String(32))
    payload: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True
    )

    project: Mapped["Project"] = relationship("Project")
    conversation: Mapped[Optional["Conversation"]] = relationship("Conversation")
    target_task: Mapped[Optional["Task"]] = relationship("Task")


class UsageRecord(Base):
    __tablename__ = "usage_records"
    __table_args__ = (
        Index("ix_usage_project_created", "project_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), index=True
    )
    conversation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("conversations.id"), nullable=True, index=True
    )
    message_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("messages.id"), nullable=True, index=True
    )
    model: Mapped[str] = mapped_column(String(255))
    tokens_in: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cost_estimate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    project: Mapped["Project"] = relationship(
        "Project", back_populates="usage_records"
    )
    conversation: Mapped[Optional["Conversation"]] = relationship(
        "Conversation", back_populates="usage_records"
    )
    message: Mapped[Optional["Message"]] = relationship(
        "Message", back_populates="usage_records"
    )


class ProjectDecision(Base):
    __tablename__ = "project_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="recorded")
    tags_raw: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_conversation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("conversations.id"), nullable=True, index=True
    )
    follow_up_task_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("tasks.id"), nullable=True
    )
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True
    )

    project: Mapped["Project"] = relationship(
        "Project", back_populates="decisions"
    )
    source_conversation: Mapped[Optional["Conversation"]] = relationship(
        "Conversation", foreign_keys=[source_conversation_id]
    )
    follow_up_task: Mapped[Optional["Task"]] = relationship(
        "Task", foreign_keys=[follow_up_task_id]
    )


class ConversationFolder(Base):
    __tablename__ = "conversation_folders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    color: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    project: Mapped["Project"] = relationship(
        "Project", back_populates="folders"
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="folder"
    )


class MemoryItem(Base):
    __tablename__ = "memory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    tags_raw: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    source_conversation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("conversations.id"), nullable=True, index=True
    )
    source_message_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("messages.id"), nullable=True, index=True
    )
    superseded_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("memory_items.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    project: Mapped["Project"] = relationship(
        "Project", back_populates="memory_items"
    )
    source_conversation: Mapped[Optional["Conversation"]] = relationship(
        "Conversation",
        back_populates="memory_items",
        foreign_keys=[source_conversation_id],
    )
    source_message: Mapped[Optional["Message"]] = relationship(
        "Message",
        foreign_keys=[source_message_id],
        back_populates="memory_items",
    )
    superseded_by: Mapped[Optional["MemoryItem"]] = relationship(
        "MemoryItem", remote_side=[id]
    )


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), index=True
    )
    kind: Mapped[str] = mapped_column(String(32))
    source: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    processed_items: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    total_bytes: Mapped[int] = mapped_column(Integer, default=0)
    processed_bytes: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    project: Mapped["Project"] = relationship("Project", back_populates="ingestion_jobs")


class FileIngestionState(Base):
    __tablename__ = "file_ingestion_state"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "relative_path",
            name="uq_file_ingestion_state_project_path",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), index=True
    )
    relative_path: Mapped[str] = mapped_column(String(512))
    sha256: Mapped[str] = mapped_column(String(64))
    last_ingested_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    project: Mapped["Project"] = relationship(
        "Project", back_populates="file_ingestion_states"
    )
