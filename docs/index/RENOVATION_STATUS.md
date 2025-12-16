---
doc_id: DOC-INDEX-005
title: Documentation renovation status
status: active
last_verified: 2025-12-16
applies_to: ca88fca949670ef863e64f8061829df67a584dde
scope: >
  Living tracker for renovation progress, completed work, and the prioritized
  backlog of remaining bundles.
canonical: yes
related_docs:
  - docs/index/INDEX.md
  - docs/index/RENOVATION_PLAN.md
  - docs/index/docs-map.yaml
related_code: []
related_tests: []
---

## Status snapshot

| Area | State | Notes |
| --- | --- | --- |
| IA foundation | ✅ Complete | Wave-1 directories/files created with metadata + docs-map entries. |
| Governance docs | ✅ Complete | Glossary, plan, status, roadmap, risks, ADR template, archive policy, and governance stubs in place. |
| Core libraries | ✅ Complete | `docs/ProjectPlans/INDEX.md` + `docs/TODO_CHECKLIST/INDEX.md` promoted to active, indexed libraries. |
| Legacy bundle audit | ✅ Complete | All requested bundles linked + marked deprecated. |
| Automation | ⏳ Pending Wave-2 | `scripts/verify_plan_sync.py` still manual; automation hardening scheduled for Wave-2. |
| Bundle migrations | ⏳ Pending Wave-3 | Legacy bundles remain read-only until targeted micro-batches rewrite them. |

## Completed in Wave-1

- Created `docs/index/INDEX.md` plus supporting governance docs.
- Added machine-readable `docs/index/docs-map.yaml`.
- Created roadmap/backlog, risk register, ADR template, archive policy, and `docs/index/PROJECT_CONTEXT.md`.
- Added README/INDEX entrypoints for `alignment`, `alignment_002`, `design-references`, and promoted `ProjectPlans` + `TODO_CHECKLIST` to core navigation.
- Added governance stubs: `FRONTMATTER_SCHEMA`, `CITATION_STANDARD`, `CHUNKING_STANDARD`, `LARGE_FILE_POLICY`, `SEVERITY_TRIAGE`.
- Updated `docs/README.md` banner and legacy links.

## Backlog (micro-batch candidates)

| Bundle | Next action | Owner | Status |
| --- | --- | --- | --- |
| `docs/tasks` | Migrate remaining TASKS_CHECKLIST + automation docs into new `guides/` area. | TBD | Not started |
| `docs/alignment` | Verify evidence freshness, consolidate into Alignment overview doc. | TBD | Not started |
| `docs/alignment_002` | Fold alignment evidence into governance once validated. | TBD | Not started |
| `docs/ProjectPlans` | Convert `.txt` plans into structured roadmap/backlog entries. | TBD | Not started |
| `docs/TODO_CHECKLIST` | Keep chunk manifest synchronized with ProjectPlans coverage + add metadata header. | TBD | Not started |
| `docs/design-references` | Decide which assets stay vs. move to `_archive`. | TBD | Not started |

## Legacy bundle audit

| Bundle | Entry doc | Status | Notes |
| --- | --- | --- | --- |
| Legacy root index | `docs/README.md` | Deprecated | Banner directs readers to `docs/index/INDEX.md`. |
| Tasks bundle | `docs/tasks/README.md` | Deprecated | Contains actionable checklists until re-written. |
| Alignment v1 | `docs/alignment/README.md` | Deprecated | Summarizes evidence + links to alignment subfiles. |
| Alignment v2 | `docs/alignment_002/README.md` | Deprecated | Summarizes matrix + evidence; waiting for validation wave. |
| Design references | `docs/design-references/README.md` | Deprecated | Captures inspiration assets; targeted for `_archive`. |

`docs/ProjectPlans/INDEX.md` and `docs/TODO_CHECKLIST/INDEX.md` graduated from this table because they are now treated as active core libraries (see `docs/index/INDEX.md#core-libraries`).

