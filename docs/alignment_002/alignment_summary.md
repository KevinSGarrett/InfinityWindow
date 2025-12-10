Total requirements: 68
Correct: 4
Misaligned: 3
To-do: 61
Unsure: 0
Coverage: 5.9% implemented correctly

Top gaps (impact-driven):
- PS.SAFETY.TERM.001 [Misaligned] (P0) — Terminal allowlist/forbidden commands :: run_terminal endpoints execute arbitrary commands with subprocess.run and no allowlist/forbidden checks.
- P3.LLM.TOOLS.001 [Misaligned] (P1) — run_agent_with_tools and tool schemas :: LLM file tool routes differ: backend exposes /projects/{id}/fs/read and /fs/write; plan expects /projects/{id}/files/content and /files/apply_edit with matching semantics. No alias routes found.
- PT.INGEST.API.001 [Misaligned] (P1) — Windowed read_file :: read_project_file exists but only returns full file; no start_line/end_line windowing support.
- P1.API.ENDPOINT.001 [To-do] (P1) — POST /projects/{id}/blueprints :: Not found in repo; no evidence of implementation.
- P1.API.ENDPOINT.002 [To-do] (P1) — GET /projects/{id}/blueprints :: Not found in repo; no evidence of implementation.
- P1.API.ENDPOINT.003 [To-do] (P1) — GET /blueprints/{id} :: Not found in repo; no evidence of implementation.
- P1.API.ENDPOINT.004 [To-do] (P1) — PATCH /blueprints/{id} :: Not found in repo; no evidence of implementation.
- P1.API.ENDPOINT.005 [To-do] (P1) — PATCH /plan_nodes/{id} :: Not found in repo; no evidence of implementation.
- P1.API.ENDPOINT.006 [To-do] (P1) — POST /blueprints/{id}/generate_plan :: Not found in repo; no evidence of implementation.
- P1.API.ENDPOINT.007 [To-do] (P1) — POST /plan_nodes/{id}/generate_tasks :: Not found in repo; no evidence of implementation.
