from collections import Counter

from fastapi.testclient import TestClient


def test_debug_telemetry_recent_actions_and_buckets(client: TestClient, project: dict) -> None:
    seeds = [
        {"description": "auto add low", "action": "auto_added", "confidence": 0.2, "model": "gpt-4o-mini"},
        {"description": "auto complete mid", "action": "auto_completed", "confidence": 0.55, "model": "gpt-5.1"},
        {"description": "auto suggest high", "action": "auto_suggested", "confidence": 0.82, "model": "gpt-5.1-codex"},
    ]

    for seed in seeds:
        resp = client.post("/debug/seed_task_action", json={"project_id": project["id"], **seed})
        assert resp.status_code == 200, resp.text

    telemetry_resp = client.get("/debug/telemetry")
    assert telemetry_resp.status_code == 200, telemetry_resp.text
    payload = telemetry_resp.json()
    tasks = payload["tasks"]
    actions = tasks["recent_actions"]
    assert len(actions) == len(seeds)

    counts = Counter(a["action"] for a in actions)
    assert counts["auto_added"] == 1
    assert counts["auto_completed"] == 1
    assert counts["auto_suggested"] == 1
    sources = {a.get("source") for a in actions}
    assert sources == {"qa_seed"}

    models = {a.get("model") or (a.get("details") or {}).get("model") for a in actions}
    assert "gpt-4o-mini" in models
    assert "gpt-5.1" in models

    buckets = tasks["confidence_buckets"]
    assert buckets["lt_0_4"] == 1
    assert buckets["0_4_0_7"] == 1
    assert buckets["gte_0_7"] == 1

    reset_resp = client.get("/debug/telemetry?reset=true")
    assert reset_resp.status_code == 200
    reset_payload = reset_resp.json()
    assert reset_payload["tasks"].get("recent_actions", []) == []
    assert all(v == 0 for v in reset_payload["tasks"].values() if isinstance(v, int))

    after_reset = client.get("/debug/telemetry")
    assert after_reset.status_code == 200
    assert after_reset.json()["tasks"]["recent_actions"] == []


def test_conversation_usage_summary_has_records(client: TestClient, project: dict) -> None:
    convo_resp = client.post(
        "/conversations",
        json={"project_id": project["id"], "title": "Usage Conv"},
    )
    assert convo_resp.status_code == 200, convo_resp.text
    conversation_id = convo_resp.json()["id"]

    chat_resp = client.post(
        "/chat",
        json={
            "conversation_id": conversation_id,
            "message": "Hello usage tracker",
            "mode": "auto",
        },
    )
    assert chat_resp.status_code == 200, chat_resp.text

    usage_resp = client.get(f"/conversations/{conversation_id}/usage")
    assert usage_resp.status_code == 200, usage_resp.text
    usage = usage_resp.json()
    assert usage["conversation_id"] == conversation_id
    assert isinstance(usage["records"], list)
    assert len(usage["records"]) >= 1
    assert usage["records"][-1]["model"]

