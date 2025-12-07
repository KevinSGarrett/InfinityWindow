"""
Noisy chat → tasks regression:
- ensures dedupe/completion still work when conversation includes unrelated chatter
"""

from __future__ import annotations


def test_chat_tasks_noisy_conversation(client, project):
    """B-Tasks-Noisy: chat adds tasks even with noise; completes one correctly."""
    convo = client.post(
        "/chat",
        json={
            "project_id": project["id"],
            "message": (
                "Random chit-chat before the TODOs. Also weather is great.\n"
                "Action items:\n"
                "- Finish the payment retry flow\n"
                "- Document the new API responses\n"
                "By the way, have you seen the latest movie trailer?"
            ),
        },
    ).json()
    convo_id = convo["conversation_id"]

    tasks = client.get(f"/projects/{project['id']}/tasks").json()
    descs = [t["description"].lower() for t in tasks]
    assert any("payment retry flow" in d for d in descs), "Missing payment task"
    assert any("document the new api responses" in d for d in descs), "Missing docs task"
    payment_task = next((t for t in tasks if "payment retry flow" in t["description"].lower()), None)
    assert payment_task is not None
    assert payment_task.get("auto_confidence") is not None
    assert payment_task.get("auto_last_action") == "auto_added"

    # Follow-up completion with more noise
    client.post(
        "/chat",
        json={
            "conversation_id": convo_id,
            "project_id": project["id"],
            "message": (
                "Side note: I had lunch. Anyway, the payment retry flow is done. "
                "Docs work is still pending."
            ),
        },
    )

    refreshed = client.get(f"/projects/{project['id']}/tasks").json()
    done = [t for t in refreshed if t["status"] == "done"]
    open_tasks = [t for t in refreshed if t["status"] == "open"]
    assert any("payment retry flow" in t["description"].lower() for t in done), "Payment should be done"
    assert any("document the new api responses" in t["description"].lower() for t in open_tasks), "Docs should remain open"
    payment_done = next((t for t in done if "payment retry flow" in t["description"].lower()), None)
    assert payment_done is not None
    assert payment_done.get("auto_last_action") == "auto_completed"
    assert payment_done.get("auto_confidence") is not None

