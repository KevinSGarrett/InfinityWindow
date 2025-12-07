from __future__ import annotations

import time
from pathlib import Path
from tempfile import TemporaryDirectory

from ._utils import ensure_backend_on_path, temporary_attr

ensure_backend_on_path()

from fastapi.testclient import TestClient  # noqa: E402

from app.api.main import app  # noqa: E402
from app.ingestion import docs_ingestor, github_ingestor  # noqa: E402
from app.llm import embeddings  # noqa: E402


def _fake_embed_texts(texts: list[str], **_: object) -> list[list[float]]:
    """Return deterministic embeddings without calling OpenAI."""
    def _vector_for(text: str) -> list[float]:
        base = ((len(text) % 13) + 1) / 13.0
        return [base] * 1536

    return [_vector_for(text) for text in texts]


def _start_ingestion_job(
    client: TestClient,
    project_id: int,
    root: Path,
    prefix: str,
) -> dict:
    resp = client.post(
        f"/projects/{project_id}/ingestion_jobs",
        json={
            "kind": "repo",
            "source": str(root),
            "name_prefix": f"{prefix}/",
            "include_globs": ["*.txt"],
        },
    )
    resp.raise_for_status()
    return resp.json()


def _poll_until_terminal(
    client: TestClient, project_id: int, job_id: int, timeout: float = 15.0
) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = client.get(
            f"/projects/{project_id}/ingestion_jobs/{job_id}",
        )
        resp.raise_for_status()
        job = resp.json()
        if job.get("status") in {"completed", "failed", "cancelled"}:
            return job
        time.sleep(0.2)
    raise AssertionError(f"Timed out waiting for ingestion job {job_id}.")


def _assert_completed(job: dict, expected_processed: int) -> None:
    if job.get("status") != "completed":
        raise AssertionError(f"Ingestion job did not complete: {job}")
    processed = job.get("processed_items")
    if processed != expected_processed:
        raise AssertionError(
            f"Expected {expected_processed} processed items, got {processed}."
        )


def run() -> None:
    """Ensure ingestion jobs succeed, skip unchanged files, and surface failures."""
    client = TestClient(app)
    unique = f"QA_INGEST_{int(time.time())}"

    with TemporaryDirectory() as tmpdir, temporary_attr(
        embeddings, "embed_texts_batched", _fake_embed_texts
    ):
        repo_root = Path(tmpdir)
        (repo_root / "README.txt").write_text(
            "Initial README content for ingestion probe."
        )
        nested = repo_root / "notes"
        nested.mkdir()
        (nested / "todo.txt").write_text(
            "Remember to keep the ingestion probe deterministic."
        )

        project_resp = client.post(
            "/projects",
            json={"name": f"Ingestion Probe {unique}"},
        )
        project_resp.raise_for_status()
        project = project_resp.json()

        # First run should process both files.
        first_job = _start_ingestion_job(client, project["id"], repo_root, unique)
        first_complete = _poll_until_terminal(client, project["id"], first_job["id"])
        _assert_completed(first_complete, expected_processed=2)

        # Second run without changes should process zero files.
        second_job = _start_ingestion_job(client, project["id"], repo_root, unique)
        second_complete = _poll_until_terminal(client, project["id"], second_job["id"])
        _assert_completed(second_complete, expected_processed=0)

        # Force a failure by patching the doc ingestor.
        def _failing_ingest_text_document(*args, **kwargs):  # type: ignore[override]
            raise RuntimeError("INGEST_PROBE_FAILURE")

        # Modify a file so the next job must process at least one entry.
        (repo_root / "README.txt").write_text("Force failure path.\n")

        with temporary_attr(
            docs_ingestor,
            "ingest_text_document",
            _failing_ingest_text_document,
        ), temporary_attr(
            github_ingestor,
            "ingest_text_document",
            _failing_ingest_text_document,
        ):
            failing_job = _start_ingestion_job(
                client, project["id"], repo_root, f"{unique}-fail"
            )
            failing_complete = _poll_until_terminal(
                client, project["id"], failing_job["id"]
            )
            if failing_complete.get("status") != "failed":
                raise AssertionError("Expected ingestion job to fail.")
            error_message = failing_complete.get("error_message") or ""
            if "INGEST_PROBE_FAILURE" not in error_message:
                raise AssertionError(
                    f"Failure message missing probe token: {error_message}"
                )

