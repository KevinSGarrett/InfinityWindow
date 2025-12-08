import uuid

from qa._utils import api_request


def test_chat_search_tasks_e2e():
    """
    End-to-end API path: chat -> tasks auto-add -> message search

    - Create project
    - Chat to add tasks (stubbed chat reply)
    - Verify tasks exist (login/logout)
    - Search messages for the request text
    """
    project_name = f"E2E ChatSearchTasks {uuid.uuid4().hex[:6]}"
    project = api_request(
        "post",
        "/projects",
        json={
            "name": project_name,
            "description": "E2E chat/search/tasks",
            "local_root_path": "C:\\InfinityWindow",
        },
    ).json()

    chat = api_request(
        "post",
        "/chat",
        json={
            "project_id": project["id"],
            "message": "We need to add a login page and fix the logout bug soon.",
        },
    ).json()

    tasks = api_request(
        "get",
        f"/projects/{project['id']}/tasks",
    ).json()
    descriptions = [t["description"].lower() for t in tasks]
    assert any("login page" in d for d in descriptions), "Missing login task"
    assert any("logout" in d for d in descriptions), "Missing logout task"

    search = api_request(
        "post",
        "/search/messages",
        json={"query": "login page", "project_id": project["id"]},
    ).json()
    assert search, "Expected search results for chat messages"

