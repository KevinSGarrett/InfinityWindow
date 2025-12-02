import * as path from 'path';
import { test, expect } from '@playwright/test';
import { createTestProject } from './helpers/api';

test('files tab allows browsing and editing project files', async ({ page, request }) => {
  const repoRoot = path.resolve(process.cwd(), '..');
  const projectName = `Playwright Files ${Date.now()}`;
  const project = await createTestProject(request, projectName, repoRoot);
  const projectId = project.id.toString();

  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page
    .waitForFunction(
      (value) => {
        const select = document.querySelector<HTMLSelectElement>(
          '.project-selector select'
        );
        return (
          !!select &&
          Array.from(select.options).some((option) => option.value === value)
        );
      },
      projectId,
      { timeout: 30_000 }
    );
  await page
    .locator('.project-selector select')
    .selectOption(projectId);

  const tabs = page.locator('.right-tabs');
  await tabs.getByRole('button', { name: /^Files$/ }).click();

  const scratchEntry = page
    .locator('.file-list-entry-button')
    .filter({ hasText: 'scratch' });
  await scratchEntry.first().click();

  const notesEntry = page
    .locator('.file-list-entry-button')
    .filter({ hasText: 'test-notes.txt' });
  await notesEntry.first().click();

  const editor = page.locator('.file-editor-textarea');
  await expect(editor).toBeVisible();

  const showOriginalToggle = page
    .locator('.show-original-toggle input[type="checkbox"]')
    .first();
  await showOriginalToggle.check();
  await expect(page.locator('.file-original-box')).toBeVisible();

  await editor.type(' // playwright-edit');
  await expect(page.locator('.unsaved-indicator')).toBeVisible();
});

