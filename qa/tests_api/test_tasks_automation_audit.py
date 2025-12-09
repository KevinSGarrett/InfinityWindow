from __future__ import annotations

from typing import Iterable, Optional


def _find_task(tasks: Iterable[dict], phrase: str) -> Optional[dict]:
    needle = phrase.lower()
    return next((t for t in tasks if needle in t["description"].lower()), None)


def _get_recent_actions(client) -> list[dict]:
    return client.get("/debug/telemetry").json()["tasks"]["recent_actions"]


def test_auto_update_tasks_adds_audit_note_on_new_task(client, project):
    convo_resp = client.post(
        "/chat",
        json={
            "project_id": project["id"],
            "message": "We need to add a login page and fix the logout bug soon.",
        },
    )
    assert convo_resp.status_code == 200, convo_resp.text

    tasks = client.get(f"/projects/{project['id']}/tasks").json()
    login_task = _find_task(tasks, "login page")
    assert login_task is not None
    assert "Added automatically" in (login_task.get("auto_notes") or "")
    assert login_task.get("auto_last_action") == "auto_added"
    assert login_task.get("auto_confidence") is not None


def test_auto_update_tasks_adds_audit_note_on_completion(client, project):
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

    refreshed = client.get(f"/projects/{project['id']}/tasks").json()
    login_task = _find_task(refreshed, "login page")
    assert login_task is not None
    assert login_task["status"] == "done"
    assert "Closed automatically" in (login_task.get("auto_notes") or "")
    assert "login" in (login_task.get("auto_notes") or "").lower()
    assert login_task.get("auto_last_action") == "auto_completed"
    assert login_task.get("auto_confidence") is not None


def test_telemetry_and_audit_are_consistent(client, project):
    convo_resp = client.post(
        "/chat",
        json={
            "project_id": project["id"],
            "message": "We need to add a login page and fix the logout bug soon.",
        },
    )
    assert convo_resp.status_code == 200, convo_resp.text
    convo_id = convo_resp.json()["conversation_id"]

    client.post(
        "/chat",
        json={
            "conversation_id": convo_id,
            "project_id": project["id"],
            "message": "The login page task is done now; logout bug still pending.",
        },
    )

    tasks = client.get(f"/projects/{project['id']}/tasks").json()
    login_task = _find_task(tasks, "login page")
    assert login_task is not None

    telemetry = client.get("/debug/telemetry").json()["tasks"]["recent_actions"]
    matching = next(
        (
            action
            for action in telemetry
            if action.get("task_id") == login_task["id"]
            and action.get("action") == login_task.get("auto_last_action")
        ),
        None,
    )
    assert matching is not None, "Expected telemetry entry for login task"
    assert matching.get("source") == "auto_conversation"
    assert matching.get("task_description") == login_task["description"]
    assert (matching.get("task_auto_notes") or "").startswith("Closed automatically")
    assert (login_task.get("auto_notes") or "").startswith("Closed automatically")
    if matching.get("matched_text"):
        assert "login" in matching["matched_text"].lower()


def test_auto_update_tasks_adds_deduped_audit_note_and_telemetry_for_exact_duplicate(
    client, project
):
    create_resp = client.post(
        f"/projects/{project['id']}/tasks",
        json={"description": "Add login page"},
    )
    assert create_resp.status_code == 200, create_resp.text
    seeded_task = create_resp.json()

    convo_resp = client.post(
        "/chat",
        json={
            "project_id": project["id"],
            "message": "We should add that login page again to the backlog.",
        },
    )
    assert convo_resp.status_code == 200, convo_resp.text

    tasks = client.get(f"/projects/{project['id']}/tasks").json()
    login_tasks = [t for t in tasks if "login page" in t["description"].lower()]
    assert len(login_tasks) == 1
    login_task = login_tasks[0]
    assert login_task["id"] == seeded_task["id"]
    notes = login_task.get("auto_notes") or ""
    assert notes.startswith("Duplicate automatically ignored")
    assert login_task.get("auto_last_action") == "auto_deduped"

    telemetry = _get_recent_actions(client)
    dedup_events = [
        action
        for action in telemetry
        if action.get("task_id") == login_task["id"]
        and action.get("action") == "auto_deduped"
    ]
    assert dedup_events, "Expected auto_deduped telemetry for login task"
    newest = dedup_events[0]
    assert newest.get("source") == "auto_conversation"
    assert newest.get("task_description") == login_task["description"]
    assert (newest.get("task_auto_notes") or "").startswith(
        "Duplicate automatically ignored"
    )
    if newest.get("matched_text"):
        assert "login" in newest["matched_text"].lower()


