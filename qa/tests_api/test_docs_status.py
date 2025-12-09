from app.api.main import CANONICAL_DOC_PATHS


def test_docs_status_reports_canonical_docs_present(client) -> None:
    resp = client.get("/debug/docs_status")
    assert resp.status_code == 200

    payload = resp.json()
    assert payload.get("missing") == []

    docs_by_path = {entry["path"]: entry for entry in payload.get("docs", [])}
    for rel_path in CANONICAL_DOC_PATHS:
        assert rel_path in docs_by_path, f"{rel_path} missing from docs_status"
        entry = docs_by_path[rel_path]
        assert entry.get("exists") is True
        assert entry.get("size", 0) > 0

