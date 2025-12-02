import { test, expect } from '@playwright/test';
import {
  addDecision,
  addMemoryItem,
  createTestProject,
  setProjectInstructions,
} from './helpers/api';

test('notes tab displays seeded instructions and decisions', async ({
  page,
  request,
}) => {
  const projectName = `Playwright Notes ${Date.now()}`;
  const instructions = 'Always include PLAYWRIGHT-NOTES-TAG in replies.';
  const decisionTitle = 'Adopt playwright smoke tests';

  const project = await createTestProject(request, projectName);
  const projectId = project.id.toString();
  await setProjectInstructions(request, project.id, instructions);
  await addDecision(
    request,
    project.id,
    decisionTitle,
    'Documented via automated UI test.'
  );

  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.waitForFunction(
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
  await tabs.getByRole('button', { name: /^Notes$/ }).click();

  const instructionsArea = page.locator('.instructions-textarea');
  await expect(instructionsArea).toHaveValue(instructions);
  await expect(page.getByText(decisionTitle, { exact: true })).toBeVisible();
});

test('memory tab shows seeded memory item', async ({ page, request }) => {
  const projectName = `Playwright Memory ${Date.now()}`;
  const memoryTitle = 'PLAYWRIGHT_MEMORY_TITLE';

  const project = await createTestProject(request, projectName);
  const projectId = project.id.toString();
  await addMemoryItem(
    request,
    project.id,
    memoryTitle,
    'Seeded via Playwright helper.'
  );

  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.waitForFunction(
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
  await tabs.getByRole('button', { name: /^Memory$/ }).click();

  await expect(
    page.getByRole('button', { name: /\+ Remember something/ })
  ).toBeVisible();
  await expect(
    page.locator('.memory-item-title', { hasText: memoryTitle })
  ).toBeVisible();
  await expect(
    page.locator('.memory-item').filter({ hasText: memoryTitle }).locator('.memory-pill')
  ).toHaveText(/Pinned/);
});

