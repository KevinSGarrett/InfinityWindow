import { test, expect } from '@playwright/test';
import {
  addDecision,
  createTestProject,
  setProjectInstructions,
} from './helpers/api';

test('decisions filters and pinned note diff are visible', async ({
  page,
  request,
}) => {
  const project = await createTestProject(request, `NotesFilters_${Date.now()}`);
  const projectId = project.id.toString();
  const pinnedNote = 'Keep PRs under 400 lines; block risky deploys.';
  const instructions = 'Base instructions for the notes UI Playwright check.';

  await setProjectInstructions(request, project.id, instructions, pinnedNote);
  await addDecision(
    request,
    project.id,
    'Architecture guardrails',
    'Ensure services stay modular.',
    { status: 'recorded', category: 'Architecture', tags: ['backend'] }
  );
  await addDecision(
    request,
    project.id,
    'Process review',
    'QA signoff required for risky changes.',
    { status: 'in-review', category: 'Process', tags: ['qa'] }
  );

  try {
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

    await page.locator('.project-selector select').selectOption(projectId);
    await page.getByRole('tab', { name: /^Notes$/ }).click();

    await expect(page.locator('#pinned-note-textarea')).toHaveValue(pinnedNote);

    const decisionItems = page.locator('.decision-item');
    await decisionItems.first().waitFor({ state: 'visible', timeout: 15000 });

    await page
      .getByLabel('Filter decisions by status')
      .selectOption('in-review');
    await expect(decisionItems.filter({ hasText: 'Process review' })).toHaveCount(1);
    await expect(
      decisionItems.filter({ hasText: 'Architecture guardrails' })
    ).toHaveCount(0);

    await page.getByLabel('Filter decisions by status').selectOption('all');
    await page
      .getByLabel('Filter decisions by category')
      .selectOption('Architecture');
    await expect(
      decisionItems.filter({ hasText: 'Architecture guardrails' })
    ).toHaveCount(1);

    await page.locator('.instructions-textarea').fill(`${instructions} (edit)`);
    await expect(page.locator('.instructions-diff')).toBeVisible();
    await page.locator('.instructions-diff summary').click();
    const diffBlocks = page.locator('.instructions-diff-block');
    await expect(diffBlocks.nth(0)).toContainText(pinnedNote);
    await expect(diffBlocks.nth(1)).toContainText(instructions);
  } finally {
    await request.delete(`${process.env.PLAYWRIGHT_API_BASE ?? 'http://127.0.0.1:8000'}/projects/${project.id}`);
  }
});

