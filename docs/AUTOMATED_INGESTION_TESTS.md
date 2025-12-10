# Automated Ingestion E2E Tests

This document describes the automated test suites for Large Repo Ingestion Batching that perform all the manual testing scenarios automatically.

## Overview

We have two comprehensive automated test suites:

1. **Playwright E2E Tests** (`frontend/tests/ingestion-e2e.spec.ts`) - Tests the UI interactions
2. **Python API Tests** (`qa/ingestion_e2e_test.py`) - Tests the API directly

Both test suites cover all scenarios from `MANUAL_TEST_GUIDE_INGESTION.md`:
- ✅ B-Docs-01: Basic Ingestion (Happy Path)
- ✅ B-Docs-02: Hash-Based Skipping (Re-ingestion)
- ✅ B-Docs-03: Progress Metrics Monitoring
- ✅ B-Docs-04: Job Cancellation
- ✅ B-Docs-05: Job History Display
- ✅ B-Docs-06: Error Handling
- ✅ B-Docs-07: Telemetry Verification

---

## Prerequisites

- Every ingestion project must have `local_root_path` set to a real directory (e.g., `C:\InfinityWindow_Recovery`). The backend now rejects ingestion jobs when the project has no root path.
- Run one ingestion suite at a time to avoid SQLite lock contention; if locks occur, restart the backend and retry.

### For Playwright Tests:
- Backend running on `http://127.0.0.1:8000` (required)
- Frontend will be **automatically started** by Playwright (no manual start needed)
- Node.js 18+ and npm installed
- Playwright installed: `npx playwright install`

### For Python API Tests:
- Backend running on `http://127.0.0.1:8000`
- Python 3.9+ with virtual environment
- `requests` library installed

---

## Running Playwright E2E Tests

### Setup

1. **Start the backend** (required):
   ```powershell
   cd C:\InfinityWindow_Recovery\backend
   .\.venv\Scripts\Activate.ps1
   uvicorn app.api.main:app --reload
   ```

2. **Install Playwright** (if not already installed):
   ```powershell
   cd C:\InfinityWindow_Recovery\frontend
   npm install
   npx playwright install
   ```

**Note**: The frontend server will be **automatically started** by Playwright's `webServer` configuration. You don't need to start it manually. If you already have it running, Playwright will reuse the existing server.

### Run Tests

```powershell
cd C:\InfinityWindow_Recovery\frontend
npm run test:e2e -- ingestion-e2e.spec.ts
```

Or run all E2E tests:
```powershell
npm run test:e2e
```

### Options

- **Headless mode** (default): Tests run in headless browser
- **Headed mode**: Add `--headed` flag to see the browser
- **Debug mode**: Use `--debug` to step through tests
- **Specific test**: Use `--grep "B-Docs-01"` to run a specific test

### Output

- Test results are displayed in the terminal
- Screenshots are saved to `frontend/test-results/` on failures
- JSON report is saved to `frontend/test-results/ingestion-e2e-report-{timestamp}.json`

---

## Running Python API Tests

### Setup

1. **Start the backend**:
   ```powershell
   cd C:\InfinityWindow_Recovery\backend
   .\.venv\Scripts\Activate.ps1
   uvicorn app.api.main:app --reload
   ```

2. **Ensure dependencies are installed**:
   ```powershell
   pip install requests
   ```

### Run Tests

```powershell
cd C:\InfinityWindow_Recovery
python -m qa.ingestion_e2e_test
```

### Options

```powershell
# Use a different repository path
python -m qa.ingestion_e2e_test --repo-path "C:\MyRepo"

# Use an existing project ID
python -m qa.ingestion_e2e_test --project-id 1

# Verbose output
python -m qa.ingestion_e2e_test --verbose

# Custom API base URL
python -m qa.ingestion_e2e_test --api-base "http://localhost:8000"

# Save report to specific file
python -m qa.ingestion_e2e_test --output "my-report.json"
```

### Output

- Test progress is displayed in real-time (if `--verbose` is used)
- JSON report is saved to `test-results/ingestion-e2e-report-{timestamp}.json`
- Exit code: 0 if all tests pass, 1 if any test fails

---

## Test Report Format

Both test suites generate JSON reports with the following structure:

```json
{
  "timestamp": "2025-12-04T19:00:00.000000",
  "project_id": 1,
  "repo_path": "C:\\InfinityWindow",
  "summary": {
    "total": 7,
    "passed": 7,
    "failed": 0
  },
  "results": [
    {
      "test_name": "B-Docs-01: Basic Ingestion",
      "passed": true,
      "details": "Processed 105/105 files in 420.5s",
      "duration_seconds": 420.5,
      "timestamp": "2025-12-04T19:00:00.000000"
    },
    ...
  ]
}
```

---

## What Each Test Does

