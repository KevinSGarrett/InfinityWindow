import { test, expect } from '@playwright/test';
import {
  createTestProject,
  createTask,
  seedTaskSuggestion,
  waitForBackend,
} from './helpers/api';

test.describe('Tasks review queue metadata and filters', () => {
  test('renders metadata, filters, and handles read-only errors', async ({
    page,
    request,
  }) => {
    await waitForBackend();
    const project = await createTestProject(
      request,
      `Review Queue ${Date.now()}`
    );

    const blockerTask = await createTask(
      request,
      project.id,
      'Playwright dependency task',
      { priority: 'critical', blocked_reason: 'waiting on upstream' }
    );

    await seedTaskSuggestion(request, {
      project_id: project.id,
      action_type: 'add',
      description: 'Seeded add suggestion with low confidence',
      priority: 'high',
      blocked_reason: 'Blocked by #123',
      confidence: 0.42,
    });

    await seedTaskSuggestion(request, {
      project_id: project.id,
      action_type: 'complete',
      target_task_id: blockerTask.id,
      description: 'Complete the dependency task',
      confidence: 0.78,
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await page.waitForSelector('.project-selector select');
    await page
      .locator('.project-selector select')
      .selectOption(project.id.toString());

    const tasksTab = page.locator('.right-tab:has-text("Tasks")');
    await tasksTab.click();
    const refreshAll = page
      .locator('.right-tabs-toolbar button')
      .filter({ hasText: 'Refresh all' })
      .first();
    if (await refreshAll.count()) {
      await refreshAll.click();
    }

    const suggestionsToggle = page.locator('.suggestions-toggle');
    await suggestionsToggle.click();
    await page.waitForTimeout(300);

    const suggestionItems = page.getByTestId('review-queue-item');
    await expect(suggestionItems.first()).toBeVisible({ timeout: 15000 });

    const reason = page.getByTestId('review-queue-reason').first();
    await expect(reason).toBeVisible();
    await expect(reason).toHaveText(/blocked|confidence/i);

    await expect(
      suggestionItems.first().locator('.suggestion-confidence')
    ).toContainText(/conf/i);
    await expect(
      suggestionItems.first().locator('.task-priority-chip')
    ).toBeVisible();

    await page
      .getByTestId('review-queue-filter-action')
      .selectOption('add');
    await expect(suggestionItems).toHaveCount(1);
    await expect(
      suggestionItems.first().locator('.suggestion-pill')
    ).toHaveText(/add/i);

    await page
      .getByTestId('review-queue-filter-action')
      .selectOption('complete');
    await expect(suggestionItems).toHaveCount(1);
    await expect(
      suggestionItems.first().locator('.suggestion-pill')
    ).toHaveText(/complete/i);

    await page
      .getByTestId('review-queue-filter-action')
      .selectOption('all');

    const initialCount = await suggestionItems.count();
    await suggestionItems
      .first()
      .getByRole('button', { name: /approve/i })
      .click();
    await page.waitForTimeout(800);
    const afterApproveCount = await suggestionItems.count();
    expect(afterApproveCount).toBeLessThanOrEqual(initialCount);
    expect(afterApproveCount).toBeGreaterThanOrEqual(
      Math.max(0, initialCount - 1)
    );

    let archivedIntercepted = false;
    await page.route('**/task_suggestions/*/dismiss', async (route) => {
      if (!archivedIntercepted) {
        archivedIntercepted = true;
        await route.fulfill({
          status: 403,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Project is archived for edits' }),
        });
        return;
      }
      await route.continue();
    });

    const remainingItem = page.getByTestId('review-queue-item').first();
    const dismissButton = remainingItem.getByRole('button', {
      name: /dismiss/i,
    });
    await dismissButton.click();
    await expect(page.locator('.toast.error').first()).toContainText(
      /archived|read-only/i
    );
    await expect(page.locator('.read-only-banner').first()).toContainText(
      /archived|read-only/i
    );
    await expect(dismissButton).toBeDisabled();
  });
});

