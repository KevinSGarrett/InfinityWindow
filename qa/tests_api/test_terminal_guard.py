from fastapi.testclient import TestClient


def test_terminal_run_allows_safe_command(client: TestClient, project: dict) -> None:
    resp = client.post(
        "/terminal/run",
        json={
            "project_id": project["id"],
            "cwd": "",
            "command": "echo ok",
            "timeout_seconds": 30,
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "ok" in (data.get("stdout") or "").lower()


def test_terminal_run_blocks_obviously_destructive_command(
    client: TestClient, project: dict
) -> None:
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
    body = resp.json()
    assert "Command blocked by terminal guard" in body.get("detail", "")

