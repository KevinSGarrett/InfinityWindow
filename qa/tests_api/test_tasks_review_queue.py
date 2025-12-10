from __future__ import annotations

import os
from datetime import datetime, timezone

import app.api.main as main
from app.db import models


def _process_candidate(
    db,
    *,
    project_id: int,
    action_type: str,
    confidence: float,
    description: str | None = None,
    target_task: models.Task | None = None,
    matched_text: str | None = None,
    priority: str = "normal",
    blocked_reason: str | None = None,
    dependency_hint: str | None = None,
    conversation_id: int | None = None,
) -> tuple[str, models.Task | None, models.TaskSuggestion | None, list[str]]:
    """Apply the same decision heuristics used by automation."""
    project = db.get(models.Project, project_id)
    blocking_ids = (
        main._blocking_dependency_ids(db, target_task) if target_task is not None else []
    )
    decision, reasons = main._classify_suggestion_decision(
        action_type=action_type,
        confidence=confidence,
        project_archived=bool(project and getattr(project, "is_archived", False)),
        has_blocking_dependencies=bool(blocking_ids),
        ambiguous_text=action_type == "complete"
        and main._is_ambiguous_completion_text(matched_text),
        manual_conflict=main._has_recent_manual_change(target_task) if target_task else False,
    )
    if decision == "auto_applied":
        if action_type == "add":
            task = models.Task(
                project_id=project_id,
                description=description or "",
                status="open",
                priority=priority,
                blocked_reason=blocked_reason,
            )
            db.add(task)
            db.flush()
            main._record_task_automation_event(
                "auto_added",
                task=task,
                confidence=confidence,
                conversation_id=conversation_id,
                matched_text=description,
                details={
                    "priority": priority,
                    "blocked_reason": blocked_reason,
                    "dependency_hint": dependency_hint,
                    "source": "review_queue_test",
                    "decision": decision,
                },
            )
            main._record_suggestion_action(
                "auto_applied",
                action_type="add",
                confidence=confidence,
                project_id=project_id,
                conversation_id=conversation_id,
                target_task=task,
                description=description,
                reasons=reasons,
                blocking_task_ids=None,
                source="review_queue_test",
            )
            db.commit()
            db.refresh(task)
            return decision, task, None, reasons
        if action_type == "complete" and target_task is not None:
            target_task.status = "done"
            target_task.updated_at = datetime.now(timezone.utc)
            main._record_task_automation_event(
                "auto_completed",
                task=target_task,
                confidence=confidence,
                conversation_id=conversation_id,
                matched_text=matched_text or target_task.description,
                details={
                    "source": "review_queue_test",
                    "blocking_task_ids": blocking_ids or None,
                    "decision": decision,
                },
            )
            main._record_suggestion_action(
                "auto_applied",
                action_type="complete",
                confidence=confidence,
                project_id=project_id,
                conversation_id=conversation_id,
                target_task=target_task,
                description=target_task.description,
                reasons=reasons,
                blocking_task_ids=blocking_ids,
                source="review_queue_test",
            )
            db.commit()
            db.refresh(target_task)
            return decision, target_task, None, reasons

    if decision == "queued_for_review":
        suggestion = main._create_task_suggestion(
            db,
            project_id=project_id,
            conversation_id=conversation_id,
            action_type=action_type,
            payload={
                "description": description,
                "priority": priority,
                "blocked_reason": blocked_reason,
                "dependency_hint": dependency_hint,
                "matched_text": matched_text,
                "task_id": getattr(target_task, "id", None),
            },
            confidence=confidence,
            target_task=target_task,
            reasons=reasons,
            blocking_task_ids=blocking_ids,
            source="review_queue_test",
        )
        db.commit()
        db.refresh(suggestion)
        return decision, target_task, suggestion, reasons

    main._record_suggestion_action(
        "ignored",
        action_type=action_type,
        confidence=confidence,
        project_id=project_id,
        conversation_id=conversation_id,
        target_task=target_task,
        description=description or getattr(target_task, "description", None),
        reasons=reasons,
        blocking_task_ids=blocking_ids,
        source="review_queue_test",
    )
    db.commit()
    return decision, target_task, None, reasons


