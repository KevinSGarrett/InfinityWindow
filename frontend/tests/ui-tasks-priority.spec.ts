import { test, expect } from "@playwright/test";
import { createTestProject, createTask } from "./helpers/api";

test.describe("Tasks priority and blocked UI", () => {
  test("shows chips and filters tasks by readiness", async ({ page, request }) => {
    const project = await createTestProject(
      request,
      `PW Tasks Priority ${Date.now()}`
    );

    await createTask(request, project.id, "Normal ready task", {
      priority: "normal",
    });
    await createTask(request, project.id, "Blocked high task", {
      priority: "high",
      blocked_reason: "waiting on approvals",
    });
    await createTask(request, project.id, "Critical ready task", {
      priority: "critical",
    });

    await page.goto("/");

    await page.waitForSelector(".project-selector select", { timeout: 20000 });
    await page
      .locator(".project-selector select")
      .selectOption(project.id.toString());

    const tasksTab = page.locator('.right-tab:has-text("Tasks")');
    await tasksTab.click();

    const refreshBtn = page
      .locator('.tab-section-header button:has-text("Refresh")')
      .first();
    if (await refreshBtn.count()) {
      await refreshBtn.click();
    }

    await page.waitForSelector("li.task-item", { timeout: 15000 });

    const blockedRow = page
      .locator("li.task-item", { hasText: /Blocked high task/i })
      .first();
    await expect(blockedRow.locator(".task-priority-chip")).toHaveText(/high/i);
    const blockedChip = blockedRow.locator(".task-blocked-chip");
    await expect(blockedChip).toBeVisible();
    await expect(blockedChip).toHaveAttribute(
      "title",
      /waiting on approvals/i
    );

    const filter = page.locator("#tasks-priority-filter");
    await expect(filter).toHaveAttribute("aria-label", /task view/i);

    await filter.selectOption("ready_only");
    await expect(
      page.locator("li.task-item", { hasText: /Blocked high task/i })
    ).toHaveCount(0);
    await expect(page.locator("li.task-item")).toHaveCount(2);

    await filter.selectOption("blocked_only");
    await expect(blockedRow).toBeVisible({ timeout: 5000 });
    await expect(page.locator("li.task-item")).toHaveCount(1);

    await filter.selectOption("high_first");
    await page.waitForSelector("li.task-item .task-priority-chip", {
      timeout: 5000,
    });
    const firstPriorityChip = page
      .locator("li.task-item .task-priority-chip")
      .first();
    await expect(firstPriorityChip).toHaveText(/critical/i);
  });
});

