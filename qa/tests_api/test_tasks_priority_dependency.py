from __future__ import annotations

from typing import Iterable, Optional


def _find_task(tasks: Iterable[dict], phrase: str) -> Optional[dict]:
    needle = phrase.lower()
    return next((t for t in tasks if needle in t["description"].lower()), None)


def _get_recent_actions(client) -> list[dict]:
    return client.get("/debug/telemetry").json()["tasks"]["recent_actions"]


def _find_action(actions: Iterable[dict], task_id: int, action: str) -> Optional[dict]:
    return next(
        (
            entry
            for entry in actions
            if entry.get("task_id") == task_id and entry.get("action") == action
        ),
        None,
    )


def test_priority_high_for_urgent_prod_issue(client, project):
    message = (
        "Urgent prod incident: we need to add a login page; blocked on auth deploy; "
        "depends on billing service rollout."
    )
    seed = client.post(
        "/debug/seed_task_action",
        json={
            "project_id": project["id"],
            "description": message,
            "action": "auto_added",
            "confidence": 0.9,
        },
    )
    assert seed.status_code == 200, seed.text
    login_task = seed.json()
    assert login_task["priority"] in {"critical", "high"}
    assert login_task.get("blocked_reason")
    notes = (login_task.get("auto_notes") or "").lower()
    assert "blocked:" in notes
    assert "depends on" in notes

    telemetry = _get_recent_actions(client)
    entry = _find_action(telemetry, login_task["id"], "auto_added")
    assert entry is not None
    assert entry.get("task_priority") in {"critical", "high"}
    assert entry.get("task_blocked_reason")
    details = entry.get("details") or {}
    assert details.get("priority") in {"critical", "high"}
    assert details.get("blocked") is True
    assert details.get("blocked_reason")
    assert details.get("dependency_hint")


def test_priority_low_for_nice_to_have(client, project):
    message = "Nice to have later: add login page polish copy tweak for onboarding."
    seed = client.post(
        "/debug/seed_task_action",
        json={
            "project_id": project["id"],
            "description": message,
            "action": "auto_added",
            "confidence": 0.9,
        },
    )
    assert seed.status_code == 200, seed.text
    login_task = seed.json()
    assert login_task["priority"] == "low"

    telemetry = _get_recent_actions(client)
    entry = _find_action(telemetry, login_task["id"], "auto_added")
    assert entry is not None
    assert entry.get("task_priority") == "low"
    assert (entry.get("details") or {}).get("priority") == "low"


def test_priority_normal_for_neutral_task(client, project):
    message = "Please add a login page for the new user onboarding."
    seed = client.post(
        "/debug/seed_task_action",
        json={
            "project_id": project["id"],
            "description": message,
            "action": "auto_added",
            "confidence": 0.9,
        },
    )
    assert seed.status_code == 200, seed.text
    login_task = seed.json()
    assert login_task["priority"] == "normal"

    telemetry = _get_recent_actions(client)
    entry = _find_action(telemetry, login_task["id"], "auto_added")
    assert entry is not None
    assert entry.get("task_priority") == "normal"
    assert (entry.get("details") or {}).get("priority") == "normal"

