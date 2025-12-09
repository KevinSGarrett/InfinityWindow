from __future__ import annotations

from typing import Iterable, Optional


def _find_task(tasks: Iterable[dict], phrase: str) -> Optional[dict]:
    needle = phrase.lower()
    return next((t for t in tasks if needle in t["description"].lower()), None)


def _get_tasks_telemetry(client) -> dict:
    return client.get("/debug/telemetry").json()["tasks"]


def _find_action(actions: Iterable[dict], task_id: int, action: str) -> Optional[dict]:
    return next(
        (
            entry
            for entry in actions
            if entry.get("task_id") == task_id and entry.get("action") == action
        ),
        None,
    )


def test_manual_close_adds_audit_note_and_telemetry_entry(client, project):
    create_resp = client.post(
        f"/projects/{project['id']}/tasks",
        json={"description": "Write release notes for sprint"},
    )
    assert create_resp.status_code == 200, create_resp.text
    task = create_resp.json()

    close_resp = client.patch(f"/tasks/{task['id']}", json={"status": "done"})
    assert close_resp.status_code == 200, close_resp.text
    closed_task = close_resp.json()

    assert closed_task["status"] == "done"
    notes = closed_task.get("auto_notes") or ""
    assert "Closed manually" in notes

    telemetry = _get_tasks_telemetry(client)
    actions = telemetry["recent_actions"]
    manual_event = _find_action(actions, closed_task["id"], "manual_completed")
    assert manual_event is not None, "Expected manual_completed telemetry entry"
    assert manual_event.get("task_description") == closed_task["description"]
    assert manual_event.get("task_status") == "done"
    assert "Closed manually" in (manual_event.get("task_auto_notes") or "")
    assert manual_event.get("source") == "manual_update"
    assert telemetry.get("manual_completed") == 1


def test_manual_close_does_not_break_auto_audit(client, project):
    convo_resp = client.post(
        "/chat",
        json={
            "project_id": project["id"],
            "message": "We need to add a login page and fix the logout bug soon.",
        },
    )
    assert convo_resp.status_code == 200, convo_resp.text
    convo_id = convo_resp.json()["conversation_id"]

    second = client.post(
        "/chat",
        json={
            "conversation_id": convo_id,
            "project_id": project["id"],
            "message": "The login page task is done now; logout bug still pending.",
        },
    )
    assert second.status_code == 200, second.text

    tasks = client.get(f"/projects/{project['id']}/tasks").json()
    login_task = _find_task(tasks, "login page")
    assert login_task is not None

    telemetry_before = _get_tasks_telemetry(client)
    auto_event = _find_action(
        telemetry_before["recent_actions"], login_task["id"], "auto_completed"
    )
    assert auto_event is not None, "Expected auto_completed telemetry for login task"
    assert auto_event.get("task_description") == login_task["description"]
    assert auto_event.get("source") == "auto_conversation"

    manual_create = client.post(
        f"/projects/{project['id']}/tasks",
        json={"description": "Archive old billing reports"},
    )
    assert manual_create.status_code == 200, manual_create.text
    manual_task = manual_create.json()

    manual_close = client.patch(f"/tasks/{manual_task['id']}", json={"status": "done"})
    assert manual_close.status_code == 200, manual_close.text
    closed_manual = manual_close.json()
    assert closed_manual["status"] == "done"

    telemetry_after = _get_tasks_telemetry(client)
    manual_event = _find_action(
        telemetry_after["recent_actions"], manual_task["id"], "manual_completed"
    )
    assert manual_event is not None, "Expected manual_completed telemetry entry"
    assert "Closed manually" in (manual_event.get("task_auto_notes") or "")
    assert manual_event.get("source") == "manual_update"
    assert telemetry_after.get("manual_completed") == 1

    auto_event_after = _find_action(
        telemetry_after["recent_actions"], login_task["id"], "auto_completed"
    )
    assert auto_event_after is not None, "Auto telemetry should remain after manual actions"
    assert auto_event_after.get("task_description") == login_task["description"]
    assert auto_event_after.get("source") == "auto_conversation"

