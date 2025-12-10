# InfinityWindow – Test Report (2025‑12‑02)

## 1. Run metadata

- **Date**: 2025‑12‑02 (QA rerun after DB reset)
- **Tester**: ChatGPT (automation + API calls + Playwright)
- **Backend version**: `v0.3.0` (`/health`)
- **Environment**: Windows 11 staging copy at `C:\InfinityWindow_QA`
- **Servers**: `uvicorn app.api.main:app --reload`, `npm run dev -- --host 127.0.0.1 --port 5174`
- **DB state**:
  - [x] Fresh DB (reset via `python tools/reset_qa_env.py --confirm --force`)
- **Chroma state**:
  - [x] Fresh `backend/chroma_data` (same helper)
- **CI**: `make ci` (pytest reported “no tests” → ignored; Vite build succeeded)

## 2. Summary

- **Overall result**: PASS
- Full QA plan rerun against a freshly reset DB/Chroma snapshot (project `id=6`) using the guarded helper. All backend workflows (projects, conversations, chat, tasks, docs, filesystem, AI edits, terminal, instructions, decisions, folders, memory) and UI flows passed.
- Playwright regression (`tests/right-column.spec.ts`) continues to pass; each right-column tab activates correctly.
- Prior blockers from ISSUE‑001/003/004/005 were retested and now pass:
  - `/search/messages` returns hits immediately after new chats.
  - `mode="research"` gracefully falls back to an available model when `o3-deep-research` is unavailable.
  - `mode="auto"` routes to fast/deep/code/research tiers based on prompt heuristics.
  - Autonomous TODO maintenance automatically closes completed work, avoids duplicates, and keeps open tasks surfaced first.
- Performance/stress tests (Phase I) remain deferred; they need dedicated generators.

## 3. Detailed results by phase

### Phase A – Environment & system sanity

| Test ID   | Description                    | Result | Notes / Errors |
|-----------|--------------------------------|--------|----------------|
| A-Env-01  | Backend health check `/health` | Pass   | `{"status":"ok","service":"InfinityWindow","version":"0.3.0"}` |
| A-Env-02  | Frontend availability          | Pass   | Dev server responds at `http://127.0.0.1:5174`. |
| A-Env-03  | Clean DB + Chroma reset        | Pass   | Used `python tools/reset_qa_env.py --confirm --force`; script guarded against running backend and vaulted DB/Chroma to timestamped backups. |

### Phase B – Core data model & CRUD

| Test ID   | Description                         | Result | Notes / Errors |
|-----------|-------------------------------------|--------|----------------|
| B-Proj-01 | Project CRUD                        | Pass   | Created “QA Regression Run 2025‑12‑02 (Reset)” (`id=4`) and verified via `GET /projects`. |
| B-Conv-01 | Conversation create/rename          | Pass   | `/chat` created conversation `id=5`; renamed to “QA Reset Conversation”. |
| B-Chat-01 | Chat pipeline basics                | Pass   | `GET /conversations/5/messages` and `/usage` show the expected records (tokens + cost). |
| B-Tasks-01| Tasks CRUD + auto-extraction        | Pass   | Added manual task (`id=18`), toggled status, and saw assistant-generated TODOs. |
| B-Tasks-02| Autonomous TODO maintenance loop    | Pass   | Conversation 22 auto-added tasks, then auto-completed “Wire message embeddings” / “Add audit logging” when completion statements appeared; follow-up “Implement audit logging” inserted automatically and ordering reflected most-recent updates. |
| B-Docs-01 | Docs CRUD + ingestion               | Pass   | Ingested text doc (“QA Reset Doc”) plus `scratch/test-notes.txt`; verified via `GET /projects/4/docs`. |

#### Chat modes & model routing

| Test ID   | Mode     | Result | Notes / Evidence |
|-----------|----------|--------|------------------|
| B-Mode-01 | auto     | Pass   | Lightweight ping routed to `gpt-5-nano` (fast tier). |
| B-Mode-01 | fast     | Pass   | Used `gpt-5-nano` per env override. |
| B-Mode-01 | deep     | Pass   | Used `gpt-5-pro`. |
| B-Mode-01 | budget   | Pass   | Used `gpt-4.1-nano`. |
| B-Mode-01 | research | Pass   | First attempted `o3-deep-research`, simulated failure triggered fallback to `gpt-5.1` with 200 OK. |
| B-Mode-01 | code     | Pass   | Used `gpt-5.1-codex`. |

#### Auto mode adaptive selection

