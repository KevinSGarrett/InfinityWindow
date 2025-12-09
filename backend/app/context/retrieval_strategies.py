from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List


class RetrievalKind(str, Enum):
    DEFAULT = "default"
    MESSAGES = "messages"
    DOCS = "docs"
    MEMORY = "memory"
    TASKS = "tasks"


@dataclass
class RetrievalProfile:
    top_k: int
    score_threshold: Optional[float] = None


_DEFAULT_TOP_K = 5
_DEFAULT_PROFILES = {
    RetrievalKind.DEFAULT.value: RetrievalProfile(top_k=_DEFAULT_TOP_K),
    RetrievalKind.MESSAGES.value: RetrievalProfile(top_k=_DEFAULT_TOP_K),
    RetrievalKind.DOCS.value: RetrievalProfile(top_k=_DEFAULT_TOP_K),
    RetrievalKind.MEMORY.value: RetrievalProfile(top_k=_DEFAULT_TOP_K),
    RetrievalKind.TASKS.value: RetrievalProfile(top_k=_DEFAULT_TOP_K),
}


def _env_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        value = int(raw)
        return value if value > 0 else default
    except ValueError:
        return default


def _env_float(key: str, default: Optional[float]) -> Optional[float]:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def get_retrieval_profile(kind: str | RetrievalKind) -> RetrievalProfile:
    normalized = (kind.value if isinstance(kind, RetrievalKind) else str(kind or "")).lower()
    base = _DEFAULT_PROFILES.get(normalized, _DEFAULT_PROFILES[RetrievalKind.DEFAULT.value])
    prefix = normalized.upper()
    top_k = _env_int(f"RETRIEVAL_{prefix}_TOP_K", base.top_k)
    score_threshold = _env_float(f"RETRIEVAL_{prefix}_SCORE_THRESHOLD", base.score_threshold)
    # Ensure a sane minimum
    top_k = max(1, top_k)
    return RetrievalProfile(top_k=top_k, score_threshold=score_threshold)


def apply_profile_to_chroma_results(
    profile: RetrievalProfile, results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply top_k and optional score_threshold to Chroma-style results.
    - Assumes lower distance is better. If no distances present, threshold is ignored.
    - Returns a new dict with nested lists trimmed/filtered.
    """
    ids_nested: List[List[Any]] = results.get("ids", [[]])
    docs_nested: List[List[Any]] = results.get("documents", [[]])
    metas_nested: List[List[Dict[str, Any]]] = results.get("metadatas", [[]])
    dists_nested: List[List[float]] = results.get("distances", [[]])

    ids = ids_nested[0] if ids_nested else []
    docs = docs_nested[0] if docs_nested else []
    metas = metas_nested[0] if metas_nested else []
    dists = dists_nested[0] if dists_nested else []

    top_k = max(1, profile.top_k)

    filtered_ids: List[Any] = []
    filtered_docs: List[Any] = []
    filtered_metas: List[Dict[str, Any]] = []
    filtered_dists: List[float] = []

    for idx, (i, doc, meta) in enumerate(zip(ids, docs, metas)):
        dist = dists[idx] if idx < len(dists) else None
        if profile.score_threshold is not None and dist is not None:
            # Chroma returns smaller distance for closer matches
            if dist > profile.score_threshold:
                continue
        filtered_ids.append(i)
        filtered_docs.append(doc)
        filtered_metas.append(meta)
        filtered_dists.append(dist if dist is not None else 0.0)
        if len(filtered_ids) >= top_k:
            break

    return {
        "ids": [filtered_ids],
        "documents": [filtered_docs],
        "metadatas": [filtered_metas],
        "distances": [filtered_dists],
    }


