# InfinityWindow Autopilot  Implementation Checklist (Design)

Status: Not started. Autopilot is design-only; no phases are implemented. Keep this checklist in sync with `docs/PROGRESS.md`, `docs/TODO_CHECKLIST.md`, and the design docs.

Use this as the entry point when Autopilot work begins:

- [ ] Phase 1  Blueprint & Plan graph (Blueprint/PlanNode/Task links; see `docs/AUTOPILOT_PLAN.md`).
- [ ] Phase 2  Project Brain & context (conversation summaries, snapshots, context builder; see `docs/AUTOPILOT_PLAN.md`).
- [ ] Phase 3  Execution runs & workers (ExecutionRun/ExecutionStep, worker wrappers; see `docs/AUTOPILOT_PLAN.md`).
- [ ] Phase 4  ManagerAgent & autonomy modes (intent classifier, manager heartbeat, approvals; see `docs/AUTOPILOT_PLAN.md`).
- [ ] Phase T  Ingestion & token/cost controls (batched ingestion, blueprint sections; see `docs/AUTOPILOT_PLAN.md`).

References:
- Design sources: `Project_Plans/Updated_Project_Plans/Updated_Project_Plan_2.txt`, `..._Phase3_4.txt`.
- Model routing: `docs/MODEL_MATRIX.md`.
- Safety & learning: `docs/AUTOPILOT_LIMITATIONS.md`, `docs/AUTOPILOT_LEARNING.md`.
