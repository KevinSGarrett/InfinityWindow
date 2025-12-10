import pytest

from app.db import models


def _seed_project_with_artifacts(client, db_session, project_id: int) -> dict:
    task_a = client.post(
        f"/projects/{project_id}/tasks", json={"description": "Task A"}
    ).json()
    task_b = client.post(
        f"/projects/{project_id}/tasks", json={"description": "Task B"}
    ).json()

    dep = models.TaskDependency(
        project_id=project_id,
        task_id=task_b["id"],
        depends_on_task_id=task_a["id"],
    )
    db_session.add(dep)
    db_session.commit()
    db_session.refresh(dep)

    memory = client.post(
        f"/projects/{project_id}/memory",
        json={"title": "Mem A", "content": "Keep this", "tags": ["foo"]},
    ).json()

    decision = client.post(
        f"/projects/{project_id}/decisions", json={"title": "Decide A"}
    ).json()

    return {
        "tasks": [task_a, task_b],
        "dependency": dep,
        "memory": memory,
        "decision": decision,
    }


def test_export_includes_core_entities(client, db_session, project):
    seeded = _seed_project_with_artifacts(client, db_session, project["id"])

    resp = client.get(f"/projects/{project['id']}/export")
    assert resp.status_code == 200, resp.text
    bundle = resp.json()

    assert bundle["project"]["id"] == project["id"]
    assert bundle["project"]["is_archived"] is False
    assert len(bundle["tasks"]) == 2
    assert len(bundle["dependencies"]) == 1
    dep = bundle["dependencies"][0]
    assert dep["task_id"] == seeded["dependency"].task_id
    assert dep["depends_on_task_id"] == seeded["dependency"].depends_on_task_id
    assert len(bundle["memories"]) == 1
    assert bundle["memories"][0]["tags"] == ["foo"]
    assert len(bundle["decisions"]) == 1
    assert bundle["decisions"][0]["title"] == seeded["decision"]["title"]


def test_import_creates_new_project_and_remaps_dependencies(client, db_session, project):
    _seed_project_with_artifacts(client, db_session, project["id"])
    export_bundle = client.get(f"/projects/{project['id']}/export").json()

    import_resp = client.post("/projects/import", json=export_bundle)
    assert import_resp.status_code == 200, import_resp.text
    result = import_resp.json()
    new_project_id = result["new_project_id"]
    assert new_project_id != project["id"]

    new_project = db_session.get(models.Project, new_project_id)
    assert new_project is not None
    assert new_project.is_archived is False
    assert "Imported" in new_project.name

    new_tasks = (
        db_session.query(models.Task)
        .filter(models.Task.project_id == new_project_id)
        .all()
    )
    assert len(new_tasks) == len(export_bundle["tasks"])
    new_deps = (
        db_session.query(models.TaskDependency)
        .filter(models.TaskDependency.project_id == new_project_id)
        .all()
    )
    assert len(new_deps) == len(export_bundle["dependencies"])
    mapped_task_ids = {t.id for t in new_tasks}
    assert new_deps[0].task_id in mapped_task_ids
    assert new_deps[0].depends_on_task_id in mapped_task_ids


def test_export_allows_archived_projects(client, db_session, project):
    _seed_project_with_artifacts(client, db_session, project["id"])
    archive_resp = client.delete(f"/projects/{project['id']}")
    assert archive_resp.status_code == 200

    export_resp = client.get(f"/projects/{project['id']}/export")
    assert export_resp.status_code == 200, export_resp.text
    payload = export_resp.json()
    assert payload["project"]["is_archived"] is True


def test_export_404_for_missing_project(client):
    resp = client.get("/projects/9999/export")
    assert resp.status_code == 404


def test_import_rejects_malformed_bundle(client):
    resp = client.post("/projects/import", json={"project": {"name": "bad"}})
    assert resp.status_code == 400
    assert "Malformed project bundle" in resp.text


def test_project_telemetry_tracks_actions(client, db_session, project):
    client.get("/debug/telemetry", params={"reset": "true"})

    _seed_project_with_artifacts(client, db_session, project["id"])
    bundle = client.get(f"/projects/{project['id']}/export").json()
    client.post("/projects/import", json=bundle)
    client.delete(f"/projects/{project['id']}")

    telemetry = client.get("/debug/telemetry").json()
    projects = telemetry["projects"]
    assert projects["exported"] >= 1
    assert projects["imported"] >= 1
    assert projects["archived"] >= 1

