from __future__ import annotations

from typing import Any, Dict, List, Optional

import chromadb
from chromadb.api.models.Collection import Collection

# We'll store Chroma data in ./chroma_data relative to the backend folder.
# This will create a "chroma_data" directory next to infinitywindow.db.
_CHROMA_CLIENT: chromadb.PersistentClient | None = None
_MESSAGES_COLLECTION_NAME = "messages"


def get_client() -> chromadb.PersistentClient:
    """
    Lazily create a singleton Chroma PersistentClient.
    """
    global _CHROMA_CLIENT
    if _CHROMA_CLIENT is None:
        _CHROMA_CLIENT = chromadb.PersistentClient(path="chroma_data")
    return _CHROMA_CLIENT


def get_messages_collection() -> Collection:
    """
    Get or create the collection used for conversation message embeddings.
    """
    client = get_client()
    collection = client.get_or_create_collection(
        name=_MESSAGES_COLLECTION_NAME,
        metadata={
            "description": "InfinityWindow conversation messages"
        },
    )
    return collection


def add_message_embedding(
    message_id: int,
    conversation_id: int,
    project_id: int,
    role: str,
    content: str,
    embedding: List[float],
) -> None:
    """
    Add a single message embedding to the Chroma 'messages' collection.
    """
    collection = get_messages_collection()
    collection.add(
        ids=[str(message_id)],
        embeddings=[embedding],
        documents=[content],
        metadatas=[
            {
                "message_id": message_id,
                "conversation_id": conversation_id,
                "project_id": project_id,
                "role": role,
            }
        ],
    )


def query_similar_messages(
    project_id: int,
    query_embedding: List[float],
    conversation_id: Optional[int] = None,
    n_results: int = 5,
) -> Dict[str, Any]:
    """
    Query messages similar to the query_embedding.

    - Always filters by project_id.
    - If conversation_id is provided, also filters by that conversation.

    Uses Chroma's newer filter syntax:
      - Single-field filter: {"field": {"$eq": value}}
      - Multi-field filter: {"$and": [ {...}, {...} ]}
    """
    collection = get_messages_collection()

    # Build the "where" filter in the format Chroma expects
    if conversation_id is None:
        where: Dict[str, Any] = {
            "project_id": {"$eq": project_id}
        }
    else:
        where = {
            "$and": [
                {"project_id": {"$eq": project_id}},
                {"conversation_id": {"$eq": conversation_id}},
            ]
        }

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
    )
    return results
