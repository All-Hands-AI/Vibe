import { test, expect } from '@playwright/test';

test.describe('Smoke Tests', () => {
  test('should load the application', async ({ page }) => {
    // Mock API to avoid backend dependency
    await page.route('/api/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ apps: [], count: 0 })
      });
    });

    await page.goto('/');
    
    // Should load without errors
    await expect(page).toHaveTitle(/OpenVibe/);
    
    // Should show some content
    await expect(page.locator('body')).toBeVisible();
  });
});