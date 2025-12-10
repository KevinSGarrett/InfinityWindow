import { test, expect } from "@playwright/test";
import { createTestProject } from "./helpers/api";

const API_BASE = process.env.PLAYWRIGHT_API_BASE ?? "http://127.0.0.1:8000";
const UI_BASE = process.env.PLAYWRIGHT_UI_BASE ?? "http://localhost:5173";

test.describe("Project archive flow", () => {
  test("archives a project and keeps Usage tab stable", async ({
    page,
    request,
  }) => {
    const keeper = await createTestProject(
      request,
      `ArchiveKeeper ${Date.now()}`
    );
    const target = await createTestProject(
      request,
      `ArchiveTarget ${Date.now()}`
    );

    const createConversation = async (projectId: number, title: string) => {
      const resp = await request.post(`${API_BASE}/conversations`, {
        data: { project_id: projectId, title },
        timeout: 30_000,
      });
      expect(resp.ok()).toBeTruthy();
      const json = await resp.json();
      return json.id as number;
    };

    const keeperConvId = await createConversation(
      keeper.id,
      "Keeper Conversation"
    );
    const targetConvId = await createConversation(
      target.id,
      "Target Conversation"
    );

    await page.goto(UI_BASE, { waitUntil: "networkidle" });
    const projectSelect = page.locator(".project-selector select");
    await projectSelect.waitFor({ state: "visible", timeout: 15000 });
    await projectSelect.selectOption(String(target.id));

    // Open Usage tab on the project that will be archived
    await page.getByRole("tab", { name: "Usage" }).click();
    const usageSelect = page.locator(
      'select[aria-label="Select conversation for usage"]'
    );
    await page.waitForSelector(
      `select[aria-label="Select conversation for usage"] option[value="${targetConvId}"]`,
      { timeout: 15000 }
    );
    await usageSelect.selectOption(String(targetConvId));
    await page
      .getByRole("button", { name: "Use current chat" })
      .click({ timeout: 5000 })
      .catch(() => {});
    await expect(page.locator(".usage-panel")).toBeVisible();

    // Archive the project via the UI
    page.once("dialog", (dialog) => dialog.accept());
    const archiveButton = page.getByTestId("archive-project-button");
    await expect(archiveButton).toBeVisible();
    await archiveButton.click();

    await expect(projectSelect).not.toHaveValue(String(target.id));
    await expect(
      projectSelect.locator(`option[value="${target.id}"]`)
    ).toHaveCount(0);

    // Switch to keeper project and verify Usage tab still works
    await projectSelect.selectOption(String(keeper.id));
    await page.getByRole("tab", { name: "Usage" }).click();
    await page.waitForSelector(
      `select[aria-label="Select conversation for usage"] option[value="${keeperConvId}"]`,
      { timeout: 15000 }
    );
    await usageSelect.selectOption(String(keeperConvId));
    await page
      .getByRole("button", { name: "Use current chat" })
      .click({ timeout: 5000 })
      .catch(() => {});
    const usageEmpty = page.locator(".usage-empty");
    await expect(usageEmpty.first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator(".usage-telemetry")).toBeVisible();

    // Cleanup
    await request.delete(`${API_BASE}/projects/${keeper.id}`);
    await request.delete(`${API_BASE}/projects/${target.id}`).catch(() => {});
  });
});

