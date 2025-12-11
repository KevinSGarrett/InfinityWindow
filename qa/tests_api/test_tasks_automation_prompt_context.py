import importlib.util
from pathlib import Path

from app.api import main
from app.db import models


def _load_fresh_main():
    spec = importlib.util.spec_from_file_location("app.api.main_fresh", Path(main.__file__))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load app.api.main for context testing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _create_conversation(db_session, project: models.Project) -> models.Conversation:
    conversation = models.Conversation(
        project_id=project.id,
        title="Context-aware conversation",
    )
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)
    return conversation


def _add_user_message(db_session, conversation: models.Conversation, content: str) -> None:
    message = models.Message(
        conversation_id=conversation.id,
        role="user",
        content=content,
    )
    db_session.add(message)
    db_session.commit()


def test_auto_update_tasks_prompt_includes_project_context_block(monkeypatch, db_session):
    project = models.Project(
        name="CtxProject",
        description="Backend reliability stream",
        instruction_text="Follow the release checklist and keep outages out.",
        pinned_note_text="Sprint focus: stabilize ingestion and telemetry",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    conversation = _create_conversation(db_session, project)
    _add_user_message(
        db_session,
        conversation,
        "Let's plan the sprint tasks and make sure we cover blockers.",
    )

    critical_task = models.Task(
        project_id=project.id,
        description="Patch ingestion crash",
        status="open",
        priority="critical",
        blocked_reason="waiting on logs",
    )
    high_task = models.Task(
        project_id=project.id,
        description="Improve telemetry alerts",
        status="open",
        priority="high",
    )
    db_session.add_all([critical_task, high_task])
    db_session.commit()

    captured: dict = {}

    def fake_generate_reply_from_history(messages, model=None, mode="fast", **kwargs):
        captured["messages"] = messages
        return '{"tasks": []}'

    fresh_main = _load_fresh_main()
    monkeypatch.setattr(fresh_main, "generate_reply_from_history", fake_generate_reply_from_history)

    fresh_main.auto_update_tasks_from_conversation(db_session, conversation)

    assert "messages" in captured, "LLM prompt was not invoked"
    system_prompt = captured["messages"][0]["content"]
    assert "[PROJECT_CONTEXT]" in system_prompt
    assert "Instructions: Follow the release checklist" in system_prompt
    assert "Pinned note / sprint focus: Sprint focus: stabilize ingestion" in system_prompt
    assert "Patch ingestion crash" in system_prompt
    assert "priority=CRITICAL" in system_prompt
    assert "blocked=Yes" in system_prompt
    assert "Improve telemetry alerts" in system_prompt
    assert "[/PROJECT_CONTEXT]" in system_prompt


def test_auto_update_tasks_prompt_handles_missing_context(monkeypatch, db_session):
    project = models.Project(
        name="CtxProjectMissing",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    conversation = _create_conversation(db_session, project)
    _add_user_message(db_session, conversation, "Quick sync on backlog.")

    captured: dict = {}

    def fake_generate_reply_from_history(messages, model=None, mode="fast", **kwargs):
        captured["messages"] = messages
        return '{"tasks": []}'

    fresh_main = _load_fresh_main()
    monkeypatch.setattr(fresh_main, "generate_reply_from_history", fake_generate_reply_from_history)

    fresh_main.auto_update_tasks_from_conversation(db_session, conversation)

    assert "messages" in captured, "LLM prompt was not invoked"
    system_prompt = captured["messages"][0]["content"]
    assert "[PROJECT_CONTEXT]" in system_prompt
    assert "Instructions: None set" in system_prompt
    assert "Pinned note / sprint focus: None set" in system_prompt
    assert "Project goal/description: None set" in system_prompt
    assert "High-priority open tasks:" in system_prompt
    assert "- None set" in system_prompt
    assert "[/PROJECT_CONTEXT]" in system_prompt

