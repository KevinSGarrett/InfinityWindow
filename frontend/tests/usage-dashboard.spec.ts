import { test, expect } from "@playwright/test";

test.describe("Usage dashboard charts and exports", () => {
  test("charts follow filters and export matches filtered actions", async ({
    page,
    request,
  }) => {
    const API = "http://127.0.0.1:8000";
    const APP = "http://localhost:5173/";

    const projectResp = await request.post(`${API}/projects`, {
      data: { name: `UsageDash_${Date.now()}`, local_root_path: "C:\\InfinityWindow" },
    });
    expect(projectResp.ok()).toBeTruthy();
    const projectId = (await projectResp.json()).id;

    const convoResp = await request.post(`${API}/conversations`, {
      data: { project_id: projectId, title: "Usage Dashboard Conv" },
    });
    expect(convoResp.ok()).toBeTruthy();
    const conversationId = (await convoResp.json()).id;

    const seeds = [
      { description: "Seed auto add", action: "auto_added", confidence: 0.2, model: "gpt-4o-mini" },
      { description: "Seed complete", action: "auto_completed", confidence: 0.55, model: "gpt-5.1" },
      { description: "Seed suggest", action: "auto_suggested", confidence: 0.82, model: "gpt-5.1-codex" },
    ];
    for (const seed of seeds) {
      const seedResp = await request.post(`${API}/debug/seed_task_action`, {
        data: { project_id: projectId, ...seed },
      });
      expect(seedResp.ok()).toBeTruthy();
    }
    const manualSeed = {
      description: "Manual dashboard note",
      action: "manual_followup",
      confidence: 0.42,
      model: "gpt-4o",
      source: "manual",
    };
    const manualSeedResp = await request.post(`${API}/debug/seed_task_action`, {
      data: { project_id: projectId, ...manualSeed },
    });
    expect(manualSeedResp.ok()).toBeTruthy();

    await page.goto(APP);
    await page.waitForLoadState("networkidle");

    await page.locator(".project-selector select").selectOption(String(projectId));

    await page.getByRole("tab", { name: "Usage" }).click();
    await page
      .locator('select[aria-label="Select conversation for usage"]')
      .selectOption(String(conversationId));
    await page.getByRole("button", { name: "Use current chat" }).click();

    const actionChartRows = page.locator(
      '[data-testid="chart-actions"] .usage-chart-row'
    );
    await actionChartRows.first().waitFor({ state: "visible", timeout: 15000 });
    expect(await actionChartRows.count()).toBeGreaterThanOrEqual(3);

    const modelChartRows = page.locator(
      '[data-testid="chart-models"] .usage-chart-row'
    );
    expect(await modelChartRows.count()).toBeGreaterThanOrEqual(2);

    const filteredActionRows = page.locator(
      '[data-testid="recent-actions-list"] li'
    );

    await page.getByLabel("Action source filter").selectOption("manual");
    await expect(
      filteredActionRows.filter({ hasText: manualSeed.description })
    ).toHaveCount(1);
    await expect(
      filteredActionRows.filter({ hasText: "Seed auto add" })
    ).toHaveCount(0);
    await page.getByRole("button", { name: "Copy JSON" }).first().click();
    const exportPreview = page.locator('[data-testid="usage-export-preview"]');
    await expect(exportPreview).toContainText(manualSeed.description);
    await expect(exportPreview).not.toContainText("Seed auto add");
    await page.getByLabel("Action source filter").selectOption("automatic");
    await expect(
      filteredActionRows.filter({ hasText: manualSeed.description })
    ).toHaveCount(0);
    await page.getByLabel("Action source filter").selectOption("all");

    await page.getByLabel("Action filter").selectOption("auto_completed");
    await page.getByLabel("Time filter").selectOption("last5");

    await expect(filteredActionRows).toHaveCount(1);
    await expect(filteredActionRows.first()).toContainText("auto_completed");

    await page.getByRole("button", { name: "Copy JSON" }).first().click();
    await expect(exportPreview).toContainText("auto_completed");
    await expect(exportPreview).not.toContainText("auto_added");

    await page.getByLabel("Action filter").selectOption("auto_dismissed");
    await expect(filteredActionRows).toHaveCount(0);
    await expect(page.locator('[data-testid="chart-actions"]')).toContainText(
      "No filtered actions yet."
    );

    await request.delete(`${API}/projects/${projectId}`);
  });
});

