from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import models


def _run_terminal_command(client: TestClient, project_id: int, command: str, cwd: str = "") -> None:
    resp = client.post(
        "/terminal/run",
        json={
            "project_id": project_id,
            "cwd": cwd,
            "command": command,
            "timeout_seconds": 30,
        },
    )
    assert resp.status_code == 200, resp.text


def test_terminal_run_logs_history_for_project(client: TestClient, project: dict) -> None:
    _run_terminal_command(client, project["id"], "echo hi", cwd="")

    history_resp = client.get(f"/projects/{project['id']}/terminal/history")
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert len(history) == 1

    entry = history[0]
    assert entry["command"] == "echo hi"
    assert entry["cwd"] == "."
    assert entry["exit_code"] == 0
    assert "hi" in (entry.get("stdout_tail") or "")
    assert entry.get("stderr_tail") in (None, "")


def test_terminal_history_respects_limit(client: TestClient, project: dict) -> None:
    commands = ["echo first", "echo second", "echo third"]
    for cmd in commands:
        _run_terminal_command(client, project["id"], cmd)

    history_resp = client.get(f"/projects/{project['id']}/terminal/history", params={"limit": 2})
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert len(history) == 2

    returned_commands = [entry["command"] for entry in history]
    assert returned_commands == commands[-1:-3:-1]  # newest first


def test_terminal_guard_blocked_command_not_logged(client: TestClient, project: dict, db_session: Session) -> None:
    resp = client.post(
        "/terminal/run",
        json={
            "project_id": project["id"],
            "cwd": "",
            "command": "rm -rf /",
            "timeout_seconds": 30,
        },
    )
    assert resp.status_code == 400
    assert "Command blocked by terminal guard" in resp.json().get("detail", "")

    history_count = (
        db_session.query(models.TerminalHistory)
        .filter(models.TerminalHistory.project_id == project["id"])
        .count()
    )
    assert history_count == 0


def test_terminal_history_retention_prunes_old_entries(client: TestClient, project: dict, db_session: Session) -> None:
    first_command = "echo cmd-0"
    last_command = None

    for i in range(205):
        last_command = f"echo cmd-{i}"
        _run_terminal_command(client, project["id"], last_command)

    assert last_command is not None

    count = (
        db_session.query(models.TerminalHistory)
        .filter(models.TerminalHistory.project_id == project["id"])
        .count()
    )
    assert count <= 200

    oldest = (
        db_session.query(models.TerminalHistory)
        .filter(
            models.TerminalHistory.project_id == project["id"],
            models.TerminalHistory.command == first_command,
        )
        .first()
    )
    assert oldest is None

    newest = (
        db_session.query(models.TerminalHistory)
        .filter(
            models.TerminalHistory.project_id == project["id"],
            models.TerminalHistory.command == last_command,
        )
        .first()
    )
    assert newest is not None

