from fastapi.testclient import TestClient


def _reset_telemetry(client: TestClient) -> None:
    resp = client.get("/debug/telemetry?reset=true")
    assert resp.status_code == 200, resp.text


def _create_conversation(client: TestClient, project: dict, title: str) -> int:
    resp = client.post("/conversations", json={"project_id": project["id"], "title": title})
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def test_auto_mode_routes_code_prompt(client: TestClient, project: dict) -> None:
    _reset_telemetry(client)
    conversation_id = _create_conversation(client, project, "code convo")

    message = "```python\nprint('hello world')\n```"
    chat_resp = client.post(
        "/chat",
        json={
            "conversation_id": conversation_id,
            "message": message,
            "mode": "auto",
        },
    )
    assert chat_resp.status_code == 200, chat_resp.text

    telemetry = client.get("/debug/telemetry").json()
    llm = telemetry["llm"]
    assert llm["auto_routes"].get("code") == 1
    latest = llm.get("latest_auto_route") or {}
    assert latest.get("route") == "code"
    assert "code" in (latest.get("reason") or "").lower()

    usage = client.get(f"/conversations/{conversation_id}/usage").json()
    assert usage.get("auto_reason")
    assert "code" in usage["auto_reason"].lower() or "patch" in usage["auto_reason"].lower()


def test_auto_mode_routes_fast_for_task_updates(client: TestClient, project: dict) -> None:
    _reset_telemetry(client)
    conversation_id = _create_conversation(client, project, "tasks convo")

    message = "Todo: update the login task status and priority."
    chat_resp = client.post(
        "/chat",
        json={
            "conversation_id": conversation_id,
            "message": message,
            "mode": "auto",
        },
    )
    assert chat_resp.status_code == 200, chat_resp.text

    telemetry = client.get("/debug/telemetry").json()
    llm = telemetry["llm"]
    assert llm["auto_routes"].get("fast") == 1
    latest = llm.get("latest_auto_route") or {}
    assert latest.get("route") == "fast"
    assert "short" in (latest.get("reason") or "").lower()


def test_auto_mode_routes_deep_for_long_context(client: TestClient, project: dict) -> None:
    _reset_telemetry(client)
    conversation_id = _create_conversation(client, project, "deep convo")

    long_message = "\n".join(
        [
            "Here is the status update for multiple workstreams:",
            "backend auth refactor needs a timeline and rollback plan.",
            "docs ingestion needs a multi-step approach and design notes.",
            "memory sync and retrieval require coordination across services.",
            "please consider risks, milestones, and coordination steps.",
            "include a plan for verification and telemetry rollouts.",
            "also keep track of file changes and staging deployment notes.",
            "finalize the checklist for the upcoming release.",
        ]
    )

    chat_resp = client.post(
        "/chat",
        json={
            "conversation_id": conversation_id,
            "message": long_message,
            "mode": "auto",
        },
    )
    assert chat_resp.status_code == 200, chat_resp.text

    telemetry = client.get("/debug/telemetry").json()
    llm = telemetry["llm"]
    latest = llm.get("latest_auto_route") or {}
    assert latest.get("route") == "deep"
    reason = (latest.get("reason") or "").lower()
    assert "long" in reason or "multi-paragraph" in reason or "plan" in reason

