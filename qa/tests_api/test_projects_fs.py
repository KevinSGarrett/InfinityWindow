from pathlib import Path


def test_fs_list_requires_local_root_path(client):
    resp = client.post(
        "/projects",
        json={
            "name": "NoRootProject",
        },
    )
    assert resp.status_code == 200, resp.text
    project_id = resp.json()["id"]

    list_resp = client.get(f"/projects/{project_id}/fs/list")
    assert list_resp.status_code == 400
    body = list_resp.json()
    assert "local_root_path" in (body.get("detail") or "").lower()


def test_fs_list_invalid_local_root_path(client, tmp_path):
    missing_dir = tmp_path / "missing-root"
    resp = client.post(
        "/projects",
        json={
            "name": "InvalidRootProject",
            "local_root_path": str(missing_dir),
        },
    )
    assert resp.status_code == 200, resp.text
    project_id = resp.json()["id"]

    list_resp = client.get(f"/projects/{project_id}/fs/list")
    assert list_resp.status_code == 400
    body = list_resp.json()
    detail = (body.get("detail") or "").lower()
    assert "local_root_path" in detail
    assert "exist" in detail


def test_fs_list_happy_path(client, tmp_path):
    root = tmp_path / "fs-root"
    root.mkdir()
    (root / "file1.txt").write_text("hello world", encoding="utf-8")
    subfolder = root / "folder1"
    subfolder.mkdir()
    (subfolder / "nested.txt").write_text("nested", encoding="utf-8")

    resp = client.post(
        "/projects",
        json={
            "name": "FsHappyProject",
            "local_root_path": str(root),
        },
    )
    assert resp.status_code == 200, resp.text
    project_id = resp.json()["id"]

    list_resp = client.get(f"/projects/{project_id}/fs/list")
    assert list_resp.status_code == 200
    data = list_resp.json()

    assert Path(data["root"]) == root.resolve()
    assert data["path"] in (".", "")  # root relative path
    names = {entry["name"] for entry in data["entries"]}
    assert {"file1.txt", "folder1"}.issubset(names)

