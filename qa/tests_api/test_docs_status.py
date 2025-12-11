from qa._utils import ensure_backend_on_path

ensure_backend_on_path()

from app.docs_guardrails import CANONICAL_DOC_PATHS  # noqa: E402


def test_docs_status_reports_all_docs(client) -> None:
    resp = client.get("/debug/docs_status")
    assert resp.status_code == 200
    payload = resp.json()

    assert payload.get("missing") == []

    docs = {entry["path"]: entry for entry in payload.get("docs", [])}
    for path in CANONICAL_DOC_PATHS:
        assert path in docs, f"{path} not listed in docs_status"
        entry = docs[path]
        assert entry.get("exists") is True, f"{path} should exist"
        size = entry.get("size")
        assert isinstance(size, int) and size > 0, f"{path} should have size > 0"

