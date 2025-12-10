"""
Project export/import API coverage.
"""

import time

from app.db import models


def _create_project(client, tmp_path, name_prefix: str = "ExportImport") -> dict:
    root = tmp_path / f"{name_prefix}_{time.time_ns()}"
    root.mkdir(parents=True, exist_ok=True)
    resp = client.post(
        "/projects",
        json={
            "name": f"{name_prefix}_{time.time_ns()}",
            "description": "export/import test project",
            "local_root_path": str(root),
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _create_task(client, project_id: int, description: str) -> dict:
    resp = client.post(
        f"/projects/{project_id}/tasks",
        json={"description": description},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_project_export_includes_tasks_and_dependencies(client, db_session, tmp_path):
    project = _create_project(client, tmp_path, name_prefix="ExportDepends")
    task_a = _create_task(client, project["id"], "First task")
    task_b = _create_task(client, project["id"], "Second task")

    db_session.add(
        models.TaskDependency(task_id=task_b["id"], depends_on_task_id=task_a["id"])
    )
    db_session.commit()

    export_resp = client.get(f"/projects/{project['id']}/export")
    assert export_resp.status_code == 200, export_resp.text
    bundle = export_resp.json()

    exported_tasks = {t["id"]: t for t in bundle["tasks"]}
    assert len(exported_tasks) == 2
    deps = bundle["task_dependencies"]
    assert len(deps) == 1
    assert deps[0]["task_id"] == task_b["id"]
    assert deps[0]["depends_on_task_id"] == task_a["id"]
    assert bundle["project"]["id"] == project["id"]


def test_project_import_creates_new_project_with_mapped_ids(client, db_session, tmp_path):
    project = _create_project(client, tmp_path, name_prefix="ImportMapped")
    task_a = _create_task(client, project["id"], "Seed task A")
    task_b = _create_task(client, project["id"], "Seed task B")

    db_session.add(
        models.TaskDependency(task_id=task_b["id"], depends_on_task_id=task_a["id"])
    )
    db_session.commit()

    export_resp = client.get(f"/projects/{project['id']}/export")
    assert export_resp.status_code == 200, export_resp.text
    bundle = export_resp.json()

    import_resp = client.post("/projects/import", json=bundle)
    assert import_resp.status_code == 200, import_resp.text
    result = import_resp.json()
    new_project_id = result["project_id"]
    assert new_project_id != project["id"]
    assert result["tasks_imported"] == len(bundle["tasks"])
    assert result["dependencies_imported"] == len(bundle["task_dependencies"])

    new_tasks_resp = client.get(f"/projects/{new_project_id}/tasks")
    assert new_tasks_resp.status_code == 200
    new_tasks = new_tasks_resp.json()
    assert len(new_tasks) == len(bundle["tasks"])

    new_task_ids = {t["id"] for t in new_tasks}
    imported_dependencies = (
        db_session.query(models.TaskDependency)
        .filter(models.TaskDependency.task_id.in_(new_task_ids))
        .all()
    )
    assert len(imported_dependencies) == len(bundle["task_dependencies"])
    for dep in imported_dependencies:
        assert dep.task_id in new_task_ids
        assert dep.depends_on_task_id in new_task_ids
        assert dep.task_id not in {task_a["id"], task_b["id"]}
        assert dep.depends_on_task_id not in {task_a["id"], task_b["id"]}


def test_export_allows_archived_projects(client, tmp_path):
    project = _create_project(client, tmp_path, name_prefix="ExportArchived")
    archive_resp = client.delete(f"/projects/{project['id']}")
    assert archive_resp.status_code == 204

    export_resp = client.get(f"/projects/{project['id']}/export")
    assert export_resp.status_code == 200, export_resp.text
    bundle = export_resp.json()
    assert bundle["project"]["is_archived"] is True


def test_export_missing_project_returns_404(client):
    resp = client.get("/projects/999999/export")
    assert resp.status_code == 404


def test_import_rejects_malformed_payload(client):
    resp = client.post("/projects/import", json={"project": {}, "tasks": []})
    assert resp.status_code == 400

