---
doc_id: AGENT-GOV-001
title: InfinityWindow Agent Governance Guide
status: active
last_verified: 2025-12-16
applies_to: ca88fca949670ef863e64f8061829df67a584dde
scope: Operating rules, navigation gates, and stop conditions for all InfinityWindow agents.
canonical: yes
related_docs:
  - docs/agent/PROMPT_TEMPLATES.md
  - docs/agent/DONE_DEFINITION.md
  - docs/agent/TEST_POLICY.md
  - docs/agent/GIT_POLICY.md
  - docs/agent/DOC_STANDARDS.md
  - docs/agent/CODE_SIZE_POLICY.md
related_code: []
related_tests: []
---

# Agent Governance Guide

Use this document as the navigation hub and behavioral contract for every Cursor agent operating inside `C:\InfinityWindow_Recovery`. It summarizes the mandatory rules (R1–R8), evidence expectations, and escalation gates the PM defined in `InitialPrompt.md`.

## Start Here Navigation Path

Follow this “Start here” chain before touching anything:

1. `docs/index/PROJECT_CONTEXT.md` – canonical repo paths + GitHub origin.
2. `docs/index/INDEX.md` – repo-wide doc index.
3. `docs/index/SYSTEM_MAP.md` – code + doc crosswalk.
4. `docs/roadmap/ROADMAP.md` – future scope + planned items.

Agents must load all three before additional searches so that context stays token-efficient and aligned with current plans.

## Token-Efficiency Navigation Protocol (R7)

- Never run blind repo-wide scans; start with the index and system map above.
- From those hubs, follow links to the smallest relevant doc or code path.
- Prefer `rg`/`codebase_search` scoped to specific folders.
- Record every navigation hop in the run summary so reviewers can trace context.

## Core Governance Rules (R1–R8)

1. **R1 – Evidence-based completion**: No task is “done” unless commands, outputs, and artifact paths are captured in the summary. Quote outputs or link logs directly.
2. **R2 – Definition of Done**: Follow `docs/agent/DONE_DEFINITION.md` and refuse completion if any gate is unmet.
3. **R3 – Documentation integrity**: Any behavioral change requires synchronized updates to the relevant docs plus index entries per `docs/agent/DOC_STANDARDS.md`.
4. **R4 – No orphan docs**: Every file must be reachable from `docs/index/INDEX.md` and the machine index. Flag any orphan immediately.
5. **R5 – No duplicate truths**: Declare one canonical doc per topic; cross-link or deprecate everything else.
6. **R6 – No destructive commands without explicit PM approval**: See gate below for the forbidden list.
7. **R7 – Token efficiency**: Already covered above; navigation must be deliberate.
8. **R8 – Future alignment policy**: Only describe planned behavior if it exists in `docs/roadmap/*`, is labeled Planned/Not Yet Implemented, and includes metadata (`last_verified`, `applies_to`).

## “No Destructive Commands” Gate (R6)

The following commands are blocked unless the PM signs off **and** you create a recovery artifact first: `git clean -fdx`, `git reset --hard`, `git checkout .`, `git restore .` (repo-wide), `rm -rf` on repo paths, DB/chroma wipes in the primary working copy. Prefer scripted helpers scoped to QA mirrors (`tools/reset_qa_env.py`) when cleanup is required.

## Evidence & Done Enforcement

- Always cite the commands that produced evidence, including working directory and environment variables.
- Call out untested surfaces explicitly with rationale.
- Update documentation, indexes, and cross-links in the same run to avoid drift.
- Refuse completion if lint/tests/docs/index updates are missing; escalate instead.

## Mandatory Agent Summary Template

Copy this verbatim into every run summary (R1, R2, R7):

1. Goal / Task ID  
2. What changed (high level)  
3. Files changed (paths)  
4. Key decisions + rationale  
5. Commands run + results (paste outputs or artifact paths)  
6. Test evidence + artifacts (reports/logs/screenshots)  
7. Docs updated (paths + sections + index entries)  
8. Cross-links/refs updated (what links were added/fixed)  
9. Known issues / follow-ups (severity)  
10. Risk assessment (what could break + mitigations)  

## Stop Conditions & Escalation Gates

Escalate to the PM (with 2–3 options and a recommendation) when:

- Ambiguity impacts architecture, data model, or safety.
- A change triggers large-scale refactors or DB migrations.
- Security/auth/payment behavior is unclear.
- Tests fail in unexpected or widespread ways.
- The required edits exceed agreed LOC/file thresholds.
- Repo rules conflict with current reality (document and propose compatibility clause).

## Execution Loop Reminder

1. PM scans repo/docs and issues the next wave plan plus prompts.
2. Agents execute in the assigned order, following file ownership boundaries.
3. Agents summarize work using the template above, including evidence for every command/test/doc update.
4. PM verifies evidence, index health, and doc cross-links before starting the next cycle.

Stay inside this loop, observe every gate, and keep all work documented for future agents.

