import { test, expect } from '@playwright/test';
import { createTestProject } from './helpers/api';

const API = process.env.PLAYWRIGHT_API_BASE ?? 'http://127.0.0.1:8000';
const APP = process.env.PLAYWRIGHT_UI_BASE ?? 'http://localhost:5173';

test.describe('Files tab and repo ingestion UX', () => {
  test('shows an error banner when local_root_path is missing/invalid', async ({ page, request }) => {
    const badRoot = process.platform === 'win32' ? 'Z:\\\\definitely-not-there' : '/no/such/path';
    const project = await createTestProject(request, `FS_Invalid_${Date.now()}`, badRoot);

    await page.goto(APP, { waitUntil: 'networkidle' });
    const projectSelect = page.locator('.project-selector select');
    await projectSelect.waitFor({ timeout: 15000, state: 'visible' });
    await projectSelect.selectOption(String(project.id));

    await page.getByRole('tab', { name: 'Files' }).click();

    const errorBanner = page.getByTestId('files-error-banner');
    await expect(errorBanner).toBeVisible({ timeout: 15000 });
    await expect(errorBanner).toContainText('project', { timeout: 15000 });

    await expect(page.locator('[data-testid="files-root-list"]')).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Go to project root' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Retry' })).toBeVisible();
  });

  test('renders file list and no error banner for valid local_root_path', async ({ page, request }) => {
    const project = await createTestProject(request, `FS_Valid_${Date.now()}`);

    await page.goto(APP, { waitUntil: 'networkidle' });
    const projectSelect = page.locator('.project-selector select');
    await projectSelect.waitFor({ timeout: 15000, state: 'visible' });
    await projectSelect.selectOption(String(project.id));

    await page.getByRole('tab', { name: 'Files' }).click();

    const rootList = page.locator('[data-testid="files-root-list"]');
    await rootList.first().waitFor({ state: 'visible', timeout: 15000 });
    await expect(rootList).toBeVisible();
    await expect(rootList.locator('li').first()).toBeVisible();
    await expect(page.getByTestId('files-error-banner')).toHaveCount(0);
  });

  test('repo ingestion surfaces backend error detail', async ({ page, request }) => {
    const missingRoot = process.platform === 'win32' ? 'Z:\\\\missing-root' : '/definitely/not/here';
    const project = await createTestProject(request, `Repo_Ingest_Fail_${Date.now()}`, missingRoot);

    await page.goto(APP, { waitUntil: 'networkidle' });
    const projectSelect = page.locator('.project-selector select');
    await projectSelect.waitFor({ timeout: 15000, state: 'visible' });
    await projectSelect.selectOption(String(project.id));

    // Ingestion UI lives in Docs tab
    await page.getByRole('tab', { name: 'Docs' }).click();

    await page.getByLabel('Repository root path').fill(missingRoot);
    await page.getByLabel('Repository name prefix').fill('BadRepo/');
    await page.getByRole('button', { name: 'Ingest repo' }).click();

    const ingestError = page.getByTestId('repo-ingest-error-banner');
    await expect(ingestError).toBeVisible({ timeout: 15000 });
    await expect(ingestError).toContainText('local_root_path', { timeout: 15000 });
  });
});

