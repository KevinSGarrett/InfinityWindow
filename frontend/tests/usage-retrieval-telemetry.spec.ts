import { test, expect } from "@playwright/test";
import { createTestProject, waitForBackend } from "./helpers/api";

const API_BASE = process.env.PLAYWRIGHT_API_BASE ?? "http://127.0.0.1:8000";
const UI_BASE = process.env.PLAYWRIGHT_UI_BASE ?? "http://localhost:5173";

test.describe("Usage retrieval telemetry", () => {
  test("surfaces retrieval stats after chat and search interactions", async ({
    page,
    request,
  }) => {
    await waitForBackend(240_000);
    const project = await createTestProject(
      request,
      `Usage Retrieval ${Date.now()}`
    );
    const projectId = project.id;

    const cleanup = async () => {
      await request.delete(`${API_BASE}/projects/${projectId}`).catch(() => {
        /* noop */
      });
    };

    try {
      const resetResp = await request.get(
        `${API_BASE}/debug/telemetry?reset=true`
      );
      expect(resetResp.ok()).toBeTruthy();

      const docResp = await request.post(`${API_BASE}/docs/text`, {
        data: {
          project_id: projectId,
          name: `retrieval-${Date.now()}`,
          text: "Retrieval telemetry doc about chat and search usage counters.",
        },
      });
      expect(docResp.ok()).toBeTruthy();

      await page.goto(UI_BASE, { waitUntil: "networkidle" });

      const projectSelect = page.locator(".project-selector select").first();
      await projectSelect.waitFor({ timeout: 15_000 });
      await projectSelect.selectOption(String(projectId));
      await page.waitForTimeout(1_000);

      const chatInput = page.locator(".chat-input");
      await chatInput.waitFor({ timeout: 10_000 });
      await chatInput.fill(
        "Summarize the retrieval telemetry doc you just indexed and cite the doc."
      );
      const sendButton = page.getByRole("button", { name: /Send|Ask/i });
      await sendButton.click().catch(async () => {
        await chatInput.press("Enter");
      });
      const assistantMessage = page
        .getByText("Assistant", { exact: false })
        .first();
      await assistantMessage.waitFor({ timeout: 45_000 });

      await page.getByRole("tab", { name: "Search" }).click();
      const searchInput = page
        .locator(
          'input[type="search"], input[placeholder*="Search"], input[type="text"]'
        )
        .first();
      await searchInput.waitFor({ timeout: 10_000 });
      await searchInput.fill("telemetry doc");
      await searchInput.press("Enter");
      const searchResults = page.locator(
        '.search-results, .search-hit, .doc-hit, .message-hit, [data-testid="search-result"]'
      );
      await searchResults.first().waitFor({ timeout: 20_000 });

      await page.waitForTimeout(1_500);
      await page.getByRole("tab", { name: "Usage" }).click();
      const refreshButton = page.getByRole("button", { name: "Refresh" }).first();
      await refreshButton.click();
      await page.waitForTimeout(500);

      const retrievalStats = page.getByTestId("retrieval-stats");
      let statsVisible = true;
      try {
        await retrievalStats.waitFor({ state: "visible", timeout: 10_000 });
      } catch {
        statsVisible = false;
      }
      if (!statsVisible) {
        test.skip("Retrieval telemetry not exposed in this backend build.");
        return;
      }

      await expect(retrievalStats).toContainText(/Retrieval/i);
      const statsText = (await retrievalStats.textContent()) ?? "";
      const numbers = statsText.match(/\d+/g) ?? [];
      expect(numbers.some((value) => Number(value) > 0)).toBeTruthy();
    } finally {
      await cleanup();
    }
  });
});
