from __future__ import annotations

import json
import os
import subprocess
import difflib
import re
import time
import threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Deque, Any, Literal, cast, TYPE_CHECKING, Generator

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, model_validator
from sqlalchemy import case
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from app.db.base import Base
from app.db.session import engine, get_db, SessionLocal
from app.db import models
from app.llm import openai_client as openai_module
from app.llm.openai_client import generate_reply_from_history
from app.llm.embeddings import get_embedding
from app.llm.pricing import estimate_call_cost
from app.vectorstore.chroma_store import (
    add_message_embedding,
    query_similar_messages,
    query_similar_document_chunks,
    add_memory_embedding,
    delete_memory_embedding,
    query_similar_memory_items,
)
from app.api.search import router as search_router
from app.api.docs import router as docs_router
from app.api.github import router as github_router
from app.ingestion.github_ingestor import ingest_repo_job, get_ingest_telemetry
from app.docs_guardrails import collect_docs_status

# Create tables on import (simple approach for now; later we can use migrations)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="InfinityWindow Backend",
    description="Backend service for the InfinityWindow personal AI workbench.",
    version="0.3.0",
)

# QA: open CORS to unblock local dev ports (5175, 5173, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)
app.include_router(docs_router)
app.include_router(github_router)

# Ensure DB dependency uses the current SessionLocal (patched in tests)
def _get_db_session_override() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _get_db_session_override


