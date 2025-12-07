"""
Chat routing and mode handling with stubbed LLM responses.
"""


def test_chat_modes_stubbed(client, project):
    """C-Chat-02: Chat returns stubbed replies for each mode."""
    for mode in ["auto", "fast", "deep", "budget", "research", "code"]:
        resp = client.post(
            "/chat",
            json={
                "project_id": project["id"],
                "mode": mode,
                "message": f"ping {mode}",
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "stub" in body["reply"]
        assert body["conversation_id"] > 0


def test_chat_requires_message(client, project):
    """C-Chat-03: Validation rejects missing message body."""
    resp = client.post("/chat", json={"project_id": project["id"]})
    assert resp.status_code == 422


def test_chat_conversation_reuse(client, project):
    """C-Chat-04: Subsequent calls reuse conversation_id."""
    first = client.post(
        "/chat",
        json={"project_id": project["id"], "message": "first", "mode": "auto"},
    ).json()
    second = client.post(
        "/chat",
        json={
            "conversation_id": first["conversation_id"],
            "message": "follow up",
            "mode": "fast",
        },
    ).json()
    assert second["conversation_id"] == first["conversation_id"]

