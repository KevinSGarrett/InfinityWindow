from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RetrievalKind(str, Enum):
    """
    Supported retrieval profile types.

    Phase 0 covers messages/docs/memory; tasks is reserved for future use.
    """

    DEFAULT = "default"
    MESSAGES = "messages"
    DOCS = "docs"
    MEMORY = "memory"
    TASKS = "tasks"


@dataclass
class RetrievalProfile:
    top_k: int
    score_threshold: Optional[float] = None


_DEFAULT_PROFILES = {
    RetrievalKind.DEFAULT.value: RetrievalProfile(top_k=5),
    RetrievalKind.MESSAGES.value: RetrievalProfile(top_k=5),
    RetrievalKind.DOCS.value: RetrievalProfile(top_k=5),
    RetrievalKind.MEMORY.value: RetrievalProfile(top_k=5),
    RetrievalKind.TASKS.value: RetrievalProfile(top_k=5),
}


def _env_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        value = int(raw)
        if value > 0:
            return value
    except ValueError:
        pass
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
    """
    Return a retrieval profile for the given kind, applying optional env overrides:
    - RETRIEVAL_<KIND>_TOP_K (int > 0)
    - RETRIEVAL_<KIND>_SCORE_THRESHOLD (float)

    Unknown kinds fall back to DEFAULT.
    """
    normalized = (kind.value if isinstance(kind, RetrievalKind) else str(kind or "")).lower()
    base = _DEFAULT_PROFILES.get(normalized, _DEFAULT_PROFILES[RetrievalKind.DEFAULT.value])

    prefix = normalized.upper()
    top_k = _env_int(f"RETRIEVAL_{prefix}_TOP_K", base.top_k)
    score_threshold = _env_float(f"RETRIEVAL_{prefix}_SCORE_THRESHOLD", base.score_threshold)

    return RetrievalProfile(top_k=top_k, score_threshold=score_threshold)


