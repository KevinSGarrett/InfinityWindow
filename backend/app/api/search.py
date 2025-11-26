from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import models
from app.llm.embeddings import get_embedding
from app.vectorstore.chroma_store import query_similar_messages

router = APIRouter(
    prefix="/search",
    tags=["search"],
)


class MessageSearchRequest(BaseModel):
    project_id: int
    query: str
    conversation_id: Optional[int] = None
    limit: int = 5


class MessageSearchHit(BaseModel):
    message_id: int
    conversation_id: int
    project_id: int
    role: str
    content: str
    distance: float


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

    # 3) Create embedding for the query
    query_emb = get_embedding(payload.query)

    # 4) Query Chroma
    results = query_similar_messages(
        project_id=payload.project_id,
        query_embedding=query_emb,
        conversation_id=payload.conversation_id,
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

    for msg_id, doc, meta, dist in zip(ids, docs, metas, dists):
        # meta contains: message_id, conversation_id, project_id, role
        hits.append(
            MessageSearchHit(
                message_id=int(meta["message_id"]),
                conversation_id=int(meta["conversation_id"]),
                project_id=int(meta["project_id"]),
                role=str(meta["role"]),
                content=doc,
                distance=float(dist),
            )
        )

    return MessageSearchResponse(hits=hits)
