import { APIRequestContext, expect } from '@playwright/test';

const API_BASE = process.env.PLAYWRIGHT_API_BASE ?? 'http://127.0.0.1:8000';

export interface TestProject {
  id: number;
  name: string;
}

export interface TestTask {
  id: number;
  description: string;
}

export async function createTestProject(
  request: APIRequestContext,
  name: string,
  localRootPath?: string
): Promise<TestProject> {
  const maxAttempts = 3;
  let lastError: unknown;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const response = await request.post(`${API_BASE}/projects`, {
        data: {
          name,
          description: 'Playwright QA project',
          local_root_path: localRootPath ?? 'C:\\InfinityWindow',
        },
        timeout: 30_000,
      });
      expect(response.ok()).toBeTruthy();
      return (await response.json()) as TestProject;
    } catch (error) {
      lastError = error;
      // exponential backoff
      const backoff = attempt * 2000;
      await new Promise((r) => setTimeout(r, backoff));
    }
  }
  throw lastError;
}

export async function setProjectInstructions(
  request: APIRequestContext,
  projectId: number,
  text: string
): Promise<void> {
  const response = await request.put(
    `${API_BASE}/projects/${projectId}/instructions`,
    {
      data: { instruction_text: text },
    }
  );
  expect(response.ok()).toBeTruthy();
}

export async function addDecision(
  request: APIRequestContext,
  projectId: number,
  title: string,
  details: string
): Promise<void> {
  const response = await request.post(
    `${API_BASE}/projects/${projectId}/decisions`,
    {
      data: {
        title,
        details,
        category: 'Playwright QA',
      },
    }
  );
  expect(response.ok()).toBeTruthy();
}

export async function addMemoryItem(
  request: APIRequestContext,
  projectId: number,
  title: string,
  content: string
): Promise<void> {
  const response = await request.post(`${API_BASE}/projects/${projectId}/memory`, {
    data: {
      title,
      content,
      tags: ['playwright'],
      pinned: true,
    },
  });
  expect(response.ok()).toBeTruthy();
}

export async function createTask(
  request: APIRequestContext,
  projectId: number,
  description: string,
  overrides?: { priority?: string; blocked_reason?: string }
): Promise<TestTask> {
  const response = await request.post(`${API_BASE}/tasks`, {
    data: {
      project_id: projectId,
      description,
      ...overrides,
    },
  });
  expect(response.ok()).toBeTruthy();
  return (await response.json()) as TestTask;
}

export async function seedTaskSuggestion(
  request: APIRequestContext,
  data: {
    project_id: number;
    action_type: "add" | "complete";
    description?: string;
    target_task_id?: number;
    priority?: string;
    blocked_reason?: string;
    confidence?: number;
  }
): Promise<void> {
  const response = await request.post(
    `${API_BASE}/debug/task_suggestions/seed`,
    {
      data,
    }
  );
  expect(response.ok()).toBeTruthy();
}

export async function waitForBackend(maxWaitMs: number = 240_000): Promise<void> {
  const start = Date.now();
  let attempt = 0;
  while (Date.now() - start < maxWaitMs) {
    attempt += 1;
    try {
      const response = await fetch(`${API_BASE}/health`, { timeout: 10_000 });
      if (response.ok) {
        return;
      }
    } catch (error) {
      // Backend not ready yet
    }
    const backoff = Math.min(5000, 500 + attempt * 200);
    await new Promise(resolve => setTimeout(resolve, backoff));
  }
  throw new Error(`Backend did not become ready within ${maxWaitMs / 1000}s`);
}

export async function createProject(name: string): Promise<TestProject> {
  const response = await fetch(`${API_BASE}/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  if (!response.ok) {
    throw new Error(`Failed to create project: ${response.statusText}`);
  }
  return await response.json();
}

