import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_list_update_project():
    # POST /projects
    r = client.post('/projects', json={
        "name": "QA_Demo",
        "description": "QA baseline project",
        "local_root_path": "C:\\InfinityWindow_QA"
    })
    assert r.status_code == 200, r.text
    proj = r.json()
    r = client.get('/projects')
    assert any(p['id']==proj['id'] for p in r.json())
    r2 = client.patch(f"/projects/{proj['id']}", json={"description":"Updated"})
    assert r2.status_code == 200
