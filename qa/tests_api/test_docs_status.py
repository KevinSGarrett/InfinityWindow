from fastapi.testclient import TestClient


def test_swagger_docs_available(client: TestClient) -> None:
    resp = client.get("/docs")
    assert resp.status_code == 200, resp.text
    assert "text/html" in resp.headers.get("content-type", "")


def test_openapi_schema_available(client: TestClient) -> None:
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert "paths" in payload
    assert "/chat" in payload["paths"]

