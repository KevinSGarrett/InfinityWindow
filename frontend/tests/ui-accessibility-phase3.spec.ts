import { test, expect } from "@playwright/test";

test.describe("Phase3 - UI accessibility & empty states", () => {
  test("keyboard focus, empty suggestions, usage empty state", async ({
    page,
    request,
  }) => {
    // Create a project via API
    const projectName = `Phase3 UI ${Date.now()}`;
    const createResp = await request.post("http://127.0.0.1:8000/projects", {
      data: {
        name: projectName,
        local_root_path: "C:\\\\InfinityWindow",
      },
    });
    expect(createResp.status()).toBe(200);
    const project = await createResp.json();

    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Select project
    const projectSelect = page.locator(".project-selector select");
    await projectSelect.waitFor({ timeout: 15000 });
    try {
      await projectSelect.selectOption(project.id.toString());
    } catch {
      // Retry once after a short wait
      await page.waitForTimeout(500);
      await projectSelect.selectOption({ value: project.id.toString() });
    }

    // Tasks tab: focus check and empty suggestions state
    const tasksTab = page.locator('.right-tab:has-text("Tasks")');
    await tasksTab.click();
    const taskInput = page.locator(".tasks-input");
    await taskInput.waitFor({ timeout: 10000 });
    await taskInput.focus();
    const isFocused = await taskInput.evaluate(
      (el) => document.activeElement === el
    );
    expect(isFocused).toBe(true);

    // Suggestions drawer should show empty state when no suggestions
    const suggestionsToggle = page.locator(".suggestions-toggle");
    if (await suggestionsToggle.count()) {
      await suggestionsToggle.click();
      const emptySuggestions = page.locator(".tasks-empty", {
        hasText: /No pending suggestions/i,
      });
      if (await emptySuggestions.count()) {
        await expect(emptySuggestions).toBeVisible({ timeout: 5000 });
      } else {
        // Fall back: ensure no suggestions render
        await expect(page.locator(".suggestion-item")).toHaveCount(0);
      }
    }

    // Usage tab: empty guidance present when no conversation selected
    const usageTab = page.locator('.right-tab:has-text("Usage")');
    await usageTab.click();
    const usageEmpty = page.locator("text=Select a conversation to view usage analytics.");
    await expect(usageEmpty).toBeVisible({ timeout: 5000 });
  });
});

