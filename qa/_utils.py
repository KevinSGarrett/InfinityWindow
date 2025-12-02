from __future__ import annotations

import contextlib
import sys
from pathlib import Path
from typing import Iterator, Callable, Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"


def ensure_backend_on_path() -> None:
    """Append the backend directory to sys.path if it is not already present."""
    backend_str = str(BACKEND_DIR)
    if backend_str not in sys.path:
        sys.path.append(backend_str)


@contextlib.contextmanager
def temporary_attr(obj: Any, attr: str, value: Any) -> Iterator[None]:
    """Temporarily replace obj.attr with value."""
    original = getattr(obj, attr)
    setattr(obj, attr, value)
    try:
        yield
    finally:
        setattr(obj, attr, original)


@contextlib.contextmanager
def multi_patch(patches: list[tuple[Any, str, Any]]) -> Iterator[None]:
    """Patch multiple attributes using `temporary_attr`."""
    stack: list[Callable[[], None]] = []
    try:
        for obj, attr, value in patches:
            original = getattr(obj, attr)
            setattr(obj, attr, value)
            stack.append(lambda o=obj, a=attr, v=original: setattr(o, a, v))
        yield
    finally:
        while stack:
            undo = stack.pop()
            undo()

