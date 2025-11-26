from __future__ import annotations

from typing import Any, Dict, List, Optional

import chromadb
from chromadb.api.models.Collection import Collection

# We'll store Chroma data in ./chroma_data relative to the backend folder.
# This will create a "chroma_data" directory next to infinitywindow.db.
_CHROMA_CLIENT: chromadb.PersistentClient | None = None

# Collection names
_MESSAGES_COLLECTION_NAME = "messages"
_DOCS_COLLECTION_NAME = "docs"


def get_client() -> chromadb.PersistentClient:
    """
    Lazily create a singleton Chroma PersistentClient.
    """
    global _CHROMA_CLIENT
    if _CHROMA_CLIENT is None:
        _CHROMA_CLIENT = chromadb.PersistentClient(path="chroma_data")
    return _CHROMA_CLIENT


# --------------------------------------------------------------------
# Message collection helpers
# --------------------------------------------------------------------


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


# --------------------------------------------------------------------
# Document chunk collection helpers
# --------------------------------------------------------------------


def get_docs_collection() -> Collection:
    """
    Get or create the collection used for document chunk embeddings.
    """
    client = get_client()
    collection = client.get_or_create_collection(
        name=_DOCS_COLLECTION_NAME,
        metadata={
            "description": "InfinityWindow document chunks"
        },
    )
    return collection


def add_document_chunks(
    document_id: int,
    project_id: int,
    chunk_ids: List[int],
    chunk_indexes: List[int],
    contents: List[str],
    embeddings: List[List[float]],
) -> None:
    """
    Add a batch of document chunks to the 'docs' collection.

    chunk_ids, chunk_indexes, contents, and embeddings must have the same length.
    """
    if not (
        len(chunk_ids)
        == len(chunk_indexes)
        == len(contents)
        == len(embeddings)
    ):
        raise ValueError(
            "chunk_ids, chunk_indexes, contents, and embeddings must have the same length."
        )

    collection = get_docs_collection()

    collection.add(
        ids=[str(cid) for cid in chunk_ids],
        embeddings=embeddings,
        documents=contents,
        metadatas=[
            {
                "document_id": document_id,
                "project_id": project_id,
                "chunk_id": cid,
                "chunk_index": idx,
            }
            for cid, idx in zip(chunk_ids, chunk_indexes)
        ],
    )


def query_similar_document_chunks(
    project_id: int,
    query_embedding: List[float],
    document_id: Optional[int] = None,
    n_results: int = 5,
) -> Dict[str, Any]:
    """
    Query document chunks similar to the query_embedding.

    - Always filters by project_id.
    - If document_id is provided, also filters by that document.

    Uses Chroma's filter syntax with $eq and $and.
    """
    collection = get_docs_collection()

    if document_id is None:
        where: Dict[str, Any] = {
            "project_id": {"$eq": project_id}
        }
    else:
        where = {
            "$and": [
                {"project_id": {"$eq": project_id}},
                {"document_id": {"$eq": document_id}},
            ]
        }

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
    )
    return results
