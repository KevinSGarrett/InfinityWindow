[P3.LLM.TOOLS.001] run_agent_with_tools and tool schemas — Misaligned
Plan: Updated_Project_Plan_2_Phase3_4.txt::3.3 LLM tool-calling
Expected contract:
- openai_client tool definitions for read_file/write_file/run_terminal/search_docs/search_messages and run_agent_with_tools mapping tool calls to ExecutionSteps.
Observed evidence:
- backend/app/api/main.py:3313-3405 — LLM file tool routes differ: backend exposes /projects/{id}/fs/read and /fs/write; plan expects /projects/{id}/files/content and /files/apply_edit with matching semantics. No alias routes found.
Rationale: LLM file tool routes differ: backend exposes /projects/{id}/fs/read and /fs/write; plan expects /projects/{id}/files/content and /files/apply_edit with matching semantics. No alias routes found.
Proposed fix: Implement per updated plan.
Owner: TBD; Suggested milestone: Phase 3

[PS.SAFETY.TERM.001] Terminal allowlist/forbidden commands — Misaligned
Plan: Updated_Project_Plan_2_AUTOPILOT_LIMITATIONS.txt::3.2 Terminal safety
Expected contract:
- Terminal commands auto-run only from safe prefixes; forbidden substrings rm/del/git push/format/shutdown/reboot etc.
Observed evidence:
- backend/app/api/main.py:3753-3838 — run_terminal endpoints execute arbitrary commands with subprocess.run and no allowlist/forbidden checks.
Rationale: run_terminal endpoints execute arbitrary commands with subprocess.run and no allowlist/forbidden checks.
Proposed fix: Enforce SAFE_COMMAND_PREFIXES and forbid dangerous substrings before invoking subprocess.run.
Owner: TBD; Suggested milestone: Safety

[PT.INGEST.API.001] Windowed read_file — Misaligned
Plan: Updated_Project_Plan_2_Ingestion_Plan.txt::T4.2 Code workers: windowed file reads
Expected contract:
- Filesystem read endpoint supports start_line/end_line to allow windowed reads for workers.
Observed evidence:
- backend/app/api/main.py:3313-3351 — read_project_file exists but only returns full file; no start_line/end_line windowing support.
Rationale: read_project_file exists but only returns full file; no start_line/end_line windowing support.
Proposed fix: Add start_line/end_line parameters to fs/read and return windowed content to cut token usage.
Owner: TBD; Suggested milestone: Phase T
