// 14) Playwright Spec Templates – Right Column & Core Flows
import { test, expect } from '@playwright/test';

test.describe('InfinityWindow – Smoke', () => {
  test('S-001 Health & App boot', async ({ page }) => {
    await page.goto('http://localhost:5173/');
    await expect(page.getByText('InfinityWindow')).toBeVisible();
    // Optionally, hit backend /health via fetch from page context
  });
});

test.describe('Projects & Conversations', () => {
  test('U-Proj-01 create/select', async ({ page }) => {
    // Implement selectors per your App.tsx
  });
  test('U-Conv-01 new chat + send message', async ({ page }) => {
    // Select mode, send prompt, expect streaming completion
  });
});

test.describe('Docs Ingestion', () => {
  test('U-Docs-01 happy path', async ({ page }) => {
    // Open Docs tab, start ingestion, assert progress → completed
  });
});
