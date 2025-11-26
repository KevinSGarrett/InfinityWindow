from __future__ import annotations

from typing import Optional, List, Dict

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine, get_db
from app.db import models
from app.llm.openai_client import generate_reply_from_history
from app.llm.embeddings import get_embedding
from app.vectorstore.chroma_store import (
    add_message_embedding,
    query_similar_messages,
    query_similar_document_chunks,
)
from app.api.search import router as search_router
from app.api.docs import router as docs_router

# Create tables on import (simple approach for now; later we can use migrations)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="InfinityWindow Backend",
    description="Backend service for the InfinityWindow personal AI workbench.",
    version="0.3.0",
)

app.include_router(search_router)
app.include_router(docs_router)


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
    conversation_id: Optional[int] = None
    message: str


class ChatResponse(BaseModel):
    conversation_id: int
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
        "version": "0.3.0",
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
    Chat within a specific conversation, backed by OpenAI, with automatic
    retrieval from stored messages and ingested documents.

    - If conversation_id is provided, we continue that conversation.
    - If conversation_id is omitted/null, we'll:
        * use the first project if it exists, or
        * create a 'Default Project', then
        * create a new conversation under it.

    Steps:
      1. Resolve or create the conversation.
      2. Load conversation history from the DB.
      3. Store the new user message.
      4. Embed the user message and retrieve:
         - relevant past messages from this conversation
         - relevant document chunks from the same project
      5. Build the message list for OpenAI with a memory context.
      6. Call OpenAI to generate a reply.
      7. Store the assistant reply + index both messages in Chroma.
    """

    # 1) Resolve or create conversation
    if payload.conversation_id is not None:
        conversation = db.get(models.Conversation, payload.conversation_id)
        if conversation is None:
            raise HTTPException(
                status_code=404, detail="Conversation not found."
            )
    else:
        # Get or create a default project
        project = (
            db.query(models.Project)
            .order_by(models.Project.id)
            .first()
        )
        if project is None:
            project = models.Project(
                name="Default Project",
                description="Auto-created default project.",
            )
            db.add(project)
            db.commit()
            db.refresh(project)

        # Create a new conversation
        conversation = models.Conversation(
            project_id=project.id,
            title="Chat conversation",
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # 2) Load existing messages for this conversation as history
    existing_messages = (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation.id)
        .order_by(models.Message.id.asc())
        .all()
    )

    # 3) Save the new user message (but don't commit yet)
    user_message = models.Message(
        conversation_id=conversation.id,
        role="user",
        content=payload.message,
    )
    db.add(user_message)
    db.flush()  # ensures user_message gets an ID before we commit

    # 4) Retrieval: embed user message and pull relevant messages & docs
    retrieval_context_text = ""
    user_embedding = None

    try:
        user_embedding = get_embedding(payload.message)

        # 4a) Similar messages in this project's conversation
        msg_results = query_similar_messages(
            project_id=conversation.project_id,
            query_embedding=user_embedding,
            conversation_id=conversation.id,
            n_results=5,
        )

        msg_docs_nested = msg_results.get("documents", [[]])
        msg_metas_nested = msg_results.get("metadatas", [[]])
        msg_docs = msg_docs_nested[0] if msg_docs_nested else []
        msg_metas = msg_metas_nested[0] if msg_metas_nested else []

        msg_snippets: List[str] = []
        for doc, meta in zip(msg_docs, msg_metas):
            role = meta.get("role", "unknown")
            msg_snippets.append(f"[{role} message] {doc}")

        # 4b) Similar document chunks in this project
        doc_results = query_similar_document_chunks(
            project_id=conversation.project_id,
            query_embedding=user_embedding,
            document_id=None,
            n_results=5,
        )

        doc_docs_nested = doc_results.get("documents", [[]])
        doc_metas_nested = doc_results.get("metadatas", [[]])
        doc_docs = doc_docs_nested[0] if doc_docs_nested else []
        doc_metas = doc_metas_nested[0] if doc_metas_nested else []

        doc_snippets: List[str] = []
        for doc_text, meta in zip(doc_docs, doc_metas):
            document_id = meta.get("document_id")
            chunk_index = meta.get("chunk_index")
            doc_snippets.append(
                f"[Document {document_id}, chunk {chunk_index}] {doc_text}"
            )

        context_parts: List[str] = []
        if msg_snippets:
            context_parts.append(
                "Relevant past messages:\n" + "\n\n".join(msg_snippets)
            )
        if doc_snippets:
            context_parts.append(
                "Relevant document excerpts:\n" + "\n\n".join(doc_snippets)
            )

        if context_parts:
            retrieval_context_text = (
                "You have access to the following retrieved memory and document excerpts.\n"
                "Use them to ground your answer to the user's latest question. "
                "If anything conflicts with the user's most recent instructions, "
                "follow the user.\n\n"
                + "\n\n---\n\n".join(context_parts)
            )

    except Exception as e:
        # Retrieval should never break the chat flow
        print(f"[WARN] Retrieval failed: {e!r}")
        user_embedding = None

    # 5) Build the message list for OpenAI
    chat_history: List[Dict[str, str]] = []

    # System prompt to define behavior
    chat_history.append(
        {
            "role": "system",
            "content": (
                "You are InfinityWindow, a helpful AI assistant. "
                "You work inside a long-lived project workspace with persistent memory. "
                "Be clear, concise, and helpful."
            ),
        }
    )

    # Optional retrieval context as an additional system message
    if retrieval_context_text:
        chat_history.append(
            {
                "role": "system",
                "content": retrieval_context_text,
            }
        )

    # Previous messages
    for m in existing_messages:
        chat_history.append(
            {
                "role": m.role,
                "content": m.content,
            }
        )

    # Current user message
    chat_history.append({"role": "user", "content": payload.message})

    # 6) Call OpenAI to generate a reply
    reply_text = generate_reply_from_history(chat_history)

    # 7) Save assistant message
    assistant_message = models.Message(
        conversation_id=conversation.id,
        role="assistant",
        content=reply_text,
    )
    db.add(assistant_message)
    db.flush()  # ensure assistant_message.id exists

    # 8) Create embeddings and index in Chroma
    try:
        # Reuse user embedding if we have it, otherwise compute now
        if user_embedding is None:
            user_embedding = get_embedding(payload.message)

        add_message_embedding(
            message_id=user_message.id,
            conversation_id=conversation.id,
            project_id=conversation.project_id,
            role="user",
            content=payload.message,
            embedding=user_embedding,
        )

        # Assistant message embedding
        assistant_embedding = get_embedding(reply_text)
        add_message_embedding(
            message_id=assistant_message.id,
            conversation_id=conversation.id,
            project_id=conversation.project_id,
            role="assistant",
            content=reply_text,
            embedding=assistant_embedding,
        )
    except Exception as e:
        # Do not fail the request if indexing fails
        print(f"[WARN] Failed to index messages in Chroma: {e!r}")

    # 9) Commit everything
    db.commit()

    return ChatResponse(
        conversation_id=conversation.id,
        reply=reply_text,
    )
