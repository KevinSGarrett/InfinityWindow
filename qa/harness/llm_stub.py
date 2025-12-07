"""
Deterministic LLM stub used by API tests to avoid external calls.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict


def stubbed_chat(mode: str, content: Any) -> Dict[str, Any]:
    """
    Return a deterministic stubbed response for any chat content.
    """
    if isinstance(content, str):
        normalized = content
    else:
        normalized = json.dumps(content, sort_keys=True, ensure_ascii=False)

    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:8]
    return {
        "mode": mode,
        "reply": f"[stub-{mode}-{digest}]",
        "tokens_in": len(normalized.split()),
        "tokens_out": 12,
        "cost": 0.0,
    }

