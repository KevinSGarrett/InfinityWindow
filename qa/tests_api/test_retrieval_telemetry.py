from fastapi.testclient import TestClient


def test_chat_retrieval_counters_increment(client: TestClient, project: dict) -> None:
    seed_resp = client.post(
        "/chat",
        json={
            "project_id": project["id"],
            "message": "Seed chat so retrieval has history.",
        },
    )
    assert seed_resp.status_code == 200, seed_resp.text
    conversation_id = seed_resp.json()["conversation_id"]

    reset_resp = client.get("/debug/telemetry?reset=true")
    assert reset_resp.status_code == 200, reset_resp.text
    baseline = reset_resp.json().get("retrieval", {})

    chat_resp = client.post(
        "/chat",
        json={
            "project_id": project["id"],
            "conversation_id": conversation_id,
            "message": "Follow up to trigger retrieval hits.",
        },
    )
    assert chat_resp.status_code == 200, chat_resp.text

    telemetry_resp = client.get("/debug/telemetry")
    assert telemetry_resp.status_code == 200, telemetry_resp.text
    retrieval = telemetry_resp.json().get("retrieval", {})
    chat_keys = [key for key in retrieval if key.startswith("chat_")]
    assert chat_keys, "Expected chat retrieval keys in telemetry."
    assert any(
        retrieval.get(key, 0) > baseline.get(key, 0) for key in chat_keys
    ), f"Retrieval counters did not increase: {retrieval}"


def test_search_retrieval_counters_increment(client: TestClient, project: dict) -> None:
    seed_resp = client.post(
        "/chat",
        json={
            "project_id": project["id"],
            "message": "Index this chat for message search.",
        },
    )
    assert seed_resp.status_code == 200, seed_resp.text

    reset_resp = client.get("/debug/telemetry?reset=true")
    assert reset_resp.status_code == 200, reset_resp.text
    baseline = reset_resp.json().get("retrieval", {})

    search_resp = client.post(
        "/search/messages",
        json={
            "project_id": project["id"],
            "query": "message search",
            "limit": 3,
        },
    )
    assert search_resp.status_code == 200, search_resp.text
    assert search_resp.json()["hits"], "Expected search to return at least one hit."

    telemetry_resp = client.get("/debug/telemetry")
    assert telemetry_resp.status_code == 200, telemetry_resp.text
    retrieval = telemetry_resp.json().get("retrieval", {})
    assert retrieval.get("search_messages_hits", 0) > baseline.get(
        "search_messages_hits", 0
    ), f"Search retrieval counter did not increase: {retrieval}"


def test_retrieval_telemetry_reset_behavior(client: TestClient, project: dict) -> None:
    first_chat = client.post(
        "/chat",
        json={
            "project_id": project["id"],
            "message": "Start conversation for telemetry reset.",
        },
    )
    assert first_chat.status_code == 200, first_chat.text
    conversation_id = first_chat.json()["conversation_id"]

    follow_up = client.post(
        "/chat",
        json={
            "project_id": project["id"],
            "conversation_id": conversation_id,
            "message": "Second message to generate retrieval hits.",
        },
    )
    assert follow_up.status_code == 200, follow_up.text

    before_reset = client.get("/debug/telemetry")
    assert before_reset.status_code == 200, before_reset.text
    retrieval_before = before_reset.json().get("retrieval", {})
    assert any(
        value > 0 for value in retrieval_before.values()
    ), "Expected retrieval counters to be non-zero before reset."

    reset_resp = client.get("/debug/telemetry?reset=true")
    assert reset_resp.status_code == 200, reset_resp.text
    retrieval_reset = reset_resp.json().get("retrieval", {})
    assert all(
        value == 0 for value in retrieval_reset.values()
    ), f"Reset response should zero retrieval counters: {retrieval_reset}"

    after_reset = client.get("/debug/telemetry")
    assert after_reset.status_code == 200, after_reset.text
    retrieval_after = after_reset.json().get("retrieval", {})
    assert all(
        value == 0 for value in retrieval_after.values()
    ), f"Retrieval counters should remain zero after reset: {retrieval_after}"
