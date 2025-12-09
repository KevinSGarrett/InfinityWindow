from __future__ import annotations

from typing import Dict, Optional


def _find_action(actions: list[Dict], task_id: int, action: str) -> Optional[Dict]:
    return next(
        (a for a in actions if a.get("task_id") == task_id and a.get("action") == action),
        None,
    )


def _get_recent_actions(client) -> list[Dict]:
    return client.get("/debug/telemetry").json()["tasks"]["recent_actions"]


def test_manual_close_records_source(client, project):
    create_resp = client.post(
        f"/projects/{project['id']}/tasks",
        json={"description": "Manually track this task", "priority": "high"},
    )
    assert create_resp.status_code == 200, create_resp.text
    task = create_resp.json()

    update_resp = client.patch(f"/tasks/{task['id']}", json={"status": "done"})
    assert update_resp.status_code == 200, update_resp.text

    actions = _get_recent_actions(client)
    manual_event = _find_action(actions, task["id"], "manual_completed")
    assert manual_event is not None, "Expected manual completion telemetry entry"
    assert manual_event.get("source") == "manual_update"
    assert manual_event.get("task_status") == "done"
    changes = (manual_event.get("details") or {}).get("changes") or {}
    assert changes.get("status", {}).get("after") == "done"