### B-Docs-01: Basic Ingestion
- Creates an ingestion job
- Monitors progress until completion
- Verifies all files are processed
- Checks that processed_items equals total_items

### B-Docs-02: Hash-Based Skipping
- Runs an initial ingestion
- Immediately re-runs the same ingestion
- Verifies that processed_items is 0 or very small (files skipped)
- Confirms the second run completes much faster

### B-Docs-03: Progress Metrics
- Starts an ingestion job
- Captures progress at T+0s and T+10s
- Verifies counters increase over time
- Ensures no negative or decreasing values

### B-Docs-04: Job Cancellation
- Starts a large ingestion
- Waits for processing to begin
- Cancels the job
- Verifies status changes to "cancelled"
- Checks cancel_requested flag

### B-Docs-05: Job History
- Retrieves job history list
- Verifies jobs are listed (newest first)
- Checks that job details are present
- Validates metrics are correct

### B-Docs-06: Error Handling
- Starts an ingestion with an invalid path
- Waits for job to fail
- Verifies status is "failed"
- Checks error message is readable (no stack traces)

### B-Docs-07: Telemetry
- Captures telemetry before ingestion
- Runs a small ingestion
- Captures telemetry after ingestion
- Verifies counters increased appropriately
- Tests telemetry reset functionality

---

## Troubleshooting

**Issue**: Status card never appears after clicking “Ingest repo”
- **Solution**: Fail fast and capture console/network logs. Verify the project has `local_root_path` set and the backend is reachable. The backend now returns 400 if the project root is missing.

### Playwright Tests

**Issue**: Tests fail with "Backend not ready"
- **Solution**: Ensure backend is running on port 8000 and accessible

**Issue**: Tests fail with "Element not found"
- **Solution**: Check that frontend is running on port 5174 and UI is accessible

**Issue**: Tests timeout
- **Solution**: Large repositories may take longer. Increase timeout in test file or use a smaller test repo

### Python API Tests

**Issue**: `ModuleNotFoundError: No module named 'requests'`
- **Solution**: Install requests: `pip install requests`

**Issue**: Connection refused errors
- **Solution**: Ensure backend is running and accessible at the API base URL

**Issue**: Database locked errors
- **Solution**: Ensure only one test suite is running at a time, or use the fixes from ISSUE-INGEST-002. Backend now retries commits and uses longer SQLite timeouts; restart if locks persist. Prefer Postgres in QA to eliminate lock contention.

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Ingestion E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install backend dependencies
        run: |
          cd backend
          python -m pip install -r requirements.txt
      
      - name: Install frontend dependencies
        run: |
          cd frontend
          npm install
          npx playwright install
      
      - name: Start backend
        run: |
          cd backend
          uvicorn app.api.main:app &
        shell: powershell
      
      - name: Start frontend
        run: |
          cd frontend
          npm run dev -- --host 127.0.0.1 --port 5174 &
        shell: powershell
      
      - name: Wait for services
        run: |
          Start-Sleep -Seconds 10
      
      - name: Run Python API tests
        run: |
          python -m qa.ingestion_e2e_test --verbose
      
      - name: Run Playwright tests
        run: |
          cd frontend
          npm run test:e2e -- ingestion-e2e.spec.ts
      
      - name: Upload test reports
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-reports
          path: |
            test-results/*.json
            frontend/test-results/*.json
```

---

## Comparison: Manual vs Automated

| Aspect | Manual Testing | Automated Testing |
|--------|---------------|-------------------|
| **Time** | 30-60 minutes | 5-15 minutes |
| **Consistency** | Varies by tester | 100% consistent |
| **Coverage** | May skip scenarios | All scenarios covered |
| **Repeatability** | Manual steps | Fully repeatable |
| **Documentation** | Manual notes | Automatic JSON reports |
| **UI Testing** | ✅ Full UI interaction | ✅ Full UI interaction (Playwright) |
| **API Testing** | Manual API calls | ✅ Automated API calls (Python) |

**Recommendation**: Use automated tests for:
- Regular regression testing
- CI/CD pipelines
- Quick validation after changes
- Comprehensive coverage verification

Use manual testing for:
- Initial feature validation
- UX/UI exploration
- Edge case discovery
- User acceptance testing

---

## Next Steps

1. **Run the automated tests** after any ingestion-related changes
2. **Compare results** with manual test results to ensure consistency
3. **Update tests** as new features are added
4. **Integrate into CI/CD** for continuous validation

---

## Related Documentation

- `docs/MANUAL_TEST_GUIDE_INGESTION.md` - Manual testing guide
- `docs/MANUAL_TEST_RESULTS_TEMPLATE.md` - Manual test results template
- `docs/TEST_PLAN.md` - Overall test plan
- `docs/ISSUES_LOG.md` - Known issues and fixes

