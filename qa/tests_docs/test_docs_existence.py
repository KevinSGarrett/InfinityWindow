from pathlib import Path


REQUIRED_DOC_PATHS = [
    Path("docs/REQUIREMENTS_CRM.md"),
    Path("docs/MODEL_MATRIX.md"),
    Path("docs/AUTOPILOT_PLAN.md"),
    Path("docs/AUTOPILOT_LEARNING.md"),
    Path("docs/AUTOPILOT_LIMITATIONS.md"),
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_required_docs_exist() -> None:
    root = _repo_root()
    missing = [str(root / path) for path in REQUIRED_DOC_PATHS if not (root / path).exists()]
    assert not missing, f"Missing required docs: {', '.join(missing)}"

