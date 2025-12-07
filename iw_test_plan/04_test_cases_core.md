# 4) Core API & Chat – Detailed Tests

> Each test has: **Preconditions**, **Steps**, **Expected**, **Telemetry**, **Cleanup**.

## Projects & Conversations

**A-Proj-01 – Create/List/Update project (API)**  
Pre: backend running.  
Steps: POST /projects; GET /projects; PATCH /projects/{id}.  
Expected: consistent fields incl. `local_root_path`; timestamps monotonically increasing.  
Telemetry: none or `projects_created++`.  
Cleanup: DELETE project if supported (else keep).

**A-Conv-01 – Create conversation**  
…

## Chat pipeline

**C-Chat-01 – Health & echo**  
Pre: /health returns version.  
Steps: POST /chat with trivial prompt `"ping"` in each mode (`auto, fast, deep, budget, research, code`).  
Expected: non‑empty response; latency recorded.  
Telemetry: `_LLM_TELEMETRY_COUNTERS.calls++` per mode.

**C-Chat-02 – Model routing – auto submode inference**  
Pre: LLM stub enabled.  
Steps: send prompts representative of `code/research/fast/deep`; assert chosen model recorded.  
Expected: `_infer_auto_submode` chooses expected; fallback chain respected if primary fails.  
Telemetry: `fallbacks++` only on injected failures.

**C-Chat-05 – Token/size enforcement**  
Steps: send payload just under/over limits; expect truncation/error handling without crash.

## Tasks auto‑update

**C-Tasks-01 – Completion detection**  
Steps: message includes “Task XYZ done ✅”; expect existing task marked done.  
**C-Tasks-02 – Creation & de‑dupe**  
Steps: message with multiple “TODO: …”; expect new tasks, no duplicates (normalization + fuzzy).

(… dozens more cases in the file …)
