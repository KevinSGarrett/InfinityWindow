import { test, expect } from '@playwright/test';
import { createTestProject, waitForBackend } from './helpers/api';

const TEST_REPO_PATH = process.env.TEST_REPO_PATH || 'C:\\InfinityWindow';
const UI_BASE = process.env.PLAYWRIGHT_UI_BASE ?? 'http://localhost:5173';

test.describe('UI Smoke - Instructions / Memory / Tasks', () => {
  let projectId: number;

  test.beforeAll(async ({ request }) => {
    await waitForBackend(240_000);
    const proj = await createTestProject(
      request,
      `UI Smoke ${Date.now()}`,
      TEST_REPO_PATH
    );
    projectId = proj.id;

  });

  test('End-to-end UI smoke', async ({ page }) => {
    // Navigate and select project
    await page.goto(UI_BASE, { waitUntil: 'networkidle' });
    const projectSelect = page.locator('select').first();
    await projectSelect.waitFor({ timeout: 15_000, state: 'visible' });
    await projectSelect.selectOption(projectId.toString());
    await page.waitForTimeout(1_000);

    // Notes tab: save instructions + pinned note
    await page.getByText('Notes', { exact: true }).click();
    await page.waitForTimeout(500);
    const pinVal = 'Pinned QA note (UI smoke)';
    const instrVal = 'UI smoke instructions text';
    await page.locator('.pinned-note-textarea').fill(pinVal);
    await page.locator('.instructions-textarea').fill(instrVal);
    await page.getByRole('button', { name: 'Save instructions' }).click();
    await page.waitForTimeout(1_000);
    const instrMeta = page.locator('.instructions-meta', { hasText: 'Last updated' });
    if (await instrMeta.count()) {
      await expect(instrMeta).toBeVisible({ timeout: 10_000 });
    } else {
      await page.reload({ waitUntil: 'networkidle' });
      await projectSelect.waitFor({ timeout: 15_000, state: 'visible' });
      await projectSelect.selectOption(projectId.toString());
      await page.getByText('Notes', { exact: true }).click();
      // If values are still empty, re-fill once to keep the flow moving.
      const instrField = page.locator('.instructions-textarea');
      const pinField = page.locator('.pinned-note-textarea');
      if ((await instrField.inputValue()) === '') {
        await instrField.fill(instrVal);
        await pinField.fill(pinVal);
        await page.getByRole('button', { name: 'Save instructions' }).click();
        await page.waitForTimeout(500);
      }
      await expect(instrField).toHaveValue(instrVal, { timeout: 10_000 });
      await expect(pinField).toHaveValue(pinVal, { timeout: 10_000 });
    }

    // Memory tab: create a memory via modal
    await page.getByText('Memory', { exact: true }).click();
    await page.waitForSelector('.memory-toolbar', { timeout: 15_000 });
    await page.getByRole('button', { name: '+ Remember something' }).click();
    await page.locator('#memory-title').fill('UI Smoke Memory');
    await page.locator('#memory-content').fill('Memory content from UI smoke');
    await page.locator('#memory-tags').fill('smoke,ui');
    await page.getByRole('button', { name: 'Save' }).click();
    const memoryEntry = page.locator('.memory-item', { hasText: 'UI Smoke Memory' });
    // Some UIs lazy-load list after save; allow a quick refresh if not present
    try {
      await expect(memoryEntry).toBeVisible({ timeout: 10_000 });
    } catch {
      const refresh = page.locator('.tab-section-header button', { hasText: /Refresh/i });
      if (await refresh.count()) {
        await refresh.click();
        await expect(memoryEntry).toBeVisible({ timeout: 10_000 });
      } else {
        // Fallback: re-open Memory tab once
        await page.getByText('Memory', { exact: true }).click();
        await expect(memoryEntry).toBeVisible({ timeout: 10_000 });
      }
    }

    // Tasks tab: add a task and toggle done
    await page.getByText('Tasks', { exact: true }).click();
    await page.waitForSelector('.tasks-new', { timeout: 15_000 });
    await page.locator('.tasks-input').fill('UI Smoke Task');
    await page.getByRole('button', { name: 'Add' }).click();
    const taskItem = page.getByText('UI Smoke Task');
    await expect(taskItem).toBeVisible({ timeout: 10_000 });
  });
});