# ---------- Pydantic Schemas ----------


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    # NEW: optional local filesystem root configured at creation
    local_root_path: Optional[str] = None
    instruction_text: Optional[str] = None
    is_archived: bool = False

    @model_validator(mode="before")
    @classmethod
    def validate_name(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        name = values.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        values["name"] = name.strip()
        return values


class ProjectRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    local_root_path: Optional[str] = None
    instruction_text: Optional[str] = None
    instruction_updated_at: Optional[datetime] = None
    pinned_note_text: Optional[str] = None
    is_archived: bool = False
    archived_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    local_root_path: Optional[str] = None
    instruction_text: Optional[str] = None
    pinned_note_text: Optional[str] = None
    is_archived: Optional[bool] = None

    @model_validator(mode="before")
    @classmethod
    def validate_name(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        name = values.get("name")
        if name is not None:
            if not isinstance(name, str) or not name.strip():
                raise ValueError("name must be a non-empty string")
            values["name"] = name.strip()
        return values


class ConversationCreate(BaseModel):
    project_id: int
    title: Optional[str] = None
    folder_id: Optional[int] = None


class ConversationRead(BaseModel):
    id: int
    project_id: int
    title: Optional[str] = None
    folder_id: Optional[int] = None
    folder_name: Optional[str] = None
    folder_color: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationRenamePayload(BaseModel):
    title: Optional[str] = None
    folder_id: Optional[int] = None


class MessageRead(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str

    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    project_id: int
    description: str
    priority: Optional[str] = None
    blocked_reason: Optional[str] = None
    auto_notes: Optional[str] = None


class TaskCreateScoped(BaseModel):
    """
    Project-scoped task creation payload that omits project_id
    (it comes from the path param).
    """

    description: str
    priority: Optional[str] = None
    blocked_reason: Optional[str] = None
    auto_notes: Optional[str] = None


class TaskRead(BaseModel):
    id: int
    project_id: int
    description: str
    status: str
    priority: str
    blocked_reason: Optional[str]
    auto_notes: Optional[str]
    auto_confidence: Optional[float] = None
    auto_last_action: Optional[str] = None
    auto_last_action_at: Optional[str] = None
    group: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    blocked_reason: Optional[str] = None
    auto_notes: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def validate_enums(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        status = values.get("status")
        if status is not None:
            if status not in {"open", "done"}:
                raise ValueError("status must be one of: open, done")
        priority = values.get("priority")
        if priority is not None:
            if priority not in {"low", "normal", "high", "critical"}:
                raise ValueError("priority must be one of: low, normal, high, critical")
        return values


class UsageRecordRead(BaseModel):
    id: int
    project_id: int
    conversation_id: Optional[int]
    message_id: Optional[int]
    model: str
    tokens_in: Optional[int]
    tokens_out: Optional[int]
    cost_estimate: Optional[float]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationUsageSummary(BaseModel):
    conversation_id: int
    total_tokens_in: Optional[int]
    total_tokens_out: Optional[int]
    total_cost_estimate: Optional[float]
    records: List[UsageRecordRead]

if TYPE_CHECKING:
    # Hints for dynamic attributes added to SQLAlchemy models at runtime
    models.Task.auto_confidence: Optional[float]
    models.Task.auto_last_action: Optional[str]
    models.Task.auto_last_action_at: Optional[str]
    models.Task.group: Optional[str]
    models.Conversation.folder_name: Optional[str]
    models.Conversation.folder_color: Optional[str]


class ProjectInstructionsRead(BaseModel):
    project_id: int
    instruction_text: Optional[str]
    instruction_updated_at: Optional[datetime]
    pinned_note_text: Optional[str] = None


class ProjectInstructionsPayload(BaseModel):
    instruction_text: Optional[str]
    pinned_note_text: Optional[str] = None


class ProjectDecisionCreate(BaseModel):
    title: str
    details: Optional[str] = None
    category: Optional[str] = None
    source_conversation_id: Optional[int] = None
    status: Optional[str] = "recorded"
    tags: Optional[List[str]] = None
    follow_up_task_id: Optional[int] = None
    is_draft: Optional[bool] = None


class ProjectDecisionRead(BaseModel):
    id: int
    project_id: int
    title: str
    details: Optional[str]
    category: Optional[str]
    source_conversation_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    status: str
    tags: List[str]
    follow_up_task_id: Optional[int]
    is_draft: bool
    auto_detected: bool

    model_config = ConfigDict(from_attributes=True)


class ProjectDecisionUpdate(BaseModel):
    title: Optional[str] = None
    details: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    follow_up_task_id: Optional[int] = None
    is_draft: Optional[bool] = None


class ConversationFolderCreate(BaseModel):
    project_id: int
    name: str
    color: Optional[str] = None
    sort_order: Optional[int] = None
    is_default: Optional[bool] = None
    is_archived: Optional[bool] = None


class ConversationFolderUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None
    is_default: Optional[bool] = None
    is_archived: Optional[bool] = None


class ConversationFolderRead(BaseModel):
    id: int
    project_id: int
    name: str
    color: Optional[str]
    sort_order: int
    is_default: bool
    is_archived: bool

    model_config = ConfigDict(from_attributes=True)


class MemoryItemCreate(BaseModel):
    title: str
    content: str
    tags: Optional[List[str]] = None
    pinned: bool = False
    expires_at: Optional[datetime] = None
    source_conversation_id: Optional[int] = None
    source_message_id: Optional[int] = None
    supersedes_memory_id: Optional[int] = None


class MemoryItemUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    pinned: Optional[bool] = None
    expires_at: Optional[datetime] = None
    source_conversation_id: Optional[int] = None
    source_message_id: Optional[int] = None
    superseded_by_id: Optional[int] = None


class MemoryItemRead(BaseModel):
    id: int
    project_id: int
    title: str
    content: str
    tags: List[str]
    pinned: bool
    expires_at: Optional[datetime]
    source_conversation_id: Optional[int]
    source_message_id: Optional[int]
    superseded_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    # project this chat belongs to (used if conversation_id is not provided)
    project_id: Optional[int] = None
    conversation_id: Optional[int] = None
    message: str

    # Logical mode: "auto", "fast", "deep", "budget", "research", "code", ...
    mode: Optional[str] = "auto"

    # Optional explicit model name, e.g. "gpt-5.1" or "o3-deep-research".
    # If provided, this overrides 'mode'.
    model: Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str


class TaskSuggestionRead(BaseModel):
    id: int
    project_id: int
    conversation_id: Optional[int]
    target_task_id: Optional[int]
    action_type: str
    payload: Dict[str, Any]
    confidence: float
    status: str
    task_description: Optional[str] = None
    task_status: Optional[str] = None
    task_priority: Optional[str] = None
    task_blocked_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskOverviewRead(BaseModel):
    tasks: List[TaskRead]
    suggestions: List[TaskSuggestionRead]

    model_config = ConfigDict(from_attributes=True)


class TaskSuggestionSeedPayload(BaseModel):
    project_id: int
    conversation_id: Optional[int] = None
    target_task_id: Optional[int] = None
    action_type: str
    description: Optional[str] = None
    priority: Optional[str] = None
    blocked_reason: Optional[str] = None
    confidence: float = 0.5


class IngestionJobCreate(BaseModel):
    kind: Literal["repo"]
    source: str
    include_globs: Optional[List[str]] = None
    name_prefix: Optional[str] = None


class IngestionJobRead(BaseModel):
    id: int
    project_id: int
    kind: str
    source: str
    status: str
    total_items: int
    processed_items: int
    error_message: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    total_bytes: int
    processed_bytes: int
    cancel_requested: bool
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FileWritePayload(BaseModel):
    """
    Payload for writing a file in a project's local_root_path.
    file_path is relative to the project's root.
    """
    file_path: str
    content: str
    create_dirs: bool = False


class FileAIEditPayload(BaseModel):
    """
    Ask the AI to edit a file under the project's local_root_path.

    - file_path: relative path under the project root.
    - instruction: what you want changed ("convert tabs to spaces",
      "refactor to use async", etc.).
    - model: optional explicit model (otherwise we let mode/model routing decide).
    - mode: logical mode; "code" is a good default for code edits.
    - apply_changes: if True, write the edited content back to disk.
    - conversation_id / message_id: optional linkage to a chat, for usage tracking.
    """
    file_path: str
    instruction: str
    # Accept legacy alias to avoid 422 when clients send "instructions"
    instructions: Optional[str] = None
    model: Optional[str] = None
    mode: Optional[str] = "code"
    apply_changes: bool = False
    conversation_id: Optional[int] = None
    message_id: Optional[int] = None
    include_diff: bool = True

    @model_validator(mode="before")
    @classmethod
    def _coalesce_instruction(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(data, dict) and "instruction" not in data:
            alias_val = data.get("instructions")
            if alias_val:
                data["instruction"] = alias_val
        return data


class TerminalRunPayload(BaseModel):
    """
    Run a shell command in the context of a project.

    - project_id: which project's local_root_path to treat as the root.
    - cwd: optional subdirectory under the project root (relative path).
    - command: the shell command to run.
    - timeout_seconds: safety timeout so commands can't hang forever.
    """
    project_id: Optional[int] = None
    command: str
    cwd: Optional[str] = None
    timeout_seconds: Optional[int] = 120



# ---------- Helpers: misc ----------


def _normalize_instruction_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _commit_with_retry(db: Session, attempts: int = 6, base_delay: float = 0.3):
    """
    Commit the session with a retry loop to tolerate transient SQLite locks.
    The delay increases linearly to give the lock holder time to finish.
    """
    last_exc: Optional[Exception] = None
    for i in range(attempts):
        try:
            db.commit()
            return
        except OperationalError as exc:  # SQLite locked
            db.rollback()
            last_exc = exc
            if "locked" not in str(exc).lower():
                raise
            # backoff: 0.3s, 0.6s, 0.9s, ...
            time.sleep(base_delay * (i + 1))
    if last_exc:
        raise last_exc


def _flush_with_retry(db: Session, attempts: int = 6, base_delay: float = 0.3):
    """
    Flush pending objects with retries to tolerate transient SQLite locks.
    """
    last_exc: Optional[Exception] = None
    for i in range(attempts):
        try:
            db.flush()
            return
        except OperationalError as exc:
            db.rollback()
            last_exc = exc
            if "locked" not in str(exc).lower():
                raise
            time.sleep(base_delay * (i + 1))
    if last_exc:
        raise last_exc


def _normalize_tags(tags: Optional[List[str]]) -> Optional[str]:
    if not tags:
        return None
    cleaned = [t.strip() for t in tags if t and t.strip()]
    if not cleaned:
        return None
    return json.dumps(cleaned)


def _tags_to_list(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(item) for item in data if isinstance(item, str)]
    except json.JSONDecodeError:
        pass
    return []


# ---------- Helper: filesystem ----------


def _ensure_project(db: Session, project_id: int) -> models.Project:
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


def _ensure_conversation(
    db: Session, conversation_id: int, project_id: Optional[int] = None
) -> models.Conversation:
    conversation = db.get(models.Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    if project_id is not None and conversation.project_id != project_id:
        raise HTTPException(
            status_code=400,
            detail="Conversation does not belong to this project.",
        )
    return conversation


def _ensure_folder(
    db: Session, folder_id: int, project_id: Optional[int] = None
) -> models.ConversationFolder:
    folder = db.get(models.ConversationFolder, folder_id)
    if folder is None:
        raise HTTPException(status_code=404, detail="Conversation folder not found.")
    if project_id is not None and folder.project_id != project_id:
        raise HTTPException(
            status_code=400,
            detail="Conversation folder does not belong to this project.",
        )
    return folder


def _get_default_folder_id(
    db: Session, project_id: int
) -> Optional[int]:
    folder = (
        db.query(models.ConversationFolder)
        .filter(
            models.ConversationFolder.project_id == project_id,
            models.ConversationFolder.is_default.is_(True),
        )
        .order_by(models.ConversationFolder.sort_order.asc())
        .first()
    )
    return folder.id if folder else None


def _set_default_folder(
    db: Session, project_id: int, folder_id: Optional[int]
) -> None:
    db.query(models.ConversationFolder).filter(
        models.ConversationFolder.project_id == project_id
    ).update({models.ConversationFolder.is_default: False})
    if folder_id is not None:
        db.query(models.ConversationFolder).filter(
            models.ConversationFolder.id == folder_id
        ).update({models.ConversationFolder.is_default: True})


def _get_project_root(project: models.Project) -> Path:
    if not project.local_root_path:
        raise HTTPException(
            status_code=400,
            detail="Project does not have local_root_path configured.",
        )
    root = Path(project.local_root_path).expanduser()
    try:
        root = root.resolve()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail=f"Invalid local_root_path: {e}",
        )
    if not root.exists():
        raise HTTPException(
            status_code=400,
            detail=f"local_root_path does not exist on disk: {root}",
        )
    if not root.is_dir():
        raise HTTPException(
            status_code=400,
            detail="local_root_path is not a directory.",
        )
    return root


def _validate_local_root_path(path_value: Optional[str]) -> Path:
    """
    Ensure a local_root_path is provided, exists, and is a directory.
    """
    if not path_value or not path_value.strip():
        raise HTTPException(
            status_code=400,
            detail="local_root_path is required and must be non-empty.",
        )
    root = Path(path_value).expanduser()
    try:
        root = root.resolve()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail=f"Invalid local_root_path: {exc}",
        ) from exc
    if not root.exists() or not root.is_dir():
        raise HTTPException(
            status_code=400,
            detail="local_root_path must exist and be a directory.",
        )
    return root


def _safe_join(root: Path, relative_path: str) -> Path:
    """
    Resolve a subpath/file_path safely under root, preventing path traversal.

    Rules:
    - 'relative_path' must be relative (no drive, no leading slash).
    - It may not contain '..' segments.
    - Final resolved path must still live under 'root'.
    - Disallow UNC-style paths or backslash separators to avoid bypasses.
    """
    if not relative_path:
        return root

    # Block UNC or backslash-based paths (e.g., \\server\share or C:\)
    if relative_path.startswith("\\\\") or relative_path.startswith("//"):
        raise HTTPException(
            status_code=400,
            detail="UNC or network paths are not allowed.",
        )
    if "\\" in relative_path:
        raise HTTPException(
            status_code=400,
            detail="Backslashes are not allowed; use forward slashes.",
        )

    rel_obj = Path(relative_path)

    # Disallow absolute paths like "C:\\Windows" or "/etc"
    if rel_obj.is_absolute():
        raise HTTPException(
            status_code=400,
            detail="Path must be relative to the project local_root_path.",
        )

    # Disallow any attempt to go up with ".." even when embedded in a segment
    if any(".." in part for part in rel_obj.parts):
        raise HTTPException(
            status_code=400,
            detail="Path may not contain '..' segments.",
        )

    # Join and normalize; strict=False so non‑existent paths (for writes) are allowed
    candidate = (root / rel_obj).resolve(strict=False)

    try:
        candidate.relative_to(root)
    except ValueError:
        # In case of weird symlink situations, still enforce staying under root
        raise HTTPException(
            status_code=400,
            detail="Path escapes project local_root_path.",
        )

    return candidate


def _extract_ai_file_edits(reply_text: str) -> tuple[str, List[Dict[str, object]]]:
    """
    Look for zero or more AI file edit request blocks in the reply text.

    Blocks are delimited like:

        <<AI_FILE_EDIT>>
        {"file_path": "backend/app/api/main.py",
         "instruction": "Describe the change to make"}
        <<END_AI_FILE_EDIT>>

    Returns:
        (cleaned_reply_text, list_of_edit_dicts)
    """
    edits: List[Dict[str, object]] = []
    start_tag = "<<AI_FILE_EDIT>>"
    end_tag = "<<END_AI_FILE_EDIT>>"

    remaining = reply_text
    while True:
        start = remaining.find(start_tag)
        if start == -1:
            break
        end = remaining.find(end_tag, start + len(start_tag))
        if end == -1:
            break

        json_str = remaining[start + len(start_tag): end].strip()
        try:
            data = json.loads(json_str)
            if isinstance(data, dict):
                edits.append(data)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        edits.append(item)
        except json.JSONDecodeError:
            # If parsing fails, ignore this block and continue
            pass

        # Remove this block from the visible text
        remaining = remaining[:start].rstrip() + remaining[end + len(end_tag):]

    cleaned = remaining.strip()
    return cleaned, edits


# ---------- Helper: AI‑assisted task extraction ----------


_TASK_TELEMETRY: Dict[str, int] = {
    "auto_added": 0,
    "auto_completed": 0,
    "auto_deduped": 0,
    "auto_suggested": 0,
}
_TASK_ACTION_HISTORY: Deque[Dict[str, Any]] = deque(maxlen=50)
_TASK_CONTEXT_STATS: Dict[str, Any] = {
    "context_included": False,
    "context_high_priority_count": 0,
}
_AUTO_UPDATE_TASKS_AFTER_CHAT = (
    os.getenv("AUTO_UPDATE_TASKS_AFTER_CHAT", "true").lower()
    not in {"0", "false", "no", "off"}
)


def get_task_telemetry(reset: bool = False) -> Dict[str, int]:
    snapshot: Dict[str, Any] = dict(_TASK_TELEMETRY)
    actions = list(_TASK_ACTION_HISTORY)
    snapshot["recent_actions"] = actions
    # Confidence stats across recent actions
    if actions:
        confidences = [
            c for c in (a.get("confidence") for a in actions) if isinstance(c, (int, float))
        ]
        if confidences:
            snapshot["confidence_stats"] = {
                "min": min(confidences),
                "max": max(confidences),
                "avg": round(sum(confidences) / len(confidences), 3),
                "count": len(confidences),
            }
        bucket = {"lt_0_4": 0, "0_4_0_7": 0, "gte_0_7": 0}
        for c in confidences:
            if c < 0.4:
                bucket["lt_0_4"] += 1
            elif c < 0.7:
                bucket["0_4_0_7"] += 1
            else:
                bucket["gte_0_7"] += 1
        snapshot["confidence_buckets"] = bucket
    if reset:
        reset_task_telemetry()
        snapshot = dict(_TASK_TELEMETRY)
        actions = []
        snapshot["recent_actions"] = actions
    snapshot["context_included"] = bool(_TASK_CONTEXT_STATS.get("context_included", False))
    snapshot["context_high_priority_count"] = int(
        _TASK_CONTEXT_STATS.get("context_high_priority_count", 0)
    )
    return snapshot


def reset_task_telemetry() -> None:
    for key in _TASK_TELEMETRY:
        _TASK_TELEMETRY[key] = 0
    _TASK_ACTION_HISTORY.clear()
    _TASK_CONTEXT_STATS["context_included"] = False
    _TASK_CONTEXT_STATS["context_high_priority_count"] = 0


def _run_auto_update_with_retry(
    db: Session,
    conversation: models.Conversation,
    model_name: Optional[str] = None,
    attempts: int = 2,
    base_delay: float = 0.2,
) -> tuple[bool, Optional[Exception]]:
    """
    Run auto_update_tasks_from_conversation with a small retry to smooth out
    transient model/vector-store hiccups. Returns (ok, last_exception).
    """
    last_exc: Optional[Exception] = None
    for i in range(attempts):
        try:
            auto_update_tasks_from_conversation(db, conversation, model_name=model_name)
            _commit_with_retry(db)
            return True, None
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            last_exc = exc
            if i < attempts - 1:
                time.sleep(base_delay * (i + 1))
    return False, last_exc


_TASK_TEXT_NORMALIZER = re.compile(r"[^a-z0-9]+")
_TASK_COMPLETION_KEYWORDS = (
    "done",
    "completed",
    "complete",
    "finished",
    "fixed",
    "merged",
    "shipped",
    "resolved",
    "delivered",
)
_TASK_INCOMPLETE_HINTS = (
    "pending",
    "still need",
    "still pending",
    "not done",
    "not finished",
    "not yet",
    "blocked",
    "in progress",
    "wip",
    "todo",
    "to do",
)
_TASK_PRIORITY_CRITICAL = (
    "production outage",
    "sev1",
    "sev 1",
    "p0",
    "critical",
    "p0 blocker",
    "urgent bug",
    "blocker",
    "security",
    "vulnerability",
    "breach",
    "data leak",
    "payment down",
    "checkout down",
    "login down",
    "incident p0",
    "p0 incident",
    "major outage",
    "severe",
)
_TASK_PRIORITY_HIGH = (
    "urgent",
    "high priority",
    "asap",
    "needs immediate",
    "high risk",
    "p1",
    "auth",
    "login failure",
    "rate limit",
    "p1 bug",
    "degraded",
    "incident",
    "hotfix",
    "regression",
    "latency",
    "slow query",
    "perf",
)
_TASK_PRIORITY_LOW = (
    "cleanup",
    "nice to have",
    "follow-up later",
    "nit",
    "optional",
    "idea",
    "brainstorm",
    "later",
)
_TASK_BLOCKED_PATTERNS = (
    re.compile(r"blocked by (?P<reason>.+)", re.IGNORECASE),
    re.compile(r"depends on (?P<reason>.+)", re.IGNORECASE),
    re.compile(r"after we (?P<reason>.+)", re.IGNORECASE),
    re.compile(r"waiting for (?P<reason>.+)", re.IGNORECASE),
    re.compile(r"need .* before (?P<reason>.+)", re.IGNORECASE),
    re.compile(r"pending approval from (?P<reason>.+)", re.IGNORECASE),
    re.compile(r"needs review from (?P<reason>.+)", re.IGNORECASE),
    re.compile(r"blocked on (?P<reason>.+)", re.IGNORECASE),
    re.compile(r"waiting on (?P<reason>.+)", re.IGNORECASE),
    re.compile(r"once we (?P<reason>.+)", re.IGNORECASE),
)
_TASK_DEPENDENCY_PATTERNS = (
    re.compile(r"depends on (?P<dep>.+)", re.IGNORECASE),
    re.compile(r"after (?P<dep>.+)", re.IGNORECASE),
    re.compile(r"after we (?P<dep>.+)", re.IGNORECASE),
    re.compile(r"waiting for (?P<dep>.+)", re.IGNORECASE),
    re.compile(r"waiting on (?P<dep>.+)", re.IGNORECASE),
)
_TASK_VAGUE_INTENT_HINTS = (
    "analysis",
    "analyze",
    "investigate",
    "look into",
    "think about",
    "notes",
    "thoughts",
    "discussion",
    "review conversation",
    "brainstorm",
    "explore",
)
_TASK_ACTION_VERBS = (
    "implement",
    "add",
    "build",
    "fix",
    "resolve",
    "ship",
    "deliver",
    "write",
    "refactor",
    "deploy",
    "document",
    "create",
)
_TASK_ADD_CONFIDENCE_THRESHOLD = 0.7
_TASK_COMPLETE_CONFIDENCE_THRESHOLD = 0.7


def _normalize_task_text(value: str) -> str:
    cleaned = _TASK_TEXT_NORMALIZER.sub(" ", (value or "").lower())
    return " ".join(cleaned.split())


def _token_overlap(normalized_a: str, normalized_b: str) -> float:
    tokens_a = set(normalized_a.split())
    tokens_b = set(normalized_b.split())
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a)


def _token_overlap_shortest(normalized_a: str, normalized_b: str) -> float:
    """
    Similar to _token_overlap but normalizes by the shorter string to better
    handle subset/shorter completion statements (e.g., "finished implement login").
    """
    tokens_a = set(normalized_a.split())
    tokens_b = set(normalized_b.split())
    if not tokens_a or not tokens_b:
        return 0.0
    denom = min(len(tokens_a), len(tokens_b))
    if denom == 0:
        return 0.0
    return len(tokens_a & tokens_b) / denom


def _clamp_confidence(value: float) -> float:
    return round(max(0.0, min(value, 1.0)), 3)


def _estimate_completion_confidence(similarity: float, overlap: float) -> float:
    raw = max(similarity, overlap)
    return _clamp_confidence(raw)


def _intent_penalty(description: str) -> float:
    """
    Penalize vague/analysis-only intents so they fall into the suggestion queue
    instead of creating noisy “analysis” tasks.
    """
    lowered = (description or "").lower()
    token_count = len(lowered.split())
    if token_count <= 3:
        return 0.25
    if any(hint in lowered for hint in _TASK_VAGUE_INTENT_HINTS):
        # If no clear action verb, treat as vague analysis.
        if not any(verb in lowered for verb in _TASK_ACTION_VERBS):
            return 0.25
        # If both present, apply a smaller penalty.
        return 0.12
    return 0.0


def _estimate_add_confidence(description: str, max_similarity: float) -> float:
    word_count = len(description.split())
    length_score = min(word_count / 12.0, 1.0)
    novelty = 1.0 - max_similarity
    penalty = _intent_penalty(description)
    raw = 0.35 + 0.4 * length_score + 0.25 * novelty - penalty
    return _clamp_confidence(raw)


def _record_task_action(
    action_type: str,
    *,
    task: Optional[models.Task] = None,
    description: Optional[str] = None,
    confidence: float,
    project_id: Optional[int] = None,
    conversation_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    timestamp: Optional[datetime] = None,
) -> None:
    ts = timestamp or datetime.now(timezone.utc)
    entry: Dict[str, Any] = {
        "timestamp": ts.isoformat(),
        "action": action_type,
        "confidence": _clamp_confidence(confidence),
        "task_id": getattr(task, "id", None),
        "task_description": getattr(task, "description", description),
        "project_id": project_id or getattr(task, "project_id", None),
        "conversation_id": conversation_id,
    }
    if isinstance(task, models.Task):
        entry["task_status"] = task.status
        entry["task_priority"] = task.priority
        entry["task_blocked_reason"] = task.blocked_reason
        entry["task_group"] = _compute_task_group(task)
        if task.auto_notes:
            entry["task_auto_notes"] = task.auto_notes
    if details:
        entry["details"] = details
        # Lift common detail fields for convenience in telemetry/Usage UI.
        if "matched_text" in details:
            entry["matched_text"] = details.get("matched_text")
        if "model" in details:
            entry["model"] = details.get("model")
        if "priority" in details and "task_priority" not in entry:
            entry["task_priority"] = details.get("priority")
        if "blocked_reason" in details and "task_blocked_reason" not in entry:
            entry["task_blocked_reason"] = details.get("blocked_reason")
    _TASK_ACTION_HISTORY.appendleft(entry)


def _short_audit_snippet(value: Optional[str], max_len: int = 160) -> str:
    if not value:
        return ""
    cleaned = " ".join(str(value).split())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 3].rstrip() + "..."


def _format_task_audit_note(
    action_type: str,
    *,
    timestamp: datetime,
    confidence: Optional[float] = None,
    matched_text: Optional[str] = None,
    existing_task_description: Optional[str] = None,
) -> str:
    ts_str = timestamp.strftime("%Y-%m-%d %H:%M UTC")
    conf_str = (
        f"(confidence {_clamp_confidence(confidence or 0.0):.2f})"
        if confidence is not None
        else None
    )
    snippet = _short_audit_snippet(matched_text)
    if action_type == "auto_added":
        parts = [f"Added automatically on {ts_str}"]
        if conf_str:
            parts.append(conf_str)
        if snippet:
            parts.append(f'from: "{snippet}"')
        return " ".join(parts)
    if action_type == "auto_completed":
        parts = [f"Closed automatically on {ts_str}"]
        if conf_str:
            parts.append(conf_str)
        if snippet:
            parts.append(f'after: "{snippet}"')
        return " ".join(parts)
    if action_type == "auto_deduped":
        parts = [f"Duplicate automatically ignored on {ts_str}"]
        if conf_str:
            parts.append(conf_str)
        details: List[str] = []
        if existing_task_description:
            details.append(
                f'similar to existing task "{_short_audit_snippet(existing_task_description)}"'
            )
        if snippet:
            details.append(f'input: "{snippet}"')
        if details:
            parts.append("; ".join(details))
        return " ".join(parts)
    return f"Automation {action_type} on {ts_str}"


def _record_task_automation_event(
    action_type: str,
    *,
    task: models.Task,
    confidence: float,
    conversation_id: Optional[int] = None,
    matched_text: Optional[str] = None,
    model: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    project_id: Optional[int] = None,
    existing_task_description: Optional[str] = None,
) -> str:
    """
    Single place to record task automation telemetry and write a short audit note.
    Returns the audit note applied to the task.
    """
    ts = datetime.now(timezone.utc)
    note = _format_task_audit_note(
        action_type,
        timestamp=ts,
        confidence=confidence,
        matched_text=matched_text,
        existing_task_description=existing_task_description,
    )
    if note:
        task.auto_notes = note
    setattr(task, "auto_confidence", _clamp_confidence(confidence))
    setattr(task, "auto_last_action", action_type)
    setattr(task, "auto_last_action_at", ts.isoformat())

    if action_type in _TASK_TELEMETRY:
        _TASK_TELEMETRY[action_type] += 1

    merged_details = dict(details or {})
    if matched_text and "matched_text" not in merged_details:
        merged_details["matched_text"] = matched_text
    if model is not None and "model" not in merged_details:
        merged_details["model"] = model
    try:
        _record_task_action(
            action_type,
            task=task,
            confidence=confidence,
            conversation_id=conversation_id,
            project_id=project_id,
            details=merged_details or None,
            timestamp=ts,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] Failed to record task action '{action_type}': {exc!r}")
    return note


def _attach_task_action_metadata(tasks: List[models.Task]) -> None:
    """
    Enrich Task objects with latest auto action metadata (confidence/action/time).
    """
    if not tasks:
        return
    latest_by_task: Dict[int, Dict[str, Any]] = {}
    for action in _TASK_ACTION_HISTORY:
        tid = action.get("task_id")
        if tid is None:
            continue
        if tid not in latest_by_task:
            latest_by_task[tid] = action
    for task in tasks:
        meta = latest_by_task.get(task.id)
        if meta:
            setattr(task, "auto_confidence", meta.get("confidence"))
            setattr(task, "auto_last_action", meta.get("action"))
            setattr(task, "auto_last_action_at", meta.get("timestamp"))
        setattr(task, "group", _compute_task_group(task))


def _compute_task_group(task: models.Task) -> str:
    """
    Derive a lightweight grouping for tasks to aid ordering/UX:
    - critical: priority critical
    - blocked: any blocked_reason set
    - ready: everything else
    """
    if getattr(task, "priority", "") == "critical":
        return "critical"
    if getattr(task, "blocked_reason", None):
        return "blocked"
    return "ready"


def _safe_int(value: Any) -> Optional[int]:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _create_task_suggestion(
    db: Session,
    *,
    project_id: int,
    conversation_id: Optional[int],
    action_type: str,
    payload: Dict[str, Any],
    confidence: float,
    target_task: Optional[models.Task] = None,
) -> models.TaskSuggestion:
    suggestion = models.TaskSuggestion(
        project_id=project_id,
        conversation_id=conversation_id,
        action_type=action_type,
        payload=json.dumps(payload),
        confidence=_clamp_confidence(confidence),
        target_task_id=getattr(target_task, "id", None),
    )
    db.add(suggestion)
    db.flush()
    _TASK_TELEMETRY["auto_suggested"] += 1
    _record_task_action(
        f"suggested_{action_type}",
        task=target_task,
        description=payload.get("description"),
        confidence=confidence,
        conversation_id=conversation_id,
        details={"suggestion_id": suggestion.id},
    )
    return suggestion


def _infer_task_priority(description: str) -> str:
    lowered = (description or "").lower()
    if any(keyword in lowered for keyword in _TASK_PRIORITY_CRITICAL):
        return "critical"
    if any(keyword in lowered for keyword in _TASK_PRIORITY_HIGH):
        return "high"
    if any(keyword in lowered for keyword in _TASK_PRIORITY_LOW):
        return "low"
    return "normal"


def _extract_blocked_reason(description: str) -> Optional[str]:
    for pattern in _TASK_BLOCKED_PATTERNS:
        match = pattern.search(description or "")
        if match:
            reason = (match.group("reason") or "").strip().rstrip(".")
            if reason:
                return reason
    return None


def _extract_dependency_hint(description: str) -> Optional[str]:
    for pattern in _TASK_DEPENDENCY_PATTERNS:
        match = pattern.search(description or "")
        if match:
            dep = (match.group("dep") or "").strip().rstrip(".")
            if dep:
                return dep
    return None


def _task_suggestion_to_schema(
    suggestion: models.TaskSuggestion,
) -> TaskSuggestionRead:
    try:
        payload = json.loads(suggestion.payload or "{}")
    except json.JSONDecodeError:
        payload = {}
    task_desc = None
    task_status = None
    task_priority = None
    task_blocked_reason = None
    if suggestion.target_task is not None:
        task_desc = suggestion.target_task.description
        task_status = suggestion.target_task.status
        task_priority = suggestion.target_task.priority
        task_blocked_reason = suggestion.target_task.blocked_reason
    elif isinstance(payload.get("description"), str):
        task_desc = payload["description"]
    return TaskSuggestionRead(
        id=suggestion.id,
        project_id=suggestion.project_id,
        conversation_id=suggestion.conversation_id,
        target_task_id=suggestion.target_task_id,
        action_type=suggestion.action_type,
        payload=payload,
        confidence=suggestion.confidence,
        status=suggestion.status,
        task_description=task_desc,
        task_status=task_status,
        task_priority=task_priority,
        task_blocked_reason=task_blocked_reason,
        created_at=suggestion.created_at,
        updated_at=suggestion.updated_at,
    )


def _decision_to_schema(
    decision: models.ProjectDecision,
) -> ProjectDecisionRead:
    return ProjectDecisionRead(
        id=decision.id,
        project_id=decision.project_id,
        title=decision.title,
        details=decision.details,
        category=decision.category,
        source_conversation_id=decision.source_conversation_id,
        created_at=decision.created_at,
        updated_at=decision.updated_at,
        status=decision.status,
        tags=_tags_to_list(decision.tags_raw),
        follow_up_task_id=decision.follow_up_task_id,
        is_draft=decision.is_draft,
        auto_detected=decision.auto_detected,
    )


def _line_mentions_completion(line: str) -> bool:
    lower = (line or "").lower()
    if not lower.startswith("user:"):
        return False
    return any(keyword in lower for keyword in _TASK_COMPLETION_KEYWORDS)


def build_task_context_for_project(
    project: Optional[models.Project],
    db: Session,
    *,
    max_tasks: int = 5,
) -> tuple[str, int]:
    """
    Build a compact, structured context block for task extraction.

    Includes:
    - Project instructions (or explicit None)
    - Pinned note / sprint focus (or explicit None)
    - Project goal/description (or explicit None)
    - Top N high-priority open tasks with blocked hints (or explicit None)
    """
    instructions = (getattr(project, "instruction_text", "") or "").strip() or "None set"
    pinned_note = (getattr(project, "pinned_note_text", "") or "").strip() or "None set"
    goal = (getattr(project, "description", "") or "").strip() or "None set"

    high_priority_tasks: List[models.Task] = []
    if project:
        priority_order = case(
            (models.Task.priority == "critical", 0),
            (models.Task.priority == "high", 1),
            else_=2,
        )
        high_priority_tasks = (
            db.query(models.Task)
            .filter(models.Task.project_id == project.id)
            .filter(models.Task.status == "open")
            .filter(models.Task.priority.in_(("critical", "high")))
            .order_by(priority_order, models.Task.updated_at.desc())
            .limit(max_tasks)
            .all()
        )

    lines: List[str] = [
        "[PROJECT_CONTEXT]",
        f"Instructions: {instructions}",
        f"Pinned note / sprint focus: {pinned_note}",
        f"Project goal/description: {goal}",
        "High-priority open tasks:",
    ]
    if high_priority_tasks:
        for task in high_priority_tasks:
            blocked_reason = (task.blocked_reason or "").strip()
            blocked_label = (
                f"blocked=Yes: {blocked_reason}" if blocked_reason else "blocked=No"
            )
            lines.append(
                f"- [TASK-{task.id}] {task.description} "
                f"(status={task.status.upper()}, priority={task.priority.upper()}, {blocked_label})"
            )
    else:
        lines.append("- None set")
    lines.append("[/PROJECT_CONTEXT]")

    return "\n".join(lines), len(high_priority_tasks)


def auto_update_tasks_from_conversation(
    db: Session,
    conversation: models.Conversation,
    max_messages: int = 16,
    model_name: Optional[str] = None,
) -> None:
    """
    Look at the recent messages in the conversation, ask a small/fast model
    to extract TODO items, and add any NEW open tasks to the project.

    This is best‑effort and should never raise out of here.
    """
    _TASK_CONTEXT_STATS["context_included"] = False
    _TASK_CONTEXT_STATS["context_high_priority_count"] = 0

    # Get recent messages (most recent first, then reverse to chronological)
    recent_messages = (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation.id)
        .order_by(models.Message.id.desc())
        .limit(max_messages)
        .all()
    )
    if not recent_messages:
        return

    recent_messages = list(reversed(recent_messages))

    convo_text_lines: List[str] = []
    for m in recent_messages:
        who = "User" if m.role == "user" else "Assistant"
        # keep it short-ish per line
        content = m.content.strip()
        if len(content) > 500:
            content = content[:500] + "..."
        convo_text_lines.append(f"{who}: {content}")

    convo_text = "\n".join(convo_text_lines)

    open_tasks = (
        db.query(models.Task)
        .filter(
            models.Task.project_id == conversation.project_id,
            models.Task.status == "open",
        )
        .all()
    )
    open_task_map: Dict[int, Dict[str, object]] = {
        task.id: {"task": task, "normalized": _normalize_task_text(task.description)}
        for task in open_tasks
    }

    completion_lines = [
        line.split(":", 1)[1].strip()
        for line in convo_text_lines[-8:]
        if ":" in line and _line_mentions_completion(line)
    ]
    completion_segments: List[str] = []
    for text in completion_lines:
        normalized = text.replace(" and ", ". ").replace(";", ".").replace(",", ".")
        for fragment in normalized.split("."):
            clause = fragment.strip()
            if not clause:
                continue
            lowered_clause = clause.lower()
            if not any(
                keyword in lowered_clause for keyword in _TASK_COMPLETION_KEYWORDS
            ):
                continue
            if any(hint in lowered_clause for hint in _TASK_INCOMPLETE_HINTS):
                continue
            completion_segments.append(clause)

    incomplete_segments: List[str] = []
    for line in convo_text_lines[-8:]:
        if ":" not in line:
            continue
        body = line.split(":", 1)[1].strip()
        if not body:
            continue
        lowered_body = body.lower()
        if not any(hint in lowered_body for hint in _TASK_INCOMPLETE_HINTS):
            continue
        normalized_body = body.replace(" and ", ". ").replace(";", ".").replace(",", ".")
        for fragment in normalized_body.split("."):
            clause = fragment.strip()
            if clause:
                incomplete_segments.append(clause)

    if completion_segments:
        for text in completion_segments:
            normalized_line = _normalize_task_text(str(text or ""))
            if not normalized_line:
                continue
            # If completion mentions a specific task id or core phrase, try to match loosely
            for info in list(open_task_map.values()):
                task_obj = info["task"]
                if not isinstance(task_obj, models.Task):
                    continue
                if task_obj.status != "open":
                    continue
                normalized_task = str(info.get("normalized") or "")
                if not normalized_task:
                    continue
                conflict_with_incomplete = False
                for incomplete in incomplete_segments:
                    normalized_incomplete = _normalize_task_text(str(incomplete or ""))
                    if not normalized_incomplete:
                        continue
                    inc_ratio = difflib.SequenceMatcher(
                        None, normalized_task, normalized_incomplete
                    ).ratio()
                    inc_overlap = _token_overlap(normalized_task, normalized_incomplete)
                    inc_short = _token_overlap_shortest(
                        normalized_task, normalized_incomplete
                    )
                    if (
                        normalized_task in normalized_incomplete
                        or normalized_incomplete in normalized_task
                        or inc_ratio >= 0.65
                        or inc_overlap >= 0.5
                        or inc_short >= 0.55
                    ):
                        conflict_with_incomplete = True
                        break
                if conflict_with_incomplete:
                    continue
                normalized_line = str(normalized_line)
                core_phrase = " ".join(normalized_task.split()[:6])
                ratio = difflib.SequenceMatcher(
                    None, normalized_task, normalized_line
                ).ratio()
                overlap_score = _token_overlap(normalized_task, normalized_line)
                short_overlap = _token_overlap_shortest(
                    normalized_task, normalized_line
                )
                # Allow short completion phrases to close if they share core phrase or overlap
                if (
                    normalized_task in normalized_line
                    or normalized_line in normalized_task
                    or (core_phrase and core_phrase in normalized_line)
                    or ratio >= 0.6
                    or overlap_score >= 0.5
                    or short_overlap >= 0.48
                ):
                    confidence = _estimate_completion_confidence(
                        max(ratio, short_overlap), max(overlap_score, short_overlap)
                    )
                    if confidence >= 0.6:  # lower threshold for short completions
                        task_obj.status = "done"
                        task_obj.updated_at = datetime.now(timezone.utc)
                        _record_task_automation_event(
                            "auto_completed",
                            task=task_obj,
                            confidence=confidence,
                            conversation_id=conversation.id,
                            matched_text=text,
                            model=model_name,
                            details={
                                "priority": task_obj.priority,
                                "blocked_reason": task_obj.blocked_reason,
                                "model": model_name,
                                "source": "auto_update",
                            },
                        )
                        print(
                            f"[Tasks] Auto-completed '{task_obj.description}' "
                            "based on recent chat."
                        )
                    else:
                        _create_task_suggestion(
                            db,
                            project_id=conversation.project_id,
                            conversation_id=conversation.id,
                            action_type="complete",
                            payload={
                                "task_id": task_obj.id,
                                "matched_text": text,
                            },
                            confidence=confidence,
                            target_task=task_obj,
                        )
                    info["normalized"] = ""
        # Remove tasks marked done from duplicate checks
        cleaned: Dict[int, Dict[str, Any]] = {}
        for task_id, info in open_task_map.items():
            t_obj = info.get("task")
            if isinstance(t_obj, models.Task) and t_obj.status == "open":
                cleaned[task_id] = info
        open_task_map = cleaned

    top_open_tasks = (
        db.query(models.Task)
        .filter(models.Task.project_id == conversation.project_id)
        .filter(models.Task.status == "open")
        .order_by(models.Task.priority.asc(), models.Task.updated_at.desc())
        .limit(5)
        .all()
    )
    priority_context = ""
    if top_open_tasks:
        summaries = []
        for task in top_open_tasks:
            label = f"{task.priority.upper()} - {task.description}"
            if task.blocked_reason:
                label += f" (blocked by {task.blocked_reason})"
            summaries.append(label)
        priority_context = (
            "Current top open tasks (for context):\n"
            + "\n".join(f"- {summary}" for summary in summaries)
            + "\n\n"
        )

    blocked_tasks = (
        db.query(models.Task)
        .filter(models.Task.project_id == conversation.project_id)
        .filter(models.Task.status == "open")
        .filter(models.Task.blocked_reason.isnot(None))
        .order_by(models.Task.updated_at.desc())
        .limit(3)
        .all()
    )
    blocked_context = ""
    if blocked_tasks:
        blocked_summaries = []
        for task in blocked_tasks:
            blocked_summaries.append(
                f"{task.description} (blocked: {task.blocked_reason})"
            )
        blocked_context = (
            "Blocked items to consider:\n"
            + "\n".join(f"- {summary}" for summary in blocked_summaries)
            + "\n\n"
        )
    dependency_context = ""
    if blocked_tasks:
        dependency_context = (
            "Dependencies to consider (may be blocking work):\n"
            + "\n".join(
                f"- {task.description} (blocked: {task.blocked_reason})"
                for task in blocked_tasks
            )
            + "\n\n"
        )

    project = conversation.project
    context_block, high_priority_count = build_task_context_for_project(project, db)
    _TASK_CONTEXT_STATS["context_included"] = bool(context_block)
    _TASK_CONTEXT_STATS["context_high_priority_count"] = high_priority_count

    system_instructions = (
        "You help maintain a TODO list for a long-running software project.\n"
        "Use the PROJECT_CONTEXT to prioritize which TODO items to extract and which existing tasks to mark complete. "
        "Focus on items aligned with the project goals, sprint focus, and blockers, and de-emphasize generic or off-topic ideas. "
        "Avoid creating noisy duplicates when equivalent work already exists in the high-priority open list.\n\n"
        f"{context_block}\n\n"
        f"{priority_context}"
        f"{dependency_context}"
        f"{blocked_context}"
        "From the recent conversation messages below, extract any NEW, "
        "actionable tasks that should be added to the project TODO list. "
        "Prefer action verbs (implement/add/fix/write/document). "
        "If the message is vague/analysis-only, return an empty list or use suggestions instead of noisy tasks. "
        "Infer priority (critical/high/normal/low) from language and mark blocked_reason when users mention blockers. "
        "If conversation snippets imply a listed high-priority task is finished, prefer completion over creating a duplicate.\n\n"
        "Rules:\n"
        "- Only include tasks that clearly represent work to be done in the future.\n"
        "- Skip questions, chit-chat, or things already clearly completed.\n"
        '- Prefer short, imperative descriptions like '
        '"Add cost panel to InfinityWindow UI".\n'
        "- Do NOT include due dates or owners; only descriptions.\n"
        "- If there are no new tasks, return an empty list.\n"
        "- If a request matches an existing open task, avoid adding another duplicate.\n\n"
        "Output JSON ONLY, with this exact structure (no commentary):\n"
        '{\"tasks\": [{\"description\": \"...\"}, ...]}'
    )

    prompt: List[Dict[str, str]] = [
        {"role": "system", "content": system_instructions},
        {
            "role": "user",
            "content": f"Recent conversation:\n\n{convo_text}",
        },
    ]

    try:
        raw = generate_reply_from_history(
            prompt,
            model=None,  # let openai_client pick a cheap/fast model
            mode="fast",
        )
        if not raw:
            return

        # Try to parse JSON. If the model added chatter, pull out the first {...} block.
        text = raw.strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return
            snippet = text[start: end + 1]
            data = json.loads(snippet)

        tasks_data = []
        if isinstance(data, dict) and isinstance(data.get("tasks"), list):
            tasks_data = data["tasks"]
        elif isinstance(data, list):
            tasks_data = data
        else:
            return

        for t in tasks_data:
            if not isinstance(t, dict):
                continue
            desc = str(t.get("description") or "").strip()
            if not desc:
                continue

            # Check if an open task with identical description already exists.
            existing = (
                db.query(models.Task)
                .filter(
                    models.Task.project_id == conversation.project_id,
                    models.Task.description == desc,
                    models.Task.status == "open",
                )
                .first()
            )
            if existing:
                _record_task_automation_event(
                    "auto_deduped",
                    task=existing,
                    confidence=1.0,
                    conversation_id=conversation.id,
                    matched_text=desc,
                    model=model_name,
                    details={"reason": "already_open", "candidate": desc},
                    existing_task_description=existing.description,
                )
                continue

            normalized_desc = _normalize_task_text(desc or "")
            is_duplicate = False
            max_similarity = 0.0
            best_match: Optional[models.Task] = None
            for info in open_task_map.values():
                normalized_task = str(info.get("normalized") or "")
                if not normalized_task:
                    continue
                ratio = difflib.SequenceMatcher(
                    None, normalized_task, normalized_desc
                ).ratio()
                overlap_score = _token_overlap(normalized_task, normalized_desc)
                similarity = max(ratio, overlap_score)
                first_tokens_task = " ".join(normalized_task.split()[:5])
                first_tokens_candidate = " ".join(normalized_desc.split()[:5])
                first_overlap = _token_overlap_shortest(
                    first_tokens_task, first_tokens_candidate
                )
                if similarity > max_similarity:
                    max_similarity = similarity
                    candidate_task = info.get("task")
                    if isinstance(candidate_task, models.Task):
                        best_match = candidate_task
                if (
                    normalized_task in normalized_desc
                    or normalized_desc in normalized_task
                    or ratio >= 0.8
                    or overlap_score >= 0.78
                    or first_overlap >= 0.75
                ):
                    is_duplicate = True
                    break
            if is_duplicate:
                target_task = best_match if isinstance(best_match, models.Task) else None
                if target_task is None:
                    target_task = next(
                        (
                            info.get("task")
                            for info in open_task_map.values()
                            if isinstance(info.get("task"), models.Task)
                        ),
                        None,
                    )
                if target_task:
                    _record_task_automation_event(
                        "auto_deduped",
                        task=target_task,
                        confidence=_clamp_confidence(max_similarity),
                        conversation_id=conversation.id,
                        matched_text=desc,
                        model=model_name,
                        details={"reason": "duplicate_candidate", "model": model_name},
                        existing_task_description=getattr(
                            target_task, "description", None
                        ),
                    )
                continue

            add_confidence = _estimate_add_confidence(desc, max_similarity)
            priority = _infer_task_priority(desc)
            blocked_reason = _extract_blocked_reason(desc)
            dependency_hint = _extract_dependency_hint(desc)
            if add_confidence < _TASK_ADD_CONFIDENCE_THRESHOLD:
                _create_task_suggestion(
                    db,
                    project_id=conversation.project_id,
                    conversation_id=conversation.id,
                    action_type="add",
                    payload={
                        "description": desc,
                        "priority": priority,
                        "blocked_reason": blocked_reason,
                        "dependency_hint": dependency_hint,
                    },
                    confidence=add_confidence,
                )
                continue

            new_task = models.Task(
                project_id=conversation.project_id,
                description=desc,
                status="open",
                priority=priority,
                blocked_reason=blocked_reason,
            )
            db.add(new_task)
            db.flush()
            _record_task_automation_event(
                "auto_added",
                task=new_task,
                confidence=add_confidence,
                conversation_id=conversation.id,
                matched_text=desc,
                model=model_name,
                details={
                    "source": "auto_update",
                    "priority": priority,
                    "blocked_reason": blocked_reason,
                    "dependency_hint": dependency_hint,
                    "model": model_name,
                },
            )
            if dependency_hint:
                note = f"Dependency hint: {dependency_hint}"
                new_task.auto_notes = (
                    (new_task.auto_notes or "").strip() + "\n" + note
                ).strip()
            open_task_map[new_task.id] = {
                "task": new_task,
                "normalized": normalized_desc,
            }



    except Exception as e:  # noqa: BLE001
        print(f"[WARN] auto_update_tasks_from_conversation failed: {e!r}")
        # swallow errors, chat should not fail because of this


# ---------- Helper: auto‑title conversations ----------


def auto_title_conversation(
    db: Session,
    conversation: models.Conversation,
    max_messages: int = 16,
) -> None:
    """
    If this conversation does not yet have a meaningful title, ask a small/fast
    model to propose one based on the recent messages.

    This is best‑effort and should never raise out of here.
    """
    # Don't overwrite a non-default/manual title
    existing_title = (conversation.title or "").strip()
    if existing_title and not existing_title.lower().startswith("chat conversation"):
        return

    # Get recent messages (most recent first, then reverse)
    recent_messages = (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation.id)
        .order_by(models.Message.id.desc())
        .limit(max_messages)
        .all()
    )
    if not recent_messages:
        return

    recent_messages = list(reversed(recent_messages))

    convo_text_lines: List[str] = []
    for m in recent_messages:
        who = "User" if m.role == "user" else "Assistant"
        content = m.content.strip().replace("\n", " ")
        if len(content) > 200:
            content = content[:200] + "..."
        convo_text_lines.append(f"{who}: {content}")

    convo_text = "\n".join(convo_text_lines)

    system_instructions = (
        "You generate concise, descriptive titles for chat conversations.\n"
        "Rules:\n"
        "- Output ONLY the title text, no quotes or extra text.\n"
        "- Keep it under 8 words and under 60 characters.\n"
        "- Make it specific to this conversation, not generic.\n"
    )

    prompt: List[Dict[str, str]] = [
        {"role": "system", "content": system_instructions},
        {
            "role": "user",
            "content": (
                "Based on the following conversation snippets, propose a short, "
                "descriptive title for this conversation:\n\n"
                f"{convo_text}"
            ),
        },
    ]

    try:
        raw = generate_reply_from_history(
            prompt,
            model=None,  # let openai_client pick a cheap/fast model
            mode="fast",
        )
        if not raw:
            return

        title = str(raw).strip().splitlines()[0].strip()
        # Strip surrounding quotes if present
        if (title.startswith('"') and title.endswith('"')) or (
            title.startswith("'") and title.endswith("'")
        ):
            title = title[1:-1].strip()

        if not title:
            return

        conversation.title = title
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] auto_title_conversation failed: {e!r}")


