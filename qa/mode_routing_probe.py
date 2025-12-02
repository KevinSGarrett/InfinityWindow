from __future__ import annotations

import time
from typing import Callable, Dict, List

from ._utils import ensure_backend_on_path, temporary_attr

ensure_backend_on_path()

from fastapi.testclient import TestClient  # noqa: E402

import app.api.main as main_module  # noqa: E402
from app.api.main import app  # noqa: E402
from app.llm import openai_client  # noqa: E402


def run() -> None:
    """
    Ensure explicit chat modes map to their configured models and
    auto-mode heuristics route to the appropriate tiers (fast, code, research, deep).
    """
    client = TestClient(app)
    failure_budget: Dict[str, int] = {}
    captured: Dict[str, str] = {}
    current_test = {"id": ""}

    def fake_call_model(messages, model, **kwargs):  # type: ignore[override]
        remaining = failure_budget.get(model, 0)
        if remaining > 0:
            failure_budget[model] = remaining - 1
            raise RuntimeError(f"Simulated failure for {model}")
        captured.setdefault(current_test["id"], model)
        return f"FAKE-{model}"

    scenarios: List[Dict[str, Callable[[], str] | str]] = [
        {
            "id": "B-Mode-01-auto",
            "mode": "auto",
            "message": "Mode auto QA ping",
            "expected": lambda: openai_client._get_model_for_mode("fast"),
        },
        {
            "id": "B-Mode-01-fast",
            "mode": "fast",
            "message": "Mode fast QA ping",
            "expected": lambda: openai_client._get_model_for_mode("fast"),
        },
        {
            "id": "B-Mode-01-deep",
            "mode": "deep",
            "message": "Mode deep QA ping",
            "expected": lambda: openai_client._get_model_for_mode("deep"),
        },
        {
            "id": "B-Mode-01-budget",
            "mode": "budget",
            "message": "Mode budget QA ping",
            "expected": lambda: openai_client._get_model_for_mode("budget"),
        },
        {
            "id": "B-Mode-01-research-fallback",
            "mode": "research",
            "message": "Mode research QA ping",
            "expected": lambda: openai_client._get_model_for_mode("auto"),
            "fail_first": openai_client._get_model_for_mode("research"),
        },
        {
            "id": "B-Mode-01-code",
            "mode": "code",
            "message": "Mode code QA ping with snippet",
            "expected": lambda: openai_client._get_model_for_mode("code"),
        },
        {
            "id": "B-Mode-02-auto-fast",
            "mode": "auto",
            "message": "Ping?",
            "expected": lambda: openai_client._get_model_for_mode("fast"),
        },
        {
            "id": "B-Mode-02-auto-code",
            "mode": "auto",
            "message": "Fix this snippet:\n```python\nprint('hi')\n```",
            "expected": lambda: openai_client._get_model_for_mode("code"),
        },
        {
            "id": "B-Mode-02-auto-research",
            "mode": "auto",
            "message": (
                "I need a comprehensive literature review about exoplanet detection "
                "methods across the last decade including references."
            ),
            "expected": lambda: openai_client._get_model_for_mode("research"),
        },
        {
            "id": "B-Mode-02-auto-deep",
            "mode": "auto",
            "message": (
                "Outline a multi-quarter roadmap for rebuilding the ingestion pipeline "
                "with schema evolution, rollbacks, and telemetry milestones."
            ),
            "expected": lambda: openai_client._get_model_for_mode("deep"),
        },
    ]

    with temporary_attr(openai_client, "_call_model", fake_call_model), temporary_attr(
        main_module, "auto_update_tasks_from_conversation", lambda *_, **__: None
    ):
        project_resp = client.post(
            "/projects",
            json={"name": f"QA Mode Probe {int(time.time())}"},
        )
        project_resp.raise_for_status()
        project = project_resp.json()

        for scenario in scenarios:
            current_test["id"] = scenario["id"]  # type: ignore[index]
            failure_budget.clear()
            fail_first = scenario.get("fail_first")
            if fail_first:
                failure_budget[str(fail_first)] = 1

            payload = {
                "project_id": project["id"],
                "message": scenario["message"],
            }
            if scenario["mode"] != "auto":
                payload["mode"] = scenario["mode"]

            resp = client.post("/chat", json=payload)
            resp.raise_for_status()

        mismatches = []
        for scenario in scenarios:
            expected_model = scenario["expected"]()  # type: ignore[operator]
            used_model = captured.get(scenario["id"])  # type: ignore[index]
            if used_model != expected_model:
                mismatches.append(
                    f"{scenario['id']} expected {expected_model}, got {used_model}"
                )

        if mismatches:
            raise AssertionError(
                "Mode routing mismatches detected:\n- " + "\n- ".join(mismatches)
            )

