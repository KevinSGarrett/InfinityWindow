import { APIRequestContext, expect } from '@playwright/test';

const API_BASE = process.env.PLAYWRIGHT_API_BASE ?? 'http://127.0.0.1:8000';

export interface TestProject {
  id: number;
  name: string;
}

export async function createTestProject(
  request: APIRequestContext,
  name: string,
  localRootPath?: string
): Promise<TestProject> {
  const response = await request.post(`${API_BASE}/projects`, {
    data: {
      name,
      description: 'Playwright QA project',
      local_root_path: localRootPath,
    },
  });
  expect(response.ok()).toBeTruthy();
  return (await response.json()) as TestProject;
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

