from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_usage_summary_documented() -> None:
    content = (REPO_ROOT / "docs" / "API_REFERENCE.md").read_text(encoding="utf-8")
    assert "/projects/{project_id}/usage_summary" in content


def test_crm_status_updated() -> None:
    content = (REPO_ROOT / "docs" / "REQUIREMENTS_CRM.md").read_text(encoding="utf-8")
    assert "Usage & telemetry dashboard" in content
    assert "Status: Implemented" in content
    assert "Task-aware auto-mode routing" in content