_DECISION_PATTERN = re.compile(
    r"(?:decision\s*:|we\s+decided\s+(?:that|to)\s)(.+)", re.IGNORECASE
)


def _normalize_decision_text(value: str) -> str:
    cleaned = _TASK_TEXT_NORMALIZER.sub(" ", (value or "").lower())
    return " ".join(cleaned.split())


def auto_capture_decisions_from_conversation(
    db: Session,
    conversation: models.Conversation,
    max_messages: int = 12,
) -> None:
    recent_messages = (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation.id)
        .order_by(models.Message.id.desc())
        .limit(max_messages)
        .all()
    )
    if not recent_messages:
        return

    recent_messages = list(reversed(recent_messages))
    assistant_messages = [
        msg for msg in recent_messages if (msg.role or "").lower() == "assistant"
    ]
    if not assistant_messages:
        return

    existing_titles = {
        _normalize_decision_text(dec.title)
        for dec in db.query(models.ProjectDecision)
        .filter(models.ProjectDecision.project_id == conversation.project_id)
        .all()
    }

    created = 0
    for message in assistant_messages[-6:]:
        match = _DECISION_PATTERN.search(message.content or "")
        if not match:
            continue
        statement = match.group(1).strip()
        if not statement:
            continue
        normalized = _normalize_decision_text(statement)
        if not normalized or normalized in existing_titles:
            continue
        title = statement.split(".")[0][:120].strip() or "Decision"
        decision = models.ProjectDecision(
            project_id=conversation.project_id,
            title=title,
            details=statement,
            category=None,
            source_conversation_id=conversation.id,
            status="draft",
            tags_raw=None,
            follow_up_task_id=None,
            is_draft=True,
            auto_detected=True,
        )
        db.add(decision)
        existing_titles.add(normalized)
        created += 1

    if created:
        db.flush()


