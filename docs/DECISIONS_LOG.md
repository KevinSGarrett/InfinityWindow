# InfinityWindow Global Decisions Log

This document records **global, cross-project decisions** about the InfinityWindow system itself: architecture choices, conventions, and process agreements.

Per‑project decisions (e.g., “Why did we choose X for Project Y?”) live in the database and are surfaced in the Notes tab; this file is for repo‑level decisions that affect all projects and contributors.

---

## 1. How to use this document

- When you make a **non-trivial, repo-wide decision**, add an entry here.
- Keep entries short but specific:
  - What did we decide?
  - Why did we pick this approach?
  - What alternatives did we reject?
  - What is the impact for future work?
- Link to:
  - Relevant PRs/commits.
  - Sections in `docs/PROGRESS.md`, `SYSTEM_OVERVIEW.md`, or `SYSTEM_MATRIX.md`.

A simple pattern for entries:

```markdown
### YYYY-MM-DD – Decision title

- **Context**: Short background.
- **Decision**: What we chose.
- **Rationale**: Why we chose it over alternatives.
- **Implications**: How this affects future work and what to watch out for.
```

---

## 2. Recorded decisions

### 2025-12-02 – Use QA copy + smoke probes for regression protection

- **Context**: The main project needed a safer way to test features and bugfixes without risking the primary working environment.
- **Decision**: Maintain a separate QA copy at `C:\InfinityWindow_QA` with:
  - A `Makefile` (`make ci`) for backend tests + frontend build.
  - A small `qa/` smoke suite for message search, tasks auto-loop, and mode routing.
  - A guarded reset helper (`tools/reset_qa_env.py`) to safely reset DB + Chroma.
- **Rationale**: This enables repeatable, automated checks on a clean environment while keeping day‑to‑day work in `C:\InfinityWindow_Recovery` stable.
- **Implications**: Any future changes to DB paths, Chroma configuration, or test layout must keep the QA copy and smoke suite up to date.

### 2025-12-02 – Make docs the primary source of truth for behavior and QA

- **Context**: The project had scattered notes and partial docs, making it hard to rehydrate context or trust behavior descriptions.
- **Decision**: Treat `docs/` as the **authoritative description** of how InfinityWindow works and is tested:
  - `SYSTEM_OVERVIEW.md` describes current behavior (non-aspirational).
  - `SYSTEM_MATRIX.md` maps features to code and endpoints.
  - `TEST_PLAN.md` / `TEST_REPORT_*.md` define and record QA.
  - `PROGRESS.md` / `TODO_CHECKLIST.md` define roadmap and status.
- **Rationale**: With AI and humans both working in the repo, a consistent, well-structured docs set is critical for reliable behavior and future evolution.
- **Implications**: Any substantial behavior or feature change should be mirrored in the docs library; leaving docs stale is considered a regression.

### 2025-12-03 – Adopt Autopilot manager/worker architecture as design direction

- **Context**: The project needs a path from “chat + tasks + files + terminal” to a full project execution engine that can handle large blueprints and long-running work safely.
- **Decision**: Standardize on the Autopilot design captured in `Updated_Project_Plans/Updated_Project_Plan_2*.txt` and surfaced in `docs/AUTOPILOT_PLAN.md`, `AUTOPILOT_LEARNING.md`, `AUTOPILOT_LIMITATIONS.md`, `AUTOPILOT_EXAMPLES.md`, and `MODEL_MATRIX.md`. This design defines Blueprint/Plan graphs, ExecutionRuns/Steps, ManagerAgent, workers, and scalable ingestion as the future architecture.
- **Rationale**: Having a single, explicit Autopilot plan avoids ad‑hoc automation experiments and gives both humans and AI a clear target for future work (including safety constraints and model routing).
- **Implications**: Until implemented, these docs remain design‑only; when Autopilot features are added, they must conform to this plan (or the plan must be revised here) and be reflected in `SYSTEM_OVERVIEW.md`, `SYSTEM_MATRIX.md`, `API_REFERENCE.md`, `CONFIG_ENV.md`, and QA docs.

### 2025-12-04 – Standardize core API and UI shapes for v2

- **Context**: Early docs and plans referenced multiple variants of project root fields, filesystem routes, usage endpoints, and right-column layouts, making it easy for future work to drift or reintroduce inconsistencies.
- **Decision**:
  - Use `local_root_path` as the canonical project root field in models, APIs, and docs.
  - Treat `/projects/{project_id}/fs/list|read|write|ai_edit` as the filesystem API surface.
  - Treat `GET /conversations/{conversation_id}/usage` as the canonical usage endpoint for the Usage tab.
  - Treat `/projects/{project_id}/memory` + `/memory_items/{memory_id}` as the memory API.
  - Treat the eight-tab right column (Tasks, Docs, Files, Search, Terminal, Usage, Notes, Memory) as the stable layout.
- **Rationale**: A single, consistent API and UI contract reduces friction for contributors and AI agents, and it makes PROGRESS/TODO/QA docs much easier to keep in sync with the code.
- **Implications**: Future changes to these surfaces must update `SYSTEM_OVERVIEW.md`, `SYSTEM_MATRIX.md`, `API_REFERENCE.md`, `USER_MANUAL.md`, and `PROGRESS.md` together; introducing alternate spellings or duplicate endpoints is considered a regression unless explicitly justified here.

### 2025-12-04 – Batch repo ingestion via jobs + hashed state

- **Context**: `POST /github/ingest_local_repo` tried to embed every file in one massive call, regularly exceeding OpenAI’s token caps and offering no progress/error visibility in the UI.
- **Decision**:
  - Move ingestion to `POST /projects/{project_id}/ingestion_jobs` + `GET /projects/{project_id}/ingestion_jobs/{job_id}`.
  - Implement `embed_texts_batched` with configurable `MAX_EMBED_TOKENS_PER_BATCH` and `MAX_EMBED_ITEMS_PER_BATCH`.
  - Persist `IngestionJob` + `FileIngestionState` so we can show progress, capture errors, and skip unchanged files via SHA-256 digests.
- **Rationale**: Batched embeddings keep us under provider limits, and job records make the UX predictable (start → see progress → view errors). Hash-based skipping avoids re-ingesting thousands of files when only a handful changed.
- **Implications**: All future ingestion flows (docs, repos, blueprints) must route through the job API and batching helper; `MAX_EMBED_*` defaults must stay documented in `CONFIG_ENV.md`. Blueprint/Autopilot ingestion (Phase T) will build on the same tables and endpoints rather than inventing a parallel system.

### 2025-12-08 – Standardize local backend port and telemetry reset behavior

- **Context**: Playwright/UI/API tests and docs had drifted between ports 8000 and 8001; telemetry reset endpoint previously echoed pre-reset counters.
- **Decision**:
  - Standardize backend to `http://127.0.0.1:8000` for dev/QA, reflected in Playwright helpers/config, docs, and API references.
  - Make `/debug/telemetry?reset=true` return cleared counters immediately; ensure Usage tab shows confidence buckets and recent task actions based on that state.
- **Rationale**: Eliminates flaky UI/API tests from port mismatches and provides reliable telemetry resets for repeated QA runs.
- **Implications**: Future config changes must update `CONFIG_ENV.md`, Playwright config, `API_REFERENCE_UPDATED.md`, and `PROGRESS.md`; telemetry contract (reset → zeroed response) is now considered stable.

Add new decisions below this line as the system evolves.