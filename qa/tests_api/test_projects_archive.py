"""
Archive and soft-delete semantics for projects.
"""

import time


def _create_project(client, root_path) -> dict:
    resp = client.post(
        "/projects",
        json={
            "name": f"Archive QA {time.time_ns()}",
            "description": "archiving flow",
            "local_root_path": str(root_path),
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_archive_hides_from_default_list(client, tmp_path):
    """A-Proj-Archive-01: Soft-delete hides project from default list."""
    root = tmp_path / "archive_default"
    root.mkdir()
    project = _create_project(client, root)

    delete_resp = client.delete(f"/projects/{project['id']}")
    assert delete_resp.status_code == 204

    default_list = client.get("/projects")
    assert default_list.status_code == 200
    assert project["id"] not in [p["id"] for p in default_list.json()]

    all_projects = client.get("/projects", params={"include_archived": True})
    assert all_projects.status_code == 200
    archived = next(p for p in all_projects.json() if p["id"] == project["id"])
    assert archived["is_archived"] is True
    assert archived["archived_at"] is not None

    detail = client.get(f"/projects/{project['id']}")
    assert detail.status_code == 200
    assert detail.json()["is_archived"] is True


def test_archived_project_blocks_ingestion(client, tmp_path):
    """A-Proj-Archive-02: Ingestion cannot start on archived projects."""
    repo_root = tmp_path / "archive_ingest"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("# archived\n", encoding="utf-8")
    project = _create_project(client, repo_root)
    client.delete(f"/projects/{project['id']}")

    job_resp = client.post(
        f"/projects/{project['id']}/ingestion_jobs",
        json={
            "kind": "repo",
            "source": str(repo_root),
            "include_globs": ["*.md"],
            "name_prefix": "qa/",
        },
    )
    assert job_resp.status_code == 400
    assert "archived" in job_resp.json()["detail"].lower()


def test_archived_project_blocks_fs_write(client, tmp_path):
    """A-Proj-Archive-03: File writes are rejected for archived projects."""
    root = tmp_path / "archive_fs"
    root.mkdir()
    project = _create_project(client, root)
    client.delete(f"/projects/{project['id']}")

    write_resp = client.put(
        f"/projects/{project['id']}/fs/write",
        json={
            "file_path": "notes.txt",
            "content": "should not write",
            "create_dirs": True,
        },
    )
    assert write_resp.status_code == 400
    assert "archived" in write_resp.json()["detail"].lower()