# ---------- Routes ----------


@app.get("/health")
def health():
    """
    Simple health check endpoint.
    """
    return {
        "status": "ok",
        "service": "InfinityWindow",
        "version": "0.3.0",
    }


# ---------- Projects ----------


@app.post("/projects", response_model=ProjectRead)
def create_project(
    payload: ProjectCreate, db: Session = Depends(get_db)
):
    """
    Create a new project.

    For now, 'name' must be unique.
    """
    validated_root = _validate_local_root_path(payload.local_root_path)

    existing = (
        db.query(models.Project)
        .filter(models.Project.name == payload.name)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Project with that name already exists.",
        )

    instructions = _normalize_instruction_text(payload.instruction_text)
    project = models.Project(
        name=payload.name,
        description=payload.description,
        local_root_path=str(validated_root),
        instruction_text=instructions,
        instruction_updated_at=datetime.now(timezone.utc) if instructions else None,
        is_archived=payload.is_archived,
        archived_at=datetime.now(timezone.utc) if payload.is_archived else None,
    )
    db.add(project)
    _commit_with_retry(db)
    db.refresh(project)
    return project


@app.get("/projects", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)):
    """
    List all projects.
    """
    projects = db.query(models.Project).order_by(models.Project.id).all()
    return projects


@app.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """
    Fetch a single project by id.
    """
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


