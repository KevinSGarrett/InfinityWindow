import os
import uuid
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from qa._utils import ensure_backend_on_path
from qa.harness.llm_stub import stubbed_chat

ensure_backend_on_path()
import app.llm.openai_client as openai_client  # noqa: E402
from app.llm import embeddings  # noqa: E402
from app.api.main import app  # noqa: E402
import app.api.main as main  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.db import models  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
LOCAL_ROOT = str(Path(__file__).resolve().parents[2])


@pytest.fixture(scope="session", autouse=True)
def _set_cwd() -> Iterator[None]:
    """
    Ensure the backend directory is the working directory for SQLite paths.
    """
    original = Path.cwd()
    os.chdir(BACKEND_DIR)
    os.environ.setdefault("LLM_MODE", "stub")
    try:
        yield
    finally:
        os.chdir(original)


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    """
    Provide a FastAPI TestClient with LLM calls stubbed out.
    """
    mp = pytest.MonkeyPatch()

    def fake_generate_reply_from_history(messages, mode: str = "auto", model_override=None, **_: object):
        stub = stubbed_chat(mode, messages)
        return stub["reply"]

    mp.setattr(openai_client, "generate_reply_from_history", fake_generate_reply_from_history)
    mp.setattr(main, "generate_reply_from_history", fake_generate_reply_from_history)

    def fake_auto_update_tasks_from_conversation(
        db,
        conversation,
        max_messages: int = 16,
    ):
        session = db or SessionLocal()
        close_session = db is None
        try:
            project_id = conversation.project_id
            existing = {
                t.description.lower()
                for t in session.query(models.Task).filter(models.Task.project_id == project_id)
            }
            seeds = [
                ("Add login page", 0.82),
                ("Fix logout bug", 0.8),
                ("Finish the payment retry flow", 0.8),
                ("Document the new API responses", 0.75),
            ]
            for desc, conf in seeds:
                if desc.lower() not in existing:
                    task_obj = models.Task(
                        project_id=project_id,
                        description=desc,
                        status="open",
                        priority="normal",
                        auto_notes="Added automatically (stub)",
                    )
                    session.add(task_obj)
                    session.flush()
                    main._record_task_action(
                        "auto_added",
                        task=task_obj,
                        confidence=conf,
                        conversation_id=conversation.id if conversation else None,
                        details={"source": "stub_auto_update"},
                    )
            session.commit()

            messages_q = (
                session.query(models.Message)
                .join(models.Conversation, models.Conversation.id == models.Message.conversation_id)
                .filter(models.Conversation.project_id == project_id)
            )
            latest = messages_q.order_by(models.Message.id.desc()).first()
            latest_message = (latest.content or "").lower() if latest else ""
            completion_texts = [
                (latest_message,),
                tuple((m.content or "").lower() for m in messages_q if m.content),
            ]
            flat_texts = [t for group in completion_texts for t in (group if isinstance(group, tuple) else (group,))]
            if any("login" in text and "done" in text for text in flat_texts):
                updated = (
                    session.query(models.Task)
                    .filter(
                        models.Task.project_id == project_id,
                        models.Task.description.ilike("%login%"),
                    )
                    .first()
                )
                if updated:
                    updated.status = "done"
                    updated.auto_notes = "Closed automatically (stub) after chat."
                    main._record_task_action(
                        "auto_completed",
                        task=updated,
                        confidence=0.91,
                        conversation_id=conversation.id if conversation else None,
                        details={"matched": "login"},
                    )
            if any("payment retry flow" in text and "done" in text for text in flat_texts):
                updated = (
                    session.query(models.Task)
                    .filter(
                        models.Task.project_id == project_id,
                        models.Task.description.ilike("%payment retry flow%"),
                    )
                    .first()
                )
                if updated:
                    updated.status = "done"
                    updated.auto_notes = "Closed automatically (stub) after chat."
                    main._record_task_action(
                        "auto_completed",
                        task=updated,
                        confidence=0.9,
                        conversation_id=conversation.id if conversation else None,
                        details={"matched": "payment"},
                    )
            session.commit()
        finally:
            if close_session:
                session.close()

    mp.setattr(main, "auto_update_tasks_from_conversation", fake_auto_update_tasks_from_conversation)
    mp.setattr(openai_client, "get_client", lambda: None)
    mp.setattr(embeddings, "get_embedding", lambda _text, _model=None: [0.0, 1.0, 2.0])

    try:
        yield TestClient(app)
    finally:
        mp.undo()


@pytest.fixture
def project(client: TestClient) -> dict:
    resp = client.post(
        "/projects",
        json={
            "name": f"QA_Project_{os.getpid()}_{uuid.uuid4().hex[:8]}",
            "description": "QA autogenerated project",
            "local_root_path": LOCAL_ROOT,
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()

