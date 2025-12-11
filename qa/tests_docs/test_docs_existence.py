from pathlib import Path

from qa._utils import ensure_backend_on_path

ensure_backend_on_path()

from app.docs_guardrails import CANONICAL_DOC_PATHS, REPO_ROOT  # noqa: E402


def test_canonical_docs_exist() -> None:
    """
    Ensure the canonical docs are present on disk and non-empty.
    """
    for rel_path in CANONICAL_DOC_PATHS:
        abs_path = REPO_ROOT / rel_path
        assert abs_path.exists(), f"{rel_path} should exist"
        assert abs_path.is_file(), f"{rel_path} should be a file"
        size = abs_path.stat().st_size
        assert size > 0, f"{rel_path} should not be empty (size={size})"