@app.patch("/projects/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a project's metadata (name, description, local_root_path).
    """
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    if payload.name is not None:
        project.name = payload.name
    if payload.description is not None:
        project.description = payload.description
    if payload.local_root_path is not None:
        validated_root = _validate_local_root_path(payload.local_root_path)
        project.local_root_path = str(validated_root)
    if payload.instruction_text is not None:
        instructions = _normalize_instruction_text(payload.instruction_text)
        project.instruction_text = instructions
        project.instruction_updated_at = datetime.now(timezone.utc)
    if payload.pinned_note_text is not None:
        project.pinned_note_text = payload.pinned_note_text.strip() or None
    if payload.is_archived is not None:
        project.is_archived = payload.is_archived
        project.archived_at = datetime.now(timezone.utc) if payload.is_archived else None

    _commit_with_retry(db)
    db.refresh(project)
    return project


# ---------- Project instructions ----------


@app.get(
    "/projects/{project_id}/instructions",
    response_model=ProjectInstructionsRead,
)
def get_project_instructions(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = _ensure_project(db, project_id)
    return {
        "project_id": project.id,
        "instruction_text": project.instruction_text,
        "instruction_updated_at": project.instruction_updated_at,
        "pinned_note_text": project.pinned_note_text,
    }


@app.put(
    "/projects/{project_id}/instructions",
    response_model=ProjectInstructionsRead,
)
def update_project_instructions(
    project_id: int,
    payload: ProjectInstructionsPayload,
    db: Session = Depends(get_db),
):
    project = _ensure_project(db, project_id)
    instructions = _normalize_instruction_text(payload.instruction_text)
    project.instruction_text = instructions
    project.instruction_updated_at = datetime.now(timezone.utc)
    if payload.pinned_note_text is not None:
        project.pinned_note_text = payload.pinned_note_text.strip() or None
    db.commit()
    db.refresh(project)
    return {
        "project_id": project.id,
        "instruction_text": project.instruction_text,
        "instruction_updated_at": project.instruction_updated_at,
        "pinned_note_text": project.pinned_note_text,
    }


# ---------- Project decisions ----------


@app.get(
    "/projects/{project_id}/decisions",
    response_model=list[ProjectDecisionRead],
)
def list_project_decisions(
    project_id: int,
    db: Session = Depends(get_db),
):
    _ensure_project(db, project_id)
    decisions = (
        db.query(models.ProjectDecision)
        .filter(models.ProjectDecision.project_id == project_id)
        .order_by(
            models.ProjectDecision.is_draft.desc(),
            models.ProjectDecision.created_at.desc(),
        )
        .all()
    )
    return [_decision_to_schema(decision) for decision in decisions]


@app.post(
    "/projects/{project_id}/decisions",
    response_model=ProjectDecisionRead,
)
def create_project_decision(
    project_id: int,
    payload: ProjectDecisionCreate,
    db: Session = Depends(get_db),
):
    project = _ensure_project(db, project_id)

    if payload.source_conversation_id is not None:
        source_conversation = db.get(
            models.Conversation, payload.source_conversation_id
        )
        if source_conversation is None:
            raise HTTPException(
                status_code=404,
                detail="source_conversation_id not found.",
            )
        if source_conversation.project_id != project_id:
            raise HTTPException(
                status_code=400,
                detail="source_conversation_id does not belong to this project.",
            )

    title = payload.title.strip()
    if not title:
        raise HTTPException(
            status_code=400, detail="Decision title cannot be empty."
        )

    follow_up_task_id = None
    if payload.follow_up_task_id is not None:
        task = db.get(models.Task, payload.follow_up_task_id)
        if task is None or task.project_id != project_id:
            raise HTTPException(
                status_code=404,
                detail="follow_up_task_id not found for this project.",
            )
        follow_up_task_id = task.id

    decision = models.ProjectDecision(
        project_id=project.id,
        title=title,
        details=(payload.details or "").strip() or None,
        category=(payload.category or "").strip() or None,
        source_conversation_id=payload.source_conversation_id,
        status=(payload.status or "recorded").strip() or "recorded",
        tags_raw=_normalize_tags(payload.tags),
        follow_up_task_id=follow_up_task_id,
        is_draft=bool(payload.is_draft),
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return _decision_to_schema(decision)


@app.patch(
    "/decisions/{decision_id}",
    response_model=ProjectDecisionRead,
)
def update_project_decision(
    decision_id: int,
    payload: ProjectDecisionUpdate,
    db: Session = Depends(get_db),
):
    decision = db.get(models.ProjectDecision, decision_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="Decision not found.")

    if payload.title is not None:
        cleaned_title = payload.title.strip()
        if not cleaned_title:
            raise HTTPException(
                status_code=400, detail="Decision title cannot be empty."
            )
        decision.title = cleaned_title
    if payload.details is not None:
        decision.details = payload.details.strip() or None
    if payload.category is not None:
        decision.category = payload.category.strip() or None
    if payload.status is not None:
        decision.status = payload.status.strip() or "recorded"
    if payload.tags is not None:
        decision.tags_raw = _normalize_tags(payload.tags)
    if payload.follow_up_task_id is not None:
        if payload.follow_up_task_id == 0:
            decision.follow_up_task_id = None
        else:
            task = db.get(models.Task, payload.follow_up_task_id)
            if task is None or task.project_id != decision.project_id:
                raise HTTPException(
                    status_code=404,
                    detail="follow_up_task_id not found for this project.",
                )
            decision.follow_up_task_id = task.id
    if payload.is_draft is not None:
        decision.is_draft = payload.is_draft
    decision.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(decision)
    return _decision_to_schema(decision)


@app.delete("/decisions/{decision_id}")
def delete_project_decision(
    decision_id: int,
    db: Session = Depends(get_db),
):
    decision = db.get(models.ProjectDecision, decision_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="Decision not found.")
    db.delete(decision)
    db.commit()
    return {"status": "deleted", "decision_id": decision_id}


# ---------- Conversation folders ----------


def _sanitize_folder_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise HTTPException(
            status_code=400, detail="Folder name cannot be empty."
        )
    return cleaned


def _sanitize_color(color: Optional[str]) -> Optional[str]:
    if color is None:
        return None
    value = color.strip()
    if not value:
        return None
    if len(value) > 32:
        raise HTTPException(
            status_code=400, detail="Folder color must be <= 32 characters."
        )
    return value


@app.get(
    "/projects/{project_id}/conversation_folders",
    response_model=list[ConversationFolderRead],
)
def list_conversation_folders(
    project_id: int,
    db: Session = Depends(get_db),
):
    _ensure_project(db, project_id)
    folders = (
        db.query(models.ConversationFolder)
        .filter(models.ConversationFolder.project_id == project_id)
        .order_by(
            models.ConversationFolder.is_archived.asc(),
            models.ConversationFolder.sort_order.asc(),
            models.ConversationFolder.name.asc(),
        )
        .all()
    )
    return folders


@app.post("/conversation_folders", response_model=ConversationFolderRead)
def create_conversation_folder(
    payload: ConversationFolderCreate,
    db: Session = Depends(get_db),
):
    project = _ensure_project(db, payload.project_id)
    name = _sanitize_folder_name(payload.name)
    color = _sanitize_color(payload.color)
    sort_order = payload.sort_order if payload.sort_order is not None else 0

    folder = models.ConversationFolder(
        project_id=project.id,
        name=name,
        color=color,
        sort_order=sort_order,
        is_default=bool(payload.is_default),
        is_archived=bool(payload.is_archived),
    )
    db.add(folder)
    db.flush()

    if folder.is_default:
        _set_default_folder(db, project.id, folder.id)

    db.commit()
    db.refresh(folder)
    return folder


@app.patch(
    "/conversation_folders/{folder_id}",
    response_model=ConversationFolderRead,
)
def update_conversation_folder(
    folder_id: int,
    payload: ConversationFolderUpdate,
    db: Session = Depends(get_db),
):
    folder = _ensure_folder(db, folder_id)

    if payload.name is not None:
        folder.name = _sanitize_folder_name(payload.name)
    if payload.color is not None:
        folder.color = _sanitize_color(payload.color)
    if payload.sort_order is not None:
        folder.sort_order = payload.sort_order
    if payload.is_archived is not None:
        folder.is_archived = payload.is_archived
    set_default = None
    if payload.is_default is not None:
        set_default = payload.is_default

    db.commit()

    if set_default is not None:
        _set_default_folder(
            db,
            folder.project_id,
            folder.id if set_default else None,
        )
        db.commit()
        db.refresh(folder)
    else:
        db.refresh(folder)

    return folder


@app.delete("/conversation_folders/{folder_id}")
def delete_conversation_folder(
    folder_id: int,
    db: Session = Depends(get_db),
):
    folder = _ensure_folder(db, folder_id)

    # Move conversations out of this folder
    db.query(models.Conversation).filter(
        models.Conversation.folder_id == folder_id
    ).update({models.Conversation.folder_id: None})
    db.delete(folder)
    db.commit()
    return {"status": "deleted", "folder_id": folder_id}


def _conversation_with_folder_meta(
    db: Session, conversation: models.Conversation
) -> models.Conversation:
    """
    Ensure conversation objects carry folder name/color when serialized.
    """
    folder: Optional[models.ConversationFolder] = None
    if getattr(conversation, "folder_id", None):
        folder = conversation.folder
        if folder is None:
            folder = db.get(models.ConversationFolder, conversation.folder_id)
    setattr(conversation, "folder_name", folder.name if folder else None)
    setattr(conversation, "folder_color", folder.color if folder else None)
    return conversation


def _ensure_memory_item(
    db: Session, memory_id: int, project_id: Optional[int] = None
) -> models.MemoryItem:
    memory_item = db.get(models.MemoryItem, memory_id)
    if memory_item is None:
        raise HTTPException(status_code=404, detail="Memory item not found.")
    if project_id is not None and memory_item.project_id != project_id:
        raise HTTPException(
            status_code=400,
            detail="Memory item does not belong to this project.",
        )
    return memory_item


def _memory_item_to_read_model(
    memory_item: models.MemoryItem,
) -> MemoryItemRead:
    return MemoryItemRead(
        id=memory_item.id,
        project_id=memory_item.project_id,
        title=memory_item.title,
        content=memory_item.content,
        tags=_tags_to_list(memory_item.tags_raw),
        pinned=memory_item.pinned,
        expires_at=memory_item.expires_at,
        source_conversation_id=memory_item.source_conversation_id,
        source_message_id=memory_item.source_message_id,
        superseded_by_id=memory_item.superseded_by_id,
        created_at=memory_item.created_at,
        updated_at=memory_item.updated_at,
    )


def _active_memory_query(db: Session, project_id: int):
    now = datetime.now(timezone.utc)
    return (
        db.query(models.MemoryItem)
        .filter(models.MemoryItem.project_id == project_id)
        .filter(
            models.MemoryItem.superseded_by_id.is_(None),
        )
        .filter(
            (models.MemoryItem.expires_at.is_(None))
            | (models.MemoryItem.expires_at > now)
        )
    )


# ---------- Memory items ----------


@app.get(
    "/projects/{project_id}/memory",
    response_model=list[MemoryItemRead],
)
def list_memory_items(
    project_id: int,
    db: Session = Depends(get_db),
):
    _ensure_project(db, project_id)
    items = (
        _active_memory_query(db, project_id)
        .order_by(models.MemoryItem.pinned.desc(), models.MemoryItem.id.desc())
        .all()
    )
    return [_memory_item_to_read_model(item) for item in items]


@app.post(
    "/projects/{project_id}/memory",
    response_model=MemoryItemRead,
)
def create_memory_item(
    project_id: int,
    payload: MemoryItemCreate,
    db: Session = Depends(get_db),
):
    project = _ensure_project(db, project_id)

    source_conversation = None
    source_message = None
    if payload.source_conversation_id is not None:
        source_conversation = _ensure_conversation(
            db, payload.source_conversation_id, project_id=project_id
        )
    if payload.source_message_id is not None:
        source_message = db.get(models.Message, payload.source_message_id)
        if (
            source_message is None
            or source_message.conversation.project_id != project_id
        ):
            raise HTTPException(
                status_code=404,
                detail="Source message not found for this project.",
            )

    tags_raw = _normalize_tags(payload.tags)
    memory_item = models.MemoryItem(
        project_id=project.id,
        title=payload.title.strip(),
        content=payload.content.strip(),
        tags_raw=tags_raw,
        pinned=payload.pinned,
        expires_at=payload.expires_at,
        source_conversation_id=payload.source_conversation_id,
        source_message_id=payload.source_message_id,
    )
    db.add(memory_item)
    _flush_with_retry(db)

    if payload.supersedes_memory_id is not None:
        superseded = _ensure_memory_item(
            db, payload.supersedes_memory_id, project_id=project_id
        )
        superseded.superseded_by_id = memory_item.id

    try:
        embedding = get_embedding(memory_item.content)
        add_memory_embedding(
            memory_id=memory_item.id,
            project_id=project.id,
            content=memory_item.content,
            embedding=embedding,
            title=memory_item.title,
        )
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Vector store unavailable while saving memory item; please retry.",
        ) from exc

    _commit_with_retry(db)
    db.refresh(memory_item)
    return _memory_item_to_read_model(memory_item)


@app.get(
    "/memory_items/{memory_id}",
    response_model=MemoryItemRead,
)
def get_memory_item(memory_id: int, db: Session = Depends(get_db)):
    memory_item = _ensure_memory_item(db, memory_id)
    return _memory_item_to_read_model(memory_item)


@app.patch(
    "/memory_items/{memory_id}",
    response_model=MemoryItemRead,
)
def update_memory_item(
    memory_id: int,
    payload: MemoryItemUpdate,
    db: Session = Depends(get_db),
):
    memory_item = _ensure_memory_item(db, memory_id)
    content_changed = False

    if payload.title is not None:
        memory_item.title = payload.title.strip()
    if payload.content is not None:
        memory_item.content = payload.content.strip()
        content_changed = True
    if payload.tags is not None:
        memory_item.tags_raw = _normalize_tags(payload.tags)
    if payload.pinned is not None:
        memory_item.pinned = payload.pinned
    if payload.expires_at is not None:
        memory_item.expires_at = payload.expires_at
    if payload.source_conversation_id is not None:
        _ensure_conversation(
            db,
            payload.source_conversation_id,
            project_id=memory_item.project_id,
        )
        memory_item.source_conversation_id = payload.source_conversation_id
    if payload.source_message_id is not None:
        source_message = db.get(models.Message, payload.source_message_id)
        if (
            source_message is None
            or source_message.conversation.project_id
            != memory_item.project_id
        ):
            raise HTTPException(
                status_code=404,
                detail="Source message not found for this project.",
            )
        memory_item.source_message_id = payload.source_message_id
    if payload.superseded_by_id is not None:
        if payload.superseded_by_id == memory_item.id:
            raise HTTPException(
                status_code=400,
                detail="Memory item cannot supersede itself.",
            )
        if payload.superseded_by_id is None:
            memory_item.superseded_by_id = None
        else:
            superseder = _ensure_memory_item(
                db,
                payload.superseded_by_id,
                project_id=memory_item.project_id,
            )
            memory_item.superseded_by_id = superseder.id

    if content_changed:
        delete_memory_embedding(memory_item.id)
        try:
            embedding = get_embedding(memory_item.content)
            add_memory_embedding(
                memory_id=memory_item.id,
                project_id=memory_item.project_id,
                content=memory_item.content,
                embedding=embedding,
                title=memory_item.title,
            )
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            raise HTTPException(
                status_code=503,
                detail="Vector store unavailable while updating memory item; please retry.",
            ) from exc

    _commit_with_retry(db)
    db.refresh(memory_item)
    return _memory_item_to_read_model(memory_item)


@app.delete("/memory_items/{memory_id}")
def delete_memory_item(memory_id: int, db: Session = Depends(get_db)):
    memory_item = _ensure_memory_item(db, memory_id)
    delete_memory_embedding(memory_item.id)
    db.delete(memory_item)
    _commit_with_retry(db)
    return {"status": "deleted", "memory_id": memory_id}


# ---------- Conversations ----------


@app.get(
    "/projects/{project_id}/conversations",
    response_model=list[ConversationRead],
)
def list_project_conversations(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    List all conversations under a given project.
    """
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    conversations = (
        db.query(models.Conversation)
        .filter(models.Conversation.project_id == project_id)
        .order_by(models.Conversation.id)
        .all()
    )
    return [_conversation_with_folder_meta(db, convo) for convo in conversations]


@app.post("/conversations", response_model=ConversationRead)
def create_conversation(
    payload: ConversationCreate, db: Session = Depends(get_db)
):
    """
    Create a new conversation under a given project.
    """
    project = db.get(models.Project, payload.project_id)
    if not project:
        raise HTTPException(
            status_code=404, detail="Project not found."
        )

    folder_id: Optional[int]
    if payload.folder_id is not None:
        _ensure_folder(db, payload.folder_id, project_id=payload.project_id)
        folder_id = payload.folder_id
    else:
        folder_id = _get_default_folder_id(db, payload.project_id)

    conversation = models.Conversation(
        project_id=payload.project_id,
        title=payload.title,
        folder_id=folder_id,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return _conversation_with_folder_meta(db, conversation)


@app.patch(
    "/conversations/{conversation_id}",
    response_model=ConversationRead,
)
def rename_conversation(
    conversation_id: int,
    payload: ConversationRenamePayload,
    db: Session = Depends(get_db),
):
    """
    Rename a conversation by updating its title.
    """
    conv = (
        db.query(models.Conversation)
        .filter(models.Conversation.id == conversation_id)
        .first()
    )

    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if payload.title is not None:
        conv.title = payload.title

    if "folder_id" in payload.model_fields_set:
        if payload.folder_id is None:
            conv.folder_id = None
        else:
            _ensure_folder(
                db, payload.folder_id, project_id=conv.project_id
            )
            conv.folder_id = payload.folder_id

    db.commit()
    db.refresh(conv)
    return _conversation_with_folder_meta(db, conv)


@app.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageRead],
)
def list_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
):
    """
    List all messages in a conversation, in chronological order.
    """
    conversation = db.get(models.Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=404, detail="Conversation not found."
        )

    messages = (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation_id)
        .order_by(models.Message.id.asc())
        .all()
    )
    return messages


# ---------- Tasks (project TODOs) ----------


