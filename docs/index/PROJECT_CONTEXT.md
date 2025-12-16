---
doc_id: DOC-INDEX-006
title: Project context & canonical paths
status: active
last_verified: 2025-12-16
applies_to: ca88fca949670ef863e64f8061829df67a584dde
scope: >
  Defines the canonical working copy, GitHub origin, and high-signal document
  entrypoints that every InfinityWindow agent must load before touching code or
  documentation.
canonical: yes
related_docs:
  - docs/index/INDEX.md
  - docs/agent/AGENT_GUIDE.md
  - docs/agent/GIT_POLICY.md
  - docs/index/docs-map.yaml
related_code: []
related_tests: []
---

## Canonical repo locations

- **Working copy path**: `C:\InfinityWindow_Recovery`
- **Remote origin**: `https://github.com/KevinSGarrett/InfinityWindow.git`
- **Default branch contract**: work happens on run-specific branches; merge down to `main` only after Wave-1 gates pass (per `docs/agent/GIT_POLICY.md`).

> Agents must confirm `(Get-Location).Path` each run and cite the active branch/commit in their summary.

## High-signal navigation chain

1. `docs/index/INDEX.md` — human-first index.  
2. `docs/index/docs-map.yaml` — machine inventory (kept in lockstep with this file).  
3. `docs/index/RENOVATION_PLAN.md` + `docs/index/RENOVATION_STATUS.md` — scope + backlog.  
4. `docs/agent/AGENT_GUIDE.md` — governance kernel and escalation gates.

Use this sequence before executing any searches (R7).

## Core knowledge libraries

- `docs/ProjectPlans/INDEX.md` — curated index across the imported plan bundles (UPIW series).  
- `docs/TODO_CHECKLIST/INDEX.md` — canonical chunked TODO ledger that mirrors ProjectPlans coverage tags.

Treat both as **active** libraries: cite them when referencing roadmap-derived scope instead of defunct `docs/todo`.

## Evidence + automation hooks

- `python scripts/verify_plan_sync.py` — verifies docs-map alignment.  
- `make ci`, `make smoke`, `npm run lint --prefix frontend`, `npm run build --prefix frontend`, `npm run test:e2e --prefix frontend` — required for every run.

Log command output excerpts + file deltas in the agent summary (see `docs/agent/AGENT_GUIDE.md`).

