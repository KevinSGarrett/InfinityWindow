import { test, expect } from "@playwright/test";
import { createTestProject, waitForBackend } from "./helpers/api";

const API_BASE = process.env.PLAYWRIGHT_API_BASE ?? "http://127.0.0.1:8000";
const UI_BASE = process.env.PLAYWRIGHT_UI_BASE ?? "http://localhost:5173";

test.describe("Retrieval context inspector", () => {
  test("shows retrieved context and handles errors", async ({
    page,
    request,
  }) => {
    test.setTimeout(150_000);
    await waitForBackend(240_000);

    const project = await createTestProject(
      request,
      `RetrievalCtx_${Date.now()}`
    );

    const convoResp = await request.post(`${API_BASE}/conversations`, {
      data: {
        project_id: project.id,
        title: "Seeded Retrieval Context: Doc and Memory Entries",
      },
    });
    expect(convoResp.ok()).toBeTruthy();
    const conversationId = (await convoResp.json()).id as number;

    const now = new Date().toISOString();
    const usagePayload = {
      conversation_id: conversationId,
      total_tokens_in: 1263,
      total_tokens_out: 1147,
      total_cost_estimate: 0.0003,
      auto_reason: "fast",
      records: [
        {
          id: 382,
          project_id: project.id,
          conversation_id: conversationId,
          message_id: 382,
          model: "gpt-5-nano",
          tokens_in: 1263,
          tokens_out: 1147,
          cost_estimate: 0.0003,
          created_at: now,
          mode: "fast",
        },
      ],
    };

    const retrievalSuccess = {
      conversation_id: conversationId,
      message_id: 382,
      profiles: {
        messages: { top_k: 7 },
        docs: { top_k: 5 },
        memory: { top_k: 3 },
      },
      messages: [
        {
          role: "user",
          snippet: "Recent user prompt about telemetry and context hints.",
          score: 0.9,
        },
      ],
      docs: [
        {
          document_id: 7581,
          title: "Retrieval doc seeded for UI test.",
          chunk_index: 0,
          snippet:
            "Retrieval doc seeded for UI test. Contains telemetry and context hints.",
          score: 0.82,
          label: "Document 7581 (Retrieval doc seeded for UI test.)",
        },
      ],
      memory: [
        {
          memory_id: 44,
          title: "Retrieval memory item",
          snippet: "Memory content for retrieval context Playwright test.",
          score: 0.77,
        },
      ],
      retrieval_context_text: "stub context",
    };

    let retrievalCallCount = 0;
    await page.route(
      `**/conversations/${conversationId}/usage`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(usagePayload),
        });
      }
    );
    await page.route("**/debug/telemetry", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          llm: { auto_routes: { fast: 10, deep: 1 }, fallback_attempts: 0, fallback_success: 0 },
          tasks: {
            auto_added: 8,
            auto_completed: 0,
            auto_deduped: 3,
            auto_suggested: 0,
            auto_dismissed: 0,
            recent_actions: [],
            confidence_stats: { min: 0.465, max: 0.933, avg: 0.738, count: 12 },
            confidence_buckets: { lt_0_4: 0, "0_4_0_7": 4, gte_0_7: 8 },
          },
          ingestion: {},
          retrieval: {},
        }),
      });
    });
    await page.route(
      `**/conversations/${conversationId}/debug/retrieval_context`,
      async (route) => {
        retrievalCallCount += 1;
        if (retrievalCallCount === 1) {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify(retrievalSuccess),
          });
          return;
        }
        await route.fulfill({
          status: 500,
          body: "forced error",
        });
      }
    );

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

    const retrievalCard = page.getByTestId("retrieval-context-card");
    await expect(retrievalCard).toBeVisible({ timeout: 20000 });
    await expect(
      page.getByTestId("retrieval-context-counts")
    ).toBeVisible({ timeout: 20000 });

    const messageItems = page
      .getByTestId("retrieval-context-messages")
      .locator(".retrieval-context-item");
    const docItems = page
      .getByTestId("retrieval-context-docs")
      .locator(".retrieval-context-item");
    const memoryItems = page
      .getByTestId("retrieval-context-memory")
      .locator(".retrieval-context-item");

    await expect(messageItems.first()).toBeVisible({ timeout: 20000 });
    expect(await messageItems.count()).toBeGreaterThan(0);
    expect(await docItems.count()).toBeGreaterThan(0);
    expect(await memoryItems.count()).toBeGreaterThan(0);

    // Force an error and verify it stays contained.
    await retrievalCard.getByRole("button", { name: "Refresh" }).click();
    await expect(
      page.getByTestId("retrieval-context-error")
    ).toBeVisible();
    await expect(page.locator(".usage-card").first()).toBeVisible();

    await request.delete(`${API_BASE}/projects/${project.id}`);
  });
});