@app.get(
    "/projects/{project_id}/tasks",
    response_model=list[TaskRead],
)
def list_project_tasks(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    List all tasks for a given project.
    """
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    status_order = case(
        (models.Task.status == "open", 0),
        else_=1,
    )
    priority_order = case(
        (models.Task.priority == "critical", 0),
        (models.Task.priority == "high", 1),
        (models.Task.priority == "normal", 2),
        else_=3,
    )
    tasks = (
        db.query(models.Task)
        .filter(models.Task.project_id == project_id)
        .order_by(
            status_order,
            priority_order,
            # Ready (no blocked_reason) should surface before blocked
            case((models.Task.blocked_reason.is_(None), 0), else_=1),
            models.Task.updated_at.desc(),
            models.Task.id.asc(),
        )
        .all()
    )
    _attach_task_action_metadata(tasks)
    _cleanup_stale_suggestions(db, project_id)
    return tasks


@app.post("/projects/{project_id}/tasks", response_model=TaskRead)
def create_task_for_project(
    project_id: int,
    payload: TaskCreateScoped,
    db: Session = Depends(get_db),
):
    """
    Project-scoped task creation convenience wrapper.
    Delegates to the global create_task handler after
    injecting the path project_id into the payload.
    """
    scoped_payload = TaskCreate(
        project_id=project_id,
        description=payload.description,
        priority=payload.priority,
        blocked_reason=payload.blocked_reason,
        auto_notes=payload.auto_notes,
    )
    return create_task(payload=scoped_payload, db=db)


@app.post("/tasks", response_model=TaskRead)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new task for a project.
    """
    project = db.get(models.Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    priority = payload.priority or _infer_task_priority(payload.description)
    blocked_reason = payload.blocked_reason or _extract_blocked_reason(
        payload.description
    )
    task = models.Task(
        project_id=payload.project_id,
        description=payload.description,
        status="open",
        priority=priority,
        blocked_reason=blocked_reason,
        auto_notes=payload.auto_notes,
    )
    db.add(task)
    _commit_with_retry(db)
    db.refresh(task)
    return task


@app.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing task (description and/or status).
    """
    task = db.get(models.Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    if payload.description is not None:
        task.description = payload.description
    if payload.status is not None:
        task.status = payload.status
    if payload.priority is not None:
        task.priority = payload.priority
    if payload.blocked_reason is not None:
        task.blocked_reason = payload.blocked_reason
    if payload.auto_notes is not None:
        task.auto_notes = payload.auto_notes

    _commit_with_retry(db)
    db.refresh(task)
    return task


@app.delete("/tasks/{task_id}", response_model=dict)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """
    Delete a task by id.
    """
    task = db.get(models.Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    db.delete(task)
    _commit_with_retry(db)
    return {"status": "deleted", "task_id": task_id}


@app.post("/projects/{project_id}/auto_update_tasks")
def trigger_auto_update_tasks(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Trigger automatic TODO extraction from the most recent conversation
    in a project. If no conversation exists, return a 400.
    """
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    conversation = (
        db.query(models.Conversation)
        .filter(models.Conversation.project_id == project_id)
        .order_by(models.Conversation.id.desc())
        .first()
    )
    if conversation is None:
        raise HTTPException(
            status_code=400,
            detail="No conversations found for project; nothing to auto-update.",
        )

    ok, err = _run_auto_update_with_retry(db, conversation, model_name=None, attempts=3)
    if not ok:
        raise HTTPException(
            status_code=503,
            detail=(
                "Auto-update failed after retries; please retry."
                f" ({err or 'unknown error'})"
            ),
        ) from err

    return {
        "status": "ok",
        "project_id": project_id,
        "conversation_id": conversation.id,
    }


@app.get(
    "/projects/{project_id}/task_suggestions",
    response_model=list[TaskSuggestionRead],
)
def list_task_suggestions(
    project_id: int,
    status: Optional[str] = "pending",
    limit: int = 50,
    db: Session = Depends(get_db),
):
    _ensure_project(db, project_id)
    query = (
        db.query(models.TaskSuggestion)
        .filter(models.TaskSuggestion.project_id == project_id)
        .order_by(models.TaskSuggestion.created_at.desc())
    )
    if status:
        query = query.filter(models.TaskSuggestion.status == status)
    suggestions = query.limit(max(5, min(limit, 200))).all()
    return [_task_suggestion_to_schema(s) for s in suggestions]


@app.get(
    "/projects/{project_id}/tasks/overview",
    response_model=TaskOverviewRead,
)
def list_tasks_with_suggestions(
    project_id: int,
    suggestion_status: Optional[str] = "pending",
    suggestion_limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    Convenience endpoint to fetch tasks plus recent task suggestions
    (low-confidence add/complete) for a project in one call.
    """
    _ensure_project(db, project_id)
    tasks = list_project_tasks(project_id=project_id, db=db)
    _cleanup_stale_suggestions(db, project_id)
    suggestions = list_task_suggestions(
        project_id=project_id,
        status=suggestion_status,
        limit=suggestion_limit,
        db=db,
    )
    return TaskOverviewRead(tasks=tasks, suggestions=suggestions)


def _ensure_task_suggestion(
    db: Session,
    suggestion_id: int,
    *,
    project_id: Optional[int] = None,
) -> models.TaskSuggestion:
    suggestion = db.get(models.TaskSuggestion, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Task suggestion not found.")
    if project_id is not None and suggestion.project_id != project_id:
        raise HTTPException(status_code=404, detail="Task suggestion not found.")
    return suggestion


@app.post(
    "/task_suggestions/{suggestion_id}/approve",
    response_model=TaskSuggestionRead,
)
def approve_task_suggestion(
    suggestion_id: int,
    db: Session = Depends(get_db),
):
    suggestion = _ensure_task_suggestion(db, suggestion_id)
    if suggestion.status != "pending":
        raise HTTPException(
            status_code=400, detail="Suggestion is not pending approval."
        )
    payload = {}
    try:
        payload = json.loads(suggestion.payload or "{}")
    except json.JSONDecodeError:
        pass

    if suggestion.action_type == "add":
        description = (payload.get("description") or "").strip()
        if not description:
            raise HTTPException(
                status_code=400, detail="Suggestion payload missing description."
            )
        priority = payload.get("priority") or _infer_task_priority(description)
        blocked_reason = payload.get("blocked_reason") or _extract_blocked_reason(
            description
        )
        new_task = models.Task(
            project_id=suggestion.project_id,
            description=description,
            status="open",
            priority=priority,
            blocked_reason=blocked_reason,
        )
        db.add(new_task)
        db.flush()
        suggestion.target_task_id = new_task.id
        suggestion.status = "approved"
        suggestion.updated_at = datetime.now(timezone.utc)
        _record_task_action(
            "suggestion_approved_add",
            task=new_task,
            confidence=suggestion.confidence,
            conversation_id=suggestion.conversation_id,
            details={"suggestion_id": suggestion.id},
        )
    elif suggestion.action_type == "complete":
        if suggestion.target_task is None:
            raise HTTPException(
                status_code=400, detail="Suggestion missing target task."
            )
        suggestion.target_task.status = "done"
        suggestion.target_task.updated_at = datetime.now(timezone.utc)
        completion_note = (
            f"Closed via suggestion {suggestion.id} on "
            f"{datetime.now(timezone.utc).isoformat()} after the user approved an automation hint."
        )
        if suggestion.target_task.auto_notes:
            suggestion.target_task.auto_notes = (
                suggestion.target_task.auto_notes + "\n" + completion_note
            )
        else:
            suggestion.target_task.auto_notes = completion_note
        suggestion.status = "approved"
        suggestion.updated_at = datetime.now(timezone.utc)
        _record_task_action(
            "suggestion_approved_complete",
            task=suggestion.target_task,
            confidence=suggestion.confidence,
            conversation_id=suggestion.conversation_id,
            details={"suggestion_id": suggestion.id},
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported suggestion action: {suggestion.action_type}",
        )

    _commit_with_retry(db)
    db.refresh(suggestion)
    return _task_suggestion_to_schema(suggestion)


@app.post(
    "/task_suggestions/{suggestion_id}/dismiss",
    response_model=TaskSuggestionRead,
)
def dismiss_task_suggestion(
    suggestion_id: int,
    db: Session = Depends(get_db),
):
    suggestion = _ensure_task_suggestion(db, suggestion_id)
    if suggestion.status != "pending":
        raise HTTPException(
            status_code=400, detail="Suggestion is not pending dismissal."
        )
    suggestion.status = "dismissed"
    suggestion.updated_at = datetime.now(timezone.utc)
    _commit_with_retry(db)
    db.refresh(suggestion)
    try:
        payload = json.loads(suggestion.payload or "{}")
    except json.JSONDecodeError:
        payload = {}
    _record_task_action(
        "suggestion_dismissed",
        task=suggestion.target_task,
        description=payload.get("description"),
        confidence=suggestion.confidence,
        conversation_id=suggestion.conversation_id,
        details={"suggestion_id": suggestion.id},
    )
    return _task_suggestion_to_schema(suggestion)


def _cleanup_stale_suggestions(db: Session, project_id: int) -> None:
    """
    Dismiss completion suggestions whose target tasks are already done.
    """
    stale = (
        db.query(models.TaskSuggestion)
        .filter(
            models.TaskSuggestion.project_id == project_id,
            models.TaskSuggestion.action_type == "complete",
            models.TaskSuggestion.status == "pending",
        )
        .all()
    )
    for s in stale:
        if s.target_task_id:
            task = db.get(models.Task, s.target_task_id)
            if task and task.status == "done":
                s.status = "dismissed"
                s.updated_at = datetime.now(timezone.utc)
    db.commit()


# ---------- Usage (per-conversation) ----------


@app.get(
    "/conversations/{conversation_id}/usage",
    response_model=ConversationUsageSummary,
)
def get_conversation_usage(
    conversation_id: int,
    db: Session = Depends(get_db),
):
    """
    Return usage records (tokens, model, etc.) for a given conversation,
    plus simple totals.

    Cost is computed dynamically from tokens using the pricing table.
    """
    conversation = db.get(models.Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=404, detail="Conversation not found."
        )

    records_db = (
        db.query(models.UsageRecord)
        .filter(models.UsageRecord.conversation_id == conversation_id)
        .order_by(models.UsageRecord.created_at.asc())
        .all()
    )
    records: List[UsageRecordRead] = [
        UsageRecordRead.model_validate(r) for r in records_db
    ]

    total_in = sum((r.tokens_in or 0) for r in records)
    total_out = sum((r.tokens_out or 0) for r in records)

    total_cost: Optional[float] = None
    if records:
        running_cost = 0.0
        for r in records:
            try:
                running_cost += estimate_call_cost(
                    model=r.model,
                    tokens_in=r.tokens_in or 0,
                    tokens_out=r.tokens_out or 0,
                )
            except Exception as e:  # noqa: BLE001
                print(
                    f"[WARN] estimate_call_cost failed for record {r.id}: {e!r}"
                )
        total_cost = running_cost

    return ConversationUsageSummary(
        conversation_id=conversation_id,
        total_tokens_in=total_in,
        total_tokens_out=total_out,
        total_cost_estimate=total_cost,
        records=cast(List[UsageRecordRead], records),  # type: ignore[arg-type]
    )


# ---------- Telemetry & diagnostics ----------


@app.get("/debug/docs_status")
def read_docs_status() -> Dict[str, Any]:
    """
    Return status for required docs. `missing` is empty when all docs exist.
    """
    return collect_docs_status()


@app.get("/debug/telemetry")
def read_telemetry(reset: bool = False) -> Dict[str, Any]:
    """
    Return counters for auto-mode routing and autonomous task upkeep.

    Pass `reset=true` to zero the counters after reading them.
    """
    llm_snapshot = openai_module.get_llm_telemetry(reset=reset)
    task_snapshot_raw = get_task_telemetry(reset=reset)
    task_snapshot: Dict[str, Any] = dict(task_snapshot_raw)
    # Expose pending task suggestions to aid QA of low-confidence flows
    try:
        suggestions = (
            SessionLocal()
            .query(models.TaskSuggestion)
            .order_by(models.TaskSuggestion.created_at.desc())
            .limit(20)
            .all()
        )
        task_snapshot["suggestions"] = [
            {
                "id": s.id,
                "project_id": s.project_id,
                "conversation_id": s.conversation_id,
                "action_type": s.action_type,
                "confidence": s.confidence,
                "payload": s.payload,
                "created_at": s.created_at.isoformat(),
            }
            for s in suggestions
        ]
    except Exception as e:  # noqa: BLE001
        task_snapshot["suggestions_error"] = str(e)

    ingestion_snapshot = get_ingest_telemetry(reset=reset)
    return {
        "llm": llm_snapshot,
        "tasks": task_snapshot,
        "ingestion": ingestion_snapshot,
    }


class SeedTaskActionPayload(BaseModel):
    project_id: int
    description: str
    action: Literal[
        "auto_added",
        "auto_completed",
        "auto_deduped",
        "auto_dismissed",
        "auto_suggested",
    ] = "auto_added"
    confidence: float = 0.9
    status: Optional[str] = None
    auto_notes: Optional[str] = None
    model: Optional[str] = None


@app.post("/debug/seed_task_action", response_model=TaskRead)
def seed_task_action(payload: SeedTaskActionPayload, db: Session = Depends(get_db)):
    """
    Test helper: seed a task with automation metadata for UI/QA.
    Creates the task if it does not exist; records a task action with confidence.
    """
    project = db.get(models.Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    task = (
        db.query(models.Task)
        .filter(
            models.Task.project_id == payload.project_id,
            models.Task.description == payload.description,
        )
        .first()
    )
    if task is None:
        task = models.Task(
            project_id=payload.project_id,
            description=payload.description,
            status="open",
            priority="normal",
        )
        db.add(task)
        db.flush()

    if payload.status:
        task.status = payload.status
    if payload.auto_notes:
        task.auto_notes = payload.auto_notes

    if payload.action in _TASK_TELEMETRY:
        _TASK_TELEMETRY[payload.action] = _TASK_TELEMETRY.get(payload.action, 0) + 1

    _record_task_action(
        payload.action,
        task=task,
        confidence=payload.confidence,
        project_id=payload.project_id,
        details={
            "source": "debug_seed",
            "model": payload.model,
        },
    )
    db.commit()
    db.refresh(task)
    return task


@app.post(
    "/debug/task_suggestions/seed",
    response_model=TaskSuggestionRead,
)
def seed_task_suggestion(
    payload: TaskSuggestionSeedPayload,
    db: Session = Depends(get_db),
):
    _ensure_project(db, payload.project_id)
    conversation_id = None
    if payload.conversation_id is not None:
        convo = _ensure_conversation(
            db, payload.conversation_id, project_id=payload.project_id
        )
        conversation_id = convo.id

    target_task = None
    if payload.target_task_id is not None:
        target_task = db.get(models.Task, payload.target_task_id)
        if target_task is None or target_task.project_id != payload.project_id:
            raise HTTPException(
                status_code=404,
                detail="Target task not found for this project.",
            )

    action = (payload.action_type or "").lower()
    if action not in {"add", "complete"}:
        raise HTTPException(
            status_code=400,
            detail="action_type must be 'add' or 'complete'.",
        )

    suggestion_payload: Dict[str, Any]
    if action == "add":
        description = (payload.description or "").strip()
        if not description:
            raise HTTPException(
                status_code=400,
                detail="description is required for add suggestions.",
            )
        suggestion_payload = {
            "description": description,
            "priority": payload.priority,
            "blocked_reason": payload.blocked_reason,
        }
    else:
        if target_task is None:
            raise HTTPException(
                status_code=400,
                detail="target_task_id is required for complete suggestions.",
            )
        suggestion_payload = {
            "task_id": target_task.id,
            "matched_text": payload.description or "Seeded completion",
        }

    suggestion = _create_task_suggestion(
        db,
        project_id=payload.project_id,
        conversation_id=conversation_id,
        action_type=action,
        payload=suggestion_payload,
        confidence=payload.confidence,
        target_task=target_task,
    )
    db.commit()
    db.refresh(suggestion)
    return _task_suggestion_to_schema(suggestion)


# ---------- Filesystem browsing / editing ----------


@app.get("/projects/{project_id}/fs/list")
def list_project_files(
    project_id: int,
    subpath: str = "",
    db: Session = Depends(get_db),
):
    """
    List files/folders under a project's local_root_path.

    - subpath: optional subdirectory under the root.
    """
    project = _ensure_project(db, project_id)
    root = _get_project_root(project)
    target = _safe_join(root, subpath or "")

    if not target.exists():
        raise HTTPException(status_code=404, detail="Path not found.")
    if not target.is_dir():
        raise HTTPException(
            status_code=400, detail="Path is not a directory."
        )

    entries = []
    for p in sorted(
        target.iterdir(), key=lambda p: (p.is_file(), p.name.lower())
    ):
        try:
            stat = p.stat()
        except OSError:
            continue
        entries.append(
            {
                "name": p.name,
                "is_dir": p.is_dir(),
                "size": None if p.is_dir() else stat.st_size,
                "modified_at": datetime.fromtimestamp(
                    stat.st_mtime
                ).isoformat(),
                "rel_path": str(p.relative_to(root)),
            }
        )

    return {
        "root": str(root),
        "path": str(target.relative_to(root)),
        "entries": entries,
    }


@app.get("/projects/{project_id}/fs/read")
def read_project_file(
    project_id: int,
    file_path: Optional[str] = None,
    subpath: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Read a text file under the project's local_root_path.
    """
    project = _ensure_project(db, project_id)
    root = _get_project_root(project)
    effective_path = file_path or subpath
    if not effective_path:
        raise HTTPException(
            status_code=422,
            detail="file_path (or subpath) is required.",
        )

    target = _safe_join(root, effective_path)

    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    if not target.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file.")

    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File is not valid UTF-8 text; cannot be read as text.",
        )

    return {
        "root": str(root),
        "path": str(target.relative_to(root)),
        "content": content,
    }


@app.put("/projects/{project_id}/fs/write")
def write_project_file(
    project_id: int,
    payload: FileWritePayload,
    db: Session = Depends(get_db),
):
    """
    Write a text file under the project's local_root_path.

    - file_path: relative path under the root.
    - content: full file contents (UTF-8).
    - create_dirs: if True, create missing parent directories.
    """
    project = _ensure_project(db, project_id)
    root = _get_project_root(project)
    target = _safe_join(root, payload.file_path)

    parent = target.parent
    if not parent.exists():
        if payload.create_dirs:
            parent.mkdir(parents=True, exist_ok=True)
        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Parent directory does not exist. "
                    "Set create_dirs=true to create it."
                ),
            )

    try:
        target.write_text(payload.content, encoding="utf-8")
        stat = target.stat()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=500, detail=f"Failed to write file: {e}"
        )

    return {
        "root": str(root),
        "path": str(target.relative_to(root)),
        "size": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }


