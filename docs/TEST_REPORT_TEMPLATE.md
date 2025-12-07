# InfinityWindow – Test Report Template

_Use this file as a template for recording results from `docs/TEST_PLAN.md`. Make a copy per run, e.g. `docs/TEST_REPORT_2025-12-02.md`._

---

## 1. Run metadata

- **Date**: `YYYY‑MM‑DD`
- **Tester**: `Your name`
- **Backend version**: `vX.Y.Z` (from `/health`; expected host `http://127.0.0.1:8000`)
- **Frontend SHA / branch**: `...` (optional)
- **OS / environment**: `Windows 11, C:\InfinityWindow`
- **DB state**:
  - [ ] Fresh DB (deleted `backend/infinitywindow.db` before run)
  - [ ] Existing DB
- **Chroma state**:
  - [ ] Fresh `backend/chroma_data`
  - [ ] Existing data

---

## 2. Summary

- **Overall result**: `PASS / FAIL / MIXED`
- **High‑level notes**:
  - `e.g., All core v2 features passed; minor UI issues in Tasks tab.`

---

## 3. Detailed results by phase

### Phase A – Environment & system sanity

| Test ID    | Description                    | Result (P/F/B) | Notes / Errors |
|-----------|--------------------------------|----------------|----------------|
| A-Env-01  | Backend health check `/health` |                |                |
| A-Env-02  | Frontend startup               |                |                |
| A-Env-03  | Clean DB + Chroma reset        |                |                |

### Phase B – Core data model & CRUD

| Test ID    | Description                         | Result (P/F/B) | Notes / Errors |
|-----------|-------------------------------------|----------------|----------------|
| B-Proj-01 | Project CRUD                        |                |                |
| B-Conv-01 | Conversation create/rename (API/UI) |                |                |
| B-Chat-01 | Chat pipeline basics                |                |                |
| B-Tasks-01| Tasks CRUD + auto‑extraction        |                |                |
| B-Tasks-02| Autonomous TODO maintenance loop    |                |                |
| B-Tasks-03| Suggested-change queue & telemetry  |                |                |
| B-Tasks-04| Task automation/UI exhaustive (see docs/tasks/TEST_PLAN_TASKS.md) |                | Use alongside main plan for ≥98/100 task coverage |
| B-Docs-01 | Docs CRUD + ingestion happy path    |                |                |
| B-Docs-02 | Ingestion reuse & hash skipping     |                |                |
| B-Docs-03 | Progress metrics (files/bytes/time) |                |                |
| B-Docs-04 | Cancel endpoint & graceful stop     |                |                |
| B-Docs-05 | Job history table parity            |                |                |
| B-Docs-06 | Failure surfacing & error text      |                |                |
| B-Docs-07 | Ingestion telemetry snapshot/reset  |                |                |

#### Large repo ingestion evidence log

| Scenario (B-Docs-0X) | Job ID | Status | Files processed / total | Bytes processed / total | Duration (UI vs API) | UI evidence (screenshot/file) | Telemetry before → after | Notes / errors |
|----------------------|--------|--------|-------------------------|-------------------------|----------------------|-------------------------------|--------------------------|----------------|
|                      |        |        |                         |                         |                      |                               |                          |                |

- Attach (or link) the raw `GET /projects/{id}/ingestion_jobs/{job_id}` payload and `/debug/telemetry` snapshots for each scenario.
- Record cancel latency (B-Docs-04) and history table screenshots (B-Docs-05) in the Notes column if not captured elsewhere.

#### Chat modes & model routing

| Test ID   | Mode     | Expected model               | Result (P/F/B) | Notes / Errors |
|-----------|----------|------------------------------|----------------|----------------|
| B-Mode-01 | auto     | `OPENAI_MODEL_AUTO` / default |                |                |
| B-Mode-01 | fast     | `OPENAI_MODEL_FAST` / default |                |                |
| B-Mode-01 | deep     | `OPENAI_MODEL_DEEP` / default |                |                |
| B-Mode-01 | budget   | `OPENAI_MODEL_BUDGET` / default |              |                |
| B-Mode-01 | research | `OPENAI_MODEL_RESEARCH` / default |            |                |
| B-Mode-01 | code     | `OPENAI_MODEL_CODE` / default |                |                |
| B-Mode-02 | auto adaptive (coding)   | codex / high-accuracy model |  |                |
| B-Mode-02 | auto adaptive (research) | deep-research model          |  |                |
| B-Mode-02 | auto adaptive (lightweight) | nano/mini tier          |  |                |
| B-Mode-02 | auto adaptive (planning/roadmap) | deep/pro tier     |  |                |

### Phase C – Retrieval & vector store

| Test ID       | Description               | Result (P/F/B) | Notes / Errors |
|--------------|---------------------------|----------------|----------------|
| C-MsgSearch-01 | Message search          |                |                |
| C-DocSearch-01 | Document search         |                |                |
| C-MemorySearch-01 | Memory item retrieval |              |                |
| C-Search-02 | Search tab filters & open-in UI |                |                |

