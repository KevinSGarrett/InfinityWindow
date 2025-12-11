import { defineConfig } from '@playwright/test';

const uiBase = process.env.PLAYWRIGHT_UI_BASE ?? 'http://localhost:5173';
const uiUrl = new URL(uiBase);
const uiHost = uiUrl.hostname || 'localhost';
const uiPort = uiUrl.port || '5173';

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
  ],
  use: {
    baseURL: uiBase,
    headless: true,
    trace: 'on-first-retry',
    // Increase timeout for slow operations
    actionTimeout: 30000,
    navigationTimeout: 30000,
  },
  // Auto-start frontend server before tests
  webServer: {
    command: `npm run dev -- --host ${uiHost} --port ${uiPort}`,
    url: uiBase,
    reuseExistingServer: !process.env.CI, // Reuse if already running (unless in CI)
    timeout: 120 * 1000, // 2 minutes to start
    stdout: 'ignore',
    stderr: 'pipe',
  },
});
