"""
Docs ingestion happy path (lightweight) with stubbed embeddings.
"""

import time
from pathlib import Path

POLL_STATUSES = {"completed", "failed", "cancelled"}


def test_basic_ingestion_happy_path(client, tmp_path):
    """D-Docs-02: Repo ingestion completes for a tiny fixture."""
    repo_root = tmp_path / "fixture_repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("# QA Fixture\n\ncontent\n", encoding="utf-8")

    proj_resp = client.post(
        "/projects",
        json={
            "name": f"Ingestion QA {time.time_ns()}",
            "local_root_path": str(repo_root),
            "description": "fixture project",
        },
    )
    assert proj_resp.status_code == 200
    project = proj_resp.json()

    job_resp = client.post(
        f"/projects/{project['id']}/ingestion_jobs",
        json={
            "kind": "repo",
            "source": str(repo_root),
            "include_globs": ["*.md"],
            "name_prefix": "qa/",
        },
    )
    assert job_resp.status_code == 200, job_resp.text
    job = job_resp.json()

    final_status = job["status"]
    for _ in range(20):
        time.sleep(0.5)
        poll = client.get(
            f"/projects/{project['id']}/ingestion_jobs/{job['id']}"
        )
        assert poll.status_code == 200
        job = poll.json()
        final_status = job["status"]
        if final_status in POLL_STATUSES:
            break

    assert final_status == "completed", job
    assert job["processed_items"] >= 1
    assert job["total_items"] >= 1

