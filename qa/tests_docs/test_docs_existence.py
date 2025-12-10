from pathlib import Path


def test_issues_log_exists() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    issues_log = repo_root / "docs" / "ISSUES_LOG.md"
    assert issues_log.exists(), "docs/ISSUES_LOG.md should exist for auditability"

