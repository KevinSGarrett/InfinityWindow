# InfinityWindow – Comprehensive Testing Program
**Date:** 2025-12-05

This package contains a *maximal* testing plan for InfinityWindow (your local AI workbench). It is designed to push toward exhaustive verification across functionality, reliability, security, performance, and UX.

**Contents**
- `01_strategy.md` – Test policy, scope, environments, and coverage philosophy
- `02_traceability_matrix.csv` – Requirements ⇄ Features ⇄ Tests mapping
- `03_test_suites.md` – Overview of all suites and when/how to run them
- `04_test_cases_core.md` – Core CRUD, chat pipeline, tasks, usage
- `05_test_cases_ingestion_search.md` – Ingestion, search, embeddings, docs
- `06_test_cases_files_terminal.md` – Files UI + AI edits, Terminal integration
- `07_test_cases_memory_notes_decisions.md` – Memory, Notes, Decision Log
- `08_test_cases_ui_accessibility.md` – UI flows, keyboarding, a11y
- `09_security_threat_model_and_tests.md` – STRIDE/OWASP and concrete test cases
- `10_performance_and_scale.md` – Targets, workloads, and measurement plans
- `11_resilience_and_recovery.md` – Fault injection, crash consistency, restart tests
- `12_release_gates_and_ci.md` – Release criteria, CI steps, and quality bars
- `13_test_data_fixtures.md` – Canonical datasets and generators
- `14_playwright_spec_templates.ts` – UI E2E templates (Playwright)
- `15_pytest_skeletons/` – API/integration test skeletons (pytest)
- `16_llm_eval_harness.md` – LLM determinism, routing, fallback & safety evaluations
- `17_checklists.md` – High‑signal operator/tester checklists
- `18_bug_bash_playbook.md` – Facilitated exploratory testing guide

See individual files for details.
