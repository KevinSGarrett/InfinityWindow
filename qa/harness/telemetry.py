from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

import requests


def fetch_telemetry(out_path: str, port: int | None = None) -> Dict[str, Any]:
    """
    Fetch telemetry from the backend debug endpoint and persist it.
    """
    target_port = port or int(os.environ.get("BACKEND_PORT", "8000"))
    url = f"http://localhost:{target_port}/debug/telemetry"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        payload: Dict[str, Any] = resp.json()
    except Exception as exc:  # noqa: BLE001 - surface telemetry fetch errors in output
        payload = {"error": str(exc)}

    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload

