"""API sweep smoke script (QA).

Calls a representative set of endpoints and emits JSON with per-call status.
"""

import json
import sys
import time
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8002"
results = []
PROJECT_NAME = f"API Full Sweep {int(time.time() * 1000)}"
TEST_DOC_PATH = Path("C:/InfinityWindow_QA/backend/README.md")


def post(path: str, payload: dict) -> httpx.Response:
    return httpx.post(f"{BASE}{path}", json=payload, timeout=30)


def get(path: str) -> httpx.Response:
    return httpx.get(f"{BASE}{path}", timeout=30)


def check(label: str, resp: httpx.Response, expect: int = 200) -> None:
    if resp.status_code != expect:
        results.append(
            {
                "label": label,
                "status": resp.status_code,
                "body": resp.text[:400],
            }
        )
    else:
        results.append({"label": label, "status": "ok", "code": resp.status_code})


def main() -> int:
    proj = post(
        "/projects",
        {"name": PROJECT_NAME, "local_root_path": "C:\\\\InfinityWindow_QA"},
    )
    if proj.status_code == 200:
        check("create project", proj)
        proj_id = proj.json().get("id")
    elif proj.status_code == 409:
        # Fallback: reuse first available project
        check("create project (conflict)", proj)
        existing = get("/projects")
        if existing.status_code == 200 and existing.json():
            proj_id = existing.json()[0]["id"]
            results.append(
                {"label": "reuse project", "status": "ok", "project_id": proj_id}
            )
        else:
            results.append(
                {
                    "label": "reuse project",
                    "status": existing.status_code,
                    "body": existing.text[:400],
                }
            )
            print(json.dumps(results, indent=2))
            return 1
    else:
        check("create project", proj)
        print(json.dumps(results, indent=2))
        return 1

    # Instructions / pinned note (PUT)
check(
    "put instructions+pinned",
    httpx.put(
        f"{BASE}/projects/{proj_id}/instructions",
        json={
            "instruction_text": "api sweep instructions",
            "pinned_note_text": "pinned from api sweep",
        },
        timeout=30,
    ),
)
check("get instructions", get(f"/projects/{proj_id}/instructions"))

    # Decisions
    check(
        "post decision",
        post(f"/projects/{proj_id}/decisions", {"title": "api decision", "details": "details"}),
    )
    check("list decisions", get(f"/projects/{proj_id}/decisions"))

    # Memory
    check(
        "post memory",
        post(
            f"/projects/{proj_id}/memory",
            {"title": "api mem", "content": "content", "tags": ["a"]},
        ),
    )
    check("list memory", get(f"/projects/{proj_id}/memory"))

# Tasks (create uses /tasks)
check("post task", post("/tasks", {"project_id": proj_id, "description": "api task"}))
check("list tasks", get(f"/projects/{proj_id}/tasks"))

    # Task update (PATCH) if a task exists
    tasks_resp = get(f"/projects/{proj_id}/tasks")
    if tasks_resp.status_code == 200 and tasks_resp.json():
        first_task_id = tasks_resp.json()[0]["id"]
        check(
            "patch task",
            httpx.patch(
                f"{BASE}/tasks/{first_task_id}",
                json={"status": "done"},
                timeout=30,
            ),
        )

    # Conversation + chat + usage
    conv = post("/conversations", {"project_id": proj_id, "title": "api conv"})
    check("create conversation", conv)
    conv_id = None
    if conv.status_code == 200:
        conv_id = conv.json().get("id")
        chat = post("/chat", {"conversation_id": conv_id, "message": "ping"})
        check("chat", chat)
        check("usage", get(f"/conversations/{conv_id}/usage"))
    else:
        results.append({"label": "usage skip", "note": "conversation not created"})

    # Filesystem list
    check("fs list", get(f"/projects/{proj_id}/fs/list"))

    # Search messages after seeding token
    if conv_id is not None:
        token = "API_SWEEP_TOKEN"
        post("/chat", {"conversation_id": conv_id, "message": token})
        search = post(
            "/search/messages",
            {"project_id": proj_id, "query": token, "limit": 5},
        )
        check("search messages", search)

    # Files read/write (basic smoke)
    check(
        "fs read",
        post(
            f"/projects/{proj_id}/fs/read",
            {"path": "backend/README.md", "offset": 0, "limit": 200},
        ),
    )
    check(
        "fs write",
        post(
            f"/projects/{proj_id}/fs/write",
            {
                "path": "backend/tmp_api_sweep_note.txt",
                "content": "api sweep note",
            },
        ),
    )

    # Text document ingestion (docs)
    if TEST_DOC_PATH.exists():
        check(
            "ingest text doc",
            post(
                f"/projects/{proj_id}/docs/text",
                {
                    "path": str(TEST_DOC_PATH),
                    "prefix": "api_sweep_doc",
                    "content": TEST_DOC_PATH.read_text(encoding="utf-8")[:2000],
                },
            ),
        )

    # Recent ingestion jobs (list)
    check("list ingestion jobs", get(f"/projects/{proj_id}/ingestion/jobs"))

    # Ingest local repo (start job with existing root)
    check(
        "ingest local repo",
        post(
            "/ingest",
            {
                "project_id": proj_id,
                "root_path": "C:\\\\InfinityWindow_QA",
                "include": ["backend"],
                "exclude": ["node_modules", ".git"],
            },
        ),
    )

    # Terminal
    check(
        "terminal run",
        post(
            "/terminal/run",
            {"project_id": proj_id, "cwd": "", "command": "pwd"},
        ),
    )

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

