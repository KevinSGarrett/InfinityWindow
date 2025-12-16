---
doc_id: DOC-INDEX-004
title: Documentation renovation plan
status: active
last_verified: 2025-12-16
applies_to: ca88fca949670ef863e64f8061829df67a584dde
scope: >
  Multi-wave plan for rebuilding the InfinityWindow documentation stack into an
  agent-first project library with enforced governance.
canonical: yes
related_docs:
  - docs/index/INDEX.md
  - docs/index/RENOVATION_STATUS.md
  - docs/agent/AGENT_GUIDE.md
related_code: []
related_tests: []
---

## Overview

The renovation runs in deliberately small waves so we can prove evidence, keep cross-links synchronized, and avoid token blowups. Each wave produces auditable artifacts (docs, indexes, automation updates) and includes explicit stop conditions that require PM review.

## Waves

### Wave 1 – IA foundation (current)
- **Objective**: Stand up the new `/docs` information architecture, governance docs, and machine-readable indexes while cordoning legacy bundles.
- **Inputs**: `docs/index/SYSTEM_MAP.md`, `docs/InfinityWindow_ui_ux_plans_001.txt`, previous doc folders.
- **Deliverables**: `docs/index/INDEX.md`, `docs/index/docs-map.yaml`, glossary, renovation plan/status, roadmap+backlog, risk register, ADR hub, archive policy, `docs/index/PROJECT_CONTEXT.md`, and governance stubs (`FRONTMATTER_SCHEMA.md`, `CITATION_STANDARD.md`, `CHUNKING_STANDARD.md`, `LARGE_FILE_POLICY.md`, `SEVERITY_TRIAGE.md`) plus legacy bundle entrypoints.
- **Acceptance criteria**:
  1. All new docs include metadata and appear in `docs-map.yaml`.
  2. `docs/ProjectPlans/INDEX.md` and `docs/TODO_CHECKLIST/INDEX.md` are elevated to active core libraries (not legacy).
  3. Legacy bundles linked under "Legacy library" with `canonical: no`.
  4. `python scripts/verify_plan_sync.py`, `make ci`, `make smoke`, `npm run lint --prefix frontend`, `npm run build --prefix frontend`, and `npm run test:e2e --prefix frontend` all pass.
- **Risks + mitigations**:
  - *Risk*: Overlooking a legacy directory → orphan. *Mitigation*: Require bundle checklist in `RENOVATION_STATUS.md`.
  - *Risk*: CI failures unrelated to docs. *Mitigation*: capture logs + triage options.
- **Stop conditions**: Missing evidence for CI/test runs, ambiguity about legacy bundle ownership, or new governance requirements not captured in AGENT_GUIDE.

### Wave 2 – Governance automation
- **Objective**: Wire scripts/lints that enforce metadata, docs-map sync, and link integrity.
- **Inputs**: Wave-1 docs, `scripts/verify_plan_sync.py`.
- **Deliverables**: CI hook or pre-commit checks, extended verification script, documentation in `docs/agent/DOC_STANDARDS.md`.
- **Acceptance criteria**: Automated failure when metadata/index drift occurs; test coverage for the scripts.
- **Risks**: False positives causing agent slowdown. Mitigate with dry-run mode + documented override instructions.
- **Stop conditions**: Need for repo-wide refactors or script touching security-sensitive areas.

### Wave 3 – Domain migration micro-batches
- **Objective**: Migrate 1–3 legacy bundles at a time into the new structure with evidence-based verification.
- **Inputs**: Legacy bundles (`todo`, `tasks`, `alignment`, `ProjectPlans`, etc.).
- **Deliverables**: Updated canonical docs per bundle, cross-links, retired legacy entries.
- **Acceptance criteria**: Each migration includes code/test references, updated indexes, and removal (or archival) of the old bundle entry.
- **Risks**: Token bloat or knowledge gaps. Mitigate by scoping micro-batches and capturing gaps in backlog.
- **Stop conditions**: Discovery of conflicting truth sources or requirement of code changes outside approved scope.

## Agent assignments per wave

| Wave | Agent A | Agent B | Agent C |
| --- | --- | --- | --- |
| 1 | Create IA folders/files | Run verification scripts/tests | Update docs/index + summary |
| 2 | Implement automation | Write/extend tests for automation | Update standards/index docs |
| 3 | Migrate specific bundles | Validate + run targeted tests | Refresh indexes, archive legacy |

## Micro-batch strategy

1. Track candidate bundles in `docs/index/RENOVATION_STATUS.md`.
2. Limit each micro-batch to ≤3 docs to keep diffs reviewable.
3. Require evidence (code refs + tests) before marking a bundle "canonical".
4. Immediately update `docs-map.yaml` and remove/retire the legacy entry once migrated.
5. Record learned risks or decisions in the relevant governance docs to avoid regressions.

