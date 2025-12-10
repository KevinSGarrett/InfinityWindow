"""
Lightweight perf smoke for CI.

Runs a small pytest subset to get a rough duration signal without full coverage.
Optional env:
- PYTEST_TARGETS: space-separated pytest targets (default: qa/tests_api/test_api_projects.py)
- PYTEST_OPTS: extra pytest args (e.g., -q --maxfail=1)
"""

from __future__ import annotations

import os
import subprocess
import sys
import time


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env = os.environ.copy()
    # Ensure repo root and backend are on PYTHONPATH
    py_path = env.get("PYTHONPATH", "")
    parts = [repo_root, os.path.join(repo_root, "backend")]
    if py_path:
        parts.append(py_path)
    env["PYTHONPATH"] = os.pathsep.join(parts)

    targets = env.get("PYTEST_TARGETS", "qa/tests_api/test_api_projects.py")
    opts = env.get("PYTEST_OPTS", "-q --maxfail=1 --disable-warnings")

    cmd = [sys.executable, "-m", "pytest", *opts.split(), *targets.split()]
    start = time.perf_counter()
    print(f"[perf_smoke] Running: {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=repo_root, env=env)
    duration = time.perf_counter() - start
    print(f"[perf_smoke] Duration: {duration:.2f}s, exit={proc.returncode}")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())

