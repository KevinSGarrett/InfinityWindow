---
doc_id: DOC-INDEX-001
title: InfinityWindow Project Library
status: active
last_verified: 2025-12-16
applies_to: ca88fca949670ef863e64f8061829df67a584dde
scope: >
  Canonical human-first entry point that explains how the docs library is
  organized, how to navigate to governance material, and where legacy bundles
  still live during Wave-1 of the renovation.
canonical: yes
related_docs:
  - docs/index/docs-map.yaml
  - docs/index/RENOVATION_PLAN.md
  - docs/index/RENOVATION_STATUS.md
related_code: []
related_tests: []
---

## At a glance

- The `docs/index` folder now contains all navigation scaffolding (human-first and machine-readable) required by Wave-1.
- Each governance document includes metadata so agents can cite scope, verification date, and related assets without scanning entire files.
- Legacy bundles remain read-only but have explicit entrypoints so we avoid orphaned knowledge until the migration finishes.

## Navigation hubs

### Index & governance
- `docs/index/GLOSSARY.md` — shared vocabulary and abbreviations.
- `docs/index/RENOVATION_PLAN.md` — multi-wave roadmap + ownership and stop conditions.
- `docs/index/RENOVATION_STATUS.md` — progress tracker + backlog of remaining doc migrations.
- `docs/index/docs-map.yaml` — machine-readable inventory for agents/tooling.
- `docs/index/PROJECT_CONTEXT.md` — canonical repo paths, host machine assumptions, and GitHub origin link.

### Core libraries
- [docs/ProjectPlans/INDEX.md](../ProjectPlans/INDEX.md) — curated index across the imported project plan bundles.
- [docs/TODO_CHECKLIST/INDEX.md](../TODO_CHECKLIST/INDEX.md) — canonical chunked TODO master checklist.

### Delivery & prioritization
- `docs/roadmap/ROADMAP.md` — time-sequenced roadmap for experience, docs, and automation work.
- `docs/roadmap/BACKLOG.md` — groomed backlog that feeds future micro-batches.

### Risk, decisions, and archive policy
- `docs/risks/RISK_REGISTER.md` — active risks plus mitigations/owners.
- `docs/risks/KNOWN_ISSUES.md` — issues accepted for now (with severity + follow-up plan).
- `docs/decisions/README.md` & `docs/decisions/ADR-0001-template.md` — process for documenting architectural/process decisions.
- `docs/_archive/README.md` — deprecation and archiving guardrails.

## Legacy library (pre-renovation)

Legacy content is still authoritative for historical behavior but is frozen. Use these bundle entrypoints to locate older material until micro-batches modernize each area:

- [docs/README.md](../README.md) — prior monolithic index and wayfinding notes.
- [docs/tasks/README.md](../tasks/README.md) — legacy tasks program.
- [docs/alignment/README.md](../alignment/README.md) — Alignment 001 bundle.
- [docs/alignment_002/README.md](../alignment_002/README.md) — Alignment 002 bundle.
- [docs/design-references/README.md](../design-references/README.md) — Image and reference archive.

Each bundle is marked `status: deprecated` in `docs/index/docs-map.yaml` and `canonical: no`, so agents know to treat them as legacy material.

## Maintenance contract

1. No document becomes canonical without metadata and an entry in `docs/index/docs-map.yaml`.
2. Any new bundle must also link back here (and from `docs/index/RENOVATION_STATUS.md`) to avoid orphans.
3. Governance changes require:
   - Updating relevant doc(s) + metadata
   - Updating `docs-map.yaml`
   - Adding evidence to `RENOVATION_STATUS.md`

## Update checklist

1. Edit the relevant doc(s) with metadata + references.
2. Update this index if navigation changes.
3. Update `docs/index/docs-map.yaml`.
4. Run `python scripts/verify_plan_sync.py`, `make ci`, `make smoke`, `npm run lint --prefix frontend`, `npm run build --prefix frontend`, and `npm run test:e2e --prefix frontend`.
5. Capture outputs + touched files in the agent summary per AGENT_GUIDE requirements.

