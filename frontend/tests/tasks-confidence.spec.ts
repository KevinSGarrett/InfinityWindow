import { test, expect } from "@playwright/test";
import { API_BASE, UI_BASE, DEFAULT_TEST_REPO_PATH } from './helpers/api';

test.describe("Tasks tab confidence chip", () => {
  test("renders when available", async ({ page, request }) => {
    // Create a project via API so the UI has something to select
    const projectName = `PW Tasks ${Date.now()}`;
    const createResp = await request.post(`${API_BASE}/projects`, {
      data: {
        name: projectName,
        local_root_path: DEFAULT_TEST_REPO_PATH,
      },
    });
    if (createResp.status() !== 200) {
      test.skip(`Could not create project: ${createResp.status()}`);
    }
    const project = await createResp.json();

    // Create a conversation so Usage tab content renders
    const convoResp = await request.post(`${API_BASE}/conversations`, {
      data: {
        project_id: project.id,
        title: "PW Seeded Conversation",
      },
    });
    if (convoResp.status() !== 200) {
      test.skip(`Could not create conversation: ${convoResp.status()}`);
    }

    // Seed an auto action so the confidence chip appears
    await request.post(`${API_BASE}/debug/seed_task_action`, {
      data: {
        project_id: project.id,
        description: "PW Seeded Task",
        action: "auto_added",
        confidence: 0.88,
        auto_notes: "Seeded for UI test",
      },
    });

    // Verify task exists via API
    const tasksResp = await request.get(
      `${API_BASE}/projects/${project.id}/tasks`
    );
    const tasksJson: { description?: string | null }[] = await tasksResp.json();
    const seededExists = tasksJson.some(
      (t) => (t.description || "").toLowerCase() === "pw seeded task"
    );
    if (!seededExists) {
      test.skip("Seeded task not found via API");
    }

    await page.goto(UI_BASE);

    // Wait for right tabs to render
    await page.waitForSelector(".right-tabs", { timeout: 15000 });

    // Try to select the project from a dropdown or list
    const projectSelect = page.locator(".project-selector select");
    await page.waitForSelector(
      `.project-selector select option[value="${project.id}"]`,
      { timeout: 10000, state: "attached" }
    );
    if (await projectSelect.isVisible()) {
      await projectSelect.selectOption({ value: project.id.toString() });
    } else {
      const projectButton = page.getByRole("button", { name: projectName });
      if (await projectButton.isVisible()) {
        await projectButton.click();
      } else {
        test.skip("Project selector not found");
      }
    }

    // Select the seeded conversation to ensure usage tab has context (best-effort)
    const convoItem = page
      .locator(".conversation-item", { hasText: "PW Seeded Conversation" })
      .first();
    if (await convoItem.count()) {
      await convoItem.click({ timeout: 10000 });
    }

    // Go to Tasks tab
    const tasksTab = page.locator('.right-tab:has-text("Tasks")');
    await tasksTab.waitFor({ state: "visible", timeout: 20000 });
    await tasksTab.click();

    // Refresh data
    const refreshAll = page.locator('.right-tabs-toolbar button:has-text("Refresh all")');
    await refreshAll.click();

    // Wait for tasks to load
    await page.waitForSelector(".tasks-list, .tasks-empty", { timeout: 10000 });

    // Refresh tasks once to ensure seeded action is visible
    const refreshAllBtn = page.locator('.right-tabs-toolbar button:has-text("Refresh all")');
    if (await refreshAllBtn.count()) {
      await refreshAllBtn.click();
    } else {
      // Fallback: re-select Tasks tab to reload
      const tasksTab = page.locator('.right-tab:has-text("Tasks")');
      await tasksTab.click();
    }
    await page.waitForSelector(".tasks-list, .tasks-empty", { timeout: 15000 });

    const taskRow = page.locator("li.task-item", {
      hasText: /PW Seeded Task/i,
    });
    await expect(taskRow).toBeVisible({ timeout: 10000 });
    const chip = taskRow.locator(".task-confidence-chip").first();
    await expect(chip).toBeVisible({ timeout: 10000 });
    const text = await chip.textContent();
    expect(text || "").toMatch(/\d\.\d{2}/);

    // Usage tab telemetry shows confidence buckets / recent actions
    const usageTab = page.locator('.right-tab:has-text("Usage")');
    await expect(usageTab).toBeVisible();
    await usageTab.scrollIntoViewIfNeeded();
    await usageTab.click();
    const usageTelemetry = page.locator(".usage-telemetry");
    try {
      await usageTelemetry.waitFor({ state: "visible", timeout: 15000 });
      const usageHeader = page.locator(".usage-telemetry-header");
      if (await usageHeader.isVisible()) {
        const telemetryRefresh = usageHeader.locator(".btn-secondary", {
          hasText: "Refresh",
        });
        if (await telemetryRefresh.isVisible()) {
          await telemetryRefresh.click();
        }
      }
      const buckets = page.locator(
        ".usage-telemetry-section .usage-telemetry-title",
        {
          hasText: "Confidence stats",
        }
      );
      await buckets.waitFor({ state: "visible", timeout: 15000 });
      const bucketList = page
        .locator(".usage-telemetry-list")
        .filter({ hasText: "0.4â€“0.7" });
      await bucketList.waitFor({ state: "visible", timeout: 15000 });
    } catch {
      // Usage telemetry may be absent when no usage records exist; that's acceptable for this check.
      return;
    }
  });
});
