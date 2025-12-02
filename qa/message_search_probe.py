from __future__ import annotations

import time
from typing import Any, Dict

from ._utils import ensure_backend_on_path, temporary_attr

ensure_backend_on_path()

from fastapi.testclient import TestClient  # noqa: E402

import app.api.main as main_module  # noqa: E402
from app.api.main import app  # noqa: E402
from app.llm import embeddings, openai_client  # noqa: E402


def _fake_embedding(text: str) -> list[float]:
    base = (len(text) % 17) / 10.0
    return [base] * 1536


def _fake_reply(messages: list[Dict[str, str]], **_: Any) -> str:
    return "FAKE-RESPONSE"


def run() -> None:
    """Insert a unique token via /chat and confirm /search/messages finds it."""
    client = TestClient(app)
    unique = f"QA_SMOKE_TOKEN_{int(time.time())}"
    project_name = f"QA Message Probe {unique}"

    with temporary_attr(embeddings, "get_embedding", _fake_embedding), temporary_attr(
        openai_client, "generate_reply_from_history", _fake_reply
    ), temporary_attr(main_module, "generate_reply_from_history", _fake_reply), temporary_attr(
        main_module, "auto_update_tasks_from_conversation", lambda *args, **kwargs: None
    ):
        project_resp = client.post("/projects", json={"name": project_name})
        project_resp.raise_for_status()
        project = project_resp.json()

        chat_resp = client.post(
            "/chat",
            json={
                "project_id": project["id"],
                "message": f"Testing search token {unique}",
            },
        )
        chat_resp.raise_for_status()

        search_resp = client.post(
            "/search/messages",
            json={
                "project_id": project["id"],
                "query": unique,
                "limit": 5,
            },
        )
        search_resp.raise_for_status()
        hits = search_resp.json()["hits"]

        if not hits:
            raise AssertionError("Message search returned no hits.")

        if not any(unique in hit.get("content", "") for hit in hits):
            raise AssertionError("Unique token missing from search hits.")

