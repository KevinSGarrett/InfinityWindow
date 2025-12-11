from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Sequence

# Resolve repo root relative to this file (backend/app -> backend -> repo)
REPO_ROOT = Path(__file__).resolve().parents[2]

# Canonical docs that must exist for guardrail/CI checks.
CANONICAL_DOC_PATHS: Sequence[str] = (
    "docs/REQUIREMENTS_CRM.md",
    "docs/TODO_CHECKLIST.md",
    "docs/PROGRESS.md",
    "docs/SYSTEM_OVERVIEW.md",
    "docs/USER_MANUAL.md",
    "docs/CONFIG_ENV.md",
    "docs/API_REFERENCE_UPDATED.md",
    "docs/DEV_GUIDE.md",
    "docs/OPERATIONS_RUNBOOK.md",
    "docs/TEST_PLAN.md",
    "docs/README.md",
)


def collect_docs_status(doc_paths: Iterable[str] | None = None) -> Dict[str, Any]:
    """
    Return existence/size info for the canonical docs.
    """
    targets = list(doc_paths) if doc_paths is not None else list(CANONICAL_DOC_PATHS)
    docs: list[Dict[str, Any]] = []
    missing: list[str] = []

    for rel_path in targets:
        rel = str(rel_path)
        abs_path = REPO_ROOT / rel
        exists = abs_path.is_file()
        size = abs_path.stat().st_size if exists else None
        docs.append(
            {
                "path": rel,
                "exists": exists,
                "size": size,
            }
        )
        if not exists:
            missing.append(rel)

    return {
        "docs": docs,
        "missing": missing,
    }

