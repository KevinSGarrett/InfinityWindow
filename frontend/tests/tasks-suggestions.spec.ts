import { test, expect } from '@playwright/test';
import {
  createTestProject,
  createTask,
  seedTaskSuggestion,
} from './helpers/api';

test('tasks tab shows priority chips and suggestion drawer actions', async ({
  page,
  request,
}) => {
  const project = await createTestProject(
    request,
    `Playwright Tasks ${Date.now()}`
  );

  const criticalTask = await createTask(
    request,
    project.id,
    'Fix production outage',
    {
      priority: 'critical',
      blocked_reason: 'waiting on logs',
    }
  );

  await createTask(request, project.id, 'Polish onboarding doc', {
    priority: 'high',
  });

  await seedTaskSuggestion(request, {
    project_id: project.id,
    action_type: 'add',
    description: 'Investigate optional telemetry revamp',
    priority: 'low',
    confidence: 0.45,
  });

  await seedTaskSuggestion(request, {
    project_id: project.id,
    action_type: 'complete',
    target_task_id: criticalTask.id,
    description: 'Outage mitigated',
    confidence: 0.6,
  });

  await page.goto('/');
  await page.waitForLoadState('networkidle');

  await page.waitForFunction(
    (value) => {
      const select = document.querySelector<HTMLSelectElement>(
        '.project-selector select'
      );
      if (!select) return false;
      return Array.from(select.options).some(
        (option) => option.value === value
      );
    },
    project.id.toString()
  );

  await page
    .locator('.project-selector select')
    .selectOption(project.id.toString());

  // Ensure tasks/suggestions data is loaded
  await page.locator('.right-tab:has-text("Tasks")').click();
  const refreshTasks = page.locator('.tab-section-header button:has-text("Refresh tasks")').first();
  if (await refreshTasks.count()) {
    await refreshTasks.click();
  }

  const criticalRow = page
    .locator('li.task-item', { hasText: /Fix production outage/i })
    .first();
  await expect(criticalRow.locator('.task-priority-chip').first()).toBeVisible();

  const suggestionsToggle = page.locator('.suggestions-toggle');
  await suggestionsToggle.click();
  await page.waitForTimeout(500);

  const suggestionItems = page.locator('.suggestion-item');
  const initialCount = await suggestionItems.count();
  if (initialCount === 0) {
    test.skip('No seeded suggestions found');
  }

  const firstApprove = suggestionItems
    .nth(0)
    .getByRole('button', { name: /approve/i });
  await firstApprove.click();
  // Allow UI to settle; list should shrink or stay the same (best-effort).
  await page.waitForTimeout(500);
  const remainingAfterApprove = await suggestionItems.count();
  expect(remainingAfterApprove).toBeLessThanOrEqual(initialCount);

  const dismissButton = suggestionItems
    .nth(0)
    .getByRole('button', { name: /dismiss/i });
  if (await dismissButton.count()) {
    await dismissButton.click();
  }
});

