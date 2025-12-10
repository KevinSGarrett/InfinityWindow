import { test, expect } from '@playwright/test';

test('right-column tabs render and activate', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  const tabs = page.locator('.right-tabs');

  const tabNames = [
    'Tasks',
    'Docs',
    'Files',
    'Search',
    'Terminal',
    'Usage',
    'Notes',
    'Memory',
  ];

  for (const name of tabNames) {
    const tab = tabs.getByRole('button', { name: new RegExp(`^${name}$`) });
    await tab.click();
    await expect(tab).toHaveClass(/active/);
  }
});

