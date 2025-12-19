"""
Security-focused API checks.
"""

from pathlib import Path

import pytest
from fastapi import HTTPException
from hypothesis import HealthCheck, given, settings, strategies as st

from app.api import main as api_main


@settings(suppress_health_check=[HealthCheck.filter_too_much])
@given(st.sampled_from(["..", "../x", "x/..", "0..", "..\\foo", "bar\\..\\baz"]))
def test_safe_join_blocks_parent_segments(bad_path: str):
    """K-SEC-FS-02: _safe_join rejects traversal attempts."""
    root = Path(".").resolve()
    with pytest.raises(HTTPException):
        api_main._safe_join(root, bad_path)


def test_terminal_injection_rejected(client, project):
    """K-SEC-TERM-01: Commands with injection characters should be rejected."""
    resp = client.post(
        "/terminal/run",
        json={
            "project_id": project["id"],
            "command": "echo SAFE & echo PWNED",
            "timeout_seconds": 5,
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == api_main.UNSAFE_TERMINAL_COMMAND_DETAIL

