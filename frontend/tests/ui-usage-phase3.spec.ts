import { test, expect } from "@playwright/test";
import { createTestProject, waitForBackend } from "./helpers/api";

const API_BASE = process.env.PLAYWRIGHT_API_BASE ?? "http://127.0.0.1:8000";
const UI_BASE = process.env.PLAYWRIGHT_UI_BASE ?? "http://localhost:5173";

test.describe("Usage dashboard phase 3 analytics", () => {
  test("shows usage summary and recent records", async ({ page, request }) => {
    test.setTimeout(120_000);
    await waitForBackend(240_000);

    const project = await createTestProject(
      request,
      `UsagePhase3_${Date.now()}`
    );

    const chat1 = await request.post(`${API_BASE}/chat`, {
      data: {
        project_id: project.id,
        message: "Seed usage summary metrics.",
      },
      timeout: 120_000,
    });
    expect(chat1.ok()).toBeTruthy();
    const conversationId = (await chat1.json()).conversation_id as number;

    await page.goto(UI_BASE);
    await page.waitForLoadState("networkidle");
    await page.locator(".project-selector select").selectOption(
      String(project.id)
    );
    await page.getByRole("tab", { name: "Usage" }).click();
    await page
      .locator('select[aria-label="Select conversation for usage"]')
      .selectOption(String(conversationId));
    await page.getByRole("button", { name: "Use current chat" }).click();

    const usageCards = page.locator(".usage-card");
    await expect(usageCards.first()).toBeVisible({ timeout: 20000 });
    const cardCount = await usageCards.count();
    expect(cardCount).toBeGreaterThanOrEqual(3);

    const recentRecord = page.locator(".usage-record-item").first();
    await expect(recentRecord).toBeVisible({ timeout: 20000 });

    await request.delete(`${API_BASE}/projects/${project.id}`);
  });
});


