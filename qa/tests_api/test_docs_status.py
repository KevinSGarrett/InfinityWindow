"""
Debug coverage for /debug/docs_status, aligned with canonical docs list.
"""

from fastapi.testclient import TestClient

import app.api.main as main


def test_docs_status_reports_known_doc_and_no_missing(client: TestClient) -> None:
    resp = client.get("/debug/docs_status")
    assert resp.status_code == 200, resp.text

    payload = resp.json()
    assert payload["missing"] == []

    docs = payload.get("docs") or []
    assert isinstance(docs, list)

    canonical_path = "docs/REQUIREMENTS_CRM.md"
    assert canonical_path in {p.as_posix() for p in main.CANONICAL_DOC_PATHS}

    doc_map = {entry["path"]: entry for entry in docs}
    assert canonical_path in doc_map

    entry = doc_map[canonical_path]
    assert entry["exists"] is True
    assert "size_bytes" in entry
    assert isinstance(entry["size_bytes"], (int, type(None)))

