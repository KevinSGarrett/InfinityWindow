import pytest

import app.api.main as main
import app.api.search as search
from app import retrieval_config


_ENV_KEYS = (
    "IW_RETRIEVAL_MESSAGES_K",
    "IW_RETRIEVAL_DOCS_K",
    "IW_RETRIEVAL_MEMORY_K",
    "IW_RETRIEVAL_TASKS_K",
)


def _clear_retrieval_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def _empty_result() -> dict:
    return {
        "ids": [[]],
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
    }


def test_debug_retrieval_config_defaults(client, monkeypatch):
    _clear_retrieval_env(monkeypatch)

    resp = client.get("/debug/retrieval_config")
    assert resp.status_code == 200
    body = resp.json()

    assert body["profile"] == {
        "messages_k": retrieval_config.DEFAULT_PROFILE.messages_k,
        "docs_k": retrieval_config.DEFAULT_PROFILE.docs_k,
        "memory_k": retrieval_config.DEFAULT_PROFILE.memory_k,
        "tasks_k": retrieval_config.DEFAULT_PROFILE.tasks_k,
    }
    assert body["source"] == "defaults"


def test_debug_retrieval_config_env_overrides(client, monkeypatch):
    overrides = {
        "IW_RETRIEVAL_MESSAGES_K": "2",
        "IW_RETRIEVAL_DOCS_K": "7",
        "IW_RETRIEVAL_MEMORY_K": "4",
        # 0 should clamp up to the minimum.
        "IW_RETRIEVAL_TASKS_K": "0",
    }
    _clear_retrieval_env(monkeypatch)
    for key, value in overrides.items():
        monkeypatch.setenv(key, value)

    resp = client.get("/debug/retrieval_config")
    assert resp.status_code == 200
    body = resp.json()

    assert body["profile"] == {
        "messages_k": 2,
        "docs_k": 7,
        "memory_k": 4,
        "tasks_k": 1,
    }
    assert body["source"] == "env_with_defaults"


def test_search_uses_profile_defaults(client, project, monkeypatch):
    profile = retrieval_config.RetrievalProfile(
        messages_k=2,
        docs_k=3,
        memory_k=4,
        tasks_k=5,
    )
    monkeypatch.setattr(retrieval_config, "get_retrieval_profile", lambda env=None: profile)

    calls: dict[str, int] = {}

    def fake_messages(*, n_results: int, **kwargs):
        calls["messages"] = n_results
        return _empty_result()

    def fake_docs(*, n_results: int, **kwargs):
        calls["docs"] = n_results
        return _empty_result()

    def fake_memory(*, n_results: int, **kwargs):
        calls["memory"] = n_results
        return _empty_result()

    monkeypatch.setattr(search, "query_similar_messages", fake_messages)
    monkeypatch.setattr(search, "query_similar_document_chunks", fake_docs)
    monkeypatch.setattr(search, "query_similar_memory_items", fake_memory)

    resp_msg = client.post(
        "/search/messages",
        json={"project_id": project["id"], "query": "hello"},
    )
    resp_doc = client.post(
        "/search/docs",
        json={"project_id": project["id"], "query": "hello"},
    )
    resp_mem = client.post(
        "/search/memory",
        json={"project_id": project["id"], "query": "hello"},
    )

    assert resp_msg.status_code == 200
    assert resp_doc.status_code == 200
    assert resp_mem.status_code == 200

    assert calls["messages"] == profile.messages_k
    assert calls["docs"] == profile.docs_k
    assert calls["memory"] == profile.memory_k


def test_chat_retrieval_uses_profile(client, project, monkeypatch):
    profile = retrieval_config.RetrievalProfile(
        messages_k=3,
        docs_k=2,
        memory_k=4,
        tasks_k=6,
    )
    monkeypatch.setattr(retrieval_config, "get_retrieval_profile", lambda env=None: profile)

    calls: dict[str, int] = {}

    def fake_messages(*, n_results: int, **kwargs):
        calls["messages"] = n_results
        return _empty_result()

    def fake_docs(*, n_results: int, **kwargs):
        calls["docs"] = n_results
        return _empty_result()

    def fake_memory(*, n_results: int, **kwargs):
        calls["memory"] = n_results
        return _empty_result()

    monkeypatch.setattr(main, "query_similar_messages", fake_messages)
    monkeypatch.setattr(main, "query_similar_document_chunks", fake_docs)
    monkeypatch.setattr(main, "query_similar_memory_items", fake_memory)

    resp = client.post(
        "/chat",
        json={"project_id": project["id"], "message": "hello from qa"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "conversation_id" in body

    assert calls["messages"] == profile.messages_k
    assert calls["docs"] == profile.docs_k
    assert calls["memory"] == profile.memory_k
