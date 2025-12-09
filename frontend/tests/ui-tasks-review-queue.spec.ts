import { test, expect } from '@playwright/test';
import { createTestProject } from './helpers/api';

const API = process.env.PLAYWRIGHT_API_BASE ?? 'http://127.0.0.1:8000';
const APP = process.env.PLAYWRIGHT_UI_BASE ?? 'http://localhost:5173/';

test.describe('Tasks review queue', () => {
  test('low-confidence suggestions can be approved or dismissed', async ({ page, request }) => {
    const project = await createTestProject(request, `ReviewQueue_${Date.now()}`);

    // Seed two low-confidence suggestions
    const suggestions = [
      { description: 'Low confidence add', action_type: 'add', confidence: 0.4 },
      { description: 'Another low confidence add', action_type: 'add', confidence: 0.3 },
    ];
    for (const suggestion of suggestions) {
      const resp = await request.post(`${API}/debug/task_suggestions/seed`, {
        data: {
          project_id: project.id,
          ...suggestion,
        },
      });
      expect(resp.ok()).toBeTruthy();
    }

    await page.goto(APP, { waitUntil: 'networkidle' });
    const projectSelect = page.locator('.project-selector select');
    await projectSelect.waitFor({ timeout: 15000, state: 'visible' });
    await projectSelect.selectOption(String(project.id));

    await page.getByRole('tab', { name: 'Tasks' }).click();

    // Open Review queue
    const reviewBtn = page.getByRole('button', { name: /Review queue/i });
    await reviewBtn.click();

    const reviewList = page.locator('.suggestion-list .suggestion-item');
    await reviewList.first().waitFor({ state: 'visible', timeout: 15000 });
    expect(await reviewList.count()).toBeGreaterThanOrEqual(2);

    // Approve first suggestion
    const firstItem = reviewList.nth(0);
    await firstItem.getByRole('button', { name: /Approve/ }).click();
    await expect(firstItem).toBeHidden({ timeout: 15000 });

    // Dismiss second suggestion
    const secondItem = reviewList.nth(1);
    await secondItem.getByRole('button', { name: /Dismiss/ }).click();
    await expect(secondItem).toBeHidden({ timeout: 15000 });

    // Task list should now include the approved item
    const taskItem = page.locator('li.task-item', { hasText: 'Low confidence add' }).first();
    await expect(taskItem).toBeVisible({ timeout: 15000 });
  });
});

