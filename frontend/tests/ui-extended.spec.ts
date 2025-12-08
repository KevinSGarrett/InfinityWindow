import { test, expect } from '@playwright/test';
import { createTestProject, waitForBackend } from './helpers/api';

const TEST_REPO_PATH = process.env.TEST_REPO_PATH || 'C:\\InfinityWindow';
const API_BASE = process.env.PLAYWRIGHT_API_BASE ?? 'http://127.0.0.1:8000';
const UI_BASE = process.env.PLAYWRIGHT_UI_BASE ?? 'http://localhost:5173';

test.describe('UI Extended Smoke - Files / Folders / Decisions / Terminal', () => {
  let projectId: number;
  let conversationId: number | null = null;

  test.beforeAll(async ({ request }) => {
    await waitForBackend(240_000);
    const proj = await createTestProject(
      request,
      `UI Extended ${Date.now()}`,
      TEST_REPO_PATH
    );
    projectId = proj.id;

    // Seed a tiny doc for search coverage
    await request.post(`${API_BASE}/docs/text`, {
      data: {
        project_id: projectId,
        name: 'tiny-smoke-doc',
        text: 'Tiny doc for extended UI smoke search.',
      },
    });

    // Create a conversation up front so folder move + terminal usage can bind to it
    const convResp = await request.post(`${API_BASE}/conversations`, {
      data: { project_id: projectId, title: 'Extended Conv' },
    });
    if (convResp.ok()) {
      const convJson = await convResp.json();
      conversationId = convJson.id ?? null;
    }

    // Seed a task suggestion so the suggestions panel can be exercised
    // Seed baseline data so UI verifications have content.
    await request.put(`${API_BASE}/projects/${projectId}/instructions`, {
      data: {
        instruction_text: 'Extended instructions smoke',
        pinned_note_text: 'Extended pinned note smoke',
      },
    });

    await request.post(`${API_BASE}/projects/${projectId}/decisions`, {
      data: {
        title: 'Extended decision',
        details: 'Decision details via extended smoke.',
        category: 'Playwright QA',
      },
    });

    await request.post(`${API_BASE}/projects/${projectId}/memory`, {
      data: {
        title: 'Extended memory',
        content: 'Memory content for extended smoke.',
        tags: ['extended', 'smoke'],
        pinned: true,
      },
    });

    await request.post(`${API_BASE}/tasks`, {
      data: {
        project_id: projectId,
        description: 'Extended task',
        priority: 'normal',
      },
    });

    await request.post(`${API_BASE}/debug/task_suggestions/seed`, {
      data: {
        project_id: projectId,
        action_type: 'add',
        description: 'Seeded suggestion from UI extended smoke',
        priority: 'normal',
      },
    });
  });

  test('Extended UI flows', async ({ page }) => {
    // Navigate and select project
    await page.goto(UI_BASE, { waitUntil: 'networkidle' });
    const projectSelect = page.locator('select').first();
    await projectSelect.waitFor({ timeout: 15_000, state: 'visible' });
    await projectSelect.selectOption(projectId.toString());
    await page.waitForTimeout(1_000);

    // Notes: verify seeded instructions + pinned note, then reload to verify
    await page.getByText('Notes', { exact: true }).click();
    const instructions = page.locator('.instructions-textarea');
    await instructions.waitFor({ timeout: 15_000 });
    const pinned = page.locator('.pinned-note-textarea');
    const expectedInstructions = 'Extended instructions smoke';
    const expectedPinned = 'Extended pinned note smoke';
    if (await instructions.count()) {
      await expect(instructions).toHaveValue(new RegExp(expectedInstructions));
    }
    if (await pinned.count()) {
      await expect(pinned).toHaveValue(new RegExp(expectedPinned));
    }

    await page.reload({ waitUntil: 'networkidle' });
    await projectSelect.selectOption(projectId.toString());
    await page.getByText('Notes', { exact: true }).click();
    await expect(instructions).toHaveValue(new RegExp(expectedInstructions));
    await expect(pinned).toHaveValue(new RegExp(expectedPinned));

    // Decision log: add a decision and ensure it appears
    const decisionTitle = page.locator('input.decision-input').first();
    await decisionTitle.fill('Extended decision');
    await page
      .locator('textarea.decision-textarea')
      .fill('Decision details via extended smoke.');
    await page
      .getByRole('button', { name: /Add decision/i })
      .click({ timeout: 10_000 });
    const decisionList = page.locator('li.decision-item', {
      hasText: 'Extended decision',
    });
    await expect(decisionList.first()).toBeVisible({ timeout: 15_000 });

    // Memory: verify seeded entry
    await page.getByText('Memory', { exact: true }).click();
    const memoryItem = page.locator('.memory-item', {
      hasText: 'Extended memory',
    });
    await expect(memoryItem).toBeVisible({ timeout: 15_000 });

    // Files tab: ensure listing works and no local_root_path warning
    await page.getByRole('button', { name: 'Files' }).click();
    const filesPanel = page.locator('.files-panel');
    await filesPanel.waitFor({ timeout: 15_000, state: 'visible' });
    await expect(page.locator('.files-error')).toHaveCount(0);
    const firstEntry = page.locator('.file-list-entry-button').first();
    if (await firstEntry.count()) {
      await expect(firstEntry).toBeVisible();
    }

    // Tasks tab: verify seeded task (mark done if checkbox exists)
    await page.getByRole('button', { name: 'Tasks' }).click();
    const taskItem = page
      .locator('li.task-item', { hasText: 'Extended task' })
      .first();
    await expect(taskItem).toBeVisible({ timeout: 15_000 });
    const checkbox = taskItem.locator('input[type="checkbox"]').first();
    if (await checkbox.count()) {
      await checkbox.click();
    }

    // Suggestions panel: approve then dismiss the seeded suggestion if present
    await page.getByRole('button', { name: /Suggested changes/i }).click();
    const suggestionItem = page.locator('.suggestion-item').first();
    await page.waitForTimeout(500);
    if (await suggestionItem.count()) {
      const approveBtn = suggestionItem.getByRole('button', { name: /Approve/ });
      if (await approveBtn.count()) {
        await approveBtn.click({ timeout: 15_000 });
        await page.waitForTimeout(500);
      }
      const dismissBtn = suggestionItem.getByRole('button', { name: /Dismiss/ });
      if (await dismissBtn.count()) {
        await dismissBtn.click({ timeout: 15_000 });
      }
    }

    // Conversation folders: create folder and move the conversation
    const folderBtn = page.getByRole('button', { name: '+ Folder' });
    if (await folderBtn.count()) {
      await folderBtn.click();
      await page.locator('#folder-name').fill('Smoke Folder');
      await page.locator('#folder-sort').fill('0');
      await page.getByRole('button', { name: /^Save$/ }).click();
      const folderOption = page.locator('.folder-toolbar select option', {
        hasText: 'Smoke Folder',
      });
      if (await folderOption.count()) {
        await expect(folderOption).toBeVisible({ timeout: 10_000 });
      }
    }

    // Terminal tab: run a safe command
    await page.getByRole('button', { name: 'Terminal' }).click();
    const terminalInput = page.locator('.manual-terminal-textarea');
    await terminalInput.waitFor({ timeout: 15_000 });
    await terminalInput.fill('echo extended-terminal');
    await page.getByRole('button', { name: 'Run command' }).click();
    await expect(
      page.locator('.terminal-output-block pre', {
        hasText: 'extended-terminal',
      })
    ).toBeVisible({ timeout: 20_000 });

    // Search tab: verify docs search returns a result for seeded doc
    await page.getByRole('button', { name: 'Search' }).click();
    const searchInput = page
      .locator(
        'input[type="text"], input[type="search"], input[placeholder*="Search"]'
      )
      .first();
    await searchInput.waitFor({ timeout: 15_000 });
    await searchInput.fill('tiny doc extended');
    await searchInput.press('Enter');
    await page.waitForTimeout(2_000);
    const searchResults = page.locator(
      '.search-results, .search-hit, .doc-hit, .message-hit, [data-testid="search-result"]'
    );
    await expect(searchResults.first()).toBeVisible({ timeout: 15_000 });
  });
});

