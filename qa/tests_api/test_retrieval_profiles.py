from __future__ import annotations

from app.context.retrieval_strategies import (
    get_retrieval_profile,
    RetrievalKind,
)


def test_retrieval_profile_defaults(monkeypatch):
    monkeypatch.delenv("RETRIEVAL_DOCS_TOP_K", raising=False)
    profile = get_retrieval_profile(RetrievalKind.DOCS)
    assert profile.top_k == 5
    assert profile.score_threshold is None


def test_retrieval_profile_env_overrides(monkeypatch):
    monkeypatch.setenv("RETRIEVAL_MEMORY_TOP_K", "2")
    monkeypatch.setenv("RETRIEVAL_MEMORY_SCORE_THRESHOLD", "0.42")
    profile = get_retrieval_profile("memory")
    assert profile.top_k == 2
    assert profile.score_threshold == 0.42


def test_retrieval_profile_unknown_falls_back(monkeypatch):
    monkeypatch.delenv("RETRIEVAL_UNKNOWN_TOP_K", raising=False)
    fallback = get_retrieval_profile(RetrievalKind.DEFAULT)
    profile = get_retrieval_profile("unknown-kind")
    assert profile.top_k == fallback.top_k
    assert profile.score_threshold == fallback.score_threshold


