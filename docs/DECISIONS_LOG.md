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
- **Rationale**: This enables repeatable, automated checks on a clean environment while keeping day‑to‑day work in `C:\InfinityWindow` stable.
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

Add new decisions below this line as the system evolves.***

