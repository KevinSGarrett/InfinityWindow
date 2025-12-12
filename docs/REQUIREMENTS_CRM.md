# Requirements CRM – Retrieval & Context Shaping

This excerpt tracks the Retrieval/context shaping requirements for the current window. It stays in lock‑step with `docs/TODO_CHECKLIST.md`, `docs/PROGRESS.md`, and `docs/ALIGNMENT_OVERVIEW.md`.

## Enhanced retrieval & context shaping — Status: Partial (v1)

| Requirement slice | Status | Evidence / Notes |
| --- | --- | --- |
| Env‑driven retrieval profiles (`IW_RETRIEVAL_*`, `/debug/retrieval_config`) | **Partial (v1)** | Retrieval fan‑out for chat/search/memory/tasks now pulls from `backend/app/retrieval_config.py`. Operators can tune `IW_RETRIEVAL_MESSAGES_K`, `IW_RETRIEVAL_DOCS_K`, `IW_RETRIEVAL_MEMORY_K`, and `IW_RETRIEVAL_TASKS_K`, all clamped between 1–50. `/debug/retrieval_config` echoes the active profile so QA can confirm what the backend is using before/after overrides. |
| Retrieval telemetry v1 (counters + `/debug/telemetry` → `retrieval` section) | **Partial (v1)** | `_RETRIEVAL_TELEMETRY` counters live in `backend/app/api/main.py` and are incremented from chat + search pathways (`record_retrieval_event` + `app/api/search.py::_record_retrieval`). `/debug/telemetry` now returns a `retrieval` object with per‑surface hit totals and supports `reset=true`. Covered by `qa/tests_api/test_retrieval_telemetry.py`. |
| Usage tab retrieval config + retrieval stats | **Partial (v1)** | `frontend/src/App.tsx` renders a **Retrieval stats** block (data‑test id `retrieval-stats`) beside the existing Usage telemetry cards. It summarizes chat/search hits per surface (messages/docs/memory/tasks) and links back to `/debug/retrieval_config` for active K’s. UI verified via `frontend/tests/usage-retrieval-telemetry.spec.ts`. |

### Future work

- **Telemetry-driven tuning** based on production retrieval logs (auto profile selection + anomaly detection for skewed counters).
- **Distinct strategy profiles per surface** (chat vs. search vs. tasks) instead of a single project-wide profile.
- **Long-window analytics & tuning flows** (persisted retrieval counter history, alerts, and Usage dashboard overlays).
