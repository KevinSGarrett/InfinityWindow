"""
Core project CRUD and filesystem guardrails.
"""

import os


def test_create_list_update_project(client, project):
    """A-Proj-01: Create project, list it, update metadata."""
    list_resp = client.get("/projects")
    assert list_resp.status_code == 200
    assert any(p["id"] == project["id"] for p in list_resp.json())

    update = client.patch(
        f"/projects/{project['id']}",
        json={"description": "Updated by QA", "pinned_note_text": "QA note"},
    )
    assert update.status_code == 200
    detail = client.get(f"/projects/{project['id']}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["description"] == "Updated by QA"
    assert body["pinned_note_text"] == "QA note"


def test_project_validation_requires_name(client):
    """A-Proj-02: Reject empty project names."""
    resp = client.post(
        "/projects",
        json={
            "name": "",
            "description": "invalid",
            "local_root_path": os.getcwd(),
        },
    )
    assert resp.status_code == 422


def test_fs_path_traversal_blocked(client, project):
    """K-SEC-FS-01: Block traversal and UNC paths in fs endpoints."""
    pid = project["id"]

    bad_relative = client.get(
        f"/projects/{pid}/fs/read", params={"subpath": "..\\windows\\system32"}
    )
    assert bad_relative.status_code == 400

    bad_unc = client.get(
        f"/projects/{pid}/fs/read", params={"subpath": r"\\\\malicious\\share"}
    )
    assert bad_unc.status_code == 400

    list_resp = client.get(f"/projects/{pid}/fs/list", params={"subpath": ""})
    assert list_resp.status_code == 200
    assert "entries" in list_resp.json()

