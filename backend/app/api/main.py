from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine, get_db
from app.db import models
from app.llm.openai_client import generate_reply_from_history
from app.llm.embeddings import get_embedding
from app.llm.pricing import estimate_call_cost
from app.vectorstore.chroma_store import (
    add_message_embedding,
    query_similar_messages,
    query_similar_document_chunks,
)
from app.api.search import router as search_router
from app.api.docs import router as docs_router
from app.api.github import router as github_router

# Create tables on import (simple approach for now; later we can use migrations)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="InfinityWindow Backend",
    description="Backend service for the InfinityWindow personal AI workbench.",
    version="0.3.0",
)

# Allow local frontend dev (Vite default ports, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)
app.include_router(docs_router)
app.include_router(github_router)


# ---------- Pydantic Schemas ----------


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    # NEW: optional local filesystem root configured at creation
    local_root_path: Optional[str] = None
    instruction_text: Optional[str] = None


class ProjectRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    local_root_path: Optional[str] = None
    instruction_text: Optional[str] = None
    instruction_updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    local_root_path: Optional[str] = None
    instruction_text: Optional[str] = None


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


class TaskRead(BaseModel):
    id: int
    project_id: int
    description: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class TaskUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None


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
    total_tokens_in: int
    total_tokens_out: int
    total_cost_estimate: Optional[float]
    records: List[UsageRecordRead]


class ProjectInstructionsRead(BaseModel):
    project_id: int
    instruction_text: Optional[str]
    instruction_updated_at: Optional[datetime]


class ProjectInstructionsPayload(BaseModel):
    instruction_text: Optional[str]


class ProjectDecisionCreate(BaseModel):
    title: str
    details: Optional[str] = None
    category: Optional[str] = None
    source_conversation_id: Optional[int] = None


class ProjectDecisionRead(BaseModel):
    id: int
    project_id: int
    title: str
    details: Optional[str]
    category: Optional[str]
    source_conversation_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


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
    model: Optional[str] = None
    mode: Optional[str] = "code"
    apply_changes: bool = False
    conversation_id: Optional[int] = None
    message_id: Optional[int] = None


class TerminalRunPayload(BaseModel):
    """
    Run a shell command in the context of a project.

    - project_id: which project's local_root_path to treat as the root.
    - cwd: optional subdirectory under the project root (relative path).
    - command: the shell command to run.
    - timeout_seconds: safety timeout so commands can't hang forever.
    """
    project_id: int
    command: str
    cwd: Optional[str] = None
    timeout_seconds: Optional[int] = 120


# ---------- Helpers: misc ----------


def _normalize_instruction_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


# ---------- Helper: filesystem ----------


def _ensure_project(db: Session, project_id: int) -> models.Project:
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


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


def _safe_join(root: Path, relative_path: str) -> Path:
    """
    Resolve a subpath/file_path safely under root, preventing path traversal.

    Rules:
    - 'relative_path' must be relative (no drive, no leading slash).
    - It may not contain '..' segments.
    - Final resolved path must still live under 'root'.
    """
    if not relative_path:
        return root

    rel_obj = Path(relative_path)

    # Disallow absolute paths like "C:\\Windows" or "/etc"
    if rel_obj.is_absolute():
        raise HTTPException(
            status_code=400,
            detail="Path must be relative to the project local_root_path.",
        )

    # Disallow any attempt to go up with ".."
    if any(part == ".." for part in rel_obj.parts):
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


