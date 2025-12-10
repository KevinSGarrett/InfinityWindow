from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.db import models


def _make_usage_record(
    project_id: int,
    created_at: datetime,
    tokens_in: int,
    tokens_out: int,
    model: str = "gpt-4.1",
) -> models.UsageRecord:
    return models.UsageRecord(
        project_id=project_id,
        conversation_id=None,
        message_id=None,
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_estimate=0.0,
        created_at=created_at,
    )


def test_usage_summary_windows(client: TestClient, db_session, project: dict) -> None:
    now = datetime.now(timezone.utc)

    def _ts(delta: timedelta) -> datetime:
        return (now - delta).replace(tzinfo=None)

    recent = _make_usage_record(project["id"], _ts(timedelta(minutes=30)), 50, 20)
    mid = _make_usage_record(project["id"], _ts(timedelta(hours=5)), 30, 10)
    days = _make_usage_record(project["id"], _ts(timedelta(days=3)), 70, 30)
    old = _make_usage_record(project["id"], _ts(timedelta(days=9)), 10, 5)

    db_session.add_all([recent, mid, days, old])
    db_session.commit()

    base_url = f"/projects/{project['id']}/usage_summary"

    one_hour = client.get(f"{base_url}?window=1h")
    assert one_hour.status_code == 200, one_hour.text
    payload = one_hour.json()
    assert payload["window"] == "1h"
    assert payload["total_tokens_in"] == 50
    assert payload["total_tokens_out"] == 20
    assert len(payload["records"]) == 1

    default_window = client.get(base_url)
    assert default_window.status_code == 200, default_window.text
    default_payload = default_window.json()
    assert default_payload["window"] == "24h"
    assert default_payload["total_tokens_in"] == 80
    assert default_payload["total_tokens_out"] == 30
    assert len(default_payload["records"]) == 2

    seven_days = client.get(f"{base_url}?window=7d")
    assert seven_days.status_code == 200, seven_days.text
    seven_payload = seven_days.json()
    assert seven_payload["window"] == "7d"
    assert seven_payload["total_tokens_in"] == 150
    assert seven_payload["total_tokens_out"] == 60
    assert len(seven_payload["records"]) == 3
    assert seven_payload["total_cost_estimate"] is None or seven_payload["total_cost_estimate"] >= 0

    invalid = client.get(f"{base_url}?window=bogus")
    assert invalid.status_code == 400


def test_usage_summary_empty_project(client: TestClient) -> None:
    root_path = str(Path(__file__).resolve().parents[2])
    proj_resp = client.post(
        "/projects",
        json={
            "name": "EmptyProject",
            "description": "no usage",
            "local_root_path": root_path,
        },
    )
    assert proj_resp.status_code == 200, proj_resp.text
    empty_project = proj_resp.json()

    resp = client.get(f"/projects/{empty_project['id']}/usage_summary")
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["records"] == []
    assert payload["total_tokens_in"] == 0
    assert payload["total_tokens_out"] == 0
    assert payload["total_cost_estimate"] is None or payload["total_cost_estimate"] == 0

