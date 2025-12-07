# QA Smoke Suite

This directory contains a tiny battery of backend-only regression probes that
can be run without starting `uvicorn`. Each probe spins up FastAPI’s
`TestClient`, stubs the expensive OpenAI calls, and validates that the latest
bug fixes still hold.

## Prerequisites

1. Run everything from the repo root (`C:\InfinityWindow`).
2. Use the backend virtual environment (`backend\.venv\Scripts\python.exe`).
3. Ensure the dev server is **stopped**; these probes instantiate the app
   directly and will fail if port 8000 is already bound.
4. Optional but recommended: reset the QA data for a clean slate.

```powershell
python tools\reset_qa_env.py --confirm --force
```

## Running the suite

```powershell
backend\.venv\Scripts\python.exe -m qa.run_smoke
```

### What it does

| Probe | Description |
| --- | --- |
| `message_search_probe` | Inserts a unique token via `/chat` and asserts `/search/messages` returns the user + assistant messages. |
| `tasks_autoloop_probe` | Creates a throwaway project/conversation, runs the autonomous TODO maintainer, and verifies that completion statements mark tasks done + insert follow-ups. |
| `ingestion_probe` | Spins up a temporary repo, runs `/projects/{id}/ingestion_jobs`, confirms batching completes, verifies the status endpoint, ensures a second run skips unchanged files, and forces a failure to check error reporting. |
| `mode_routing_probe` | Patches `_call_model` to capture models, then hits `/chat` with all explicit modes and four auto-mode scenarios (code, research, lightweight, planning). |

If any probe raises, `qa.run_smoke` exits with a non-zero status and prints the
failure context.

## Adding new probes

1. Add a module alongside the others (e.g., `qa/new_probe.py`) exposing a
   `run()` function.
2. Import and call it from `qa/run_smoke.py`.
3. Document the new probe in the table above.


