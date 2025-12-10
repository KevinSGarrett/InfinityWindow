from pathlib import Path


def test_core_docs_exist_and_nonempty() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    required_docs = [
        "docs/README.md",
        "docs/CONFIG_ENV.md",
        "docs/ISSUES_LOG.md",
        "docs/TODO_CHECKLIST.md",
    ]
    for rel_path in required_docs:
        path = repo_root / rel_path
        assert path.exists(), f"{rel_path} is missing"
        assert path.stat().st_size > 0, f"{rel_path} is empty"