| Test ID   | Scenario                | Result | Notes / Evidence |
|-----------|-------------------------|--------|------------------|
| B-Mode-02 | Auto (coding request)   | Pass   | Code-fenced snippet routed to `gpt-5.1-codex`. |
| B-Mode-02 | Auto (research request) | Pass   | Long research prompt routed to `o3-deep-research`. |
| B-Mode-02 | Auto (lightweight ask)  | Pass   | “Ping?” prompt routed to `gpt-5-nano`. |
| B-Mode-02 | Auto (deep planning)    | Pass   | Multi-paragraph roadmap prompt routed to `gpt-5-pro`. |

### Phase C – Retrieval & vector store

| Test ID       | Description               | Result | Notes / Errors |
|---------------|---------------------------|--------|----------------|
| C-MsgSearch-01| Message search            | Pass   | Unique token (`SNOWCRASH-XYZ`) inserted via `/chat`; `/search/messages` returned user + assistant hits with correct metadata. |
| C-DocSearch-01| Document search           | Pass   | Querying “DOC_RESET_TOKEN” returned the expected chunk. |
| C-MemorySearch-01 | Memory item retrieval | Pass   | Pinned memory items (“MEM_RESET_ALPHA”) surfaced inside chat replies, confirming prompt injection. |

### Phase D – Filesystem & AI file edits

| Test ID   | Description                     | Result | Notes / Errors |
|-----------|---------------------------------|--------|----------------|
| D-FS-01   | List and read files             | Pass   | `/fs/list?scratch` and `/fs/read?scratch/test-notes.txt` matched disk. |
| D-FS-02   | Write file and verify           | Pass   | Appended `QA_RESET_TEMP`, confirmed via `/fs/read`, then restored the file. |
| D-AIEdit-01| AI file edit with diff/preview | Pass   | `/fs/ai_edit` previewed + applied “AI_EDIT_RESET”; file reverted manually afterwards. |

### Phase E – Terminal integration

| Test ID   | Description                       | Result | Notes / Errors |
|-----------|-----------------------------------|--------|----------------|
| E-Term-01 | AI terminal proposal loop         | Pass   | Assistant proposed `dir`; executed via `/terminal/run` and posted the structured summary back into `/chat`. |
| E-Term-02 | Manual terminal runner + history  | Pass   | Additional manual runs (`dir`, `dir nonexistent_folder`) returned correct exit codes and stderr. |

### Phase F – Instructions, decisions, folders, memory

| Test ID   | Description                          | Result | Notes / Errors |
|-----------|--------------------------------------|--------|----------------|
| F-Inst-01 | Instructions CRUD + prompt injection | Pass   | Saved “QA_RESET_RULE: include QA_RESET_TAG…”; replies now end with `QA_RESET_TAG`. |
| F-Dec-01  | Decision log CRUD                    | Pass   | Added “QA Reset Decision”; visible via `GET /projects/4/decisions`. |
| F-Fold-01 | Conversation folders (CRUD + usage)  | Pass   | Created `QA Reset Folder`, moved conversation 5 into it, verified folder listing. |
| F-Mem-01  | Memory items CRUD + retrieval        | Pass   | Created pinned/unpinned memory items (`MEM_RESET_ALPHA`, `MEM_RESET_BETA`) and confirmed they appear in `/memory` and chat replies. |

### Phase G – Right-column UI 2.0 regression

| Test ID   | Tab      | Description                          | Result | Notes / Errors |
|-----------|----------|--------------------------------------|--------|----------------|
| G-Tasks-01| Tasks    | Playwright regression                | Pass   | |
| G-Docs-01 | Docs     | Playwright regression                | Pass   | |
| G-Files-01| Files    | Playwright regression                | Pass   | |
| G-Search-01| Search  | Playwright regression                | Pass   | |
| G-Term-01 | Terminal | Playwright regression                | Pass   | |
| G-Usage-01| Usage    | Playwright regression                | Pass   | |
| G-Notes-01| Notes    | Playwright regression                | Pass   | |
| G-Mem-01  | Memory   | Playwright regression                | Pass   | |

`npx playwright test` (tests/right-column.spec.ts) passed on Chromium; the script clicks each tab and verifies the `.right-tab` button becomes active.

### Phase H – Error handling & edge cases

| Test ID   | Description                        | Result | Notes / Errors |
|-----------|------------------------------------|--------|----------------|
| H-FS-01   | Invalid file path (`..`, absolute) | Pass   | `/fs/list?subpath=..\etc` returned 400 with `detail: "Path may not contain '..' segments."` |
| H-Term-01 | Terminal timeout / invalid command | Pass   | `dir nonexistent_folder` returned exit code `1` with stderr `File Not Found`. |
| H-Chat-01 | Invalid conversation_id/project_id | Pass   | `GET /conversations/9999/messages` returned 404 `Conversation not found.` |

### Phase I – Performance & durability spot checks

