import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 60_000,
  testMatch: [
    'tests/ui-smoke.spec.ts',
    'tests/ui-chat-smoke.spec.ts',
    'tests/ui-extended.spec.ts',
    'tests/tasks-suggestions.spec.ts',
    'tests/tasks-confidence.spec.ts',
    'tests/ui-accessibility-phase3.spec.ts',
    'tests/usage-dashboard.spec.ts',
    'tests/usage-retrieval-config.spec.ts',
  ],
  use: {
    baseURL: 'http://localhost:5173',
    headless: true,
    trace: 'on-first-retry',
    // Increase timeout for slow operations
    actionTimeout: 30000,
    navigationTimeout: 30000,
  },
  // Auto-start frontend server before tests
  webServer: {
    command: 'npm run dev -- --host localhost --port 5173',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI, // Reuse if already running (unless in CI)
    timeout: 120 * 1000, // 2 minutes to start
    stdout: 'ignore',
    stderr: 'pipe',
  },
});