@app.post("/projects/{project_id}/fs/ai_edit")
def ai_edit_project_file(
    project_id: int,
    payload: FileAIEditPayload,
    db: Session = Depends(get_db),
):
    """
    Ask the AI to rewrite a file under the project's local_root_path.

    Flow:
    - Read the file (must exist, UTF-8 text).
    - Call OpenAI via generate_reply_from_history with clear instructions:
      "return ONLY the updated file content, no explanation".
    - Optionally write the edited content back to disk (apply_changes).
    - Log usage in usage_records.
    - Return original + edited content + basic usage info.

    This is the backend building block for "AI edits this file for me".
    The UI (or Swagger) can choose to:
      - just preview (apply_changes=false), or
      - auto-apply (apply_changes=true).
    """
    # 1) Resolve project + root + file path
    project = _ensure_project(db, project_id)
    root = _get_project_root(project)
    target = _safe_join(root, payload.file_path)

    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    if not target.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file.")

    try:
        original_content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File is not valid UTF-8 text; cannot be edited as text.",
        )

    # 2) Build AI prompt
    system_prompt = (
        "You are an expert code and text editor.\n"
        "You will be given a file path, editing instructions, and the current "
        "file content.\n"
        "Your job is to apply the instructions and return the FULL updated file "
        "content.\n"
        "IMPORTANT:\n"
        "- Return ONLY the new file content.\n"
        "- Do NOT include explanations, comments, or code fences.\n"
    )

    user_prompt = (
        f"File path: {payload.file_path}\n\n"
        f"Editing instructions:\n{payload.instruction}\n\n"
        "Current file content:\n"
        f"{original_content}"
    )

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # 3) Call OpenAI
    usage_info: Dict[str, object] = {}
    edited_content = generate_reply_from_history(
        messages,
        model=payload.model,
        mode=payload.mode or "code",
        usage_out=usage_info,
    )

    if not isinstance(edited_content, str):
        edited_content = str(edited_content)

    # 4) Optionally write back to disk
    applied = False
    if payload.apply_changes:
        try:
            target.write_text(edited_content, encoding="utf-8")
            applied = True
        except Exception as e:  # noqa: BLE001
            raise HTTPException(
                status_code=500,
                detail=f"Failed to write AI-edited file: {e}",
            )

    # 5) Log usage (best-effort)
    try:
        model_name = str(
            usage_info.get("model")
            or (payload.model or (payload.mode or "code"))
        )

        tokens_in = usage_info.get("tokens_in")
        tokens_out = usage_info.get("tokens_out")

        ti = _safe_int(tokens_in)
        to = _safe_int(tokens_out)

        cost_estimate: Optional[float] = None
        try:
            if ti is not None or to is not None:
                cost_estimate = estimate_call_cost(
                    model=model_name,
                    tokens_in=ti or 0,
                    tokens_out=to or 0,
                )
        except Exception as e:  # noqa: BLE001
            print(
                f"[WARN] estimate_call_cost failed while logging fs ai_edit usage: {e!r}"
            )

        usage_record = models.UsageRecord(
            project_id=project.id,
            conversation_id=payload.conversation_id,
            message_id=payload.message_id,
            model=model_name,
            tokens_in=ti,
            tokens_out=to,
            cost_estimate=cost_estimate,
        )
        db.add(usage_record)
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] Failed to create usage record for fs ai_edit: {e!r}")

    db.commit()

    # 6) Return both versions so the UI (or you in Swagger) can diff
    diff_text = "\n".join(
        difflib.unified_diff(
            original_content.splitlines(),
            edited_content.splitlines(),
            fromfile="original",
            tofile="edited",
            lineterm="",
        )
    )

    return {
        "root": str(root),
        "path": str(target.relative_to(root)),
        "applied": applied,
        "original_content": original_content,
        "edited_content": edited_content,
        "diff": diff_text if payload.include_diff else None,
        "usage": {
            "model": usage_info.get("model"),
            "tokens_in": usage_info.get("tokens_in"),
            "tokens_out": usage_info.get("tokens_out"),
        },
    }


# ---------- Ingestion jobs ----------


def _run_ingestion_job(
    job_id: int,
    include_globs: Optional[List[str]],
    name_prefix: Optional[str],
) -> None:
    session = SessionLocal()
    try:
        job = session.get(models.IngestionJob, job_id)
        if job is None:
            return
        if job.status not in {"failed", "completed"}:
            job.status = "running"
            job.started_at = datetime.now(timezone.utc)
            job.error_message = None
            _commit_with_retry(session)
        try:
            ingest_repo_job(
                db=session,
                job=job,
                include_globs=include_globs,
                name_prefix=name_prefix,
            )
            session.refresh(job)
            if job.status in {None, "pending", "running"}:
                job.status = "completed"
                job.finished_at = datetime.now(timezone.utc)
                _commit_with_retry(session)
        except Exception as exc:  # noqa: BLE001
            try:
                session.refresh(job)
            except Exception:
                pass
            if job is not None and job.status not in {"failed", "completed"}:
                job.status = "failed"
                job.error_message = str(exc)
                job.finished_at = datetime.now(timezone.utc)
                _commit_with_retry(session)
            print(f"[INGEST] Job {job_id} failed: {exc!r}")
    except Exception as exc:  # noqa: BLE001
        print(f"[INGEST] Unable to run job {job_id}: {exc!r}")
    finally:
        session.close()


def _schedule_ingestion_job(
    background_tasks: BackgroundTasks,
    job: models.IngestionJob,
    include_globs: Optional[List[str]],
    name_prefix: Optional[str],
) -> None:
    thread = threading.Thread(
        target=_run_ingestion_job,
        args=(job.id, include_globs, name_prefix),
        daemon=True,
    )
    thread.start()


@app.post(
    "/projects/{project_id}/ingestion_jobs",
    response_model=IngestionJobRead,
)
def create_ingestion_job_endpoint(
    project_id: int,
    payload: IngestionJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    project = _ensure_project(db, project_id)
    # Guard: require local_root_path for repo ingestions
    if not project.local_root_path:
        raise HTTPException(
            status_code=400,
            detail="Project local_root_path is not configured.",
        )
    project_root = Path(project.local_root_path).expanduser()
    if not project_root.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"Project local_root_path does not exist: {project.local_root_path}",
        )

    job = models.IngestionJob(
        project_id=project_id,
        kind=payload.kind,
        source=payload.source,
        status="pending",
        total_items=0,
        processed_items=0,
        meta={
            "include_globs": payload.include_globs,
            "name_prefix": payload.name_prefix,
        },
    )
    db.add(job)
    _commit_with_retry(db)
    db.refresh(job)

    if payload.kind != "repo":
        job.status = "failed"
        job.error_message = f"Unsupported ingestion kind: {payload.kind}"
        job.finished_at = datetime.now(timezone.utc)
        _commit_with_retry(db)
        db.refresh(job)
        return job

    source_path = Path(payload.source).expanduser()
    if not source_path.is_dir():
        job.status = "failed"
        job.error_message = f"Root path is not a directory: {payload.source}"
        job.finished_at = datetime.now(timezone.utc)
        _commit_with_retry(db)
        db.refresh(job)
        return job

    job.source = str(source_path)
    _commit_with_retry(db)
    _schedule_ingestion_job(
        background_tasks,
        job,
        payload.include_globs,
        payload.name_prefix,
    )
    return job


