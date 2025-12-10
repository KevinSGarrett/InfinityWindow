from __future__ import annotations

from app.db import models
import app.api.main as main


def test_task_dependency_records_blockers(db_session, project):
    blocker = models.Task(
        project_id=project["id"], description="Prepare backend migration", status="open"
    )
    target = models.Task(
        project_id=project["id"], description="Release deployment", status="open"
    )
    db_session.add_all([blocker, target])
    db_session.flush()
    db_session.add(
        models.TaskDependency(
            project_id=project["id"], task_id=target.id, depends_on_task_id=blocker.id
        )
    )
    db_session.commit()

    blocking_ids = main._blocking_dependency_ids(db_session, target)
    assert blocking_ids == [blocker.id]

    # Mark dependency done and ensure it no longer blocks.
    blocker.status = "done"
    db_session.commit()
    assert main._blocking_dependency_ids(db_session, target) == []

