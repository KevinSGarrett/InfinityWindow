import { test, expect } from '@playwright/test';

test('usage filters and exports', async ({ page, request }) => {
  const API = 'http://127.0.0.1:8000';
  const APP = 'http://localhost:5173/';

  // Seed data
  const projectName = `UsageFilters_${Date.now()}`;
  const projectResp = await request.post(`${API}/projects`, {
    data: { name: projectName, local_root_path: 'C:\\InfinityWindow' },
  });
  expect(projectResp.ok()).toBeTruthy();
  const projectId = (await projectResp.json()).id;

  const convResp = await request.post(`${API}/conversations`, {
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
    const seedResp = await request.post(`${API}/debug/seed_task_action`, {
      data: { project_id: projectId, ...seed },
    });
    expect(seedResp.ok()).toBeTruthy();
  }
  const manualSeed = {
    description: 'Manual checklist update',
    action: 'manual_review',
    confidence: 0.4,
    model: 'gpt-4o',
    source: 'manual',
  };
  const manualResp = await request.post(`${API}/debug/seed_task_action`, {
    data: { project_id: projectId, ...manualSeed },
  });
  expect(manualResp.ok()).toBeTruthy();

  await page.goto(APP);
  await page.waitForLoadState('networkidle');

  // Select project
  await page.locator('.project-selector select').selectOption(String(projectId));

  // Go to Usage tab
  await page.getByRole('tab', { name: 'Usage' }).click();

  // Select conversation and load telemetry
  await page.locator('select[aria-label="Select conversation for usage"]').selectOption(String(conversationId));
  await page.getByRole('button', { name: 'Use current chat' }).click();

  // Wait for telemetry list
  // Recent task action rows (li entries that display "conf")
  const actionsList = page.locator('ul.usage-telemetry-list li:has-text("conf")');
  await actionsList.first().waitFor({ state: 'visible' });
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

  // Reset action/model filters so source filter can show manual entries
  await page.getByLabel('Action filter').selectOption('all');
  await page.getByLabel('Model filter').selectOption('all');

  // Source filter hides or shows manual vs automatic
  await page.getByLabel('Action source filter').selectOption('automatic');
  await expect(
    actionsList.filter({ hasText: manualSeed.description })
  ).toHaveCount(0);
  await page.getByLabel('Action source filter').selectOption('manual');
  await expect(
    actionsList.filter({ hasText: manualSeed.description })
  ).toHaveCount(1);
  await expect(actionsList.filter({ hasText: 'Add task' })).toHaveCount(0);

  // Usage time window (records) should not throw and keeps list visible
  await page.getByLabel('Usage records window').selectOption('24h');
  await expect(actionsList.first()).toBeVisible();

  // Exports clickable
  await page.getByRole('button', { name: 'Copy JSON' }).first().click();
  await page.getByRole('button', { name: 'Copy CSV' }).first().click();

  // Basic sanity after filters
  await expect(actionsList.first()).toBeVisible();

  // Cleanup
  await request.delete(`${API}/projects/${projectId}`);
});

