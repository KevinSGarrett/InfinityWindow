import { defineConfig } from '@playwright/test';
import path from 'path';

const frontendDir = path.join(__dirname, '..', '..', 'frontend');
const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173';

export default defineConfig({
  testDir: path.join(__dirname, '..', 'tests_e2e'),
  reporter: [
    ['html', { outputFolder: 'test-results/playwright-html' }],
    ['line'],
  ],
  use: {
    baseURL,
    trace: 'on',
    video: 'on',
    screenshot: 'on',
    headless: true,
  },
  webServer: {
    command: 'npm run dev',
    url: baseURL,
    cwd: frontendDir,
    reuseExistingServer: !process.env.CI,
    stdout: 'pipe',
    stderr: 'pipe',
    timeout: 120_000,
  },
});

