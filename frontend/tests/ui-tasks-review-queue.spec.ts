import { test, expect } from "@playwright/test";
import {
  createTestProject,
  createTask,
  seedTaskSuggestion,
} from "./helpers/api";

test.describe("Tasks review queue priority/blocked badges", () => {
  test("renders priority and blocked chips for suggestions", async ({
    page,
    request,
  }) => {
    const project = await createTestProject(
      request,
      `PW Review Queue ${Date.now()}`
    );

    const blockedTask = await createTask(
      request,
      project.id,
      "Backend dependency",
      {
        priority: "high",
        blocked_reason: "waiting on deploy",
      }
    );

    await seedTaskSuggestion(request, {
      project_id: project.id,
      action_type: "add",
      description: "Add auth hardening",
      priority: "critical",
      blocked_reason: "awaiting signoff",
      confidence: 0.35,
    });

    await seedTaskSuggestion(request, {
      project_id: project.id,
      action_type: "complete",
      target_task_id: blockedTask.id,
      description: "Mark backend dependency done",
      priority: "high",
      blocked_reason: "pending release",
      confidence: 0.55,
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

    const suggestionsToggle = page.locator(".suggestions-toggle");
    await suggestionsToggle.click();

    const suggestionItems = page.locator(".suggestion-item");
    await expect(suggestionItems.first()).toBeVisible({ timeout: 15000 });
    const suggestionCount = await suggestionItems.count();
    if (suggestionCount === 0) {
      test.skip("No suggestions rendered");
    }

    const blockedSuggestion = suggestionItems
      .filter({ hasText: /auth hardening/i })
      .first();
    await expect(
      blockedSuggestion.locator(".task-priority-chip")
    ).toHaveText(/critical/i);
    const blockedBadge = blockedSuggestion.locator(".task-blocked-chip");
    await expect(blockedBadge).toBeVisible();
    await expect(blockedBadge).toHaveAttribute("title", /awaiting signoff/i);

    const secondSuggestion = suggestionItems
      .filter({ hasText: /backend dependency/i })
      .first();
    await expect(
      secondSuggestion.locator(".task-priority-chip")
    ).toHaveText(/high/i);
    await expect(secondSuggestion.locator(".task-blocked-chip")).toBeVisible();

    const approveButton = suggestionItems
      .first()
      .getByRole("button", { name: /approve/i });
    await approveButton.click();
    await page.waitForTimeout(400);

    const dismissButton = suggestionItems
      .first()
      .getByRole("button", { name: /dismiss/i });
    if (await dismissButton.count()) {
      await dismissButton.click();
    }
  });
});