### Phase D – Filesystem & AI file edits

| Test ID   | Description                     | Result (P/F/B) | Notes / Errors |
|----------|---------------------------------|----------------|----------------|
| D-FS-01  | List and read files             |                |                |
| D-FS-02  | Write file and verify           |                |                |
| D-AIEdit-01 | AI file edit with diff/preview |              |                |
| D-Usage-01 | Usage API summary              |                |                |
| D-Usage-02 | Usage tab dashboard            |                |                |

### Phase E – Terminal integration

| Test ID    | Description                       | Result (P/F/B) | Notes / Errors |
|-----------|-----------------------------------|----------------|----------------|
| E-Term-01 | AI terminal proposal loop         |                |                |
| E-Term-02 | Manual terminal runner + history  |                |                |

### Phase F – Instructions, decisions, folders, memory

| Test ID    | Description                          | Result (P/F/B) | Notes / Errors |
|-----------|--------------------------------------|----------------|----------------|
| F-Inst-01 | Instructions CRUD + prompt injection |                |                |
| F-Inst-02 | Pinned note + diff/preview           |                |                |
| F-Dec-01  | Decision log CRUD                    |                |                |
| F-Dec-02  | Decision filters & actions (UI)      |                |                |
| F-Dec-03  | Decision automation & drafts         |                |                |
| F-Fold-01 | Conversation folders (CRUD + usage)  |                |                |
| F-Mem-01  | Memory items CRUD + retrieval        |                |                |

### Phase G – Right‑column UI 2.0 regression

For each tab, record at least one “visual sanity” test and any discovered issues:

| Test ID    | Tab      | Description                          | Result (P/F/B) | Notes / Errors |
|-----------|----------|--------------------------------------|----------------|----------------|
| G-Tasks-01| Tasks    | Basic layout + add/toggle            |                |                |
| G-Docs-01 | Docs     | List + ingest forms                  |                |                |
| G-Files-01| Files    | Browser + editor + AI diff           |                |                |
| G-Search-01| Search  | Messages/docs search                 |                |                |
| G-Term-01 | Terminal | Manual + AI, last run, history       |                |                |
| G-Usage-01| Usage    | Totals + recent records              |                |                |
| G-Tasks-02| Tasks    | Suggestions drawer & priority UI     |                |                |
| G-Notes-01| Notes    | Instructions + decisions             |                |                |
| G-Mem-01  | Memory   | List, create, pin/unpin, delete      |                |                |

### Phase H – Error handling & edge cases

| Test ID    | Description                        | Result (P/F/B) | Notes / Errors |
|-----------|------------------------------------|----------------|----------------|
| H-FS-01   | Invalid file path (`..`, absolute) |                |                |
| H-Term-01 | Terminal timeout / invalid command |                |                |
| H-Chat-01 | Invalid conversation_id / project_id |              |                |
| H-Debug-01| Telemetry endpoint sanity          |                |                |

### Phase J (Autopilot & Blueprint – future)

> These rows become active once Autopilot & Blueprint features are implemented (`AUTOPILOT_PLAN.md`). Leave blank for current runs.

| Test ID       | Description                                   | Result (P/F/B) | Notes / Errors |
|--------------|-----------------------------------------------|----------------|----------------|
| J-Blueprint-01 | Large blueprint ingestion & Plan tree       |                |                |
| J-Autopilot-01 | Semi‑auto run lifecycle                     |                |                |
| J-Autopilot-02 | Full‑auto with rollback safety              |                |                |

### Phase I – Performance & durability spot checks

| Test ID    | Description                                   | Result (P/F/B) | Notes / Errors |
|-----------|-----------------------------------------------|----------------|----------------|
| I-Perf-01 | Many conversations/messages                   |                |                |
| I-Perf-02 | Many tasks/docs/memory items                  |                |                |
| I-Perf-03 | Repeated AI edits & terminal runs, general UX |                |                |

---

## 4. Issues & follow‑up plan

For each failure or concern, file a short entry here (or link to an issue tracker if you use one):

| ID          | Related Test(s)   | Description of Issue                                    | Severity (Low/Med/High) | Proposed Fix / Next Step                   |
|-------------|-------------------|---------------------------------------------------------|--------------------------|--------------------------------------------|
| ISSUE-001   | B-Tasks-01        | Auto‑extracted tasks occasionally duplicate existing…  | Med                      | Add stricter dedupe in `auto_update_tasks` |
| ISSUE-002   | G-Files-01        | Files tab editor scrolls weird on small screens…       | Low                      | Adjust CSS `max-height` and padding…       |

Use this section to drive future work on v3/v4/v5 as outlined in `docs/PROGRESS.md` (Next phases).
- Remember to mirror each ISSUE-00x entry in `docs/ISSUES_LOG.md` (same ID, summary, fix, and verification reference) so future runs can quickly reference historical problems.