| Test ID   | Description                                   | Result | Notes / Errors |
|-----------|-----------------------------------------------|--------|----------------|
| I-Perf-01 | Many conversations/messages                   | Not Run | Requires dedicated data generators. |
| I-Perf-02 | Many tasks/docs/memory items                  | Not Run | Same as above. |
| I-Perf-03 | Repeated AI edits & terminal runs, general UX | Not Run | Deferred to a future QA pass. |

## 4. Issues & follow-up plan

| ID        | Related Test(s) | Description of Issue                                                                 | Severity | Proposed Fix / Next Step |
|-----------|-----------------|---------------------------------------------------------------------------------------|----------|--------------------------|
| ISSUE-001 | C-MsgSearch-01  | Fixed. `add_message_embedding` skips `folder_id=None`, so Chroma accepts inserts and `/search/messages` returns hits (SNOWCRASH token). | Resolved | No further action required. |
| ISSUE-002 | A-Env-03        | Fixed. Guarded reset helper (`tools/reset_qa_env.py`) automates DB/Chroma resets with port-safety checks. | Resolved | Documented in Progress log. |
| ISSUE-003 | B-Mode-01 (research) | Fixed. Research mode now falls back to available models when `o3-deep-research` is unavailable, preventing HTTP 500s. | Resolved | Keep model env overrides up to date. |
| ISSUE-004 | B-Mode-02       | Fixed. Auto mode heuristics now route to fast/code/research/deep tiers based on prompt characteristics, with logging for auditability. | Resolved | Consider telemetry in future. |
| ISSUE-005 | B-Tasks-02      | Fixed. Auto-maintainer dedupes, auto-completes, and reorders tasks when completions are mentioned. | Resolved | Monitor accuracy over time. |

All QA artifacts (project 6, associated conversations/tasks/docs/memory/etc.) remain in `C:\InfinityWindow_QA`. Playwright + `make ci` logs come from the same QA environment. Use this report as the baseline for the next regression run.

## 5. Additional QA validation – Search / Usage / Notes focus (2025‑12‑02 PM)

- **Commands**: `python -X utf8 -m qa.run_smoke`, `npx playwright test tests/right-column.spec.ts tests/files-tab.spec.ts tests/notes-memory.spec.ts`
- **Backend / Frontend**: `uvicorn app.api.main:app --host 127.0.0.1 --port 8000`, Vite dev server on `127.0.0.1:5174`
- **Goal**: Re-run the high-impact rows that cover auto-mode routing, autonomous TODO maintenance, Search/Usage UX, and Notes/Decisions automation after syncing the QA repo with `C:\InfinityWindow`.

| Test ID        | Description / Focus                                         | Result | Notes / Evidence |
|----------------|-------------------------------------------------------------|--------|------------------|
| B-Mode-02      | Auto-mode multi-scenario routing                            | Pass   | qa.run_smoke captured `auto-fast`, `auto-code`, `auto-research`, `auto-deep` → routed to the expected models; “roadmap” prompt now chooses `gpt-5-pro`. |
| B-Tasks-02     | Autonomous TODO maintenance                                 | Pass   | Probe confirmed ≥3 tasks added, “message embeddings” / “docs polish” auto-closed, while “audit logging” remained open (new completion parsing skips “still pending”). |
| C-Search-02    | Search tab filters, grouping, open-in actions               | Pass   | Manual UI check (project seeded via helpers) verified conversation/document filters, grouped hit headers, and “open conversation/View in docs” buttons. |
| D-Usage-01     | Usage API sanity (per-conversation breakdown)               | Pass   | `/conversations/{id}/usage` returns aggregated token + model entries; verified Usage tab refresh picks them up. |
| D-Usage-02     | Usage tab dashboard + telemetry block                       | Pass   | Model breakdown + Routing & tasks telemetry refresh/reset buttons function; counters increment when smoke probes run. |
| G-Notes-02     | Notes tab pinned note + instructions diff                   | Pass   | Playwright (notes-memory.spec.ts) ensures pinned textarea + diff toggle reflect seeded instructions. |
| G-Dec-02       | Decision filters, metadata editing                          | Pass   | Same Playwright flow validates category/tag filters and status dropdown interactions. |
| G-Dec-03       | Decision automation & draft review                          | Pass   | qa.run_smoke auto-detects decisions from assistant chatter; drafts highlighted and can be confirmed/dismissed. |
| G-Notes-01/Memory| Right-column regression                                   | Pass   | `tests/right-column.spec.ts` + `tests/notes-memory.spec.ts` cover rendering, tab activation, and memory list visibility. |

**Issues observed**: none. Auto-mode routing and autonomous task handling both passed without regressions after the latest fixes.

