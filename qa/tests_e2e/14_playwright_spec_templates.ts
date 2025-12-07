import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import {
  createTestProject,
  waitForBackend,
} from '../../frontend/tests/helpers/api';

const UI_BASE = process.env.PLAYWRIGHT_UI_BASE ?? 'http://localhost:5173';
const TEST_REPO_PATH = process.env.TEST_REPO_PATH || 'C:\\InfinityWindow_QA';
const TEST_OUT_DIR = process.env.TEST_OUT_DIR;

test.describe('InfinityWindow – Smoke', () => {
  let projectId: number;

  test.beforeAll(async ({ request }) => {
    await waitForBackend(120_000);
    const proj = await createTestProject(
      request,
      `QA UI Smoke ${Date.now()}`,
      TEST_REPO_PATH
    );
    projectId = proj.id;
  });

  test('S-001 Health & App boot', async ({ page }) => {
    await page.goto(UI_BASE, { waitUntil: 'networkidle' });
    await expect(page.getByText(/InfinityWindow/i)).toBeVisible();
  });

  test('U-Proj-01 select project + update notes/memory/tasks', async ({ page }) => {
    await page.goto(UI_BASE, { waitUntil: 'networkidle' });
    const projectSelect = page.locator('select').first();
    await projectSelect.waitFor({ timeout: 15_000, state: 'visible' });
    await projectSelect.selectOption(projectId.toString());
    await page.waitForTimeout(1_000);

    // Notes tab: instructions + pinned note
    await page.getByText('Notes', { exact: true }).click();
    await page.locator('.pinned-note-textarea').fill('Pinned QA note');
    await page.locator('.instructions-textarea').fill('QA instructions text');
    await page.getByRole('button', { name: 'Save instructions' }).click();
    await expect(
      page.locator('.instructions-meta', { hasText: 'Last updated' })
    ).toBeVisible({ timeout: 15_000 });

    // Memory tab: create memory item
    await page.getByText('Memory', { exact: true }).click();
    await page.getByRole('button', { name: '+ Remember something' }).click();
    await page.locator('#memory-title').fill('QA memory item');
    await page.locator('#memory-content').fill('Memory created during QA smoke');
    await page.locator('#memory-tags').fill('qa,smoke');
    await page.getByRole('button', { name: 'Save' }).click();
    await expect(page.getByText('QA memory item')).toBeVisible({
      timeout: 10_000,
    });

    // Tasks tab: add a task
    await page.getByText('Tasks', { exact: true }).click();
    await page.locator('.tasks-input').fill('QA smoke task');
    await page.getByRole('button', { name: 'Add' }).click();
    await expect(page.getByText('QA smoke task')).toBeVisible({
      timeout: 10_000,
    });

    // Accessibility scan on the main UI surface
    const axe = await new AxeBuilder({ page }).analyze();
    if (TEST_OUT_DIR) {
      const outPath = join(TEST_OUT_DIR, 'a11y', 'axe-results.json');
      mkdirSync(dirname(outPath), { recursive: true });
      writeFileSync(outPath, JSON.stringify(axe, null, 2));
    }
    const critical = axe.violations.filter((v) => v.impact === 'critical');
    expect(critical.length).toBe(0);
  });
});

