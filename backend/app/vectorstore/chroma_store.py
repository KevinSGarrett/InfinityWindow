from __future__ import annotations

from typing import Any, Dict, List, Optional

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb import errors as chroma_errors
import logging
import os
import shutil
from pathlib import Path

# We'll store Chroma data in ./chroma_data relative to the backend folder.
# This will create a "chroma_data" directory next to infinitywindow.db.
_CHROMA_CLIENT: chromadb.PersistentClient | _StubClient | None = None
_CHROMA_PATH = Path("chroma_data")

# Collection names
_MESSAGES_COLLECTION_NAME = "messages"
_DOCS_COLLECTION_NAME = "docs"
_MEMORY_COLLECTION_NAME = "memory_items"
_CHROMA_MAX_BATCH = 5000

logger = logging.getLogger(__name__)


class _StubCollection:
    """
    Minimal in-memory stand-in for a Chroma collection.

    Only implements the subset of the API that the app uses in tests:
    - add
    - query
    - delete
    """

    def __init__(self, name: str):
        self.name = name
        self._records: List[Dict[str, Any]] = []

    def reset(self) -> None:
        self._records = []

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        docs = documents or [""] * len(ids)
        metas = metadatas or [{} for _ in ids]
        for rid, embedding, doc, meta in zip(ids, embeddings, docs, metas):
            rid_str = str(rid)
            # Replace existing record with same id to mimic upsert-like behavior
            self._records = [rec for rec in self._records if rec["id"] != rid_str]
            self._records.append(
                {
                    "id": rid_str,
                    "embedding": embedding or [],
                    "document": doc or "",
                    "metadata": dict(meta or {}),
                }
            )

    def delete(self, ids: Optional[List[str]] = None, **_: Any) -> None:
        if not ids:
            return
        target_ids = {str(_id) for _id in ids}
        self._records = [rec for rec in self._records if rec["id"] not in target_ids]

    def _matches_where(self, meta: Dict[str, Any], where: Optional[Dict[str, Any]]) -> bool:
        if not where:
            return True
        if "$and" in where:
            return all(self._matches_where(meta, clause) for clause in where.get("$and", []))
        for key, cond in where.items():
            if isinstance(cond, dict) and "$eq" in cond:
                if meta.get(key) != cond["$eq"]:
                    return False
            else:
                if meta.get(key) != cond:
                    return False
        return True

    def _simple_distance(self, query_embedding: List[float], stored_embedding: List[float]) -> float:
        if not query_embedding or not stored_embedding:
            return 0.0
        size = min(len(query_embedding), len(stored_embedding))
        if size == 0:
            return 0.0
        # Lightweight average absolute difference; enough for deterministic ordering
        return float(
            sum(abs(query_embedding[i] - stored_embedding[i]) for i in range(size)) / size
        )

    def query(
        self,
        query_embeddings: Optional[List[List[float]]] = None,
        query_texts: Optional[List[str]] = None,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        # Filter by metadata
        filtered = [rec for rec in self._records if self._matches_where(rec["metadata"], where)]

        # Optional simple where_document substring filter
        if where_document:
            needle = where_document.get("$contains")
            if isinstance(needle, str):
                filtered = [rec for rec in filtered if needle in rec.get("document", "")]

        max_results = n_results or len(filtered)
        trimmed = filtered[:max_results]
        query_vec = query_embeddings[0] if query_embeddings else []

        ids = [rec["id"] for rec in trimmed]
        docs = [rec["document"] for rec in trimmed]
        metas = [rec["metadata"] for rec in trimmed]
        dists = [self._simple_distance(query_vec, rec["embedding"]) for rec in trimmed]

        return {
            "ids": [ids],
            "documents": [docs],
            "metadatas": [metas],
            "distances": [dists],
        }


class _StubClient:
    def __init__(self):
        self._collections: Dict[str, _StubCollection] = {}

    def get_or_create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        del metadata  # not used in stub, but accepted for API parity
        if name not in self._collections:
            self._collections[name] = _StubCollection(name)
        return self._collections[name]

    def reset(self) -> None:
        for collection in self._collections.values():
            collection.reset()
        self._collections = {}


def _vectorstore_mode() -> str:
    mode = os.getenv("VECTORSTORE_MODE", "persistent").lower()
    return mode if mode in {"persistent", "stub"} else "persistent"


def _is_stub_mode() -> bool:
    return _vectorstore_mode() == "stub"


def _create_client() -> chromadb.PersistentClient | _StubClient:
    if _is_stub_mode():
        return _StubClient()
    _CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(_CHROMA_PATH))


def get_client() -> chromadb.PersistentClient | _StubClient:
    """
    Lazily create a singleton Chroma client (persistent or in-memory stub).
    """
    global _CHROMA_CLIENT
    if _CHROMA_CLIENT is None:
        _CHROMA_CLIENT = _create_client()
    return _CHROMA_CLIENT


