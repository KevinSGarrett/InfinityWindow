from pathlib import Path

from qa._utils import ensure_backend_on_path

ensure_backend_on_path()
from app.api.main import CANONICAL_DOC_PATHS  # noqa: E402


def test_canonical_docs_exist_on_disk() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    missing: list[str] = []
    empty: list[str] = []

    for rel_path in CANONICAL_DOC_PATHS:
        abs_path = repo_root / rel_path
        if not abs_path.exists():
            missing.append(rel_path)
            continue
        if abs_path.stat().st_size == 0:
            empty.append(rel_path)

    assert missing == [], f"Missing canonical docs on disk: {missing}"
    assert empty == [], f"Canonical docs should not be empty: {empty}"

