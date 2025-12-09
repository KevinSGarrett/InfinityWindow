import { test, expect } from '@playwright/test';
import { createTestProject } from './helpers/api';

const UI_BASE = process.env.PLAYWRIGHT_UI_BASE ?? 'http://localhost:5173';

test.describe('Files tab local_root_path UX', () => {
  test('shows error banner when local_root_path is missing/invalid', async ({ page, request }) => {
    const badRoot = process.platform === 'win32' ? 'Z:\\\\definitely-not-there' : '/no/such/path';
    const resp = await request.post('http://127.0.0.1:8000/projects', {
      data: {
        name: `NoRoot_${Date.now()}`,
        local_root_path: badRoot,
      },
    });
    expect(resp.ok()).toBeTruthy();
    const projectId = (await resp.json()).id;

    await page.goto(UI_BASE, { waitUntil: 'networkidle' });
    const projectSelect = page.locator('.project-selector select');
    await projectSelect.waitFor({ timeout: 15000, state: 'visible' });
    await projectSelect.selectOption(String(projectId));

    await page.getByRole('tab', { name: 'Files' }).click();

    const errorBanner = page.getByTestId('files-error-banner');
    await expect(errorBanner).toBeVisible({ timeout: 10000 });
    await expect(errorBanner).toContainText('project folder', { timeout: 10000 });

    // Error banner should be present and list should not render
    await expect(page.locator('[data-testid="files-root-list"]')).toHaveCount(0);

    await expect(page.getByRole('button', { name: 'Go to project root' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Retry' })).toBeVisible();
  });

  test('shows file listing with no error banner when local_root_path is valid', async ({ page, request }) => {
    const project = await createTestProject(request, `FilesHappy_${Date.now()}`);

    await page.goto(UI_BASE, { waitUntil: 'networkidle' });
    const projectSelect = page.locator('.project-selector select');
    await projectSelect.waitFor({ timeout: 15000, state: 'visible' });
    await projectSelect.selectOption(String(project.id));

    await page.getByRole('tab', { name: 'Files' }).click();

    const rootList = page.locator('[data-testid="files-root-list"]');
    await rootList.first().waitFor({ state: 'visible', timeout: 15000 });
    await expect(rootList).toBeVisible();

    await expect(page.getByTestId('files-error-banner')).toHaveCount(0);

    // Ensure at least one entry is visible
    await expect(rootList.locator('li').first()).toBeVisible();
  });
});

