import { test, expect } from '@playwright/test';
import { SetupPage } from './pages/SetupPage.js';
import { AppsPage } from './pages/AppsPage.js';
import { AppDetailPage } from './pages/AppDetailPage.js';
import { setupTestEnvironment, generateTestAppName } from './utils/test-helpers.js';

test.describe('App Management Flow', () => {
  let setupPage;
  let appsPage;
  let appDetailPage;

  test.beforeEach(async ({ page }) => {
    setupPage = new SetupPage(page);
    appsPage = new AppsPage(page);
    appDetailPage = new AppDetailPage(page);
    
    // Set up test environment with comprehensive app management mocking
    await setupTestEnvironment(page);
    
    // Enhanced API mocking for app management
    await page.route('/api/apps', async (route) => {
      const method = route.request().method();
      
      if (method === 'GET') {
        const apps = await page.evaluate(() => window.testApps || []);
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            apps: apps,
            count: apps.length
          })
        });
      } else if (method === 'POST') {
        const requestBody = route.request().postDataJSON();
        const slug = requestBody.name.toLowerCase()
          .replace(/[^a-zA-Z0-9\s-]/g, '')
          .replace(/\s+/g, '-')
          .replace(/-+/g, '-')
          .replace(/^-|-$/g, '');
        
        const newApp = {
          name: requestBody.name,
          slug: slug,
          created_at: new Date().toISOString(),
          created_by: 'test-user',
          fly_app_name: `openvibe-${slug}`,
          github_url: `https://github.com/testuser/${slug}`,
          riffs: []
        };
        
        await page.evaluate((app) => {
          window.testApps = window.testApps || [];
          window.testApps.push(app);
        }, newApp);
        
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            message: 'App created successfully',
            app: newApp
          })
        });
      }
    });
    
    // Mock individual app endpoints
    await page.route('/api/apps/*', async (route) => {
      const url = route.request().url();
      const pathParts = url.split('/');
      const slug = pathParts[pathParts.indexOf('apps') + 1];
      const method = route.request().method();
      
      if (method === 'GET') {
        const apps = await page.evaluate(() => window.testApps || []);
        const app = apps.find(a => a.slug === slug);
        
        if (app) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(app)
          });
        } else {
          await route.fulfill({
            status: 404,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'App not found' })
          });
        }
      } else if (method === 'DELETE') {
        const apps = await page.evaluate(() => window.testApps || []);
        const appToDelete = apps.find(a => a.slug === slug);
        
        if (appToDelete) {
          await page.evaluate((slugToDelete) => {
            window.testApps = (window.testApps || []).filter(app => app.slug !== slugToDelete);
          }, slug);
          
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              message: `App "${appToDelete.name}" deleted successfully`,
              warnings: []
            })
          });
        } else {
          await route.fulfill({
            status: 404,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'App not found' })
          });
        }
      }
    });
    
    // Mock riffs endpoints
    await page.route('/api/apps/*/riffs', async (route) => {
      const url = route.request().url();
      const pathParts = url.split('/');
      const appSlug = pathParts[pathParts.indexOf('apps') + 1];
      const method = route.request().method();
      
      if (method === 'GET') {
        const apps = await page.evaluate(() => window.testApps || []);
        const app = apps.find(a => a.slug === appSlug);
        
        if (app) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              riffs: app.riffs || [],
              count: (app.riffs || []).length
            })
          });
        } else {
          await route.fulfill({
            status: 404,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'App not found' })
          });
        }
      } else if (method === 'POST') {
        const requestBody = route.request().postDataJSON();
        const riffSlug = requestBody.name.toLowerCase()
          .replace(/[^a-zA-Z0-9\s-]/g, '')
          .replace(/\s+/g, '-')
          .replace(/-+/g, '-')
          .replace(/^-|-$/g, '');
        
        const newRiff = {
          name: requestBody.name,
          slug: riffSlug,
          description: requestBody.description || '',
          created_at: new Date().toISOString(),
          created_by: 'test-user'
        };
        
        await page.evaluate((appSlug, riff) => {
          window.testApps = window.testApps || [];
          const app = window.testApps.find(a => a.slug === appSlug);
          if (app) {
            app.riffs = app.riffs || [];
            app.riffs.push(riff);
          }
        }, appSlug, newRiff);
        
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            message: 'Riff created successfully',
            riff: newRiff
          })
        });
      }
    });
  });

  test('should view app details after creation', async ({ page }) => {
    const appName = generateTestAppName();
    
    // Skip setup and go to apps page
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Create an app
    await appsPage.createApp(appName);
    await appsPage.waitForAppsToLoad();
    
    // Click on the app to view details
    await appsPage.clickAppCard(appName);
    
    // Should be on app detail page
    expect(await appDetailPage.isPageLoaded()).toBe(true);
    expect(await appDetailPage.getAppName()).toBe(appName);
    
    // Should show no riffs initially
    expect(await appDetailPage.isNoRiffsMessageVisible()).toBe(true);
    expect(await appDetailPage.getRiffCount()).toBe(0);
  });

  test('should navigate back to apps list from app detail', async ({ page }) => {
    const appName = generateTestAppName();
    
    // Skip setup and create app
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    await appsPage.createApp(appName);
    await appsPage.clickAppCard(appName);
    
    // Should be on app detail page
    expect(await appDetailPage.isPageLoaded()).toBe(true);
    
    // Go back to apps list
    await appDetailPage.goBackToApps();
    
    // Should be back on apps page
    expect(await appsPage.isPageLoaded()).toBe(true);
    expect(await appsPage.appExists(appName)).toBe(true);
  });

  test('should delete an app successfully', async ({ page }) => {
    const appName = generateTestAppName();
    
    // Skip setup and create app
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    await appsPage.createApp(appName);
    await appsPage.waitForAppsToLoad();
    
    // Verify app exists
    expect(await appsPage.appExists(appName)).toBe(true);
    expect(await appsPage.getAppCount()).toBe(1);
    
    // Delete the app
    await appsPage.deleteApp(appName);
    
    // App should be removed from list
    await appsPage.waitForAppsToLoad();
    expect(await appsPage.appExists(appName)).toBe(false);
    expect(await appsPage.getAppCount()).toBe(0);
    expect(await appsPage.isNoAppsMessageVisible()).toBe(true);
  });

  test('should show confirmation modal before deleting app', async ({ page }) => {
    const appName = generateTestAppName();
    
    // Skip setup and create app
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    await appsPage.createApp(appName);
    await appsPage.waitForAppsToLoad();
    
    // Click delete button
    const card = page.locator(appsPage.appCards).filter({ hasText: appName });
    const deleteButton = card.locator('button[title*="Delete app"]');
    await deleteButton.click();
    
    // Confirmation modal should appear
    const modal = page.locator('.modal, [role="dialog"]');
    await expect(modal).toBeVisible();
    
    // Modal should contain app name and warning
    await expect(page.locator(`text="${appName}"`)).toBeVisible();
    await expect(page.locator('text=This action cannot be undone')).toBeVisible();
    
    // Cancel deletion
    await page.locator('button:has-text("Cancel")').click();
    
    // App should still exist
    expect(await appsPage.appExists(appName)).toBe(true);
  });

  test('should handle app deletion errors gracefully', async ({ page }) => {
    // Mock API to return error
    await page.route('/api/apps/*', async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Failed to delete app'
          })
        });
      }
    });
    
    const appName = generateTestAppName();
    
    // Skip setup and create app
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    await appsPage.createApp(appName);
    
    // Try to delete app
    const card = page.locator(appsPage.appCards).filter({ hasText: appName });
    const deleteButton = card.locator('button[title*="Delete app"]');
    await deleteButton.click();
    
    // Confirm deletion
    await page.locator('button:has-text("Delete App")').click();
    
    // Should show error message
    await appsPage.waitForErrorMessage('Failed to delete app');
    
    // App should still exist
    expect(await appsPage.appExists(appName)).toBe(true);
  });

  test('should manage multiple apps correctly', async ({ page }) => {
    const appNames = [
      generateTestAppName(),
      generateTestAppName(),
      generateTestAppName()
    ];
    
    // Skip setup and create multiple apps
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    for (const appName of appNames) {
      await appsPage.createApp(appName);
      await appsPage.waitForAppsToLoad();
    }
    
    // Verify all apps exist
    expect(await appsPage.getAppCount()).toBe(3);
    for (const appName of appNames) {
      expect(await appsPage.appExists(appName)).toBe(true);
    }
    
    // Delete middle app
    await appsPage.deleteApp(appNames[1]);
    await appsPage.waitForAppsToLoad();
    
    // Verify correct app was deleted
    expect(await appsPage.getAppCount()).toBe(2);
    expect(await appsPage.appExists(appNames[0])).toBe(true);
    expect(await appsPage.appExists(appNames[1])).toBe(false);
    expect(await appsPage.appExists(appNames[2])).toBe(true);
    
    // View details of remaining app
    await appsPage.clickAppCard(appNames[0]);
    expect(await appDetailPage.isPageLoaded()).toBe(true);
    expect(await appDetailPage.getAppName()).toBe(appNames[0]);
  });

  test('should display app metadata correctly', async ({ page }) => {
    const appName = generateTestAppName();
    
    // Skip setup and create app
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    await appsPage.createApp(appName);
    await appsPage.waitForAppsToLoad();
    
    // Get app details from card
    const appDetails = await appsPage.getAppDetails(appName);
    
    // Verify app details
    expect(appDetails.name).toBe(appName);
    expect(appDetails.slug).toBeTruthy();
    expect(appDetails.createdDate).toBeTruthy();
    
    // Click on app to view full details
    await appsPage.clickAppCard(appName);
    
    // Verify details on app page
    expect(await appDetailPage.getAppName()).toBe(appName);
    expect(await appDetailPage.getAppSlug()).toBe(appDetails.slug);
  });

  test('should handle app not found error', async ({ page }) => {
    // Skip setup
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Try to navigate to non-existent app
    await appDetailPage.goto('non-existent-app');
    
    // Should show 404 or error message
    const errorElement = page.locator('text=App not found, text=404, text=Not Found');
    await expect(errorElement).toBeVisible();
  });

  test('should show loading states during app operations', async ({ page }) => {
    // Mock API with delays
    await page.route('/api/apps', async (route) => {
      const method = route.request().method();
      
      if (method === 'GET') {
        await new Promise(resolve => setTimeout(resolve, 500));
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ apps: [], count: 0 })
        });
      }
    });
    
    await page.route('/api/apps/*', async (route) => {
      if (route.request().method() === 'DELETE') {
        await new Promise(resolve => setTimeout(resolve, 1000));
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            message: 'App deleted successfully',
            warnings: []
          })
        });
      }
    });
    
    // Skip setup and go to apps page
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Should show loading spinner while fetching apps
    await expect(page.locator('.animate-spin')).toBeVisible();
    await appsPage.waitForAppsToLoad();
    
    // Create an app for deletion test
    await appsPage.createApp(generateTestAppName());
    
    // Test deletion loading state
    const card = page.locator(appsPage.appCards).first();
    const deleteButton = card.locator('button[title*="Delete app"]');
    await deleteButton.click();
    
    // Confirm deletion
    await page.locator('button:has-text("Delete App")').click();
    
    // Should show loading state in modal
    const loadingElement = page.locator('.animate-spin, text=Deleting, button:disabled');
    await expect(loadingElement).toBeVisible();
  });

  test('should preserve app list state when navigating back', async ({ page }) => {
    const appNames = [generateTestAppName(), generateTestAppName()];
    
    // Skip setup and create apps
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    for (const appName of appNames) {
      await appsPage.createApp(appName);
    }
    
    // Navigate to first app
    await appsPage.clickAppCard(appNames[0]);
    expect(await appDetailPage.isPageLoaded()).toBe(true);
    
    // Go back to apps list
    await appDetailPage.goBackToApps();
    
    // Apps should still be there
    expect(await appsPage.getAppCount()).toBe(2);
    for (const appName of appNames) {
      expect(await appsPage.appExists(appName)).toBe(true);
    }
  });
});