def auto_update_tasks_from_conversation(
    db: Session,
    conversation: models.Conversation,
    max_messages: int = 16,
) -> None:
    """
    Look at the recent messages in the conversation, ask a small/fast model
    to extract TODO items, and add any NEW open tasks to the project.

    This is best‑effort and should never raise out of here.
    """
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

    system_instructions = (
        "You help maintain a TODO list for a long-running software project.\n"
        "From the recent conversation messages below, extract any NEW, "
        "actionable tasks that should be added to the project TODO list.\n\n"
        "Rules:\n"
        "- Only include tasks that clearly represent work to be done in the future.\n"
        "- Skip questions, chit-chat, or things already clearly completed.\n"
        '- Prefer short, imperative descriptions like '
        '"Add cost panel to InfinityWindow UI".\n'
        "- Do NOT include due dates or owners; only descriptions.\n"
        "- If there are no new tasks, return an empty list.\n\n"
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
            desc = (t.get("description") or "").strip()
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
                continue

            new_task = models.Task(
                project_id=conversation.project_id,
                description=desc,
                status="open",
            )
            db.add(new_task)

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
    existing = (
        db.query(models.Project)
        .filter(models.Project.name == payload.name)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Project with that name already exists.",
        )

    instructions = _normalize_instruction_text(payload.instruction_text)
    project = models.Project(
        name=payload.name,
        description=payload.description,
        local_root_path=payload.local_root_path,
        instruction_text=instructions,
        instruction_updated_at=datetime.utcnow() if instructions else None,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@app.get("/projects", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)):
    """
    List all projects.
    """
    projects = db.query(models.Project).order_by(models.Project.id).all()
    return projects


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
        project.local_root_path = payload.local_root_path
    if payload.instruction_text is not None:
        instructions = _normalize_instruction_text(payload.instruction_text)
        project.instruction_text = instructions
        project.instruction_updated_at = datetime.utcnow()

    db.commit()
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
    project.instruction_updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    return {
        "project_id": project.id,
        "instruction_text": project.instruction_text,
        "instruction_updated_at": project.instruction_updated_at,
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
        .order_by(models.ProjectDecision.created_at.desc())
        .all()
    )
    return decisions


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

    decision = models.ProjectDecision(
        project_id=project.id,
        title=title,
        details=(payload.details or "").strip() or None,
        category=(payload.category or "").strip() or None,
        source_conversation_id=payload.source_conversation_id,
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


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


def _conversation_with_folder_meta(
    db: Session, conversation: models.Conversation
) -> models.Conversation:
    """
    Ensure conversation objects carry folder name/color when serialized.
    """
    folder = None
    if conversation.folder_id:
        folder = conversation.folder
        if folder is None:
            folder = db.get(models.ConversationFolder, conversation.folder_id)
    conversation.folder_name = folder.name if folder else None
    conversation.folder_color = folder.color if folder else None
    return conversation

    db.delete(folder)
    db.commit()

    return {"status": "deleted", "folder_id": folder_id}


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

    tasks = (
        db.query(models.Task)
        .filter(models.Task.project_id == project_id)
        .order_by(models.Task.created_at.asc())
        .all()
    )
    return tasks


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

    task = models.Task(
        project_id=payload.project_id,
        description=payload.description,
        status="open",
    )
    db.add(task)
    db.commit()
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

    db.commit()
    db.refresh(task)
    return task


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

    records = (
        db.query(models.UsageRecord)
        .filter(models.UsageRecord.conversation_id == conversation_id)
        .order_by(models.UsageRecord.created_at.asc())
        .all()
    )

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
        records=records,
    )


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
    file_path: str,
    db: Session = Depends(get_db),
):
    """
    Read a text file under the project's local_root_path.
    """
    project = _ensure_project(db, project_id)
    root = _get_project_root(project)
    target = _safe_join(root, file_path)

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

        ti = int(tokens_in) if tokens_in is not None else None
        to = int(tokens_out) if tokens_out is not None else None

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
    return {
        "root": str(root),
        "path": str(target.relative_to(root)),
        "applied": applied,
        "original_content": original_content,
        "edited_content": edited_content,
        "usage": {
            "model": usage_info.get("model"),
            "tokens_in": usage_info.get("tokens_in"),
            "tokens_out": usage_info.get("tokens_out"),
        },
    }


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
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        exit_code = result.returncode
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout or ""
        stderr = (e.stderr or "") + f"\n[Command timed out after {timeout} seconds]"
        exit_code = -1
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run command: {e}",
        )

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

        doc_snippets: List[str] = []
        for doc_text, meta in zip(doc_docs, doc_metas):
            document_id = meta.get("document_id")
            chunk_index = meta.get("chunk_index")
            doc_snippets.append(
                f"[Document {document_id}, chunk {chunk_index}] {doc_text}"
            )

        context_parts: List[str] = []
        if msg_snippets:
            context_parts.append(
                "Relevant past messages:\n" + "\n\n".join(msg_snippets)
            )
        if doc_snippets:
            context_parts.append(
                "Relevant document excerpts:\n" + "\n\n".join(doc_snippets)
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
    raw_reply_text = generate_reply_from_history(
        chat_history,
        model=payload.model,
        mode=payload.mode or "auto",
        usage_out=usage_info,  # filled by openai_client if supported
    )

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
    if file_edit_requests:
        for req in file_edit_requests:
            file_path = (req.get("file_path") or "").strip()
            instruction = (req.get("instruction") or "").strip()
            if not file_path or not instruction:
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
            or (payload.model or (payload.mode or "auto"))
        )

        tokens_in = usage_info.get("tokens_in")
        tokens_out = usage_info.get("tokens_out")

        ti = int(tokens_in) if tokens_in is not None else None
        to = int(tokens_out) if tokens_out is not None else None

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
    try:
        auto_update_tasks_from_conversation(db, conversation)
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] auto_update_tasks_from_conversation outer failed: {e!r}")

    # 12) Commit everything
    db.commit()

    return ChatResponse(
        conversation_id=conversation.id,
        reply=reply_text,
    )
