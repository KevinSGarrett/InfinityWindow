from fastapi.testclient import TestClient


def _create_doc(client: TestClient, project_id: int) -> int:
    resp = client.post(
        f"/projects/{project_id}/docs/text",
        json={
            "name": "Requirements CRM",
            "text": "CRM requirements and onboarding checklist.",
            "description": "Test doc",
        },
    )
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    return payload["document"]["id"]


def _create_memory(client: TestClient, project_id: int) -> None:
    resp = client.post(
        f"/projects/{project_id}/memory",
        json={
            "title": "Important decision",
            "content": "Use retrieval telemetry to tune context windows.",
            "tags": ["retrieval", "decision"],
            "pinned": False,
        },
    )
    assert resp.status_code == 200, resp.text


def test_retrieval_debug_endpoint(client: TestClient, project: dict) -> None:
    project_id = project["id"]
    _create_doc(client, project_id)
    _create_memory(client, project_id)

    # First chat seeds embeddings for later retrieval; second call exercises retrieval.
    first_chat = client.post(
        "/chat",
        json={"project_id": project_id, "message": "Seed retrieval context."},
    )
    assert first_chat.status_code == 200, first_chat.text
    conversation_id = first_chat.json()["conversation_id"]

    followup = client.post(
        "/chat",
        json={
            "conversation_id": conversation_id,
            "message": "What did we decide about telemetry and docs?",
        },
    )
    assert followup.status_code == 200, followup.text

    resp = client.get(f"/conversations/{conversation_id}/debug/retrieval_context")
    assert resp.status_code == 200, resp.text

    payload = resp.json()
    assert payload["conversation_id"] == conversation_id
    assert payload.get("message_id")

    profiles = payload["profiles"]
    assert profiles["messages"]["top_k"] >= 1
    assert profiles["docs"]["top_k"] >= 1
    assert profiles["memory"]["top_k"] >= 1

    assert isinstance(payload["messages"], list)
    assert isinstance(payload["docs"], list)
    assert isinstance(payload["memory"], list)
    assert payload["messages"], "expected at least one retrieved message"
    assert payload["docs"], "expected at least one retrieved doc chunk"
    assert payload["memory"], "expected at least one retrieved memory item"
    assert payload.get("retrieval_context_text", "") != ""

