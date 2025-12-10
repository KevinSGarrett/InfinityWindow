import { test, expect } from "@playwright/test";
import { createTestProject } from "./helpers/api";

const API = "http://127.0.0.1:8000";
const APP = "http://localhost:5173/";

test.describe("Usage analytics Phase 3 and auto-mode transparency", () => {
  test("shows analytics card defaults and auto-route reason", async ({
    page,
    request,
  }) => {
    const project = await createTestProject(
      request,
      `UsagePhase3_${Date.now()}`
    );
    const conversationResp = await request.post(`${API}/conversations`, {
      data: { project_id: project.id, title: "Usage Phase3 Conversation" },
    });
    expect(conversationResp.ok()).toBeTruthy();
    const conversationId = (await conversationResp.json()).id;

    const windowsHit: string[] = [];

    await page.route(`**/projects/${project.id}/usage_summary**`, (route) => {
      const url = new URL(route.request().url());
      const windowParam = url.searchParams.get("window") ?? "24h";
      windowsHit.push(windowParam);
      const payload = {
        window: windowParam,
        total_calls: windowParam === "7d" ? 70 : windowParam === "1h" ? 5 : 24,
        total_tokens_in: 12345,
        total_tokens_out: 6789,
        total_cost_estimate: 1.2345,
        model_breakdown: [
          { model: "gpt-5.1", calls: 10, tokens_in: 6000, tokens_out: 3200 },
          {
            model: "gpt-4o-mini",
            calls: 14,
            tokens_in: 5345,
            tokens_out: 3589,
          },
        ],
        group_breakdown: [
          { group: "auto → fast", calls: 12 },
          { group: "auto → deep", calls: 12 },
        ],
      };
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(payload),
      });
    });

    await page.route("**/debug/telemetry**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          llm: {
            auto_routes: { fast: 3, deep: 1 },
            auto_route_reasons: [
              {
                route: "fast",
                reason: "short prompt",
                project_id: project.id,
                conversation_id: conversationId,
                at: new Date().toISOString(),
              },
            ],
            fallback_attempts: 0,
            fallback_success: 0,
          },
          tasks: {
            auto_added: 0,
            auto_completed: 0,
            auto_deduped: 0,
            auto_suggested: 0,
            recent_actions: [],
            confidence_buckets: { lt_0_4: 0, "0_4_0_7": 0, gte_0_7: 0 },
          },
          ingestion: {},
        }),
      })
    );

    await page.goto(APP);
    await page.waitForLoadState("networkidle");
    await page.waitForSelector(".project-selector select", { timeout: 45000 });
    await page.locator(".project-selector select").selectOption(String(project.id));
    await page.getByRole("tab", { name: "Usage" }).click();
    await page
      .locator('select[aria-label="Select conversation for usage"]')
      .selectOption(String(conversationId));
    await page.getByRole("button", { name: "Use current chat" }).click();

    const analyticsCard = page.getByTestId("usage-analytics-card");
    await expect(analyticsCard).toBeVisible();
    const windowSelect = page.getByTestId("usage-analytics-window");
    await expect(windowSelect).toHaveValue("24h");
    await expect(
      page.getByTestId("usage-analytics-total-calls")
    ).toContainText("24");

    await expect(page.getByTestId("auto-mode-route-pill")).toBeVisible();
    await expect(
      page.getByTestId("auto-mode-route-reason")
    ).toContainText("short prompt");

    await windowSelect.selectOption("7d");
    await expect(windowSelect).toHaveValue("7d");
    await windowSelect.selectOption("1h");
    await expect(windowSelect).toHaveValue("1h");

    expect(windowsHit).toContain("24h");
    expect(windowsHit).toContain("7d");
    expect(windowsHit).toContain("1h");

    await request.delete(`${API}/projects/${project.id}`);
  });

  test("falls back safely when telemetry or summary data is missing", async ({
    page,
    request,
  }) => {
    const project = await createTestProject(
      request,
      `UsagePhase3Fallback_${Date.now()}`
    );
    const conversationResp = await request.post(`${API}/conversations`, {
      data: { project_id: project.id, title: "Usage Phase3 Fallback" },
    });
    expect(conversationResp.ok()).toBeTruthy();
    const conversationId = (await conversationResp.json()).id;

    await page.route(`**/projects/${project.id}/usage_summary**`, (route) =>
      route.fulfill({ status: 502, body: "backend unavailable" })
    );

    await page.route("**/debug/telemetry**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          llm: {
            auto_routes: {},
            auto_route_reasons: [],
            fallback_attempts: 0,
            fallback_success: 0,
          },
          tasks: {
            auto_added: 0,
            auto_completed: 0,
            auto_deduped: 0,
            auto_suggested: 0,
            recent_actions: [],
            confidence_buckets: { lt_0_4: 0, "0_4_0_7": 0, gte_0_7: 0 },
          },
          ingestion: {},
        }),
      })
    );

    await page.goto(APP);
    await page.waitForLoadState("networkidle");
    await page.waitForSelector(".project-selector select", { timeout: 45000 });
    await page.locator(".project-selector select").selectOption(String(project.id));
    await page.getByRole("tab", { name: "Usage" }).click();
    await page
      .locator('select[aria-label="Select conversation for usage"]')
      .selectOption(String(conversationId));
    await page.getByRole("button", { name: "Use current chat" }).click();

    await expect(page.getByTestId("usage-analytics-card")).toBeVisible();
    await expect(
      page.getByTestId("usage-analytics-card")
    ).toContainText("Failed to load usage analytics");
    await expect(page.getByTestId("auto-mode-route-fallback")).toBeVisible();

    await request.delete(`${API}/projects/${project.id}`);
  });
});

