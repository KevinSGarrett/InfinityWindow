import { test, expect } from '@playwright/test';
import { API_BASE, UI_BASE, DEFAULT_TEST_REPO_PATH } from './helpers/api';

test('usage filters and exports', async ({ page, request }) => {
  const projectName = `UsageFilters_${Date.now()}`;
  const projectResp = await request.post(`${API_BASE}/projects`, {
    data: { name: projectName, local_root_path: DEFAULT_TEST_REPO_PATH },
  });
  expect(projectResp.ok()).toBeTruthy();
  const projectId = (await projectResp.json()).id;

  const convResp = await request.post(`${API_BASE}/conversations`, {
    data: { project_id: projectId, title: 'Usage Filters Conv' },
  });
  expect(convResp.ok()).toBeTruthy();
  const conversationId = (await convResp.json()).id;

  // Seed recent task actions with different actions/models
  const seeds = [
    { description: 'Add task', action: 'auto_added', confidence: 0.9, model: 'gpt-5-nano' },
    { description: 'Complete task', action: 'auto_completed', confidence: 0.85, model: 'gpt-4o-mini' },
    { description: 'Suggest task', action: 'auto_suggested', confidence: 0.65, model: 'gpt-5.1-pro' },
    { description: 'Dismiss suggestion', action: 'auto_dismissed', confidence: 0.55, model: 'gpt-4o-mini' },
  ];
  for (const seed of seeds) {
    const seedResp = await request.post(`${API_BASE}/debug/seed_task_action`, {
      data: { project_id: projectId, ...seed },
    });
    expect(seedResp.ok()).toBeTruthy();
  }

  await page.goto(UI_BASE);
  await page.waitForLoadState('networkidle');

  // Select project
  await page.locator('.project-selector select').selectOption(String(projectId));

  // Go to Usage tab
  await page.getByRole('tab', { name: 'Usage' }).click();
  const usagePanel = page.locator('.usage-panel');
  await usagePanel.waitFor({ timeout: 15000 });

  // Select conversation and load telemetry
  await page
    .locator('select[aria-label="Select conversation for usage"]')
    .selectOption(String(conversationId));
  const useCurrentChat = page.getByRole('button', { name: 'Use current chat' });
  if (await useCurrentChat.isVisible()) {
    await useCurrentChat.click();
  }

  // Wait for telemetry list
  const actionsList = page.locator('[data-testid="recent-actions-list"] li');
  await expect(actionsList.first()).toBeVisible({ timeout: 15000 });
  const initialCount = await actionsList.count();
  expect(initialCount).toBeGreaterThan(0);

  // Time filter should cap list
  await page.getByLabel('Time filter').selectOption('last5');
  const last5Count = await actionsList.count();
  expect(last5Count).toBeLessThanOrEqual(5);

  // Action filter narrows to auto_added
  await page.getByLabel('Action filter').selectOption('auto_added');
  const autoAddedCount = await actionsList.count();
  expect(autoAddedCount).toBeGreaterThan(0);
  expect(autoAddedCount).toBeLessThanOrEqual(last5Count);

  // Model filter narrows to gpt-4o-mini
  await page.getByLabel('Model filter').selectOption('gpt-4o-mini');
  const modelFilteredCount = await actionsList.count();
  expect(modelFilteredCount).toBeGreaterThan(0);
  expect(modelFilteredCount).toBeLessThanOrEqual(autoAddedCount);

  // Usage time window (records) should not throw and keeps list visible
  await page.getByLabel('Usage records window').selectOption('24h');
  await expect(actionsList.first()).toBeVisible();

  // Exports clickable
  await page.getByRole('button', { name: 'Copy JSON' }).first().click();
  await page.getByRole('button', { name: 'Copy CSV' }).first().click();

  // Basic sanity after filters
  await expect(actionsList.first()).toBeVisible();

  // Cleanup
  await request.delete(`${API_BASE}/projects/${projectId}`);
});
