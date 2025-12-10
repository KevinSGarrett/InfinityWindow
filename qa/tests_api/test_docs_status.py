from fastapi.testclient import TestClient


def test_docs_crud_round_trip(client: TestClient, project: dict) -> None:
    list_empty = client.get(f"/projects/{project['id']}/docs")
    assert list_empty.status_code == 200, list_empty.text
    assert list_empty.json() == []

    create_resp = client.post(
        f"/projects/{project['id']}/docs",
        json={"title": "QA Doc", "description": "guardrail doc"},
    )
    assert create_resp.status_code == 200, create_resp.text
    created = create_resp.json()
    doc_id = created["id"]

    read_resp = client.get(f"/docs/{doc_id}")
    assert read_resp.status_code == 200, read_resp.text
    assert read_resp.json()["id"] == doc_id

    list_resp = client.get(f"/projects/{project['id']}/docs")
    assert list_resp.status_code == 200, list_resp.text
    listed_ids = [doc["id"] for doc in list_resp.json()]
    assert doc_id in listed_ids

    delete_resp = client.delete(f"/docs/{doc_id}")
    assert delete_resp.status_code == 200, delete_resp.text
    assert delete_resp.json()["status"] == "deleted"

