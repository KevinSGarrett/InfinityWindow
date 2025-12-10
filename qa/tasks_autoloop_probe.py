from __future__ import annotations

from datetime import datetime

from ._utils import ensure_backend_on_path

ensure_backend_on_path()

from app.api.main import auto_update_tasks_from_conversation  # noqa: E402
from app.db import models  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402


def run() -> None:
    """Verify the autonomous TODO maintainer adds and completes tasks."""
    session = SessionLocal()
    try:
        project = models.Project(
            name=f"QA Task Loop {datetime.utcnow().isoformat()}",
            description="Smoke probe",
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        conversation = models.Conversation(project_id=project.id, title="Task probe")
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

        todo_content = (
            "Here are the TODOs we must knock out next:\n"
            "- Wire message embeddings end-to-end.\n"
            "- Add audit logging to the backend.\n"
            "- Polish the docs for this release."
        )
        seed_messages = [
            models.Message(
                conversation_id=conversation.id,
                role="user",
                content=todo_content,
            ),
            models.Message(
                conversation_id=conversation.id,
                role="assistant",
                content="Copy that; logging the TODOs now.",
            ),
        ]
        session.add_all(seed_messages)
        session.commit()

        auto_update_tasks_from_conversation(session, conversation)
        session.commit()

        tasks = (
            session.query(models.Task)
            .filter(models.Task.project_id == project.id)
            .order_by(models.Task.id)
            .all()
        )
        if len(tasks) < 3:
            raise AssertionError(
                f"Expected at least 3 auto-generated tasks, found {len(tasks)}."
            )

        completion_message = models.Message(
            conversation_id=conversation.id,
            role="user",
            content=(
                "Wire message embeddings end-to-end is now done and polish the docs for this release is complete. "
                "Audit logging to the backend is still pending."
            ),
        )
        session.add(completion_message)
        session.commit()

        auto_update_tasks_from_conversation(session, conversation)
        session.commit()

        refreshed_tasks = (
            session.query(models.Task)
            .filter(models.Task.project_id == project.id)
            .order_by(models.Task.id)
            .all()
        )
        done = [task for task in refreshed_tasks if task.status == "done"]
        open_tasks = [task for task in refreshed_tasks if task.status == "open"]

        if len(done) < 1:
            raise AssertionError(
                "Expected at least one task to be auto-completed after completion message."
            )

        if not any("audit logging" in task.description.lower() for task in open_tasks):
            raise AssertionError(
                "Expected 'audit logging' follow-up task to remain open."
            )
    finally:
        # Clean up temp data to keep the DB tidy for future runs.
        session.query(models.Task).filter(models.Task.project_id == project.id).delete()
        session.query(models.Message).filter(
            models.Message.conversation_id == conversation.id
        ).delete()
        session.delete(conversation)
        session.delete(project)
        session.commit()
        session.close()