@app.get(
    "/projects/{project_id}/ingestion_jobs/{job_id}",
    response_model=IngestionJobRead,
)
def read_ingestion_job_endpoint(
    project_id: int,
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.get(models.IngestionJob, job_id)
    if job is None or job.project_id != project_id:
        raise HTTPException(status_code=404, detail="Ingestion job not found.")
    return job


@app.get(
    "/projects/{project_id}/ingestion_jobs",
    response_model=List[IngestionJobRead],
)
def list_ingestion_jobs_endpoint(
    project_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    _ensure_project(db, project_id)
    limit = max(1, min(limit, 100))
    jobs = (
        db.query(models.IngestionJob)
        .filter(models.IngestionJob.project_id == project_id)
        .order_by(models.IngestionJob.created_at.desc())
        .limit(limit)
        .all()
    )
    return jobs


@app.post(
    "/projects/{project_id}/ingestion_jobs/{job_id}/cancel",
    response_model=IngestionJobRead,
)
def cancel_ingestion_job_endpoint(
    project_id: int,
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.get(models.IngestionJob, job_id)
    if job is None or job.project_id != project_id:
        raise HTTPException(status_code=404, detail="Ingestion job not found.")
    if job.status not in {"pending", "running"}:
        raise HTTPException(status_code=400, detail="Job already finished.")
    job.cancel_requested = True
    _commit_with_retry(db)
    db.refresh(job)
    return job


# Legacy ingest endpoint: create a repo ingestion job for backwards compatibility
@app.post("/ingest")
def legacy_ingest(payload: dict, db: Session = Depends(get_db)):
    project_id = payload.get("project_id")
    root_path = payload.get("root_path")
    if project_id is None or root_path is None:
        raise HTTPException(status_code=400, detail="project_id and root_path are required.")
    include = payload.get("include")
    name_prefix = payload.get("name_prefix", None)

    project = _ensure_project(db, project_id)
    if not project.local_root_path:
        raise HTTPException(status_code=400, detail="Project local_root_path is not configured.")

    job = models.IngestionJob(
        project_id=project_id,
        kind="repo",
        source=root_path,
        status="pending",
        total_items=0,
        processed_items=0,
        meta={"include_globs": include, "name_prefix": name_prefix},
    )
    db.add(job)
    _commit_with_retry(db)
    db.refresh(job)
    return job


# ---------- Terminal ----------


@app.post("/terminal/run")
def run_terminal_command(
    payload: TerminalRunPayload,
    db: Session = Depends(get_db),
):
    """
    Run a shell command for a given project, safely constrained under
    that project's local_root_path.

    Body:
    {
      "project_id": 1,
      "cwd": "backend",       # optional, relative to project root
      "command": "git status",
      "timeout_seconds": 60
    }
    """
    if payload.project_id is None:
        raise HTTPException(status_code=422, detail="project_id is required (path or body).")

    project = _ensure_project(db, payload.project_id)
    root = _get_project_root(project)

    # Resolve working directory
    if payload.cwd:
        workdir = _safe_join(root, payload.cwd)
    else:
        workdir = root

    if not workdir.exists() or not workdir.is_dir():
        raise HTTPException(
            status_code=400,
            detail="Working directory does not exist or is not a directory.",
        )

    timeout = payload.timeout_seconds or 120

    try:
        result = subprocess.run(
            payload.command,
            shell=True,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        exit_code = result.returncode
    except subprocess.TimeoutExpired as e:
        stdout_raw = e.stdout or ""
        stderr_raw = e.stderr or ""
        stdout = (
            stdout_raw.decode() if isinstance(stdout_raw, (bytes, bytearray)) else str(stdout_raw)
        )
        stderr = (
            stderr_raw.decode() if isinstance(stderr_raw, (bytes, bytearray)) else str(stderr_raw)
        )
        stderr += f"\n[Command timed out after {timeout} seconds]"
        exit_code = -1
    except subprocess.CalledProcessError as e:
        stdout = e.stdout or ""
        stderr = (e.stderr or "") + f"\n[Command failed with exit code {e.returncode}]"
        exit_code = e.returncode
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run command: {e}",
        ) from e

    # Truncate very long output so we don't blow up the UI
    max_len = 8000
    if len(stdout) > max_len:
        stdout = stdout[:max_len] + "\n...[truncated]..."
    if len(stderr) > max_len:
        stderr = stderr[:max_len] + "\n...[truncated]..."

    return {
        "project_id": project.id,
        "cwd": str(workdir.relative_to(root)) if workdir != root else "",
        "command": payload.command,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
    }


@app.post("/projects/{project_id}/terminal/run")
def run_terminal_command_scoped(
    project_id: int,
    payload: TerminalRunPayload,
    db: Session = Depends(get_db),
):
    """
    Scoped variant for terminal.run matching API reference.
    """
    payload.project_id = project_id
    return run_terminal_command(payload=payload, db=db)


@app.get("/projects/{project_id}/terminal/history")
def list_terminal_history(project_id: int, db: Session = Depends(get_db)):
    """
    Placeholder history endpoint. Currently returns an empty list after
    verifying the project exists. Extend later to persist and return
    recent terminal runs.
    """
    _ensure_project(db, project_id)
    return []


# ---------- Chat ----------


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Chat within a specific conversation, backed by OpenAI, with automatic
    retrieval from stored messages and ingested documents.

    - If conversation_id is provided, we continue that conversation.
    - If conversation_id is omitted/null, we'll:
        * use the provided project_id if it exists, or
        * fall back to the first project if it exists, or
        * create a 'Default Project', then
        * create a new conversation under it.
    """

    # 1) Resolve or create conversation
    project: Optional[models.Project] = None

    folder: Optional[models.ConversationFolder] = None

    if payload.conversation_id is not None:
        conversation = db.get(models.Conversation, payload.conversation_id)
        if conversation is None:
            raise HTTPException(
                status_code=404, detail="Conversation not found."
            )
        project = db.get(models.Project, conversation.project_id)
        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project associated with conversation not found.",
            )
    else:
        # Use explicit project_id if provided
        if payload.project_id is not None:
            project = db.get(models.Project, payload.project_id)
            if project is None:
                raise HTTPException(
                    status_code=404, detail="Project not found."
                )
        else:
            # Get or create a default project
            project = (
                db.query(models.Project)
                .order_by(models.Project.id)
                .first()
            )
            if project is None:
                project = models.Project(
                    name="Default Project",
                    description="Auto-created default project.",
                )
                db.add(project)
                db.commit()
                db.refresh(project)

        # Create a new conversation
        conversation = models.Conversation(
            project_id=project.id,
            title="Chat conversation",
            folder_id=_get_default_folder_id(db, project.id),
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    if project is None:
        project = db.get(models.Project, conversation.project_id)
        if project is None:
            raise HTTPException(
                status_code=404, detail="Project not found for conversation."
            )

    if conversation.folder_id:
        folder = db.get(models.ConversationFolder, conversation.folder_id)

    # 2) Load existing messages for this conversation as history
    existing_messages = (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation.id)
        .order_by(models.Message.id.asc())
        .all()
    )

    # 3) Save the new user message (but don't commit yet)
    user_message = models.Message(
        conversation_id=conversation.id,
        role="user",
        content=payload.message,
    )
    db.add(user_message)
    db.flush()  # ensures user_message gets an ID before we commit

    # 4) Retrieval: embed user message and pull relevant messages & docs
    retrieval_context_text = ""
    user_embedding = None

    try:
        user_embedding = get_embedding(payload.message)

        # 4a) Similar messages in this project's conversation
        msg_results = query_similar_messages(
            project_id=conversation.project_id,
            query_embedding=user_embedding,
            conversation_id=conversation.id,
            folder_id=conversation.folder_id,
            n_results=5,
        )

        msg_docs_nested = msg_results.get("documents", [[]])
        msg_metas_nested = msg_results.get("metadatas", [[]])
        msg_docs = msg_docs_nested[0] if msg_docs_nested else []
        msg_metas = msg_metas_nested[0] if msg_metas_nested else []

        msg_snippets: List[str] = []
        for doc, meta in zip(msg_docs, msg_metas):
            role = meta.get("role", "unknown")
            msg_snippets.append(f"[{role} message] {doc}")

        # 4b) Similar document chunks in this project
        doc_results = query_similar_document_chunks(
            project_id=conversation.project_id,
            query_embedding=user_embedding,
            document_id=None,
            n_results=5,
        )

        doc_docs_nested = doc_results.get("documents", [[]])
        doc_metas_nested = doc_results.get("metadatas", [[]])
        doc_docs = doc_docs_nested[0] if doc_docs_nested else []
        doc_metas = doc_metas_nested[0] if doc_metas_nested else []

        # Resolve document titles for the retrieved chunks so responses can
        # surface doc names (not just ids).
        doc_snippets: List[str] = []
        doc_id_set = {
            int(meta.get("document_id"))
            for meta in doc_metas
            if meta.get("document_id") is not None
        }
        doc_title_map: Dict[int, str] = {}
        if doc_id_set:
            docs = (
                db.query(models.Document)
                .filter(models.Document.id.in_(doc_id_set))
                .all()
            )
            doc_title_map = {d.id: (d.name or f"Document {d.id}") for d in docs}

        for doc_text, meta in zip(doc_docs, doc_metas):
            document_id = meta.get("document_id")
            chunk_index = meta.get("chunk_index")
            title = doc_title_map.get(int(document_id)) if document_id is not None else None
            label = (
                f"Document {document_id}" if title is None else f"Document {document_id} ({title})"
            )
            doc_snippets.append(f"[{label}, chunk {chunk_index}] {doc_text}")

        context_parts: List[str] = []
        if msg_snippets:
            context_parts.append(
                "Relevant past messages:\n" + "\n\n".join(msg_snippets)
            )
        if doc_snippets:
            context_parts.append(
                "Relevant document excerpts:\n" + "\n\n".join(doc_snippets)
            )

        memory_results = query_similar_memory_items(
            project_id=conversation.project_id,
            query_embedding=user_embedding,
            n_results=5,
        )
        mem_ids_nested = memory_results.get("ids", [[]])
        mem_docs_nested = memory_results.get("documents", [[]])
        mem_metas_nested = memory_results.get("metadatas", [[]])
        mem_ids = mem_ids_nested[0] if mem_ids_nested else []
        mem_docs = mem_docs_nested[0] if mem_docs_nested else []
        mem_metas = mem_metas_nested[0] if mem_metas_nested else []

        mem_id_ints = [
            int(meta.get("memory_id", mid))
            for mid, meta in zip(mem_ids, mem_metas)
        ]
        memory_items = {}
        if mem_id_ints:
            memory_items = {
                item.id: item
                for item in _active_memory_query(db, conversation.project_id)
                .filter(models.MemoryItem.id.in_(mem_id_ints))
                .all()
            }

        memory_snippets: List[str] = []
        for mid, doc in zip(mem_id_ints, mem_docs):
            item = memory_items.get(mid)
            if not item:
                continue
            memory_snippets.append(f"[Memory: {item.title}] {doc}")

        if memory_snippets:
            context_parts.append(
                "Relevant project memories:\n" + "\n\n".join(memory_snippets)
            )

        if context_parts:
            retrieval_context_text = (
                "You have access to the following retrieved memory and document excerpts.\n"
                "Use them to ground your answer to the user's latest question. "
                "If anything conflicts with the user's most recent instructions, "
                "follow the user.\n\n"
                + "\n\n---\n\n".join(context_parts)
            )

    except Exception as e:  # noqa: BLE001
        # Retrieval should never break the chat flow
        print(f"[WARN] Retrieval failed: {e!r}")
        user_embedding = None

    # 5) Build the message list for OpenAI
    chat_history: List[Dict[str, str]] = []

    # System prompt to define behavior
    chat_history.append(
        {
            "role": "system",
            "content": (
                "You are InfinityWindow, a helpful AI assistant. "
                "You work inside a long-lived project workspace with persistent memory. "
                "Be clear, concise, and helpful.\n\n"
                "You are connected to the user's local project files through a backend API. "
                "You cannot see arbitrary files, only files under the project's local_root_path.\n\n"
                "FILE EDITS\n"
                "==========\n"
                "When (and only when) the user explicitly asks you to update a file, "
                "or clearly gives you permission to apply changes to a specific file, "
                "you may request an automatic edit by emitting an AI_FILE_EDIT block at "
                "the END of your reply, using this exact format:\n\n"
                "<<AI_FILE_EDIT>>\n"
                "{\"file_path\": \"relative/path/from/project/root.ext\", "
                "\"instruction\": \"Short, high-level description of the edit to apply\"}\n"
                "<<END_AI_FILE_EDIT>>\n\n"
                "Rules for AI_FILE_EDIT:\n"
                "- First, explain what you plan to change in natural language so the user understands.\n"
                "- Do NOT include the full file contents in your explanation; at most small code snippets.\n"
                "- Only emit AI_FILE_EDIT when the user has asked you to update a file "
                "or clearly agreed you should apply the change.\n"
                "- The backend will take care of reading and writing the actual file.\n\n"
                "TERMINAL COMMAND PROPOSALS\n"
                "==========================\n"
                "You also have access to a sandboxed terminal via a /terminal/run API. "
                "You CANNOT execute commands directly yourself. Instead, when you believe "
                "running a command would help (for example to inspect git status, check "
                "backend health, run tests, etc.), you should propose a command by returning "
                "a single JSON object at the END of your reply with this exact shape:\n\n"
                "{\"type\":\"terminal_command_proposal\", "
                "\"cwd\":\"backend\", "
                "\"command\":\"git status\", "
                "\"reason\":\"Short explanation for the human\"}\n\n"
                "Rules for terminal_command_proposal:\n"
                "- This JSON object MUST be valid JSON and MUST be the last thing in your reply.\n"
                "- 'cwd' is optional. When provided, it MUST be a path RELATIVE to the project root "
                "(for example: \"\", \"backend\", \"frontend\", \"backend/app\").\n"
                "- Do NOT put 'cd ...' inside the 'command' string. The backend will set the working "
                "directory using 'cwd'. For example, to run 'git status' in the backend folder, use:\n"
                "  {\"type\":\"terminal_command_proposal\", \"cwd\":\"backend\", \"command\":\"git status\", \"reason\":\"...\"}\n"
                "  NOT: {\"type\":\"terminal_command_proposal\", \"command\":\"cd backend && git status\"}\n"
                "- Assume a Windows development environment. Prefer commands that work in cmd/PowerShell "
                "on Windows (e.g. 'dir' instead of 'ls', 'type' instead of 'cat').\n"
                "- Treat the project root as the root of the InfinityWindow repo (it already points at "
                "the correct folder; do NOT invent absolute paths like '/path/to/your/infinitywindow').\n"
                "- Prefer small, diagnostic commands: 'git status', 'dir', 'python -m pip list', "
                "'pytest -q', 'uvicorn app.api.main:app --reload', 'npm run dev', etc.\n"
                "- Never suggest destructive commands such as 'rm -rf', 'del /s', 'format', "
                "'docker system prune', 'git reset --hard', or anything that obviously destroys data.\n"
                "- For this project, prefer non-Docker workflows (the backend is usually run via "
                "'uvicorn app.api.main:app --reload' in the 'backend' folder, and the frontend via "
                "'npm run dev' in the 'frontend' folder). Avoid 'docker compose' and 'journalctl' "
                "unless the user explicitly asks for Docker-specific help.\n"
                "- When the user explicitly asks you to output ONLY a terminal_command_proposal JSON, "
                "do so with no extra commentary.\n"
                "- Otherwise, you may include normal explanation first, then the JSON object as the last "
                "thing in your message.\n"
                "- When the user uses language like 'run X', 'execute X', 'start X', or "
                "'run git status / git diff and then explain the output', interpret that as a request "
                "to use the terminal API on their behalf. In those cases you should propose a "
                "terminal_command_proposal instead of telling the user to run the commands manually.\n\n"
                "TERMINAL RUN RESULT MESSAGES\n"
                "============================\n"
                "The UI will sometimes send you a message that begins with the exact sentence "
                "\"I ran the terminal command you proposed.\" followed by lines like:\n"
                "Command: <command>\n"
                "CWD: <cwd or (project root)>\n"
                "Exit code: <integer exit code>\n"
                "\n"
                "STDOUT:\n"
                "<stdout text (possibly truncated)>\n"
                "\n"
                "STDERR:\n"
                "<stderr text or '(no stderr)'>\n"
                "\n"
                "Treat this as a structured report of the result of the last terminal_command_proposal "
                "you emitted. Use the exit code and the stdout/stderr contents to decide what to do next:\n"
                "- If exit_code is non-zero and STDERR contains an error or traceback, you may propose "
                "file edits (via AI_FILE_EDIT) or follow-up terminal commands to investigate or fix it.\n"
                "- If exit_code is 0 but the output shows that nothing meaningful happened (for example, "
                "pytest reporting 'no tests ran'), you should consider proposing a different command that "
                "is more likely to help (for example starting the backend with uvicorn).\n"
                "- You should generally NOT repeat the exact same terminal_command_proposal immediately "
                "after seeing a result for that command, unless the user explicitly asks you to rerun it.\n"
                "- Remember that the human still has to click the 'Run command' button; your job is to "
                "choose helpful, safe commands and then interpret the results you are given.\n"
            ),
        }
    )

    if folder:
        folder_desc = (
            f"This conversation is organized under the folder "
            f"'{folder.name}'. "
        )
        if folder.is_archived:
            folder_desc += (
                "That folder is archived, so treat this thread as historical "
                "context unless the user says otherwise. "
            )
        chat_history.append(
            {
                "role": "system",
                "content": folder_desc
                + "Use this to understand the theme or status of the work.",
            }
        )

    pinned_memories = (
        _active_memory_query(db, project.id)
        .filter(models.MemoryItem.pinned.is_(True))
        .order_by(models.MemoryItem.updated_at.desc())
        .limit(5)
        .all()
    )

    if project.instruction_text:
        instructions = project.instruction_text.strip()
        if instructions:
            chat_history.append(
                {
                    "role": "system",
                    "content": (
                        "Project-specific instructions:\n"
                        f"{instructions}\n\n"
                        "Always follow these instructions while assisting with "
                        "this project."
                    ),
                }
            )

    if pinned_memories:
        pinned_lines = "\n".join(
            f"- {item.title}: {item.content}"
            for item in pinned_memories
        )
        chat_history.append(
            {
                "role": "system",
                "content": (
                    "Pinned project memories:\n"
                    f"{pinned_lines}\n\n"
                    "Respect these pinned memories unless the user explicitly "
                    "says they are outdated."
                ),
            }
        )

    # Optional retrieval context as an additional system message
    if retrieval_context_text:
        chat_history.append(
            {
                "role": "system",
                "content": retrieval_context_text,
            }
        )

    # Previous messages
    for m in existing_messages:
        chat_history.append(
            {
                "role": m.role,
                "content": m.content,
            }
        )

    # Current user message
    chat_history.append({"role": "user", "content": payload.message})

    # 6) Call OpenAI to generate a reply, capturing usage metadata if available
    usage_info: Dict[str, object] = {}
    try:
        raw_reply = generate_reply_from_history(
            chat_history,
            model=payload.model,
            mode=payload.mode or "auto",
            usage_out=usage_info,  # filled by openai_client if supported
        )
    except Exception as e:  # noqa: BLE001
        # If the chosen model is not available, attempt a safe fallback.
        msg = str(e).lower()
        if "model_not_found" in msg or "does not exist" in msg:
            raw_reply = generate_reply_from_history(
                chat_history,
                model=None,
                mode=payload.mode or "auto",
                usage_out=usage_info,
            )
        else:
            raise
    raw_reply_text = raw_reply if isinstance(raw_reply, str) else raw_reply.get("reply", "")
    chosen_model = None
    if isinstance(raw_reply, dict):
        chosen_model = raw_reply.get("model")
        # In case the stub returns tokens/cost, include them
        if "tokens_in" in raw_reply:
            usage_info["tokens_in"] = raw_reply["tokens_in"]
        if "tokens_out" in raw_reply:
            usage_info["tokens_out"] = raw_reply["tokens_out"]
        if "cost" in raw_reply:
            usage_info["cost_estimate"] = raw_reply["cost"]
        if "mode" in raw_reply and not payload.mode:
            usage_info["mode"] = raw_reply["mode"]

    # 6b) Look for any AI_FILE_EDIT blocks in the reply and strip them from the visible text
    clean_reply_text, file_edit_requests = _extract_ai_file_edits(raw_reply_text)
    reply_text = clean_reply_text or raw_reply_text

    # 7) Save assistant message
    assistant_message = models.Message(
        conversation_id=conversation.id,
        role="assistant",
        content=reply_text,
    )
    db.add(assistant_message)
    db.flush()  # ensure assistant_message.id exists

    # 7b) If the model requested AI file edits, run them now (best-effort)
    project_root = None
    try:
        if conversation.project:
            project_root = _get_project_root(conversation.project)
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] Could not resolve project root for AI edit: {e!r}")

    if file_edit_requests:
        for req in file_edit_requests:
            file_path = str(req.get("file_path") or "").strip()
            instruction = str(req.get("instruction") or "").strip()
            if not file_path or not instruction:
                continue

            if project_root:
                target = _safe_join(project_root, file_path)
                if not target.exists():
                    print(
                        f"[WARN] Skipping AI file edit for missing file {file_path!r} "
                        f"in conversation {conversation.id}"
                    )
                    continue

            try:
                payload_for_edit = FileAIEditPayload(
                    file_path=file_path,
                    instruction=instruction,
                    model=None,
                    mode="code",
                    apply_changes=True,
                    conversation_id=conversation.id,
                    message_id=assistant_message.id,
                )
                # Reuse the existing AI edit endpoint logic directly
                ai_edit_project_file(
                    project_id=conversation.project_id,
                    payload=payload_for_edit,
                    db=db,
                )
            except HTTPException as e:
                print(
                    f"[WARN] AI file edit failed for {file_path!r} in conversation "
                    f"{conversation.id}: {e.detail!r}"
                )
            except Exception as e:  # noqa: BLE001
                print(
                    f"[WARN] Unexpected error while running AI file edit for "
                    f"{file_path!r}: {e!r}"
                )

    # 8) Create embeddings and index in Chroma
    try:
        # Reuse user embedding if we have it, otherwise compute now
        if user_embedding is None:
            user_embedding = get_embedding(payload.message)

        add_message_embedding(
            message_id=user_message.id,
            conversation_id=conversation.id,
            project_id=conversation.project_id,
            role="user",
            content=payload.message,
            embedding=user_embedding,
            folder_id=conversation.folder_id,
        )

        # Assistant message embedding
        assistant_embedding = get_embedding(reply_text)
        add_message_embedding(
            message_id=assistant_message.id,
            conversation_id=conversation.id,
            project_id=conversation.project_id,
            role="assistant",
            content=reply_text,
            embedding=assistant_embedding,
            folder_id=conversation.folder_id,
        )
    except Exception as e:  # noqa: BLE001
        # Do not fail the request if indexing fails
        print(f"[WARN] Failed to index messages in Chroma: {e!r}")

    # 9) Persist an approximate usage record (best-effort)
    try:
        model_name = str(
            usage_info.get("model")
            or chosen_model
            or (payload.model or (payload.mode or "auto"))
        )

        tokens_in = usage_info.get("tokens_in")
        tokens_out = usage_info.get("tokens_out")

        ti = _safe_int(tokens_in)
        to = _safe_int(tokens_out)

        cost_estimate: Optional[float] = None
        try:
            if ti is not None or to is not None:
                cost_estimate = estimate_call_cost(
                    model=model_name,
                    tokens_in=ti or 0,
                    tokens_out=to or 0,
                )
        except Exception as e:  # noqa: BLE001
            print(
                f"[WARN] estimate_call_cost failed while logging usage: {e!r}"
            )

        usage_record = models.UsageRecord(
            project_id=conversation.project_id,
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            model=model_name,
            tokens_in=ti,
            tokens_out=to,
            cost_estimate=cost_estimate,
        )
        db.add(usage_record)
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] Failed to create usage record: {e!r}")

    # 10) Auto‑title the conversation (best‑effort, doesn't block)
    try:
        auto_title_conversation(db, conversation)
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] auto_title_conversation outer failed: {e!r}")

    # 11) AI‑assist the project TODO list (best‑effort, doesn't block)
    if _AUTO_UPDATE_TASKS_AFTER_CHAT:
        ok, err = _run_auto_update_with_retry(
            db, conversation, model_name=model_name, attempts=2, base_delay=0.2
        )
        if not ok:
            print(
                "[WARN] auto_update_tasks_from_conversation failed after retry: "
                f"{err!r}"
            )
    else:
        print(
            "[Tasks] Skipping auto-update after chat "
            "(AUTO_UPDATE_TASKS_AFTER_CHAT disabled)."
        )
    try:
        auto_capture_decisions_from_conversation(db, conversation)
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] auto_capture_decisions_from_conversation failed: {e!r}")

    # 12) Commit everything
    db.commit()

    return ChatResponse(
        conversation_id=conversation.id,
        reply=reply_text,
    )
