def test_delete_soft_archives_project(client, project):
    delete_resp = client.delete(f"/projects/{project['id']}")
    assert delete_resp.status_code == 200
    archived = delete_resp.json()
    assert archived["is_archived"] is True
    assert archived["archived_at"] is not None

    detail_resp = client.get(f"/projects/{project['id']}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["is_archived"] is True


def test_archive_telemetry_increment(client, project):
    client.get("/debug/telemetry", params={"reset": "true"})
    client.delete(f"/projects/{project['id']}")
    telemetry = client.get("/debug/telemetry").json()
    assert telemetry["projects"]["archived"] >= 1

