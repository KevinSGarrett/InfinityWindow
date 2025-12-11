# Branch Catalog (recovery-main-2025-12-10)

- Source: git branch -r plus local recovery branches on 2025-12-10. origin/HEAD points to origin/main.
- No branches were deleted or renamed in this catalog. Any cleanup of legacy branches must be a deliberate GitHub action after human review.

## Active
| Branch | Purpose (inferred) | Safe to ignore now? |
| --- | --- | --- |
| origin/recovery-main-2025-12-10 | Clean recovered baseline from backup 019; current working branch. | No |
| origin/main | Legacy/default main; target for recovery PR once histories are reconciled. | No |
| origin/docs/agent-c-recovery-workflow | Recovery workflow/runbook documentation. | Mostly (keep for reference) |
| origin/safety/local-snapshot-2025-12-10 | Safety snapshot of recovered repo. | Yes (keep as backup) |
| local/feature/agent-b-recovery-frontend | Local UI recovery branch (pre-stash). | No |

## Legacy / pre-recovery
| Branch | Purpose (inferred) | Safe to ignore now? |
| --- | --- | --- |
| origin/docs/agent-b-issues-log-discipline | Docs branch for issues log discipline. | Yes |
| origin/docs/agent-c-crm-and-workflow | Docs for CRM/workflow alignment. | Yes |
| origin/docs/agent-c-crm-matrix-autopilot-docs | Docs for CRM/autopilot matrix. | Yes |
| origin/docs/agent-c-crm-phase1b-and-fs-ux | Docs for CRM phase1b + filesystem UX. | Yes |
| origin/docs/agent-c-crm-retrieval-fs-workflow | Docs for CRM retrieval/fs workflow. | Yes |
| origin/docs/agent-c-retrieval-phase1-alignment | Docs for retrieval phase1 alignment. | Yes |
| origin/docs/agent-c-tasks-dependency-intelligence | Docs for task dependency intelligence. | Yes |
| origin/docs/agent-c-todo-priority-v1 | Docs for todo priority v1. | Yes |
| origin/docs/agent-c-usage-phase3-auto-mode-v2 | Docs for usage phase3 auto-mode v2. | Yes |
| origin/feature/agent-a-auto-mode-v2 | Agent A auto-mode v2 feature. | Yes |
| origin/feature/agent-a-autotodo-v2 | Agent A autotodo v2 feature. | Yes |
| origin/feature/agent-a-debug-docs-status-test | Agent A debug/docs status work. | Yes |
| origin/feature/agent-a-docs-telemetry-guardrails | Docs + telemetry guardrails feature. | Yes |
| origin/feature/agent-a-project-archive | Project archive feature. | Yes |
| origin/feature/agent-a-project-export-import-v1 | Project export/import v1 feature. | Yes |
| origin/feature/agent-a-retrieval-phase1 | Retrieval phase1 feature. | Yes |
| origin/feature/agent-a-retrieval-phase1-tuning2 | Retrieval phase1 tuning work. | Yes |
| origin/feature/agent-a-retrieval-v1-5 | Retrieval v1.5 feature. | Yes |
| origin/feature/agent-a-telemetry-sources | Telemetry sources feature. | Yes |
| origin/feature/agent-a-todo-priority-v1 | Todo priority v1 feature. | Yes |
| origin/feature/agent-b-auto-mode-ui | Agent B auto-mode UI. | Yes |
| origin/feature/agent-b-autotodo-v2 | Agent B autotodo v2. | Yes |
| origin/feature/agent-b-retrieval-context-ui | Agent B retrieval context UI. | Yes |
| origin/feature/agent-b-review-queue-ui | Agent B review queue UI. | Yes |
| origin/feature/agent-b-tasks-priority-ui | Agent B tasks priority UI. | Yes |
| origin/fix/agent-a-ci-docs-guardrails | CI/docs guardrails fix. | Yes |
| origin/fix/agent-a-ci-docs-sync | CI/docs sync fix. | Yes |

## Unknown / needs human review
| Branch | Purpose (inferred) | Safe to ignore now? |
| --- | --- | --- |
| origin/feature/agent-b-notes-usage-polish | Notes/usage polish UI work; confirm status. | Maybe |
| origin/fix/agent-b-fs-files-playwright | Playwright/filesystem fix; check if superseded. | Maybe |
| origin/fix/agent-b-fs-list-ux | Filesystem list UX fix; check before cleanup. | Maybe |
| local/master | Default init branch; no remote tracking. | Yes |
