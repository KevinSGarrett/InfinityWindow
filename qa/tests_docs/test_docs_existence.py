from pathlib import Path

import pytest


DOC_PATHS = [
    Path("docs/REQUIREMENTS_CRM.md"),
    Path("docs/ALIGNMENT_OVERVIEW.md"),
    Path("docs/TODO_CHECKLIST.md"),
    Path("docs/PROGRESS.md"),
    Path("docs/USAGE_TELEMETRY_DASHBOARD.md"),
    Path("docs/USER_MANUAL.md"),
    Path("docs/API_REFERENCE.md"),
    Path("docs/API_REFERENCE_UPDATED.md"),
    Path("docs/ISSUES_LOG.md"),
]


@pytest.mark.parametrize("path", DOC_PATHS)
def test_docs_exist(path: Path) -> None:
    assert path.exists(), f"{path} is missing"

