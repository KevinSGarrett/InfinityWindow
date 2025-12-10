from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict

_DEFAULT_STATS = {"total_calls": 0, "total_requested_top_k": 0, "total_returned": 0}
_RETRIEVAL_TELEMETRY: Dict[str, Dict[str, int]] = defaultdict(
    lambda: dict(_DEFAULT_STATS)
)
# Pre-seed standard retrieval kinds so snapshots always expose the keys.
for _kind in ("messages", "docs", "memory", "tasks"):
    _RETRIEVAL_TELEMETRY[_kind]


def record_retrieval_event(
    kind: str, requested_top_k: int, returned_count: int
) -> None:
    stats = _RETRIEVAL_TELEMETRY[kind]
    stats["total_calls"] = stats.get("total_calls", 0) + 1
    stats["total_requested_top_k"] = stats.get("total_requested_top_k", 0) + max(
        0, int(requested_top_k or 0)
    )
    stats["total_returned"] = stats.get("total_returned", 0) + max(
        0, int(returned_count or 0)
    )


def _with_averages(stats: Dict[str, int]) -> Dict[str, Any]:
    calls = stats.get("total_calls", 0)
    avg_top_k = 0.0
    avg_returned = 0.0
    if calls:
        avg_top_k = stats.get("total_requested_top_k", 0) / calls
        avg_returned = stats.get("total_returned", 0) / calls
    snapshot = dict(stats)
    snapshot["average_requested_top_k"] = round(avg_top_k, 3)
    snapshot["average_returned"] = round(avg_returned, 3)
    return snapshot


def get_retrieval_telemetry(reset: bool = False) -> Dict[str, Any]:
    snapshot = {kind: _with_averages(stats) for kind, stats in _RETRIEVAL_TELEMETRY.items()}
    if reset:
        reset_retrieval_telemetry()
        if snapshot:
            snapshot = {
                kind: _with_averages(dict(_DEFAULT_STATS)) for kind in snapshot.keys()
            }
    return snapshot


def reset_retrieval_telemetry() -> None:
    _RETRIEVAL_TELEMETRY.clear()
    for _kind in ("messages", "docs", "memory", "tasks"):
        _RETRIEVAL_TELEMETRY[_kind]


__all__ = [
    "get_retrieval_telemetry",
    "record_retrieval_event",
    "reset_retrieval_telemetry",
]

