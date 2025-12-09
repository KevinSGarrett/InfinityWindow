from __future__ import annotations

import copy
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

from app.context.retrieval_strategies import (
    RetrievalKind,
    RetrievalProfile,
    apply_profile_to_chroma_results,
    get_retrieval_profile,
)


def _sample_results() -> Dict[str, Any]:
    return {
        "ids": [["1", "2"]],
        "documents": [["doc1", "doc2"]],
        "metadatas": [
            [
                {
                    "message_id": 1,
                    "conversation_id": 1,
                    "project_id": 1,
                    "role": "user",
                },
                {
                    "message_id": 2,
                    "conversation_id": 1,
                    "project_id": 1,
                    "role": "assistant",
                },
            ]
        ],
        "distances": [[0.1, 0.9]],
    }


def test_profile_defaults(monkeypatch):
    monkeypatch.delenv("RETRIEVAL_MESSAGES_TOP_K", raising=False)
    monkeypatch.delenv("RETRIEVAL_MESSAGES_SCORE_THRESHOLD", raising=False)
    profile = get_retrieval_profile(RetrievalKind.MESSAGES)
    assert profile.top_k == 5
    assert profile.score_threshold is None


def test_profile_env_overrides(monkeypatch):
    monkeypatch.setenv("RETRIEVAL_DOCS_TOP_K", "2")
    monkeypatch.setenv("RETRIEVAL_DOCS_SCORE_THRESHOLD", "0.42")
    profile = get_retrieval_profile("docs")
    assert profile.top_k == 2
    assert profile.score_threshold == 0.42


def test_apply_profile_filters_threshold_and_topk():
    profile = RetrievalProfile(top_k=1, score_threshold=0.5)
    results = apply_profile_to_chroma_results(profile, _sample_results())
    ids = results["ids"][0]
    dists = results["distances"][0]
    assert ids == ["1"]
    assert dists == [0.1]


def test_search_messages_respects_topk_and_threshold(monkeypatch, client: TestClient, project: dict):
    # Force top_k=1 and threshold that keeps only the first hit.
    monkeypatch.setenv("RETRIEVAL_MESSAGES_TOP_K", "1")
    monkeypatch.setenv("RETRIEVAL_MESSAGES_SCORE_THRESHOLD", "0.5")

    # Stub embedding + vectorstore query
    monkeypatch.setenv("LLM_MODE", "stub")
    monkeypatch.setenv("VECTORSTORE_MODE", "stub")

    def fake_get_embedding(_: str) -> List[float]:
        return [1.0, 0.0, 0.0]

    def fake_query_similar_messages(**_: Any) -> Dict[str, Any]:
        return copy.deepcopy(_sample_results())

    monkeypatch.setattr("app.api.search.get_embedding", fake_get_embedding)
    monkeypatch.setattr("app.api.search.query_similar_messages", fake_query_similar_messages)

    resp = client.post(
        "/search/messages",
        json={
            "project_id": project["id"],
            "query": "hello",
            "limit": 5,
        },
    )
    assert resp.status_code == 200, resp.text
    hits = resp.json()["hits"]
    assert len(hits) == 1
    assert hits[0]["content"] == "doc1"
    assert hits[0]["distance"] == pytest.approx(0.1)