def test_auto_update_tasks_adds_deduped_audit_note_for_similar_description(
    client, project
):
    convo_resp = client.post(
        "/chat",
        json={
            "project_id": project["id"],
            "message": "We need to add a login page and fix logout soon.",
        },
    )
    assert convo_resp.status_code == 200, convo_resp.text
    convo_id = convo_resp.json()["conversation_id"]

    second = client.post(
        "/chat",
        json={
            "conversation_id": convo_id,
            "project_id": project["id"],
            "message": "Let's add a simple login page UI to the app as well.",
        },
    )
    assert second.status_code == 200, second.text

    refreshed = client.get(f"/projects/{project['id']}/tasks").json()
    login_task = _find_task(refreshed, "login page")
    assert login_task is not None
    assert login_task["status"] == "open"
    assert login_task.get("auto_last_action") == "auto_deduped"
    notes = (login_task.get("auto_notes") or "").lower()
    assert notes.startswith("duplicate automatically ignored")
    assert "simple login page" in notes

    telemetry = _get_recent_actions(client)
    matching = next(
        (
            action
            for action in telemetry
            if action.get("task_id") == login_task["id"]
            and action.get("action") == "auto_deduped"
            and "simple login page" in (action.get("matched_text") or "").lower()
        ),
        None,
    )
    assert matching is not None, "Expected telemetry entry for similar login task"
    assert matching.get("source") == "auto_conversation"
    assert matching.get("task_description") == login_task["description"]


def test_auto_update_tasks_dedupes_login_screen_with_noise(client, project):
    convo_resp = client.post(
        "/chat",
        json={
            "project_id": project["id"],
            "message": "We need to add a login page and fix logout soon.",
        },
    )
    assert convo_resp.status_code == 200, convo_resp.text
    convo_id = convo_resp.json()["conversation_id"]

    noisy_followup = client.post(
        "/chat",
        json={
            "conversation_id": convo_id,
            "project_id": project["id"],
            "message": (
                "Side chatter about priorities. Also the simple login screen variant "
                "is mentioned again; it's not done, just noted."
            ),
        },
    )
    assert noisy_followup.status_code == 200, noisy_followup.text

    refreshed = client.get(f"/projects/{project['id']}/tasks").json()
    login_task = _find_task(refreshed, "login page")
    assert login_task is not None
    assert login_task["status"] == "open"
    notes = (login_task.get("auto_notes") or "").lower()
    assert notes.startswith("duplicate automatically ignored")
    assert "login screen" in notes

    telemetry = _get_recent_actions(client)
    dedup_event = next(
        (
            action
            for action in telemetry
            if action.get("task_id") == login_task["id"]
            and action.get("action") == "auto_deduped"
            and "login screen" in (action.get("matched_text") or "").lower()
        ),
        None,
    )
    assert dedup_event is not None
    assert dedup_event.get("source") == "auto_conversation"


def test_auto_update_tasks_handles_noisy_conversation_without_wrong_completions(
    client, project
):
    convo_resp = client.post(
        "/chat",
        json={
            "project_id": project["id"],
            "message": "Add login page, fix logout bug, and refactor settings module.",
        },
    )
    assert convo_resp.status_code == 200, convo_resp.text
    convo_id = convo_resp.json()["conversation_id"]

    settings_resp = client.post(
        f"/projects/{project['id']}/tasks",
        json={"description": "Refactor settings module"},
    )
    assert settings_resp.status_code == 200, settings_resp.text

    noisy_resp = client.post(
        "/chat",
        json={
            "conversation_id": convo_id,
            "project_id": project["id"],
            "message": "The login page is done, logout bug still pending, "
            "and we also need to refactor settings later.",
        },
    )
    assert noisy_resp.status_code == 200, noisy_resp.text

    tasks = client.get(f"/projects/{project['id']}/tasks").json()
    login_task = _find_task(tasks, "login page")
    logout_task = _find_task(tasks, "logout bug")
    settings_task = _find_task(tasks, "settings")
    assert login_task is not None and logout_task is not None and settings_task is not None
    assert login_task["status"] == "done"
    assert logout_task["status"] == "open"
    assert settings_task["status"] == "open"
    assert (login_task.get("auto_notes") or "").startswith("Closed automatically")
    assert login_task.get("auto_last_action") == "auto_completed"

    telemetry = _get_recent_actions(client)
    completion_event = next(
        (
            action
            for action in telemetry
            if action.get("task_id") == login_task["id"]
            and action.get("action") == "auto_completed"
        ),
        None,
    )
    assert completion_event is not None, "Expected auto_completed telemetry for login"
    assert completion_event.get("source") == "auto_conversation"
    assert completion_event.get("task_description") == login_task["description"]
    if completion_event.get("matched_text"):
        assert "login" in completion_event["matched_text"].lower()

    assert not any(
        action.get("task_id") == logout_task["id"]
        and action.get("action") == "auto_completed"
        for action in telemetry
    )
    assert not any(
        action.get("task_id") == settings_task["id"]
        and action.get("action") == "auto_completed"
        for action in telemetry
    )


def test_seed_task_action_sets_source(client, project):
    payload = {
        "project_id": project["id"],
        "description": "Seeded auto-added task",
        "action": "auto_added",
        "confidence": 0.9,
        "model": "gpt-4o-mini",
    }
    seed_resp = client.post("/debug/seed_task_action", json=payload)
    assert seed_resp.status_code == 200, seed_resp.text

    telemetry = _get_recent_actions(client)
    assert telemetry, "Expected seeded telemetry action"
    seeded = telemetry[0]
    assert seeded.get("action") == "auto_added"
    assert seeded.get("task_description") == payload["description"]
    assert seeded.get("source") == "qa_seed"

