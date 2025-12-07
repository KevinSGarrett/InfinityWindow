from __future__ import annotations

import os
from pathlib import Path
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from app.db import models
from app.ingestion.docs_ingestor import ingest_text_document

# Default patterns for files we consider "text/code" in a repo
DEFAULT_INCLUDE_GLOBS: List[str] = [
    "*.py",
    "*.md",
    "*.txt",
    "*.json",
    "*.yml",
    "*.yaml",
    "*.js",
    "*.ts",
    "*.tsx",
    "*.css",
    "*.html",
]

# Directories we usually want to skip in repos
DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
}


def _should_include_file(filename: str, include_globs: List[str]) -> bool:
    """
    Return True if the filename matches any of the glob patterns.
    """
    from fnmatch import fnmatch

    return any(fnmatch(filename, pattern) for pattern in include_globs)


def discover_repo_files(
    root_path: Path,
    include_globs: Optional[List[str]] = None,
) -> List[Path]:
    """
    Walk the directory tree under root_path and collect files that match
    the include_globs patterns, skipping typical junk directories.
    """
    if include_globs is None:
        include_globs = DEFAULT_INCLUDE_GLOBS

    files: List[Path] = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Remove excluded directories in-place (so os.walk won't descend into them)
        dirnames[:] = [
            d for d in dirnames
            if d not in DEFAULT_EXCLUDE_DIRS and not d.startswith(".")
        ]

        for filename in filenames:
            if not _should_include_file(filename, include_globs):
                continue

            full_path = Path(dirpath) / filename
            files.append(full_path)

    return files


_INGEST_TELEMETRY: Dict[str, float] = {
    "jobs_started": 0,
    "jobs_completed": 0,
    "jobs_failed": 0,
    "jobs_cancelled": 0,
    "files_processed": 0,
    "files_skipped": 0,
    "bytes_processed": 0,
    "total_duration_seconds": 0.0,
}


def _record_ingest_event(
    event: str,
    *,
    files: int = 0,
    skipped: int = 0,
    bytes_processed: int = 0,
    duration: float = 0.0,
) -> None:
    if event in _INGEST_TELEMETRY:
        _INGEST_TELEMETRY[event] += 1
    _INGEST_TELEMETRY["files_processed"] += files
    _INGEST_TELEMETRY["files_skipped"] += skipped
    _INGEST_TELEMETRY["bytes_processed"] += bytes_processed
    _INGEST_TELEMETRY["total_duration_seconds"] += max(duration, 0.0)


def get_ingest_telemetry(reset: bool = False) -> Dict[str, float]:
    snapshot = dict(_INGEST_TELEMETRY)
    if reset:
        reset_ingest_telemetry()
    return snapshot


def reset_ingest_telemetry() -> None:
    for key in _INGEST_TELEMETRY:
        _INGEST_TELEMETRY[key] = 0 if isinstance(_INGEST_TELEMETRY[key], int) else 0.0


def _job_duration_seconds(job: models.IngestionJob) -> float:
    if job.started_at and job.finished_at:
        return max(
            0.0, (job.finished_at - job.started_at).total_seconds()
        )
    return 0.0


def ingest_local_repo(
    db: Session,
    project_id: int,
    root_path: str,
    name_prefix: Optional[str] = None,
    include_globs: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Legacy helper used by /github/ingest_local_repo.

    Internally creates an IngestionJob and delegates to ingest_repo_job so both
    code paths share batching, hashing, and progress logic.
    """
    root = Path(root_path).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Root path is not a directory: {root_path}")

    job = models.IngestionJob(
        project_id=project_id,
        kind="repo",
        source=str(root),
        status="pending",
        total_items=0,
        processed_items=0,
        meta={
            "include_globs": include_globs or DEFAULT_INCLUDE_GLOBS,
            "name_prefix": name_prefix,
        },
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        return ingest_repo_job(
            db=db,
            job=job,
            include_globs=include_globs,
            name_prefix=name_prefix,
        )
    except Exception:
        db.refresh(job)
        raise


def ingest_repo_job(
    db: Session,
    job: models.IngestionJob,
    *,
    include_globs: Optional[List[str]] = None,
    name_prefix: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute an ingestion job with batching, hashing, and progress updates.
    """
    job.status = "running"
    job.error_message = None
    job.started_at = datetime.utcnow()
    job.finished_at = None
    job.processed_items = 0
    job.processed_bytes = 0
    db.commit()
    _record_ingest_event("jobs_started")

    root = Path(job.source).expanduser().resolve()
    if not root.is_dir():
        job.status = "failed"
        job.error_message = f"Root path is not a directory: {job.source}"
        job.finished_at = datetime.utcnow()
        db.commit()
        _record_ingest_event("jobs_failed")
        raise ValueError(job.error_message)

    include_patterns = include_globs or DEFAULT_INCLUDE_GLOBS
    all_files = discover_repo_files(root, include_patterns)
    total_discovered = len(all_files)

    job.meta = {
        **(job.meta or {}),
        "include_globs": include_patterns,
        "name_prefix": name_prefix,
        "num_files_discovered": total_discovered,
    }
    db.commit()

    existing_states: Dict[str, models.FileIngestionState] = {
        state.relative_path: state
        for state in db.query(models.FileIngestionState)
        .filter(models.FileIngestionState.project_id == job.project_id)
        .all()
    }

    files_to_process: List[Dict[str, Any]] = []
    total_bytes = 0
    for file_path in all_files:
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        rel_path = file_path.relative_to(root).as_posix()
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        state = existing_states.get(rel_path)
        if state and state.sha256 == sha:
            continue
        file_size = file_path.stat().st_size
        files_to_process.append(
            {
                "relative_path": rel_path,
                "text": text,
                "sha": sha,
                "size": file_size,
            }
        )
        total_bytes += file_size

    skipped_files = total_discovered - len(files_to_process)
    job.total_items = len(files_to_process)
    job.total_bytes = total_bytes
    db.commit()

    num_documents = 0
    num_chunks_total = 0
    cancelled = False
    # Batch commits every 10 files to reduce database contention
    # SQLite can have locking issues with frequent concurrent reads/writes
    COMMIT_BATCH_SIZE = 10
    files_since_commit = 0

    try:
        for entry in files_to_process:
            # Check for cancellation every file (but commit in batches)
            db.refresh(job, attribute_names=["cancel_requested"])
            if job.cancel_requested:
                cancelled = True
                job.status = "cancelled"
                job.error_message = "Cancelled by user"
                job.finished_at = datetime.utcnow()
                db.commit()
                break

            rel_path = entry["relative_path"]
            text = entry["text"]
            sha = entry["sha"]
            size = entry["size"]

            doc_name = f"{name_prefix}{rel_path}" if name_prefix else rel_path
            description = f"File from repo {root}: {rel_path}"

            _, num_chunks = ingest_text_document(
                db=db,
                project_id=job.project_id,
                name=doc_name,
                text=text,
                description=description,
            )
            num_documents += 1
            num_chunks_total += num_chunks

            state = existing_states.get(rel_path)
            if state is None:
                state = models.FileIngestionState(
                    project_id=job.project_id,
                    relative_path=rel_path,
                    sha256=sha,
                    last_ingested_at=datetime.utcnow(),
                )
                db.add(state)
                existing_states[rel_path] = state
            else:
                state.sha256 = sha
                state.last_ingested_at = datetime.utcnow()

            job.processed_items += 1
            job.processed_bytes += size
            files_since_commit += 1

            # Commit in batches to reduce database contention
            if files_since_commit >= COMMIT_BATCH_SIZE:
                db.commit()
                files_since_commit = 0

        # Commit any remaining files that didn't reach the batch size
        if files_since_commit > 0:
            db.commit()

    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)
        job.finished_at = datetime.utcnow()
        db.commit()
        _record_ingest_event(
            "jobs_failed",
            files=job.processed_items,
            skipped=skipped_files + (job.total_items - job.processed_items),
            bytes_processed=job.processed_bytes,
            duration=_job_duration_seconds(job),
        )
        raise

    if cancelled:
        job.meta = {
            **(job.meta or {}),
            "include_globs": include_patterns,
            "name_prefix": name_prefix,
            "num_files_discovered": total_discovered,
            "files_processed": job.processed_items,
            "files_skipped": skipped_files + (job.total_items - job.processed_items),
            "num_documents": num_documents,
            "num_chunks": num_chunks_total,
        }
        db.commit()
        _record_ingest_event(
            "jobs_cancelled",
            files=job.processed_items,
            skipped=skipped_files + (job.total_items - job.processed_items),
            bytes_processed=job.processed_bytes,
            duration=_job_duration_seconds(job),
        )
        return {
            "project_id": job.project_id,
            "root_path": str(root),
            "num_files": total_discovered,
            "num_documents": num_documents,
            "num_chunks": num_chunks_total,
            "files_processed": job.processed_items,
            "files_skipped": skipped_files + (job.total_items - job.processed_items),
            "total_bytes": job.total_bytes,
            "processed_bytes": job.processed_bytes,
        }

    job.status = "completed"
    job.error_message = None
    job.finished_at = datetime.utcnow()
    job.meta = {
        **(job.meta or {}),
        "include_globs": include_patterns,
        "name_prefix": name_prefix,
        "num_files_discovered": total_discovered,
        "files_processed": job.processed_items,
        "files_skipped": skipped_files,
        "num_documents": num_documents,
        "num_chunks": num_chunks_total,
    }
    db.commit()
    _record_ingest_event(
        "jobs_completed",
        files=job.processed_items,
        skipped=skipped_files,
        bytes_processed=job.processed_bytes,
        duration=_job_duration_seconds(job),
    )

    return {
        "project_id": job.project_id,
        "root_path": str(root),
        "num_files": total_discovered,
        "num_documents": num_documents,
        "num_chunks": num_chunks_total,
        "files_processed": job.processed_items,
        "files_skipped": skipped_files,
        "total_bytes": job.total_bytes,
        "processed_bytes": job.processed_bytes,
    }
