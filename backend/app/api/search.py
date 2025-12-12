from __future__ import annotations

from typing import Dict, List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import models
from app.llm.embeddings import get_embedding
from app.vectorstore.chroma_store import (
    query_similar_messages,
    query_similar_document_chunks,
    query_similar_memory_items,
)

router = APIRouter(
    prefix="/search",
    tags=["search"],
)


def _record_retrieval(
    surface: Literal["chat", "search"],
    kind: Literal["messages", "docs", "memory", "tasks"],
    hits: int,
) -> None:
    try:
        from app.api import main as main_api

        main_api.record_retrieval_event(surface=surface, kind=kind, hits=hits)
    except Exception:
        # Telemetry should never block search endpoints.
        return


# ---------------------------------------------------------------------------
# Message search
# ---------------------------------------------------------------------------


class MessageSearchRequest(BaseModel):
    project_id: int
    query: str
    conversation_id: Optional[int] = None
    folder_id: Optional[int] = None
    limit: int = 5


class MessageSearchHit(BaseModel):
    message_id: int
    conversation_id: int
    project_id: int
    role: str
    content: str
    distance: float
    folder_id: Optional[int] = None
    folder_name: Optional[str] = None
    folder_color: Optional[str] = None


class MessageSearchResponse(BaseModel):
    hits: List[MessageSearchHit]


