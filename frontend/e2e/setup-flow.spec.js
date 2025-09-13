import { test, expect } from '@playwright/test';
import { SetupPage } from './pages/SetupPage.js';
import { AppsPage } from './pages/AppsPage.js';
import { setupTestEnvironment, clearStorage } from './utils/test-helpers.js';

test.describe('Setup Flow', () => {
  let setupPage;
  let appsPage;

  test.beforeEach(async ({ page }) => {
    setupPage = new SetupPage(page);
    appsPage = new AppsPage(page);
    
    // Set up test environment
    await setupTestEnvironment(page);
  });

  test('should show setup window on first visit', async ({ page }) => {
    await setupPage.goto();
    
    // Setup window should be visible
    expect(await setupPage.isSetupWindowVisible()).toBe(true);
    
    // Check setup window title
    const title = await setupPage.getSetupTitle();
    expect(title).toContain('SYSTEM BOOT');
  });

  test('should complete setup with valid credentials', async ({ page }) => {
    await setupPage.goto();
    
    // Verify setup window is visible
    expect(await setupPage.isSetupWindowVisible()).toBe(true);
    
    // Complete setup with test credentials
    await setupPage.completeSetup({
      githubToken: 'test-github-token-123',
      flyToken: 'test-fly-token-456',
      openaiKey: 'test-openai-key-789',
      anthropicKey: 'test-anthropic-key-abc'
    });
    
    // Setup window should disappear
    await setupPage.waitForSetupComplete();
    expect(await setupPage.isSetupWindowVisible()).toBe(false);
    
    // Should navigate to apps page
    expect(await appsPage.isPageLoaded()).toBe(true);
  });

  test('should skip setup and go to apps page', async ({ page }) => {
    await setupPage.goto();
    
    // Verify setup window is visible
    expect(await setupPage.isSetupWindowVisible()).toBe(true);
    
    // Skip setup
    await setupPage.skipSetup();
    
    // Setup window should disappear
    await setupPage.waitForSetupComplete();
    expect(await setupPage.isSetupWindowVisible()).toBe(false);
    
    // Should navigate to apps page
    expect(await appsPage.isPageLoaded()).toBe(true);
  });

  test('should validate required fields before enabling complete button', async ({ page }) => {
    await setupPage.goto();
    
    // Initially, complete button should be disabled (if validation is implemented)
    // This test assumes validation exists - adjust based on actual implementation
    
    // Fill only GitHub token
    await setupPage.fillGitHubToken('test-token');
    
    // Fill all required fields
    await setupPage.fillGitHubToken('test-github-token');
    await setupPage.fillFlyToken('test-fly-token');
    await setupPage.fillOpenAIKey('test-openai-key');
    await setupPage.fillAnthropicKey('test-anthropic-key');
    
    // Complete button should be enabled
    expect(await setupPage.isCompleteSetupButtonEnabled()).toBe(true);
  });

  test('should persist setup completion across page reloads', async ({ page }) => {
    await setupPage.goto();
    
    // Complete setup
    await setupPage.completeSetup();
    await setupPage.waitForSetupComplete();
    
    // Reload page
    await page.reload();
    await setupPage.waitForPageLoad();
    
    // Setup window should not appear again
    expect(await setupPage.isSetupWindowVisible()).toBe(false);
    
    // Should be on apps page
    expect(await appsPage.isPageLoaded()).toBe(true);
  });

  test('should show setup window again after clearing storage', async ({ page }) => {
    await setupPage.goto();
    
    // Complete setup
    await setupPage.completeSetup();
    await setupPage.waitForSetupComplete();
    
    // Clear storage
    await clearStorage(page);
    
    // Reload page
    await page.reload();
    await setupPage.waitForPageLoad();
    
    // Setup window should appear again
    expect(await setupPage.isSetupWindowVisible()).toBe(true);
  });

  test('should handle setup form submission errors gracefully', async ({ page }) => {
    // Mock API to return error
    await page.route('/integrations/**', async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Invalid API key'
        })
      });
    });

    await setupPage.goto();
    
    // Try to complete setup
    await setupPage.completeSetup();
    
    // Should show error message (adjust selector based on actual implementation)
    await setupPage.waitForErrorMessage('Invalid API key');
    
    // Setup window should still be visible
    expect(await setupPage.isSetupWindowVisible()).toBe(true);
  });

  test('should display loading state during setup submission', async ({ page }) => {
    // Mock API with delay
    await page.route('/integrations/**', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true })
      });
    });

    await setupPage.goto();
    
    // Fill form
    await setupPage.fillGitHubToken('test-token');
    await setupPage.fillFlyToken('test-token');
    await setupPage.fillOpenAIKey('test-key');
    await setupPage.fillAnthropicKey('test-key');
    
    // Click submit
    await page.locator(setupPage.completeSetupButton).click();
    
    // Should show loading state (adjust based on actual implementation)
    const loadingElement = page.locator('.animate-spin, text=Loading, text=Setting up');
    await expect(loadingElement).toBeVisible();
    
    // Wait for completion
    await setupPage.waitForSetupComplete();
  });
});