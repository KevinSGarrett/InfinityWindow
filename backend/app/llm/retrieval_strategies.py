from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


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


_DEFAULT_PROFILES: Dict[RetrievalKind, RetrievalProfile] = {
    RetrievalKind.DEFAULT: RetrievalProfile(top_k=5),
    RetrievalKind.MESSAGES: RetrievalProfile(top_k=7),
    RetrievalKind.DOCS: RetrievalProfile(top_k=9),
    RetrievalKind.MEMORY: RetrievalProfile(top_k=4),
    RetrievalKind.TASKS: RetrievalProfile(top_k=3),
}

_NAME_MAP = {kind.value: kind for kind in RetrievalKind}


def _parse_int(value: Optional[str], fallback: int) -> int:
    if value is None:
        return fallback
    try:
        parsed = int(value)
        return parsed if parsed > 0 else fallback
    except (TypeError, ValueError):
        return fallback


def _parse_float(value: Optional[str], fallback: Optional[float]) -> Optional[float]:
    if value is None:
        return fallback
    try:
        parsed = float(value)
        return parsed if parsed >= 0 else fallback
    except (TypeError, ValueError):
        return fallback


def _resolve_kind(kind: RetrievalKind | str | None) -> RetrievalKind:
    if isinstance(kind, RetrievalKind):
        return kind
    key = str(kind or "").lower()
    return _NAME_MAP.get(key, RetrievalKind.DEFAULT)


def _env_key(kind: RetrievalKind, suffix: str) -> str:
    return f"RETRIEVAL_{kind.value.upper()}_{suffix}"


def get_retrieval_profile(kind: RetrievalKind | str | None) -> RetrievalProfile:
    resolved = _resolve_kind(kind)
    base = _DEFAULT_PROFILES.get(resolved, _DEFAULT_PROFILES[RetrievalKind.DEFAULT])

    top_k_env = os.getenv(_env_key(resolved, "TOP_K"))
    threshold_env = os.getenv(_env_key(resolved, "SCORE_THRESHOLD"))

    top_k = _parse_int(top_k_env, base.top_k)
    score_threshold = _parse_float(threshold_env, base.score_threshold)

    return RetrievalProfile(top_k=top_k, score_threshold=score_threshold)


def _score_from_distance(distance: Optional[float]) -> Optional[float]:
    if distance is None:
        return None
    try:
        d = float(distance)
    except (TypeError, ValueError):
        return None
    return 1.0 / (1.0 + d)


def apply_profile_to_chroma_results(
    results: Dict[str, Any], profile: RetrievalProfile
) -> Dict[str, Any]:
    """
    Trim and threshold Chroma query results according to the given profile.

    The input is expected to match Chroma's response shape:
      {
        "ids": [[...]],
        "documents": [[...]],
        "metadatas": [[...]],
        "distances": [[...]],  # optional
      }
    """
    if not results or profile.top_k <= 0:
        return {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
            "scores": [[]],
        }

    ids_nested: List[List[Any]] = results.get("ids") or [[]]
    docs_nested: List[List[str]] = results.get("documents") or [[]]
    metas_nested: List[List[Dict[str, Any]]] = results.get("metadatas") or [[]]
    dists_nested: List[List[Optional[float]]] = results.get("distances") or [[]]

    ids = ids_nested[0] if ids_nested else []
    docs = docs_nested[0] if docs_nested else []
    metas = metas_nested[0] if metas_nested else []
    dists = dists_nested[0] if dists_nested else []

    filtered_ids: List[Any] = []
    filtered_docs: List[str] = []
    filtered_metas: List[Dict[str, Any]] = []
    filtered_dists: List[Optional[float]] = []
    filtered_scores: List[Optional[float]] = []

    for idx, (doc_id, doc, meta) in enumerate(zip(ids, docs, metas)):
        dist = dists[idx] if idx < len(dists) else None
        score = _score_from_distance(dist)
        if profile.score_threshold is not None and score is not None:
            if score < profile.score_threshold:
                continue
        filtered_ids.append(doc_id)
        filtered_docs.append(doc)
        filtered_metas.append(meta)
        filtered_dists.append(dist)
        filtered_scores.append(score)

    trimmed_ids = filtered_ids[: profile.top_k]
    trimmed_docs = filtered_docs[: profile.top_k]
    trimmed_metas = filtered_metas[: profile.top_k]
    trimmed_dists = filtered_dists[: profile.top_k]
    trimmed_scores = filtered_scores[: profile.top_k]

    return {
        "ids": [trimmed_ids],
        "documents": [trimmed_docs],
        "metadatas": [trimmed_metas],
        "distances": [trimmed_dists],
        "scores": [trimmed_scores],
    }


__all__ = [
    "RetrievalKind",
    "RetrievalProfile",
    "get_retrieval_profile",
    "apply_profile_to_chroma_results",
]

