from __future__ import annotations

from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine, get_db
from app.db import models


# Create tables on startup (for now; later we might use migrations)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="InfinityWindow Backend",
    description="Backend service for InfinityWindow personal AI workbench.",
    version="0.2.0",
)


# ---------- Pydantic Schemas ----------


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(BaseModel):
    project_id: int
    title: Optional[str] = None


class ConversationRead(BaseModel):
    id: int
    project_id: int
    title: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    conversation_id: int
    message: str


class ChatResponse(BaseModel):
    reply: str


# ---------- Routes ----------


@app.get("/health")
def health():
    """
    Simple health check endpoint.
    """
    return {
        "status": "ok",
        "service": "InfinityWindow",
        "version": "0.2.0",
    }


@app.post("/projects", response_model=ProjectRead)
def create_project(
    payload: ProjectCreate, db: Session = Depends(get_db)
):
    """
    Create a new project.

    For now, 'name' must be unique.
    """
    existing = (
        db.query(models.Project)
        .filter(models.Project.name == payload.name)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Project with that name already exists.",
        )

    project = models.Project(
        name=payload.name,
        description=payload.description,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@app.get("/projects", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)):
    """
    List all projects.
    """
    projects = db.query(models.Project).order_by(models.Project.id).all()
    return projects


@app.post("/conversations", response_model=ConversationRead)
def create_conversation(
    payload: ConversationCreate, db: Session = Depends(get_db)
):
    """
    Create a new conversation under a given project.
    """
    project = db.get(models.Project, payload.project_id)
    if not project:
        raise HTTPException(
            status_code=404, detail="Project not found."
        )

    conversation = models.Conversation(
        project_id=payload.project_id,
        title=payload.title,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Chat within a specific conversation.

    For now, this is still a placeholder that just echoes what you said,
    but we *do* store both the user message and the assistant response
    into the database.

    Later we'll replace the placeholder logic with real LLM calls + memory.
    """
    conversation = db.get(models.Conversation, payload.conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=404, detail="Conversation not found."
        )

    # Store user message
    user_message = models.Message(
        conversation_id=payload.conversation_id,
        role="user",
        content=payload.message,
    )
    db.add(user_message)

    # Placeholder assistant reply
    reply_text = f"(placeholder) You said: {payload.message}"

    assistant_message = models.Message(
        conversation_id=payload.conversation_id,
        role="assistant",
        content=reply_text,
    )
    db.add(assistant_message)

    db.commit()

    return ChatResponse(reply=reply_text)
