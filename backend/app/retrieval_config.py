from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping, Tuple

# Caps to prevent extreme or negative values from misconfigured envs.
_MIN_K = 1
_MAX_K = 50


@dataclass(frozen=True)
class RetrievalProfile:
    messages_k: int
    docs_k: int
    memory_k: int
    tasks_k: int


# Defaults mirror the previous hard-coded behavior.
DEFAULT_PROFILE = RetrievalProfile(
    messages_k=5,
    docs_k=5,
    memory_k=5,
    tasks_k=5,
)

_ENV_MAP = {
    "messages_k": "IW_RETRIEVAL_MESSAGES_K",
    "docs_k": "IW_RETRIEVAL_DOCS_K",
    "memory_k": "IW_RETRIEVAL_MEMORY_K",
    "tasks_k": "IW_RETRIEVAL_TASKS_K",
}


def _parse_int(value: str | None, default: int) -> int:
    try:
        parsed = int(str(value)) if value is not None else default
    except (TypeError, ValueError):
        return default
    return parsed


def _clamp_k(value: int) -> int:
    return max(_MIN_K, min(_MAX_K, value))


def get_retrieval_profile(
    env: Mapping[str, str] | None = None,
) -> RetrievalProfile:
    """
    Build the active retrieval profile using environment overrides
    and safe defaults.
    """
    source_env = env or os.environ
    messages_k = _clamp_k(
        _parse_int(source_env.get(_ENV_MAP["messages_k"]), DEFAULT_PROFILE.messages_k)
    )
    docs_k = _clamp_k(
        _parse_int(source_env.get(_ENV_MAP["docs_k"]), DEFAULT_PROFILE.docs_k)
    )
    memory_k = _clamp_k(
        _parse_int(source_env.get(_ENV_MAP["memory_k"]), DEFAULT_PROFILE.memory_k)
    )
    tasks_k = _clamp_k(
        _parse_int(source_env.get(_ENV_MAP["tasks_k"]), DEFAULT_PROFILE.tasks_k)
    )
    return RetrievalProfile(
        messages_k=messages_k,
        docs_k=docs_k,
        memory_k=memory_k,
        tasks_k=tasks_k,
    )


def get_retrieval_profile_with_source(
    env: Mapping[str, str] | None = None,
) -> Tuple[RetrievalProfile, str]:
    """
    Return the active profile and a simple source indicator for diagnostics.
    """
    source_env = env or os.environ
    overrides_present = any(source_env.get(var) is not None for var in _ENV_MAP.values())
    source = "env_with_defaults" if overrides_present else "defaults"
    return get_retrieval_profile(source_env), source