@router.post("/messages", response_model=MessageSearchResponse)
def search_messages(
    payload: MessageSearchRequest,
    db: Session = Depends(get_db),
):
    """
    Semantic search over stored messages using Chroma.

    - Required: project_id, query
    - Optional: conversation_id (to restrict results)
    - 'limit' controls how many results to return.
    """

    # 1) Verify project exists
    project = db.get(models.Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    # 2) If conversation_id is provided, verify it exists and belongs to project
    if payload.conversation_id is not None:
        conversation = db.get(models.Conversation, payload.conversation_id)
        if conversation is None:
            raise HTTPException(
                status_code=404, detail="Conversation not found."
            )
        if conversation.project_id != payload.project_id:
            raise HTTPException(
                status_code=400,
                detail="Conversation does not belong to the given project.",
            )
    # 2b) If folder_id is provided, ensure it belongs to this project
    if payload.folder_id is not None:
        folder = db.get(models.ConversationFolder, payload.folder_id)
        if folder is None or folder.project_id != payload.project_id:
            raise HTTPException(
                status_code=404,
                detail="Conversation folder not found for this project.",
            )

    # 3) Create embedding for the query
    query_emb = get_embedding(payload.query)

    # 4) Query Chroma
    results = query_similar_messages(
        project_id=payload.project_id,
        query_embedding=query_emb,
        conversation_id=payload.conversation_id,
        folder_id=payload.folder_id,
        n_results=payload.limit,
    )

    # Chroma response structure:
    # {
    #   "ids": [[...]],
    #   "documents": [[...]],
    #   "metadatas": [[{...}, {...}, ...]],
    #   "distances": [[...]]
    # }
    ids_nested = results.get("ids", [[]])
    docs_nested = results.get("documents", [[]])
    metas_nested = results.get("metadatas", [[]])
    dists_nested = results.get("distances", [[]])

    ids = ids_nested[0] if ids_nested else []
    docs = docs_nested[0] if docs_nested else []
    metas = metas_nested[0] if metas_nested else []
    dists = dists_nested[0] if dists_nested else []

    hits: List[MessageSearchHit] = []

    # Fetch folder metadata for each conversation referenced in the hits
    conversation_ids = {
        int(meta["conversation_id"]) for meta in metas if "conversation_id" in meta
    }
    folder_meta_map: Dict[int, Dict[str, Optional[str]]] = {}
    if conversation_ids:
        rows = (
            db.query(
                models.Conversation.id,
                models.Conversation.folder_id,
                models.ConversationFolder.name,
                models.ConversationFolder.color,
            )
            .outerjoin(
                models.ConversationFolder,
                models.Conversation.folder_id == models.ConversationFolder.id,
            )
            .filter(models.Conversation.id.in_(conversation_ids))
            .all()
        )
        for convo_id, folder_id, folder_name, folder_color in rows:
            folder_meta_map[convo_id] = {
                "folder_id": folder_id,
                "folder_name": folder_name,
                "folder_color": folder_color,
            }

    for msg_id, doc, meta, dist in zip(ids, docs, metas, dists):
        # meta contains: message_id, conversation_id, project_id, role
        convo_id = int(meta["conversation_id"])
        folder_info = folder_meta_map.get(
            convo_id,
            {
                "folder_id": meta.get("folder_id"),
                "folder_name": None,
                "folder_color": None,
            },
        )
        hits.append(
            MessageSearchHit(
                message_id=int(meta["message_id"]),
                conversation_id=convo_id,
                project_id=int(meta["project_id"]),
                role=str(meta["role"]),
                content=doc,
                distance=float(dist),
                folder_id=folder_info.get("folder_id"),
                folder_name=folder_info.get("folder_name"),
                folder_color=folder_info.get("folder_color"),
            )
        )

    _record_retrieval(surface="search", kind="messages", hits=len(hits))
    return MessageSearchResponse(hits=hits)


# ---------------------------------------------------------------------------
# Document chunk search
# ---------------------------------------------------------------------------


class DocSearchRequest(BaseModel):
    project_id: int
    query: str
    document_id: Optional[int] = None
    limit: int = 5


class DocSearchHit(BaseModel):
    chunk_id: int
    document_id: int
    project_id: int
    chunk_index: int
    content: str
    distance: float


class DocSearchResponse(BaseModel):
    hits: List[DocSearchHit]


@router.post("/docs", response_model=DocSearchResponse)
def search_docs(
    payload: DocSearchRequest,
    db: Session = Depends(get_db),
):
    """
    Semantic search over document chunks using Chroma.

    - Required: project_id, query
    - Optional: document_id (to restrict results to a single document)
    - 'limit' controls how many results to return.
    """

    # 1) Verify project exists
    project = db.get(models.Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    # 2) If document_id is provided, verify it exists and belongs to project
    if payload.document_id is not None:
        document = db.get(models.Document, payload.document_id)
        if document is None:
            raise HTTPException(
                status_code=404, detail="Document not found."
            )
        if document.project_id != payload.project_id:
            raise HTTPException(
                status_code=400,
                detail="Document does not belong to the given project.",
            )

    # 3) Create embedding for the query
    query_emb = get_embedding(payload.query)

    # 4) Query Chroma
    results = query_similar_document_chunks(
        project_id=payload.project_id,
        query_embedding=query_emb,
        document_id=payload.document_id,
        n_results=payload.limit,
    )

    ids_nested = results.get("ids", [[]])
    docs_nested = results.get("documents", [[]])
    metas_nested = results.get("metadatas", [[]])
    dists_nested = results.get("distances", [[]])

    ids = ids_nested[0] if ids_nested else []
    docs = docs_nested[0] if docs_nested else []
    metas = metas_nested[0] if metas_nested else []
    dists = dists_nested[0] if dists_nested else []

    hits: List[DocSearchHit] = []

    for _id, doc, meta, dist in zip(ids, docs, metas, dists):
        # meta contains: document_id, project_id, chunk_id, chunk_index
        hits.append(
            DocSearchHit(
                chunk_id=int(meta["chunk_id"]),
                document_id=int(meta["document_id"]),
                project_id=int(meta["project_id"]),
                chunk_index=int(meta["chunk_index"]),
                content=doc,
                distance=float(dist),
            )
        )

    _record_retrieval(surface="search", kind="docs", hits=len(hits))
    return DocSearchResponse(hits=hits)


# ---------------------------------------------------------------------------
# Memory search
# ---------------------------------------------------------------------------


class MemorySearchRequest(BaseModel):
    project_id: int
    query: str
    limit: int = 5


class MemorySearchRequest(BaseModel):
    project_id: int
    query: str
    limit: int = 5


class MemorySearchHit(BaseModel):
    memory_id: int
    project_id: int
    content: str
    distance: float


class MemorySearchResponse(BaseModel):
    hits: List[MemorySearchHit]


class MemorySearchRequest(BaseModel):
    project_id: int
    query: str
    limit: int = 5


class MemorySearchHit(BaseModel):
    memory_id: int
    project_id: int
    title: str
    content: str
    distance: float


class MemorySearchResponse(BaseModel):
    hits: List[MemorySearchHit]


@router.post("/memory", response_model=MemorySearchResponse)
def search_memory(
    payload: MemorySearchRequest,
    db: Session = Depends(get_db),
):
    """
    Semantic search over memory items.
    """
    project = db.get(models.Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    query_emb = get_embedding(payload.query)
    results = query_similar_memory_items(
        project_id=payload.project_id,
        query_embedding=query_emb,
        n_results=payload.limit,
    )

    ids_nested = results.get("ids", [[]])
    docs_nested = results.get("documents", [[]])
    metas_nested = results.get("metadatas", [[]])
    dists_nested = results.get("distances", [[]])

    ids = ids_nested[0] if ids_nested else []
    docs = docs_nested[0] if docs_nested else []
    metas = metas_nested[0] if metas_nested else []
    dists = dists_nested[0] if dists_nested else []

    hits: List[MemorySearchHit] = []
    for mem_id, doc, meta, dist in zip(ids, docs, metas, dists):
        hits.append(
            MemorySearchHit(
                memory_id=int(meta["memory_id"]),
                project_id=int(meta["project_id"]),
                title=meta.get("title") or "",
                content=doc,
                distance=float(dist),
            )
        )

    _record_retrieval(surface="search", kind="memory", hits=len(hits))
    return MemorySearchResponse(hits=hits)
