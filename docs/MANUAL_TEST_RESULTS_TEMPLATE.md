# Manual Test Results – Large Repo Ingestion Batching

**Test Date**: `___________`  
**Tester Name**: `___________`  
**Environment**: `___________` (e.g., Windows 11, Chrome 120)  
**Backend Version**: `___________` (from `/health` endpoint)  
**Frontend Version**: `___________` (if available)

---

## Part 1: Service Startup

### Backend
- [ ] Backend started successfully
- [ ] Health endpoint returns correct response
- **Notes**: `___________`

### Frontend
- [ ] Frontend started successfully
- [ ] Browser console shows no errors
- **Notes**: `___________`

---

## Part 2: Test Project Setup

- [ ] Project created
- **Project ID**: `___________`
- **Project Name**: `___________`
- **local_root_path set and accessible?**: [ ] Yes [ ] No

---

## Part 3: Basic Ingestion (Happy Path)

### Step 3.1: Docs Tab
- [ ] Docs tab visible
- [ ] "Ingest local repo" section visible

### Step 3.2: Start Ingestion
- [ ] Button clicked successfully
- [ ] Status card appeared (within 10s; fail fast if not)
- **Root Path Used**: `___________`
- **Name Prefix Used**: `___________`
- **Include Globs**: `___________`

### Step 3.3: Monitor Job Status (UI)
- [ ] Status transitions: `pending` → `running` → `completed`
- [ ] Counters increased during run
- [ ] Final processed_items = total_items
- [ ] Screenshot taken at T+10s
- [ ] Screenshot taken at completion
- **Initial Status**: `___________`
- **Final Status**: `___________`
- **Final processed_items**: `___________`
- **Final total_items**: `___________`
- **Final processed_bytes**: `___________`
- **Final total_bytes**: `___________`
- **Duration**: `___________` seconds

### Step 3.4: Verify via API
- [ ] Job ID retrieved
- [ ] API status matches UI
- [ ] All fields present and correct
- **Job ID**: `___________`
- **API Response** (paste JSON):
```json

```

### Step 3.5: Verify Documents Created
- [ ] Documents visible in UI
- [ ] Document names have correct prefix
- [ ] Files tab loads without root-path warning / 400
- **Number of Documents Created**: `___________`
- **Sample Document Names**: 
  - `___________`
  - `___________`
  - `___________`

---

## Part 4: Hash-Based Skipping

### Step 4.1: Re-run (No Changes)
- [ ] Second job started
- [ ] processed_items = 0 (or very small)
- [ ] Completion time < 5 seconds
- **processed_items**: `___________`
- **Completion Time**: `___________` seconds

### Step 4.2: Modify File and Re-ingest
- [ ] File modified
- [ ] processed_items = 1
- [ ] Only modified file processed
- **File Modified**: `___________`
- **processed_items**: `___________`

### Step 4.3: Verify Document Update
- [ ] Document updated
- [ ] Timestamp is recent
- **Updated Timestamp**: `___________`

---

## Part 5: Progress Metrics

### Step 5.1: Monitor Progress
- [ ] Screenshot at T+0s taken
- [ ] Screenshot at T+10s taken
- [ ] Counters increased
- [ ] No negative or decreasing values
- **T+0s Values**:
  - processed_items: `___________`
  - total_items: `___________`
  - processed_bytes: `___________`
  - total_bytes: `___________`
- **T+10s Values**:
  - processed_items: `___________`
  - total_items: `___________`
  - processed_bytes: `___________`
  - total_bytes: `___________`

### Step 5.2: Compare UI vs API
- [ ] UI matches API (within polling delay)
- **T+5s Comparison**:
  - UI processed_items: `___________`
  - API processed_items: `___________`
- **T+15s Comparison**:
  - UI processed_items: `___________`
  - API processed_items: `___________`

---

## Part 6: Cancellation

### Step 6.1: Start Large Ingestion
- [ ] Large job started
- [ ] processed_items > 0
- **processed_items when cancelled**: `___________`

### Step 6.2: Cancel Job
- [ ] Cancel button clicked
- [ ] Status changed to `cancelled`
- [ ] Counters froze
- **Cancel Latency**: `___________` seconds
- **Time Cancel Clicked**: `___________`
- **Time Status Changed**: `___________`

