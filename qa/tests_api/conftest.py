import difflib
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from qa._utils import ensure_backend_on_path
from qa.harness.llm_stub import stubbed_chat

ensure_backend_on_path()
import app.llm.openai_client as openai_client  # noqa: E402
from app.llm import embeddings  # noqa: E402
from app.api.main import app  # noqa: E402
import app.api.main as main  # noqa: E402
import app.db.session as db_session  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db import models  # noqa: E402
from app.vectorstore import chroma_store  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
LOCAL_ROOT = str(Path(__file__).resolve().parents[2])
STUB_EMBED_DIM = 1536


def _stub_embedding(text: str, dim: int = STUB_EMBED_DIM) -> list[float]:
    base = float(len(text) % 13) / 10.0
    return [base + (i % 5) * 0.01 for i in range(dim)]


@pytest.fixture(scope="session", autouse=True)
def _set_cwd() -> Iterator[None]:
    """
    Ensure the backend directory is the working directory for SQLite paths.
    """
    original = Path.cwd()
    os.chdir(BACKEND_DIR)
    os.environ.setdefault("LLM_MODE", "stub")
    os.environ.setdefault("VECTORSTORE_MODE", "stub")
    try:
        yield
    finally:
        os.chdir(original)


@pytest.fixture(scope="session")
def _temp_db_and_chroma(tmp_path_factory: pytest.TempPathFactory) -> Iterator[dict]:
    """
    Isolate SQLite and Chroma storage for API tests.
    """
    db_dir = tmp_path_factory.mktemp("api-db")
    db_path = db_dir / "infinitywindow.db"

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={
            "check_same_thread": False,
            "timeout": 60.0,
        },
        pool_pre_ping=True,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)

    mp = pytest.MonkeyPatch()
    mp.setattr(db_session, "engine", engine, raising=False)
    mp.setattr(db_session, "SessionLocal", TestingSessionLocal, raising=False)
    mp.setattr(main, "engine", engine, raising=False)
    mp.setattr(main, "SessionLocal", TestingSessionLocal, raising=False)
    mp.setattr(sys.modules[__name__], "SessionLocal", TestingSessionLocal, raising=False)

    chroma_dir = tmp_path_factory.mktemp("api-chroma")
    mp.setattr(chroma_store, "_CHROMA_PATH", chroma_dir, raising=False)
    chroma_store._reset_chroma_persistence(clear_data=True)

    def fake_embed_texts_batched(texts, **_: object):
        return [_stub_embedding(text) for text in texts] if texts else []

    mp.setattr(embeddings, "embed_texts_batched", fake_embed_texts_batched, raising=False)

    try:
        yield {"engine": engine, "SessionLocal": TestingSessionLocal}
    finally:
        chroma_store._reset_chroma_persistence(clear_data=True)
        engine.dispose()
        mp.undo()


@pytest.fixture(autouse=True)
def _reset_state(_temp_db_and_chroma: dict) -> Iterator[None]:
    """
    Reset database tables and Chroma persistence between tests.
    """
    engine = _temp_db_and_chroma["engine"]
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    chroma_store._reset_chroma_persistence(clear_data=True)
    main.reset_task_telemetry()
    yield


@pytest.fixture
def db_session(_temp_db_and_chroma: dict) -> Iterator[db_session.SessionLocal]:
    session = _temp_db_and_chroma["SessionLocal"]()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def client(_temp_db_and_chroma: dict) -> Iterator[TestClient]:
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
        model_name: str | None = None,
        **_: object,
    ):
        session = db or SessionLocal()
        close_session = db is None
        try:
            project_id = conversation.project_id
            seeds = [
                ("Add login page", 0.82),
                ("Fix logout bug", 0.8),
                ("Finish the payment retry flow", 0.8),
                ("Document the new API responses", 0.75),
            ]
            for desc, conf in seeds:
                existing_task = (
                    session.query(models.Task)
                    .filter(
                        models.Task.project_id == project_id,
                        models.Task.description == desc,
                    )
                    .first()
                )
                if existing_task:
                    main._record_task_automation_event(
                        "auto_deduped",
                        task=existing_task,
                        confidence=conf,
                        conversation_id=conversation.id if conversation else None,
                        matched_text=desc,
                        details={"source": "stub_auto_update"},
                        existing_task_description=existing_task.description,
                    )
                    continue

                task_obj = models.Task(
                    project_id=project_id,
                    description=desc,
                    status="open",
                    priority="normal",
                )
                session.add(task_obj)
                session.flush()
                main._record_task_automation_event(
                    "auto_added",
                    task=task_obj,
                    confidence=conf,
                    conversation_id=conversation.id if conversation else None,
                    matched_text=desc,
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
            user_messages = [
                (m.content or "").lower()
                for m in messages_q
                if getattr(m, "role", "").lower() == "user"
            ]
            latest_user_message = user_messages[-1] if user_messages else latest_message
            dedupe_candidates: list[str] = []
            if "simple login page" in latest_user_message:
                dedupe_candidates.append("Add simple login page")
            for candidate in dedupe_candidates:
                open_tasks = (
                    session.query(models.Task)
                    .filter(
                        models.Task.project_id == project_id,
                        models.Task.status == "open",
                    )
                    .all()
                )
                best_task = None
                best_score = 0.0
                normalized_candidate = main._normalize_task_text(candidate)
                for task in open_tasks:
                    normalized_task = main._normalize_task_text(task.description or "")
                    ratio = difflib.SequenceMatcher(
                        None, normalized_task, normalized_candidate
                    ).ratio()
                    overlap = main._token_overlap(normalized_task, normalized_candidate)
                    score = max(ratio, overlap)
                    if score > best_score:
                        best_score = score
                        best_task = task
                if best_task and best_score >= 0.7:
                    main._record_task_automation_event(
                        "auto_deduped",
                        task=best_task,
                        confidence=main._clamp_confidence(best_score),
                        conversation_id=conversation.id if conversation else None,
                        matched_text=candidate,
                        details={
                            "source": "stub_auto_update",
                            "reason": "similar_candidate",
                            "matched_text": candidate,
                        },
                        existing_task_description=best_task.description,
                    )
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
                    updated.updated_at = datetime.now(timezone.utc)
                    main._record_task_automation_event(
                        "auto_completed",
                        task=updated,
                        confidence=0.91,
                        conversation_id=conversation.id if conversation else None,
                        matched_text=latest_user_message or "login done",
                        details={"matched_text": "login", "source": "stub_auto_update"},
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
                    updated.updated_at = datetime.now(timezone.utc)
                    main._record_task_automation_event(
                        "auto_completed",
                        task=updated,
                        confidence=0.9,
                        conversation_id=conversation.id if conversation else None,
                        matched_text=latest_user_message or "payment retry flow is done",
                        details={"matched_text": "payment", "source": "stub_auto_update"},
                    )
            session.commit()
        finally:
            if close_session:
                session.close()

    mp.setattr(main, "auto_update_tasks_from_conversation", fake_auto_update_tasks_from_conversation)
    mp.setattr(openai_client, "get_client", lambda: None)
    mp.setattr(embeddings, "get_embedding", lambda _text, _model=None: _stub_embedding(str(_text)))

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

