import { test, expect } from "@playwright/test";

test.describe("Retrieval config summary", () => {
  test("shows retrieval config from backend in Usage tab", async ({
    page,
    request,
  }) => {
    const API = "http://127.0.0.1:8000";
    const APP = "http://localhost:5173/";

    type RetrievalProfile = {
      messages_k?: number;
      docs_k?: number;
      memory_k?: number;
      tasks_k?: number;
    };

    const retrievalResp = await request.get(`${API}/debug/retrieval_config`);
    const hasRetrievalConfig = retrievalResp.ok();
    const retrievalConfig: RetrievalProfile | null = hasRetrievalConfig
      ? await retrievalResp.json()
      : null;
    const requiredKeys = ["messages_k", "docs_k", "memory_k", "tasks_k"] as const;
    if (retrievalConfig) {
      requiredKeys.forEach((key) =>
        expect(typeof retrievalConfig[key]).toBe("number")
      );
    }

    let projectId: number | null = null;
    try {
      const projectResp = await request.post(`${API}/projects`, {
        data: {
          name: `RetrievalConfig_${Date.now()}`,
          local_root_path: "C:\\InfinityWindow",
        },
      });
      expect(projectResp.ok()).toBeTruthy();
      projectId = (await projectResp.json()).id;

      const conversationResp = await request.post(`${API}/conversations`, {
        data: { project_id: projectId, title: "Retrieval Config Conversation" },
      });
      expect(conversationResp.ok()).toBeTruthy();
      const conversationId = (await conversationResp.json()).id;

      await page.goto(APP);
      await page.waitForLoadState("networkidle");

      await page
        .locator(".project-selector select")
        .selectOption(String(projectId));

      await page.getByRole("tab", { name: "Usage" }).click();
      await page
        .locator('select[aria-label="Select conversation for usage"]')
        .selectOption(String(conversationId));
      await page.getByRole("button", { name: "Use current chat" }).click();

      const summary = page.locator('[data-testid="retrieval-config-summary"]');
      await summary.waitFor({ state: "visible", timeout: 15000 });
      await expect(summary).toContainText("Retrieval config");
      if (retrievalConfig) {
        for (const key of requiredKeys) {
          await expect(summary).toContainText(
            String(retrievalConfig[key] as number)
          );
        }
      } else {
        await expect(summary).toContainText("N/A");
      }
    } finally {
      if (projectId) {
        await request.delete(`${API}/projects/${projectId}`);
      }
    }
  });
});
