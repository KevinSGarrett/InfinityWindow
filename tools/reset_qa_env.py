#!/usr/bin/env python3
"""
Guarded helper for resetting the local QA data stores.

Usage:
    python tools/reset_qa_env.py --confirm

It performs the following steps:
1. Verifies that the default backend port (8000) is not in use unless --force is set.
2. Moves `backend/infinitywindow.db` to a timestamped backup (or deletes with --purge).
3. Moves `backend/chroma_data` to a timestamped backup (or deletes with --purge).

The script avoids destructive operations when the backend is still running so we
don't hit file-lock errors on Windows. Pass --force if you're absolutely sure the
process has been stopped but the port-check still fails.
"""

from __future__ import annotations

import argparse
import shutil
import socket
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
DB_PATH = BACKEND_DIR / "infinitywindow.db"
CHROMA_PATH = BACKEND_DIR / "chroma_data"


def _is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def _timestamp_suffix() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def _backup_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.bak.{_timestamp_suffix()}")


def _move_with_backup(path: Path) -> Path:
    backup = _backup_path(path)
    shutil.move(str(path), str(backup))
    return backup


def _delete_path(path: Path) -> None:
    if path.is_file():
        path.unlink()
    else:
        shutil.rmtree(path)


def _reset_target(path: Path, *, purge: bool) -> str:
    if not path.exists():
        return f"{path} (already missing)"

    if purge:
        _delete_path(path)
        return f"{path} deleted"

    backup = _move_with_backup(path)
    return f"{path} moved to {backup}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reset QA database + Chroma store.")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required safety latch to run destructive steps.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip the backend port check (only use if you're sure it's stopped).",
    )
    parser.add_argument(
        "--purge",
        action="store_true",
        help="Delete instead of moving to timestamped backups.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to probe for the backend (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Backend port to probe (default: 8000).",
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Do not touch backend/infinitywindow.db.",
    )
    parser.add_argument(
        "--skip-chroma",
        action="store_true",
        help="Do not touch backend/chroma_data.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.confirm:
        print("Refusing to run without --confirm (safety latch).")
        return 1

    if not args.force and _is_port_open(args.host, args.port):
        print(
            f"Port {args.port} on {args.host} appears to be in use. "
            "Stop uvicorn/frontend first or pass --force if you're sure it's safe."
        )
        return 2

    results: list[str] = []
    if not args.skip_db:
        results.append(_reset_target(DB_PATH, purge=args.purge))
    else:
        results.append(f"Skipping {DB_PATH}")

    if not args.skip_chroma:
        results.append(_reset_target(CHROMA_PATH, purge=args.purge))
    else:
        results.append(f"Skipping {CHROMA_PATH}")

    print("\n".join(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())