### Step 6.3: Verify Cancellation via API
- [ ] API shows status = "cancelled"
- [ ] cancel_requested = true
- **API Response** (paste JSON):
```json

```

### Step 6.4: Start Another Ingestion
- [ ] New job started after cancellation
- [ ] Hash skipping still works
- **Notes**: `___________`

---

## Part 7: Job History

### Step 7.1: View Job History (UI)
- [ ] Job history table visible
- [ ] Jobs listed (newest first)
- [ ] All columns present
- **Number of Jobs in Table**: `___________`

### Step 7.2: Verify Job History via API
- [ ] API returns job list
- [ ] UI matches API
- **Number of Jobs in API**: `___________`
- **API Response** (first 3 jobs, paste JSON):
```json

```

### Step 7.3: Test Empty State
- [ ] Empty state shown correctly
- **Notes**: `___________`

---

## Part 8: Error Handling

### Step 8.1: Invalid Root Path
- [ ] Job failed as expected
- [ ] Error message readable
- **Error Message**: `___________`

### Step 8.2: Verify Failed Job in History
- [ ] Failed job in history
- [ ] Error message visible in UI
- [ ] API shows failed status
- **Job ID**: `___________`
- **Error Message**: `___________`

---

## Part 9: Telemetry

### Step 9.1: Initial Telemetry
- [ ] Telemetry retrieved
- **Initial Telemetry** (paste JSON):
```json

```

### Step 9.2: Telemetry After Jobs
- [ ] Counters increased correctly
- **Telemetry After Jobs** (paste JSON):
```json

```

### Step 9.3: Telemetry Reset
- [ ] Telemetry reset
- [ ] Ingestion counters = 0
- [ ] Other telemetry unchanged
- **Post-Reset Telemetry** (paste JSON):
```json

```

---

## Part 10: Edge Cases

### Step 10.1: Empty Directory
- [ ] Empty directory handled
- [ ] No errors
- **Notes**: `___________`

### Step 10.2: Very Large File
- [ ] Large file processed
- **Notes**: `___________`

### Step 10.3: Concurrent Jobs
- [ ] Multiple jobs handled
- **Behavior Observed**: `___________`

---

## Part 11: Final Verification

### Step 11.1: Complete Workflow
- [ ] Complete workflow successful
- [ ] No errors in backend terminal
- [ ] No errors in browser console
- **Notes**: `___________`

### Step 11.2: Issues Found
**List any issues encountered**:

1. **Issue**: `___________`
   - **Severity**: `___________` (Critical/High/Medium/Low)
   - **Steps to Reproduce**: `___________`
   - **Expected Behavior**: `___________`
   - **Actual Behavior**: `___________`

2. **Issue**: `___________`
   - **Severity**: `___________`
   - **Steps to Reproduce**: `___________`
   - **Expected Behavior**: `___________`
   - **Actual Behavior**: `___________`

3. **Issue**: `___________`
   - **Severity**: `___________`
   - **Steps to Reproduce**: `___________`
   - **Expected Behavior**: `___________`
   - **Actual Behavior**: `___________`

---

## Overall Assessment

### Test Summary
- **Total Tests Run**: `___________`
- **Tests Passed**: `___________`
- **Tests Failed**: `___________`
- **Tests Skipped**: `___________`

### Functionality Assessment
- [ ] All core features work as expected
- [ ] UI is clear and intuitive
- [ ] Performance is acceptable
- [ ] Error handling is adequate
- [ ] Documentation is helpful

### Missing Features or Improvements
**List any features you expected but didn't find, or improvements you'd suggest**:

1. `___________`
2. `___________`
3. `___________`

### Performance Observations
- **Average job completion time** (for ~100 files): `___________` seconds
- **Hash skipping speed**: `___________` seconds
- **Cancel latency**: `___________` seconds
- **UI update frequency**: `___________` seconds (polling interval)

### Screenshots Attached
- [ ] Screenshot: Status card during running job
- [ ] Screenshot: Completed job status
- [ ] Screenshot: Job history table
- [ ] Screenshot: Error state (if encountered)
- [ ] Screenshot: Progress metrics (T+0s and T+10s)

### Additional Notes
**Any other observations, comments, or suggestions**:

```
___________


___________


___________
```

---

## Sign-off

**Tester Signature**: `___________`  
**Date Completed**: `___________`  
**Ready for Review**: [ ] Yes [ ] No

---

**End of Test Results**