def _telemetry(client):
    return client.get("/debug/telemetry").json()["tasks"]


def test_low_confidence_add_queues_review(client, db_session, project):
    decision, _, suggestion, reasons = _process_candidate(
        db_session,
        project_id=project["id"],
        action_type="add",
        confidence=0.35,
        description="Maybe add a follow-up later",
    )
    assert decision == "queued_for_review"
    assert suggestion is not None
    assert suggestion.status == "pending"
    assert "low_confidence" in reasons or "mid_confidence" in reasons

    suggestions = client.get(
        f"/projects/{project['id']}/task_suggestions", params={"status": "pending"}
    ).json()
    assert suggestions and suggestions[0]["status"] == "pending"
    assert suggestions[0]["reasons"]

    telemetry = _telemetry(client)
    assert telemetry["task_suggestion_queued_for_review"] == 1
    assert telemetry["auto_suggested"] == 1


def test_high_confidence_add_auto_applies(client, db_session, project):
    decision, task, suggestion, _ = _process_candidate(
        db_session,
        project_id=project["id"],
        action_type="add",
        confidence=0.91,
        description="Implement optimistic UI updates",
        priority="high",
    )
    assert decision == "auto_applied"
    assert task is not None
    assert suggestion is None
    tasks = client.get(f"/projects/{project['id']}/tasks").json()
    assert any("optimistic ui updates" in t["description"].lower() for t in tasks)

    telemetry = _telemetry(client)
    assert telemetry["auto_added"] == 1
    assert telemetry["task_suggestion_auto_applied"] == 1


def test_dependency_blocks_completion_queue(client, db_session, project):
    dep = models.Task(project_id=project["id"], description="Finish API refactor", status="open")
    target = models.Task(project_id=project["id"], description="Ship release notes", status="open")
    db_session.add_all([dep, target])
    db_session.flush()
    db_session.add(
        models.TaskDependency(
            project_id=project["id"], task_id=target.id, depends_on_task_id=dep.id
        )
    )
    db_session.commit()

    decision, _, suggestion, reasons = _process_candidate(
        db_session,
        project_id=project["id"],
        action_type="complete",
        confidence=0.9,
        target_task=target,
        matched_text="Release notes are done",
    )
    assert decision == "queued_for_review"
    assert suggestion is not None
    assert suggestion.status == "pending"
    assert "blocking_dependencies" in reasons

    refreshed_target = db_session.get(models.Task, target.id)
    assert refreshed_target.status == "open"

    suggestions = client.get(
        f"/projects/{project['id']}/task_suggestions", params={"status": "pending"}
    ).json()
    assert suggestions[0]["blocking_task_ids"] == [dep.id]

    telemetry = _telemetry(client)
    assert telemetry["task_suggestion_queued_for_review"] == 1
    assert telemetry["task_suggestion_blocked_by_dependency"] == 1


def test_archived_project_automation_noops(client, db_session):
    archived_resp = client.post(
        "/projects",
        json={
            "name": "ArchivedProject",
            "description": "archived",
            "is_archived": True,
            "local_root_path": os.getcwd(),
        },
    )
    assert archived_resp.status_code == 200, archived_resp.text
    archived = archived_resp.json()

    # Direct automation request should error safely.
    auto_resp = client.post(f"/projects/{archived['id']}/auto_update_tasks")
    assert auto_resp.status_code == 400

    decision, task, suggestion, reasons = _process_candidate(
        db_session,
        project_id=archived["id"],
        action_type="add",
        confidence=0.9,
        description="Do not add in archived project",
    )
    assert decision == "ignored"
    assert task is None and suggestion is None
    assert "project_archived" in reasons

    tasks = client.get(f"/projects/{archived['id']}/tasks").json()
    assert tasks == []

    telemetry = _telemetry(client)
    assert telemetry["task_suggestion_ignored"] == 1

