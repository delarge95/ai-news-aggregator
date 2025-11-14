import { test as base, Page } from '@playwright/test';

export interface Fixtures {
  page: Page;
}

/**
 * Custom test fixtures with additional helpers
 */
export const test = base.extend<Fixtures>({
  page: async ({ page }, use) => {
    // Page setup
    await page.goto('/');
    
    // Set up common page helpers
    page.addInitScript(() => {
      // Mock localStorage for consistent testing
      localStorage.setItem('theme', 'light');
      localStorage.setItem('mockUser', JSON.stringify({
        id: '1',
        name: 'Test User',
        email: 'test@example.com'
      }));
    });

    await use(page);
  },
});

export { expect } from '@playwright/test';