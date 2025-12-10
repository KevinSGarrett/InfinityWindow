from fastapi.testclient import TestClient


def _seed_retrieval_surfaces(client: TestClient, project_id: int) -> None:
    client.post(
        f"/projects/{project_id}/docs/text",
        json={
            "name": "Telemetry Doc",
            "text": "Telemetry doc chunk one. Another chunk about retrieval context shaping.",
        },
    )
    client.post(
        f"/projects/{project_id}/memory",
        json={
            "title": "Telemetry plan",
            "content": "Track retrieval calls per surface for tuning.",
            "tags": ["telemetry"],
            "pinned": False,
        },
    )


def test_retrieval_telemetry_in_debug_endpoint(
    client: TestClient, project: dict
) -> None:
    project_id = project["id"]
    _seed_retrieval_surfaces(client, project_id)

    chat1 = client.post(
        "/chat",
        json={"project_id": project_id, "message": "First retrieval telemetry run."},
    )
    assert chat1.status_code == 200, chat1.text
    conversation_id = chat1.json()["conversation_id"]

    chat2 = client.post(
        "/chat",
        json={
            "conversation_id": conversation_id,
            "message": "Second run to build telemetry stats.",
        },
    )
    assert chat2.status_code == 200, chat2.text

    telemetry_resp = client.get("/debug/telemetry")
    assert telemetry_resp.status_code == 200, telemetry_resp.text
    payload = telemetry_resp.json()
    retrieval = payload["retrieval"]

    for kind in ("messages", "docs", "memory"):
        assert retrieval[kind]["total_calls"] >= 1
        assert retrieval[kind]["average_requested_top_k"] >= 1
        assert retrieval[kind]["average_returned"] >= 0

