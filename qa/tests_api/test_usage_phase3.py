from fastapi.testclient import TestClient


def _seed(client: TestClient, project_id: int) -> int:
    client.post(
        f"/projects/{project_id}/docs/text",
        json={"name": "Phase3 Doc", "text": "phase 3 usage telemetry doc content."},
    )
    client.post(
        f"/projects/{project_id}/memory",
        json={"title": "Phase3 memory", "content": "phase3 retrieval memory"},
    )
    resp = client.post(
        "/chat",
        json={"project_id": project_id, "message": "kick off phase3 usage"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["conversation_id"]


def test_retrieval_telemetry_reset_via_debug_endpoint(
    client: TestClient, project: dict
) -> None:
    project_id = project["id"]
    _seed(client, project_id)

    resp = client.get("/debug/telemetry")
    assert resp.status_code == 200, resp.text
    snapshot = resp.json()["retrieval"]
    for kind in ("messages", "docs", "memory"):
        assert snapshot[kind]["total_calls"] >= 1

    reset = client.get("/debug/telemetry?reset=true")
    assert reset.status_code == 200, reset.text
    reset_payload = reset.json()["retrieval"]
    for kind in ("messages", "docs", "memory"):
        assert reset_payload[kind]["total_calls"] == 0

