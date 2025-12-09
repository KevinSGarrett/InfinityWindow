from qa._utils import ensure_backend_on_path

ensure_backend_on_path()
from app.api.main import CANONICAL_DOC_PATHS  # noqa: E402


def test_docs_status_endpoint(client) -> None:
    response = client.get("/debug/docs_status")
    assert response.status_code == 200

    payload = response.json()
    assert payload.get("missing") == []

    docs = payload.get("docs", [])
    canonical_paths = {item.get("path") for item in docs}
    assert set(CANONICAL_DOC_PATHS).issubset(canonical_paths)

    crm_path = "docs/REQUIREMENTS_CRM.md"
    assert crm_path in CANONICAL_DOC_PATHS
    crm_entry = next((item for item in docs if item.get("path") == crm_path), None)
    assert crm_entry is not None
    assert crm_entry.get("exists") is True
    assert isinstance(crm_entry.get("size_bytes"), int)
    assert crm_entry["size_bytes"] > 0

    for item in docs:
        assert {"path", "exists", "size_bytes"} <= set(item.keys())
        assert isinstance(item["exists"], bool)
        assert isinstance(item["size_bytes"], int)
        assert item["size_bytes"] >= 0

