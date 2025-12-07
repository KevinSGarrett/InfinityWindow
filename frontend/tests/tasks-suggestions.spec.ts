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

  await expect(
    page.locator('.task-priority-chip', { hasText: /critical/i })
  ).toBeVisible();

  const suggestionsToggle = page.locator('.suggestions-toggle');
  await suggestionsToggle.click();

  const suggestionItems = page.locator('.suggestion-item');
  await expect(suggestionItems).toHaveCount(2);

  const firstApprove = suggestionItems
    .nth(0)
    .getByRole('button', { name: /approve/i });
  await firstApprove.click();
  await expect(suggestionItems).toHaveCount(1);

  const dismissButton = suggestionItems
    .nth(0)
    .getByRole('button', { name: /dismiss/i });
  await dismissButton.click();

  await expect(
    page.locator('.tasks-empty', { hasText: /No pending suggestions/i })
  ).toBeVisible();
});

