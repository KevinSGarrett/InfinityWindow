# Retrieval Telemetry v1 – Alignment Notes

## Scope
- **Profiles**: `backend/app/retrieval_config.py` parses `IW_RETRIEVAL_MESSAGES_K`, `IW_RETRIEVAL_DOCS_K`, `IW_RETRIEVAL_MEMORY_K`, `IW_RETRIEVAL_TASKS_K`, clamps them (1–50), and surfaces the active profile via `/debug/retrieval_config`.
- **Counters**: `_RETRIEVAL_TELEMETRY` lives in `backend/app/api/main.py` and is incremented from chat (messages/docs/memory/tasks) plus `app/api/search.py` for the `/search/*` endpoints.
- **UI**: `frontend/src/App.tsx` shows Retrieval stats inside the Usage tab, adjacent to usage cards/filters, and links back to `/debug/retrieval_config` to keep CRM + UI evidence in sync.

## Telemetry surfaces
- `GET /debug/telemetry` → `retrieval` block with eight keys: `chat_{messages,docs,memory,tasks}_hits`, `search_{messages,docs,memory,tasks}_hits`.
- `GET /debug/telemetry?reset=true` zeros the counters after snapshots so QA logs stay scoped per run.
- `GET /debug/retrieval_config` returns `{ profile: {messages_k,...}, source }`, making it easy to confirm env overrides.
- Usage tab `retrieval-stats` component renders once telemetry returns at least one key; legacy builds simply omit it.

## Tests
- **API**: `qa/tests_api/test_retrieval_telemetry.py` drives chat/search/reset flows and asserts the counters increment and reset deterministically.
- **Docs guardrails**: `qa/tests_api/test_docs_status.py` now expects `/debug/retrieval_config` to respond (smoke coverage for the CRM link).
- **UI**: `frontend/tests/usage-retrieval-telemetry.spec.ts` covers the happy path (seed doc, chat, search, refresh telemetry, assert UI shows non-zero hits) and skips gracefully if the backend build predates this feature.

## Remaining work / Future phases
- Telemetry-driven tuning (recommendations + alerts when certain surfaces never produce hits).
- Multiple retrieval profiles per surface (chat vs. search vs. tasks) with UI to switch quickly.
- Long-window analytics: persist retrieval counters alongside Usage telemetry exports for historical comparisons.
