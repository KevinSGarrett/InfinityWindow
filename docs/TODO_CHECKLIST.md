# InfinityWindow TODO / Roadmap Checklist (Recovery Baseline)

This checklist matches the recovered `C:\InfinityWindow_Recovery` repo. It is aligned with `docs/PROGRESS.md` and `docs/REQUIREMENTS_CRM.md`. Legend: `[x]` done, `[~]` partial/validate, `[ ]` not started.

---

## 0) Recovery & repo hygiene
- [x] BE-RECOVERY-001: Restore code and DB from `C:\InfinityWindow_Backup\019` into `C:\InfinityWindow_Recovery`; rebuild SQLite/Chroma and health-check `/health` and `/projects`.
- [x] FE-RECOVERY-001: Frontend/tests pointed to `http://127.0.0.1:8000`; removed hard-coded legacy paths; Playwright helpers aligned.
- [x] DOC-RECOVERY-001: Update docs (workflow, CRM, TODO, alignment) to mark `C:\InfinityWindow_Recovery` as the only writable repo; quarantine `C:\InfinityWindow`; keep backup read-only.
- [x] Branch hygiene: main kept clean; feature branches only; no mega-merge/conflict cleanups by agents.

---

## 1) Shipped in the recovery build (re-validated)
- [x] Core workspace: projects, conversations, chat modes, search over messages/docs/memory.
- [x] Tasks: CRUD + auto add/complete/dedupe with telemetry; tasks ordered (open first, most recent first).
- [x] Docs & ingestion: text + repo ingestion jobs with progress/history/cancel; hash skip; `embed_texts_batched` caps; search works across docs/messages/memory.
- [x] Files & terminal safety: scoped fs list/read/write + AI edits under project root; terminal run scoped with `check=True`; `local_root_path` validation enforced.
- [x] Notes/Decisions/Memory: instructions + pinned note, decision log with follow-ups, memory items + retrieval, “Remember this” button.
- [x] Usage & telemetry: per-conversation usage records; task automation telemetry with basic charts/filters/JSON export; reset via `/debug/telemetry`.
- [x] UI workbench: eight tabs (Tasks, Docs, Files, Search, Terminal, Usage, Notes, Memory) with refresh-all + keyboard shortcuts.
- [x] QA tooling: smoke probes (`qa/run_smoke.py`), ingestion probes, Playwright smokes, guarded QA reset script.

---

## 2) Partial / needs validation after recovery
- [~] Task automation tuning: priority/dependency heuristics and low-confidence approval UX need refinement and fresh QA after recovery.
- [~] Auto-mode routing: heuristics + telemetry exist; revisit with real data; ensure model override UI stays wired.
- [~] Usage/telemetry dashboard: Phase 1/2 (charts/filters/exports) present; long-window persistence/analytics still future.
- [~] QA/CI reruns on recovery baseline: run `python -m pytest qa/tests_api -q --disable-warnings` and `LLM_MODE=stub VECTORSTORE_MODE=stub make ci` to reconfirm green.

---

## 3) Future / design-only (not in this repo)
- [ ] Autopilot/Blueprint/Manager/ExecutionRuns; autonomy modes and Runs UI.
- [ ] Blueprint ingestion/summaries and Plan tree in Tasks tab.
- [ ] Export/import/archive flows for projects.
- [ ] Long-horizon telemetry/analytics storage and advanced dashboards.
- [ ] Rich diff UX (multi-file/hunk apply) and multi-user/roles support.

---

## 4) Documentation & alignment
- [x] `docs/REQUIREMENTS_CRM.md` added and aligned to recovery build.
- [x] `docs/ALIGNMENT_OVERVIEW.md` updated to point at CRM/TODO/PROGRESS and mark design-only items.
- [x] `docs/PROGRESS.md` carries “Recovery 2025-12-10” note and current status.
- [x] `docs/USER_MANUAL.md` scoped to shipped features; Autopilot/Blueprint clearly labeled design-only.

Keep TODO and PROGRESS in lockstep; downgrade any item to `[ ]` if code/tests in this repo do not prove it.
