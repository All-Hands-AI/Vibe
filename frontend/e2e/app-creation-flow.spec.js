import { test, expect } from '@playwright/test';
import { SetupPage } from './pages/SetupPage.js';
import { AppsPage } from './pages/AppsPage.js';
import { AppDetailPage } from './pages/AppDetailPage.js';
import { setupTestEnvironment, generateTestAppName } from './utils/test-helpers.js';

test.describe('App Creation Flow', () => {
  let setupPage;
  let appsPage;
  let appDetailPage;

  test.beforeEach(async ({ page }) => {
    setupPage = new SetupPage(page);
    appsPage = new AppsPage(page);
    appDetailPage = new AppDetailPage(page);
    
    // Set up test environment with enhanced mocking
    await setupTestEnvironment(page);
    
    // Enhanced API mocking for app creation flow
    await page.route('/api/apps', async (route) => {
      const method = route.request().method();
      
      if (method === 'GET') {
        // Return list of apps (initially empty, then with created apps)
        const apps = page.evaluate(() => window.testApps || []);
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            apps: await apps,
            count: (await apps).length
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
          github_url: `https://github.com/testuser/${slug}`
        };
        
        // Store app in page context for subsequent GET requests
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
      const slug = url.split('/').pop();
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
        await page.evaluate((slugToDelete) => {
          window.testApps = (window.testApps || []).filter(app => app.slug !== slugToDelete);
        }, slug);
        
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            message: `App "${slug}" deleted successfully`,
            warnings: []
          })
        });
      }
    });
  });

  test('should create a new app successfully', async ({ page }) => {
    const appName = generateTestAppName();
    
    // Skip setup and go to apps page
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Verify we're on the apps page
    expect(await appsPage.isPageLoaded()).toBe(true);
    
    // Initially should show no apps
    await appsPage.waitForAppsToLoad();
    expect(await appsPage.isNoAppsMessageVisible()).toBe(true);
    expect(await appsPage.getAppCount()).toBe(0);
    
    // Create a new app
    await appsPage.createApp(appName);
    
    // Verify app was created and appears in the list
    await appsPage.waitForAppsToLoad();
    expect(await appsPage.appExists(appName)).toBe(true);
    expect(await appsPage.getAppCount()).toBe(1);
    
    // Verify app details
    const appDetails = await appsPage.getAppDetails(appName);
    expect(appDetails.name).toBe(appName);
    expect(appDetails.slug).toBe(appName.toLowerCase().replace(/[^a-zA-Z0-9\s-]/g, '').replace(/\s+/g, '-'));
  });

  test('should show slug preview while typing app name', async ({ page }) => {
    // Skip setup and go to apps page
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Type app name and check slug preview
    await appsPage.fillInput(appsPage.appNameInput, 'My Awesome App!');
    
    const slugPreview = await appsPage.getSlugPreview();
    expect(slugPreview).toBe('my-awesome-app');
  });

  test('should validate app name input', async ({ page }) => {
    // Skip setup and go to apps page
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Create button should be disabled with empty name
    expect(await appsPage.isCreateButtonEnabled()).toBe(false);
    
    // Fill app name
    await appsPage.fillInput(appsPage.appNameInput, 'Valid App Name');
    
    // Create button should be enabled
    expect(await appsPage.isCreateButtonEnabled()).toBe(true);
    
    // Clear app name
    await appsPage.fillInput(appsPage.appNameInput, '');
    
    // Create button should be disabled again
    expect(await appsPage.isCreateButtonEnabled()).toBe(false);
  });

  test('should handle app creation errors gracefully', async ({ page }) => {
    // Mock API to return error
    await page.route('/api/apps', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'App name already exists'
          })
        });
      }
    });
    
    // Skip setup and go to apps page
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    const appName = generateTestAppName();
    
    // Try to create app
    await appsPage.fillInput(appsPage.appNameInput, appName);
    await page.locator(appsPage.createAppButton).click();
    
    // Should show error message
    await appsPage.waitForErrorMessage('App name already exists');
    
    // App should not appear in list
    expect(await appsPage.appExists(appName)).toBe(false);
  });

  test('should create multiple apps and display them correctly', async ({ page }) => {
    // Skip setup and go to apps page
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    const appNames = [
      generateTestAppName(),
      generateTestAppName(),
      generateTestAppName()
    ];
    
    // Create multiple apps
    for (const appName of appNames) {
      await appsPage.createApp(appName);
      await appsPage.waitForAppsToLoad();
    }
    
    // Verify all apps are displayed
    expect(await appsPage.getAppCount()).toBe(3);
    
    for (const appName of appNames) {
      expect(await appsPage.appExists(appName)).toBe(true);
    }
    
    // Verify no apps message is not visible
    expect(await appsPage.isNoAppsMessageVisible()).toBe(false);
  });

  test('should navigate to app detail page when clicking on app', async ({ page }) => {
    const appName = generateTestAppName();
    
    // Skip setup and go to apps page
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Create an app
    await appsPage.createApp(appName);
    await appsPage.waitForAppsToLoad();
    
    // Click on the app card
    await appsPage.clickAppCard(appName);
    
    // Should navigate to app detail page
    expect(await appDetailPage.isPageLoaded()).toBe(true);
    expect(await appDetailPage.getAppName()).toBe(appName);
  });

  test('should clear form after successful app creation', async ({ page }) => {
    const appName = generateTestAppName();
    
    // Skip setup and go to apps page
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Create an app
    await appsPage.createApp(appName);
    
    // Form should be cleared
    expect(await appsPage.getAppNameInputValue()).toBe('');
    expect(await appsPage.getSlugPreview()).toBe(null);
  });

  test('should show loading state during app creation', async ({ page }) => {
    // Mock API with delay
    await page.route('/api/apps', async (route) => {
      if (route.request().method() === 'POST') {
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const requestBody = route.request().postDataJSON();
        const slug = requestBody.name.toLowerCase().replace(/[^a-zA-Z0-9\s-]/g, '').replace(/\s+/g, '-');
        
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            message: 'App created successfully',
            app: {
              name: requestBody.name,
              slug: slug,
              created_at: new Date().toISOString(),
              created_by: 'test-user',
              fly_app_name: `openvibe-${slug}`,
              github_url: `https://github.com/testuser/${slug}`
            }
          })
        });
      }
    });
    
    const appName = generateTestAppName();
    
    // Skip setup and go to apps page
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Fill app name and click create
    await appsPage.fillInput(appsPage.appNameInput, appName);
    await page.locator(appsPage.createAppButton).click();
    
    // Should show loading state
    await expect(page.locator('button:has-text("Creating...")')).toBeVisible();
    
    // Wait for completion
    await appsPage.waitForSuccessMessage();
  });

  test('should handle special characters in app names', async ({ page }) => {
    // Skip setup and go to apps page
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    const testCases = [
      { name: 'App with Spaces', expectedSlug: 'app-with-spaces' },
      { name: 'App-With-Hyphens', expectedSlug: 'app-with-hyphens' },
      { name: 'App_With_Underscores', expectedSlug: 'appwithunderscores' },
      { name: 'App123 With Numbers', expectedSlug: 'app123-with-numbers' },
      { name: 'App!@# With Special', expectedSlug: 'app-with-special' }
    ];
    
    for (const testCase of testCases) {
      // Fill app name and check slug preview
      await appsPage.fillInput(appsPage.appNameInput, testCase.name);
      
      const slugPreview = await appsPage.getSlugPreview();
      expect(slugPreview).toBe(testCase.expectedSlug);
      
      // Create the app
      await page.locator(appsPage.createAppButton).click();
      await appsPage.waitForSuccessMessage();
      
      // Verify app was created with correct slug
      const appDetails = await appsPage.getAppDetails(testCase.name);
      expect(appDetails.slug).toBe(testCase.expectedSlug);
      
      // Clear form for next test
      await appsPage.fillInput(appsPage.appNameInput, '');
    }
  });
});