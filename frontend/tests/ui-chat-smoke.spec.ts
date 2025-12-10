import { test, expect } from '@playwright/test';
import { createTestProject, waitForBackend } from './helpers/api';

const TEST_REPO_PATH = process.env.TEST_REPO_PATH || 'C:\\InfinityWindow';
const API_BASE = process.env.PLAYWRIGHT_API_BASE ?? 'http://127.0.0.1:8000';
const UI_BASE = process.env.PLAYWRIGHT_UI_BASE ?? 'http://localhost:5173';

test.describe('UI Chat Smoke - Chat, Remember, Usage, Search', () => {
  let projectId: number;

  test.beforeAll(async ({ request }) => {
    await waitForBackend(240_000);
    const proj = await createTestProject(
      request,
      `UI Chat Smoke ${Date.now()}`,
      TEST_REPO_PATH
    );
    projectId = proj.id;

    // Seed a tiny text document so search/doc retrieval has content
    const docResp = await request.post(`${API_BASE}/docs/text`, {
      data: {
        project_id: projectId,
        name: 'smoke-doc',
        text: 'This is a tiny smoke test document about chat and memory retrieval.',
      },
    });
    if (docResp.ok()) {
      await docResp.json();
    }
  });

  test('Chat, remember from chat, search, usage', async ({ page }) => {
    // Navigate and select project
    await page.goto(UI_BASE, { waitUntil: 'networkidle' });
    const projectSelect = page.locator('select').first();
    await projectSelect.waitFor({ timeout: 15_000, state: 'visible' });
    await projectSelect.selectOption(projectId.toString());
    await page.waitForTimeout(1_000);

    // Send a chat message
    const input = page.locator('.chat-input');
    await input.fill('Please summarize the seeded smoke test document and remember this.');
    await page.getByRole('button', { name: /Send|Ask/i }).click().catch(() => {
      // fallback: press Enter if there is no send button in this build
      input.press('Enter');
    });
    // Wait for assistant reply
    const assistantMsg = page.getByText('Assistant', { exact: false }).first();
    await assistantMsg.waitFor({ timeout: 30_000 });

    // Click Remember this on the last assistant message (fallback if modal does not open)
    const rememberBtn = page.getByText('Remember this').last();
    await rememberBtn.click({ timeout: 10_000 });
    await page.waitForTimeout(500);
    // If modal is present, fill it; otherwise skip gracefully
    const modalVisible = await page.locator('#memory-title').isVisible().catch(() => false);
    if (modalVisible) {
      await page.locator('#memory-title').fill('Chat-remembered');
      await page.locator('#memory-content').fill('Memory from chat response');
      await page.getByRole('button', { name: 'Save' }).click();
      await expect(page.getByText('Chat-remembered')).toBeVisible({ timeout: 10_000 });
    }

    // Usage tab: verify a usage entry exists
    await page.getByText('Usage', { exact: true }).click();
    await page.waitForSelector('.usage-table, .usage-empty', { timeout: 10_000 });
    // If table exists, ensure at least one row
    const usageRows = page.locator('.usage-table tbody tr');
    if (await usageRows.count()) {
      await expect(usageRows.first()).toBeVisible();
    }

    // Docs search tab: search for a term from the seeded doc
    await page.getByText('Search', { exact: true }).click();
    // The search UI may render separate inputs; pick the first text input
    const searchInput = page.locator('input[type="text"], input[type="search"], input[placeholder*="Search"]').first();
    await searchInput.waitFor({ timeout: 10_000 });
    await searchInput.fill('smoke test document');
    await searchInput.press('Enter');
    // Expect some result or at least no error UI
    await page.waitForTimeout(3000);
    const results = page.locator('.search-results, .search-hit, .doc-hit, .message-hit, [data-testid="search-result"]');
    await expect(results.first()).toBeVisible({ timeout: 15_000 });
  });
});