def _reset_chroma_persistence(clear_data: bool = False) -> None:
    """
    Reset the global Chroma client (and optionally clear on-disk data) to recover from
    compaction/database errors.
    """
    global _CHROMA_CLIENT
    if isinstance(_CHROMA_CLIENT, _StubClient):
        if clear_data:
            _CHROMA_CLIENT.reset()
            try:
                shutil.rmtree(_CHROMA_PATH, ignore_errors=True)
            except Exception:  # noqa: BLE001
                logger.exception("Failed to remove chroma_data during stub reset")
        _CHROMA_CLIENT = None
        return
    _CHROMA_CLIENT = None
    if clear_data:
        try:
            shutil.rmtree(_CHROMA_PATH, ignore_errors=True)
        except Exception:  # noqa: BLE001
            logger.exception("Failed to remove chroma_data during reset")


def _with_chroma_retry(action: str, func, attempts: int = 2):
    """
    Run a Chroma operation with a limited retry/reset strategy.

    If we hit a compaction/internal error, we reset the client (and clear the on-disk
    store for the compaction case) and try again. This keeps the API responsive even if
    Chroma's metadata segment becomes inconsistent.
    """
    if _is_stub_mode():
        return func()

    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            return func()
        except chroma_errors.InternalError as exc:
            last_exc = exc
            msg = str(exc)
            clear = "Failed to apply logs to the metadata segment" in msg
            logger.warning(
                "Chroma error during %s (attempt %s/%s): %s",
                action,
                i + 1,
                attempts,
                msg,
            )
            _reset_chroma_persistence(clear_data=clear)
        except Exception:
            # Do not mask non-Chroma errors
            raise
    if last_exc:
        raise last_exc


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
    folder_id: Optional[int] = None,
) -> None:
    """
    Add a single message embedding to the Chroma 'messages' collection.
    """
    collection = get_messages_collection()
    metadata = {
        "message_id": message_id,
        "conversation_id": conversation_id,
        "project_id": project_id,
        "role": role,
    }
    if folder_id is not None:
        metadata["folder_id"] = folder_id

    def _add():
        collection = get_messages_collection()
        collection.add(
            ids=[str(message_id)],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata],
        )

    _with_chroma_retry("add message embedding", _add)


def query_similar_messages(
    project_id: int,
    query_embedding: List[float],
    conversation_id: Optional[int] = None,
    folder_id: Optional[int] = None,
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
    filters: List[Dict[str, Any]] = [
        {"project_id": {"$eq": project_id}},
    ]
    if conversation_id is not None:
        filters.append({"conversation_id": {"$eq": conversation_id}})
    if folder_id is not None:
        filters.append({"folder_id": {"$eq": folder_id}})

    if len(filters) == 1:
        where: Dict[str, Any] = filters[0]
    else:
        where = {"$and": filters}

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

    total_chunks = len(chunk_ids)
    for start in range(0, total_chunks, _CHROMA_MAX_BATCH):
        end = min(start + _CHROMA_MAX_BATCH, total_chunks)
        slice_ids = chunk_ids[start:end]
        slice_indexes = chunk_indexes[start:end]
        slice_contents = contents[start:end]
        slice_embeddings = embeddings[start:end]

        # Coerce all metadata fields to concrete types (no None allowed by Chroma)
        metadatas = []
        for cid, idx in zip(slice_ids, slice_indexes):
            metadatas.append(
                {
                    "document_id": int(document_id),
                    "project_id": int(project_id),
                    "chunk_id": int(cid),
                    "chunk_index": int(idx),
                }
            )

        def _add_slice():
            collection = get_docs_collection()
            collection.add(
                ids=[str(cid) for cid in slice_ids],
                embeddings=slice_embeddings,
                documents=slice_contents,
                metadatas=metadatas,
            )

        _with_chroma_retry("add document chunks", _add_slice)


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


# --------------------------------------------------------------------
# Memory item collection helpers
# --------------------------------------------------------------------


def get_memory_collection() -> Collection:
    client = get_client()
    collection = client.get_or_create_collection(
        name=_MEMORY_COLLECTION_NAME,
        metadata={
            "description": "InfinityWindow project memory items"
        },
    )
    return collection


def add_memory_embedding(
    memory_id: int,
    project_id: int,
    content: str,
    embedding: List[float],
    title: str | None = None,
) -> None:
    def _add():
        collection = get_memory_collection()
        collection.add(
            ids=[str(memory_id)],
            embeddings=[embedding],
            documents=[content],
            metadatas=[
                {
                    "memory_id": memory_id,
                    "project_id": project_id,
                    "title": title,
                }
            ],
        )

    _with_chroma_retry("add memory embedding", _add)


def delete_memory_embedding(memory_id: int) -> None:
    collection = get_memory_collection()
    try:
        collection.delete(ids=[str(memory_id)])
    except Exception:
        # Missing embeddings are not fatal
        pass


def query_similar_memory_items(
    project_id: int,
    query_embedding: List[float],
    n_results: int = 5,
) -> Dict[str, Any]:
    collection = get_memory_collection()
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where={"project_id": {"$eq": project_id}},
    )
