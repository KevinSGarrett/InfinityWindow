"""
Noisy chat → tasks regression:
- ensures dedupe/completion still work when conversation includes unrelated chatter
"""

from __future__ import annotations


def _find_task(tasks: list[dict], phrase: str) -> dict | None:
    needle = phrase.lower()
    return next((t for t in tasks if needle in t["description"].lower()), None)


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


def test_chat_tasks_long_history_prefers_latest_completion_signal(client, project):
    """B-Tasks-Noisy-Long: prefer latest completion, respect pending cues."""
    convo = client.post(
        "/chat",
        json={
            "project_id": project["id"],
            "message": (
                "Action items: finish the payment retry flow and document the new API responses.\n"
                "Reminder: keep the conversation focused even with random chatter."
            ),
        },
    ).json()
    convo_id = convo["conversation_id"]

    # Early update says work is NOT done yet.
    client.post(
        "/chat",
        json={
            "conversation_id": convo_id,
            "project_id": project["id"],
            "message": "Quick note: payment retry flow is not done yet; docs also not done.",
        },
    )
    open_snapshot = client.get(f"/projects/{project['id']}/tasks").json()
    payment_task = _find_task(open_snapshot, "payment retry flow")
    docs_task = _find_task(open_snapshot, "api responses")
    assert payment_task is not None and docs_task is not None
    assert payment_task["status"] == "open"
    assert docs_task["status"] == "open"

    # Latest update closes only the truly finished work.
    client.post(
        "/chat",
        json={
            "conversation_id": convo_id,
            "project_id": project["id"],
            "message": (
                "Update: payment retry flow is done; docs work still pending and logout bug remains."
            ),
        },
    )
    refreshed = client.get(f"/projects/{project['id']}/tasks").json()
    payment_done = _find_task(refreshed, "payment retry flow")
    docs_pending = _find_task(refreshed, "api responses")
    assert payment_done is not None and docs_pending is not None
    assert payment_done["status"] == "done"
    assert docs_pending["status"] == "open"

    telemetry = client.get("/debug/telemetry").json()["tasks"]["recent_actions"]
    assert any(
        action.get("task_id") == payment_done["id"] and action.get("action") == "auto_completed"
        for action in telemetry
    )
    assert not any(
        action.get("task_id") == docs_pending["id"] and action.get("action") == "auto_completed"
        for action in telemetry
    )


def test_chat_tasks_ignores_pure_chatter(client, project):
    """B-Tasks-Noisy-Chatter: avoid creating tasks from non-actionable noise."""
    client.post(
        "/chat",
        json={
            "project_id": project["id"],
            "message": "Thanks team, weather is nice and let's sync tomorrow with no tasks listed here.",
        },
    )
    tasks = client.get(f"/projects/{project['id']}/tasks").json()
    assert tasks == []
    telemetry = client.get("/debug/telemetry").json()["tasks"]["recent_actions"]
    assert telemetry == []

