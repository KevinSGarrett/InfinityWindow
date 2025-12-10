# Manual Testing Guide – Large Repo Ingestion Batching

This guide provides step-by-step instructions for manually testing all aspects of the Large Repo Ingestion Batching feature. Follow these instructions carefully and record your results as you go.

---

## Prerequisites

- **Backend**: Python 3.9+ with virtual environment set up
- **Frontend**: Node.js 18+ with npm installed
- **Test Repository**: A local repository or directory with multiple files to ingest (we'll use `C:\InfinityWindow` itself as the test repo)
- **Browser**: Chrome, Firefox, or Edge (for testing the frontend UI)
- **API Testing Tool** (optional): Postman, curl, or PowerShell for direct API calls
- **Project root requirement**: Each project used for ingestion must have `local_root_path` set to a real directory (e.g., `C:\InfinityWindow`). The backend now rejects ingestion jobs without it.

---

## Part 1: Starting the Services

### Step 1.1: Start the Backend

1. Open a PowerShell terminal
2. Navigate to the backend directory:
   ```powershell
   cd C:\InfinityWindow\backend
   ```
3. Activate the virtual environment:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
4. Start the FastAPI server:
   ```powershell
   uvicorn app.api.main:app --host 127.0.0.1 --port 8000
   ```
5. **Verify**: You should see output like:
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
   INFO:     Started reloader process
   ```
6. **Test the health endpoint**:
   - Open a new PowerShell window (keep the backend running)
   - Run: `Invoke-RestMethod http://127.0.0.1:8000/health`
   - **Expected Result**: JSON response: `{"status":"ok","service":"InfinityWindow","version":"0.3.0"}`
   - If port 8000 is occupied, temporarily use another port (e.g., 8001) but adjust all API calls accordingly.

**✅ Record**: Backend started successfully? (Yes/No)

---

### Step 1.2: Start the Frontend

1. Open a **new** PowerShell terminal (keep backend running)
2. Navigate to the frontend directory:
   ```powershell
   cd C:\InfinityWindow\frontend
   ```
3. Install dependencies (if not already done):
   ```powershell
   npm install
   ```
4. Start the development server:
   ```powershell
   npm run dev
   ```
5. **Verify**: You should see output like:
   ```
   VITE v5.x.x  ready in xxx ms
   ➜  Local:   http://127.0.0.1:5173/
   ```
6. **Open the application**:
   - Open your browser and navigate to `http://127.0.0.1:5173`
   - You should see the InfinityWindow interface with three columns

**✅ Record**: Frontend started successfully? (Yes/No)
**✅ Record**: Browser console shows no errors? (Yes/No)

---

## Part 2: Setting Up a Test Project

### Step 2.1: Create a Test Project

1. In the browser (InfinityWindow UI), look at the **left column** (Projects/Conversations panel)
2. If you see an existing project, you can use it, OR create a new one:
   - Click the **"+"** button or "New Project" button (if available)
   - Enter project name: `Ingestion Test Project`
   - Click **Create** or **Save**
3. **Note the Project ID**: 
   - You'll need this for API testing
   - You can find it by:
     - Opening browser DevTools (F12) → Network tab
     - Creating the project and looking at the API request/response
    - OR checking the project list API: `Invoke-RestMethod http://127.0.0.1:8001/projects`
   - The project ID is typically a number like `1`, `2`, etc.

**✅ Record**: Project created? (Yes/No)
**✅ Record**: Project ID: `___________`
**✅ Record**: local_root_path set and accessible? (Yes/No)

---

## Part 3: Testing Basic Ingestion (Happy Path)

### Step 3.1: Navigate to Docs Tab

1. In the InfinityWindow UI, click on the **Docs** tab in the right column (workbench area)
2. You should see:
   - "Ingest text document" section (collapsible)
   - "Ingest local repo" section (collapsible)

**✅ Record**: Docs tab visible? (Yes/No)

---

### Step 3.2: Start a Repository Ingestion Job

1. In the Docs tab, expand the **"Ingest local repo"** section (click the `<summary>` or arrow)
2. Fill in the form fields:
   - **Root path**: `C:\InfinityWindow` (or another directory with multiple files)
   - **Name prefix**: `TestRepo/` (this will prefix all document names)
   - **Include globs**: Leave empty for default, OR enter specific patterns like `*.py,*.ts,*.md` to limit files
3. Click the **"Ingest repo"** button
4. **Observe**:
   - The button should change to "Queueing…" and become disabled
   - After a moment, a status card should appear below the form  
   - **Fail-fast**: If no status card appears within 10 seconds, stop, capture console/network, and check that the project has `local_root_path` set. If the “Job History” list later loads slowly, allow up to 60s; you may defer that single check if all other steps pass.

**✅ Record**: Button clicked successfully? (Yes/No)
**✅ Record**: Status card appeared? (Yes/No)

---

### Step 3.3: Monitor Job Status (UI)

1. **Watch the status card** that appeared after clicking "Ingest repo"
2. **Initial State** (should appear within 1-2 seconds):
   - Status should show: `pending` or `running`
   - If `running`, you should see:
     - `processed_items / total_items` (e.g., "5/100 files")
     - Progress bar or percentage (if implemented)
     - Bytes processed (e.g., "1.2 MB / 5.0 MB")
   - Started at timestamp (if available)

3. **While Running** (wait 10-30 seconds):
   - Status should remain `running`
   - `processed_items` should **increase** over time
   - `total_items` should remain constant (or increase slightly as more files are discovered)
   - Bytes counters should increase
   - **Take a screenshot** at this point (T+10 seconds)

4. **Completion** (wait until job finishes):
   - Status should change to `completed`
   - `processed_items` should equal `total_items`
   - Finished at timestamp should appear
   - Error message should be empty/null
   - **Take a screenshot** of the completed state

**✅ Record**: Status transitions: `pending` → `running` → `completed`? (Yes/No)
**✅ Record**: Counters increased during run? (Yes/No)
**✅ Record**: Final processed_items = total_items? (Yes/No)
**✅ Record**: Screenshot taken at T+10s? (Yes/No)
**✅ Record**: Screenshot taken at completion? (Yes/No)

---

### Step 3.4: Verify via API (Direct Check)

1. **Get the Job ID**:
   - From the UI status card, note the job ID (if displayed)
   - OR check browser DevTools → Network tab → Look for `GET /projects/{id}/ingestion_jobs/{job_id}` requests
   - OR call the list endpoint to see all jobs:
     ```powershell
     $projectId = 1  # Replace with your project ID
     Invoke-RestMethod "http://127.0.0.1:8000/projects/$projectId/ingestion_jobs?limit=1" | ConvertTo-Json -Depth 10
     ```
     - The first job in the list is the most recent
     - Note the `id` field

2. **Check Job Status via API**:
   ```powershell
   $projectId = 1  # Replace with your project ID
   $jobId = 1      # Replace with the job ID from step 1
   Invoke-RestMethod "http://127.0.0.1:8000/projects/$projectId/ingestion_jobs/$jobId" | ConvertTo-Json -Depth 10
   ```

3. **Verify the Response**:
   - `status` should be `"completed"`
   - `processed_items` should equal `total_items`
   - `error_message` should be `null`
   - `started_at` and `finished_at` should have timestamps
   - `total_bytes` and `processed_bytes` should be non-zero
   - `cancel_requested` should be `false`

**✅ Record**: Job ID: `___________`
**✅ Record**: API status matches UI? (Yes/No)
**✅ Record**: All fields present and correct? (Yes/No)
**✅ Record**: Paste the full API response JSON here:
```json

```

---

### Step 3.5: Verify Documents Were Created

1. **Check Documents List (UI)**:
   - In the Docs tab, scroll down to see the list of documents
   - You should see documents with names prefixed with `TestRepo/` (or your chosen prefix)
   - Count how many documents appear

2. **Check Files tab (UI)**:
   - Open the Files tab for the same project
   - Ensure it lists without warnings (no “local_root_path not configured”) and does not return 400

3. **Check Documents List (API)**:
   ```powershell
   $projectId = 1  # Replace with your project ID
   Invoke-RestMethod "http://127.0.0.1:8000/projects/$projectId/docs" | ConvertTo-Json -Depth 10
   ```
   - Count documents with names starting with your prefix
   - Verify document names match the file paths (with prefix)

**✅ Record**: Documents visible in UI? (Yes/No)
**✅ Record**: Number of documents created: `___________`
**✅ Record**: Document names have correct prefix? (Yes/No)
**✅ Record**: Files tab loads without root-path warning? (Yes/No)

---

## Part 4: Testing Hash-Based Skipping (Re-ingestion)

### Step 4.1: Re-run Ingestion (No Changes)

1. **Immediately re-run** the same ingestion:
   - Same root path: `C:\InfinityWindow`
   - Same name prefix: `TestRepo/`
   - Same include globs (or leave empty)
   - Click **"Ingest repo"** again

2. **Observe**:
   - A new job should start (new job ID)
   - Status should quickly go to `running` then `completed`
   - **Key Test**: `processed_items` should be **0** (or very small) because files haven't changed
   - Elapsed time should be **< 5 seconds** (much faster than the first run)

**✅ Record**: Second job started? (Yes/No)
**✅ Record**: processed_items = 0 (or very small)? (Yes/No)
**✅ Record**: Completion time < 5 seconds? (Yes/No)

---

### Step 4.2: Modify a File and Re-ingest

1. **Modify a file** in the repository:
   - Open a file in `C:\InfinityWindow` (e.g., `README.md` or any `.py` file)
   - Add a comment or change a line (e.g., add `# Test change for ingestion` at the top)
   - Save the file

2. **Re-run ingestion**:
   - Same root path and prefix
   - Click **"Ingest repo"** again

3. **Observe**:
   - New job starts
   - `processed_items` should be **1** (only the modified file)
   - `total_items` might be the same or slightly different
   - Job should complete quickly

**✅ Record**: File modified? (Yes/No)
**✅ Record**: processed_items = 1? (Yes/No)
**✅ Record**: Only the modified file was processed? (Yes/No)

---

### Step 4.3: Verify Document Update

1. **Check the document** for the modified file:
   - In the Docs tab, find the document corresponding to the file you modified
   - OR use the API:
     ```powershell
     $projectId = 1
     $docs = Invoke-RestMethod "http://127.0.0.1:8000/projects/$projectId/docs"
     # Find the doc for your modified file and check its updated_at timestamp
     ```

2. **Verify**:
   - The document's `updated_at` timestamp should be recent (matching the ingestion time)
   - The document content should reflect your changes

**✅ Record**: Document updated? (Yes/No)
**✅ Record**: Timestamp is recent? (Yes/No)

---

## Part 5: Testing Progress Metrics (Real-time Updates)

### Step 5.1: Start a Medium-Sized Ingestion

1. **Choose a larger subset** to test progress:
   - Root path: `C:\InfinityWindow`
   - Name prefix: `ProgressTest/`
   - Include globs: `*.py,*.ts,*.md` (to limit but still have many files)
   - Click **"Ingest repo"**

2. **Monitor Progress**:
   - **At T+0 seconds**: Take a screenshot of the status card
     - Note: status, processed_items, total_items, processed_bytes, total_bytes
   - **At T+10 seconds**: Take another screenshot
     - Compare: processed_items should have increased
     - Compare: processed_bytes should have increased
   - **Continue monitoring** until completion

3. **Verify Counters**:
   - Counters should **never decrease**
   - `processed_items` should never exceed `total_items`
   - Bytes should increase monotonically

**✅ Record**: Screenshot at T+0s taken? (Yes/No)
**✅ Record**: Screenshot at T+10s taken? (Yes/No)
**✅ Record**: Counters increased? (Yes/No)
**✅ Record**: No negative or decreasing values? (Yes/No)

---

### Step 5.2: Compare UI vs API (During Run)

1. **While the job is running** (status = `running`):
   - **UI**: Note the values from the status card (processed_items, total_items, bytes, etc.)
   - **API**: Call the job status endpoint:
     ```powershell
     $projectId = 1
     $jobId = <current_job_id>
     Invoke-RestMethod "http://127.0.0.1:8000/projects/$projectId/ingestion_jobs/$jobId" | ConvertTo-Json -Depth 10
     ```
   - **Compare**: UI values should match API values (allowing for ~1-2 second polling delay)

2. **Repeat** this comparison 2-3 times during the run

**✅ Record**: UI matches API (within polling delay)? (Yes/No)
**✅ Record**: Comparison timestamps:
   - T+5s: UI processed_items = `___`, API processed_items = `___`
   - T+15s: UI processed_items = `___`, API processed_items = `___`

---

## Part 6: Testing Cancellation

### Step 6.1: Start a Large Ingestion

1. **Start a large ingestion** that will take time:
   - Root path: `C:\InfinityWindow`
   - Name prefix: `CancelTest/`
   - Include globs: Leave empty (to ingest everything)
   - Click **"Ingest repo"**

2. **Wait** until `processed_items > 0` (at least 5-10 files processed) or status shows `running`. If the job completes before you can cancel, record it as a race.

**✅ Record**: Large job started? (Yes/No)
**✅ Record**: processed_items > 0? (Yes/No)

---

### Step 6.2: Cancel the Job

1. **Cancel the job** (if still running):
   - In the UI status card, look for a **"Cancel job"** button
   - Click it
   - **OR** use the API:
     ```powershell
     $projectId = 1
     $jobId = <current_job_id>
    Invoke-RestMethod -Method Post "http://127.0.0.1:8001/projects/$projectId/ingestion_jobs/$jobId/cancel" | ConvertTo-Json -Depth 10
     ```

2. **Observe**:
   - Status should change to `cancelled` within a few seconds; if it completes first, note the race condition.
   - Counters should **freeze** (stop increasing)
   - A success toast/notification may appear (if implemented)
   - Error message should show "Cancelled by user" or similar

3. **Record timing**:
   - Note the time when you clicked Cancel
   - Note the time when status changed to `cancelled`
   - Calculate the latency

**✅ Record**: Cancel button clicked? (Yes/No)
**✅ Record**: Status changed to `cancelled`? (Yes/No)
**✅ Record**: Counters froze? (Yes/No)
**✅ Record**: Cancel latency: `___________` seconds

---

### Step 6.3: Verify Cancellation via API

1. **Check the job status**:
   ```powershell
   $projectId = 1
   $jobId = <cancelled_job_id>
   Invoke-RestMethod "http://127.0.0.1:8000/projects/$projectId/ingestion_jobs/$jobId" | ConvertTo-Json -Depth 10
   ```

2. **Verify**:
   - `status` = `"cancelled"`
   - `cancel_requested` = `true`
   - `error_message` may contain cancellation reason
   - `finished_at` should have a timestamp
   - `processed_items` should be less than `total_items`

**✅ Record**: API shows status = "cancelled"? (Yes/No)
**✅ Record**: cancel_requested = true? (Yes/No)

---

### Step 6.4: Start Another Ingestion After Cancellation

1. **Immediately start another ingestion**:
   - Same root path and prefix
   - Click **"Ingest repo"** again

2. **Observe**:
   - New job should start normally
   - Hash skipping should still work (files already processed before cancellation should be skipped)
   - Job should complete successfully

**✅ Record**: New job started after cancellation? (Yes/No)
**✅ Record**: Hash skipping still works? (Yes/No)

---

## Part 7: Testing Job History

### Step 7.1: View Job History (UI)

1. **In the Docs tab**, scroll down to the **"Recent ingestion jobs"** section
2. **Click "Refresh"** (if there's a refresh button)
3. **Observe the table**:
   - Should show a list of jobs (newest first)
   - Columns should include: Job ID, Status, Files processed, Bytes, Duration, Finished at, Error message
   - Should show at least the jobs you created during testing

**✅ Record**: Job history table visible? (Yes/No)
**✅ Record**: Jobs listed (newest first)? (Yes/No)
**✅ Record**: All columns present? (Yes/No)

---

### Step 7.2: Verify Job History via API

1. **Get job history**:
   ```powershell
   $projectId = 1
   Invoke-RestMethod "http://127.0.0.1:8000/projects/$projectId/ingestion_jobs?limit=20" | ConvertTo-Json -Depth 10
   ```

2. **Compare with UI**:
   - Count the number of jobs in the API response
   - Count the number of jobs in the UI table
   - Verify job IDs match
   - Verify statuses match
   - Verify metrics (files, bytes, duration) match

**✅ Record**: API returns job list? (Yes/No)
**✅ Record**: UI matches API? (Yes/No)
**✅ Record**: Number of jobs in history: `___________`

---

### Step 7.3: Test Empty State

1. **If possible**, test with a fresh project (or note the current state):
   - Create a new project
   - Go to Docs tab
   - Check the "Recent ingestion jobs" section
   - Should show a placeholder message like "No ingestion jobs yet" or empty state

**✅ Record**: Empty state shown correctly? (Yes/No)

---

## Part 8: Testing Error Handling

### Step 8.1: Test Invalid Root Path

1. **Start an ingestion with an invalid path**:
   - Root path: `C:\NonExistentDirectory12345`
   - Name prefix: `ErrorTest/`
   - Click **"Ingest repo"**

2. **Observe**:
   - Job should start but quickly fail
   - Status should change to `failed`
   - Error message should appear (e.g., "Root path is not a directory")
   - Error message should be **readable** (not a stack trace)

**✅ Record**: Job failed as expected? (Yes/No)
**✅ Record**: Error message readable? (Yes/No)
**✅ Record**: Error message text: `___________`

---

### Step 8.2: Verify Failed Job in History

1. **Check the job history**:
   - The failed job should appear in the "Recent ingestion jobs" table
   - Status column should show `failed`
   - Error column should show the error message

2. **Check via API**:
   ```powershell
   $projectId = 1
   $jobId = <failed_job_id>
   Invoke-RestMethod "http://127.0.0.1:8000/projects/$projectId/ingestion_jobs/$jobId" | ConvertTo-Json -Depth 10
   ```
   - Verify `status` = `"failed"`
   - Verify `error_message` contains the error text
   - Verify `finished_at` has a timestamp

**✅ Record**: Failed job in history? (Yes/No)
**✅ Record**: Error message visible in UI? (Yes/No)
**✅ Record**: API shows failed status? (Yes/No)

---

## Part 9: Testing Telemetry

### Step 9.1: Check Telemetry Before Jobs

1. **Get telemetry snapshot**:
   ```powershell
   Invoke-RestMethod "http://127.0.0.1:8001/debug/telemetry" | ConvertTo-Json -Depth 10
   ```

2. **Note the ingestion metrics**:
   - `ingestion.jobs_started`
   - `ingestion.jobs_completed`
   - `ingestion.jobs_cancelled`
   - `ingestion.jobs_failed`
   - `ingestion.files_processed`
   - `ingestion.files_skipped`
   - `ingestion.bytes_processed`
   - `ingestion.total_duration_seconds`

**✅ Record**: Initial telemetry values:
```json

```

---

### Step 9.2: Run Multiple Jobs and Check Telemetry

1. **Run a few jobs** (success, skip, cancel if you haven't already)
2. **After each job**, check telemetry:
   ```powershell
   Invoke-RestMethod "http://127.0.0.1:8001/debug/telemetry" | ConvertTo-Json -Depth 10
   ```
3. **Verify**:
   - `jobs_started` increased
   - `jobs_completed` increased (for successful jobs)
   - `jobs_cancelled` increased (if you cancelled one)
   - `jobs_failed` increased (if you had a failure)
   - `files_processed` and `files_skipped` increased appropriately
   - `bytes_processed` increased
   - `total_duration_seconds` increased

**✅ Record**: Telemetry after jobs:
```json

```

**✅ Record**: Counters increased correctly? (Yes/No)

---

### Step 9.3: Test Telemetry Reset

1. **Reset telemetry**:
   ```powershell
   Invoke-RestMethod "http://127.0.0.1:8001/debug/telemetry?reset=true" | ConvertTo-Json -Depth 10
   ```

2. **Verify**:
   - Ingestion counters should be **zero** (or reset to initial state)
   - LLM and tasks telemetry should **not** be affected (if they exist)

**✅ Record**: Telemetry reset? (Yes/No)
**✅ Record**: Ingestion counters = 0? (Yes/No)
**✅ Record**: Other telemetry unchanged? (Yes/No)

---

## Part 10: Testing Edge Cases

### Step 10.1: Test with Empty Directory

1. **Create an empty directory** (or use a directory with no matching files):
   - Root path: `C:\Temp\EmptyTest` (create if needed)
   - Name prefix: `Empty/`
   - Include globs: `*.nonexistent`
   - Click **"Ingest repo"**

2. **Observe**:
   - Job should complete successfully
   - `processed_items` should be 0
   - `total_items` should be 0 (or very small)
   - No errors should occur

**✅ Record**: Empty directory handled? (Yes/No)
**✅ Record**: No errors? (Yes/No)

---

### Step 10.2: Test with Very Large File

1. **If possible**, test with a very large file (if you have one):
   - Include it in the ingestion
   - Verify it processes correctly
   - Check that bytes counters reflect the large file size

**✅ Record**: Large file processed? (Yes/No)

---

### Step 10.3: Test Concurrent Jobs (if possible)

1. **Try starting two jobs at the same time** (if the UI allows):
   - Start one job
   - Immediately start another (different prefix or path)
   - Observe both jobs

2. **Note**: The system may queue jobs or run them sequentially

**✅ Record**: Multiple jobs handled? (Yes/No)
**✅ Record**: Behavior: `___________`

---

## Part 11: Final Verification

### Step 11.1: Verify All Features Work Together

1. **Run a complete workflow**:
   - Create a new project (or use existing)
   - Start an ingestion
   - Monitor progress
   - Let it complete
   - Re-run (should skip)
   - Modify a file and re-run (should process 1 file)
   - Check job history
   - Check telemetry

2. **Verify**:
   - All features work together
   - No UI errors
   - No backend errors (check backend terminal)
   - No browser console errors

**✅ Record**: Complete workflow successful? (Yes/No)
**✅ Record**: No errors in backend terminal? (Yes/No)
**✅ Record**: No errors in browser console? (Yes/No)

---

### Step 11.2: Document Issues

1. **List any issues** you encountered:
   - Bugs
   - UI problems
   - Performance issues
   - Confusing behavior
   - Missing features

**✅ Record Issues Found**:
```
1. 
2. 
3. 
```

---

## Summary Checklist

Before finishing, verify you've completed all tests:

- [ ] Backend and frontend started successfully
- [ ] Basic ingestion (happy path) works
- [ ] Job status updates in real-time
- [ ] Hash-based skipping works (re-ingestion)
- [ ] Progress metrics are accurate
- [ ] Cancellation works
- [ ] Job history displays correctly
- [ ] Error handling works
- [ ] Telemetry tracks correctly
- [ ] Edge cases handled
- [ ] All features work together

---

## Notes for Results Submission

When submitting your test results, please include:

1. **Screenshots**: At least 3-5 screenshots showing:
   - Status card during a running job
   - Completed job status
   - Job history table
   - Any error states

2. **API Responses**: Paste JSON responses for:
   - At least one completed job
   - Job history list
   - Telemetry snapshot (before and after)

3. **Timing Data**: Note any performance observations:
   - How long did large jobs take?
   - How fast was hash skipping?
   - Cancel latency?

4. **Issues Found**: List any bugs, problems, or confusing behavior

5. **Overall Assessment**: 
   - Does everything work as expected?
   - Are there any missing features?
   - Is the UI clear and intuitive?

---

## Troubleshooting

If you encounter issues:

1. **Backend not starting**:
   - Check Python version: `python --version` (should be 3.9+)
   - Check virtual environment is activated
   - Check port 8000 is not in use: `Get-NetTCPConnection -LocalPort 8000`

2. **Frontend not starting**:
   - Run `npm install` again
   - Check Node.js version: `node --version` (should be 18+)
   - Check port 5173 is not in use

3. **Jobs not starting**:
   - Check backend is running
   - Check browser console for errors
   - Verify project ID is correct
   - Check root path exists and is accessible

4. **Jobs stuck in "pending"**:
   - Check backend terminal for errors
   - Verify background tasks are running
   - Try restarting the backend

5. **UI not updating**:
   - Check browser console for JavaScript errors
   - Verify WebSocket/SSE connections (if used)
   - Try refreshing the page

---

**End of Manual Testing Guide**

Good luck with your testing! Record your results carefully and share them when complete.

