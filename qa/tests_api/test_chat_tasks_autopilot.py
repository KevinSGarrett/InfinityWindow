"""
End-to-end chat → tasks automation:
- auto-adds tasks after chat
- auto-completes tasks after a follow-up message
"""

from __future__ import annotations


def test_chat_auto_add_and_complete(client, project):
    """B-Tasks-E2E: chat creates tasks, then marks one done on follow-up."""
    # First chat: seed TODOs
    resp = client.post(
        "/chat",
        json={
            "project_id": project["id"],
            "message": "We need to add a login page and fix the logout bug soon.",
        },
    )
    assert resp.status_code == 200, resp.text
    convo_id = resp.json()["conversation_id"]

    # Tasks should be auto-added after chat hook runs
    tasks_resp = client.get(f"/projects/{project['id']}/tasks")
    assert tasks_resp.status_code == 200, tasks_resp.text
    tasks = tasks_resp.json()
    descriptions = [t["description"].lower() for t in tasks]
    assert any("login page" in d for d in descriptions), "Expected login page task"
    assert any("logout" in d for d in descriptions), "Expected logout bug task"
    login_task = next((t for t in tasks if "login page" in t["description"].lower()), None)
    assert login_task is not None
    assert login_task.get("auto_confidence") is not None
    assert login_task.get("auto_last_action") == "auto_added"

    # Second chat: mark one task as complete
    resp2 = client.post(
        "/chat",
        json={
            "conversation_id": convo_id,
            "project_id": project["id"],
            "message": "The login page task is done now.",
        },
    )
    assert resp2.status_code == 200, resp2.text

    # Refresh tasks: one should be done, the other still open
    tasks_after = client.get(f"/projects/{project['id']}/tasks").json()
    done = [t for t in tasks_after if t["status"] == "done"]
    open_tasks = [t for t in tasks_after if t["status"] == "open"]
    assert any("login page" in t["description"].lower() for t in done), "Login page should be done"
    assert any("logout" in t["description"].lower() for t in open_tasks), "Logout bug should remain open"
    completed_login = next((t for t in done if "login page" in t["description"].lower()), None)
    assert completed_login is not None
    assert completed_login.get("auto_last_action") == "auto_completed"
    assert completed_login.get("auto_confidence") is not None

