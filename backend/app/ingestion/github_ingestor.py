from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

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


def ingest_local_repo(
    db: Session,
    project_id: int,
    root_path: str,
    name_prefix: Optional[str] = None,
    include_globs: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Ingest a local repository (or any folder) into the given project.

    - root_path: local filesystem path to the repo root.
    - name_prefix: optional prefix for Document.name (e.g. "MyRepo/").
    - include_globs: optional override for which file patterns to ingest.

    For each discovered file:
      * Reads file as UTF-8 text (ignoring decode errors).
      * Creates a Document record via ingest_text_document.
      * Chunks, embeds, and indexes it into Chroma.
    """
    root = Path(root_path).expanduser().resolve()

    if not root.is_dir():
        raise ValueError(f"Root path is not a directory: {root_path}")

    include_patterns = include_globs or DEFAULT_INCLUDE_GLOBS

    all_files = discover_repo_files(root, include_patterns)

    num_files_discovered = len(all_files)
    num_documents = 0
    num_chunks_total = 0

    for file_path in all_files:
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            # Skip files we can't read or decode
            continue

        rel_path = file_path.relative_to(root)
        rel_path_str = rel_path.as_posix()

        if name_prefix:
            doc_name = f"{name_prefix}{rel_path_str}"
        else:
            doc_name = rel_path_str

        description = f"File from repo {root}: {rel_path_str}"

        document, num_chunks = ingest_text_document(
            db=db,
            project_id=project_id,
            name=doc_name,
            text=text,
            description=description,
        )

        num_documents += 1
        num_chunks_total += num_chunks

    return {
        "project_id": project_id,
        "root_path": str(root),
        "num_files": num_files_discovered,
        "num_documents": num_documents,
        "num_chunks": num_chunks_total,
    }
