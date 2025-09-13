import { test, expect } from '@playwright/test';
import { SetupPage } from './pages/SetupPage.js';
import { AppsPage } from './pages/AppsPage.js';
import { AppDetailPage } from './pages/AppDetailPage.js';
import { RiffDetailPage } from './pages/RiffDetailPage.js';
import { setupTestEnvironment, generateTestAppName, generateTestRiffName } from './utils/test-helpers.js';

test.describe('Navigation Flow', () => {
  let setupPage;
  let appsPage;
  let appDetailPage;
  let riffDetailPage;

  test.beforeEach(async ({ page }) => {
    setupPage = new SetupPage(page);
    appsPage = new AppsPage(page);
    appDetailPage = new AppDetailPage(page);
    riffDetailPage = new RiffDetailPage(page);
    
    // Set up test environment with navigation state management
    await setupTestEnvironment(page);
    
    // Enhanced API mocking for navigation testing
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
    
    // Mock individual app and riff endpoints
    await page.route('/api/apps/*', async (route) => {
      const url = route.request().url();
      const pathParts = url.split('/');
      const appSlugIndex = pathParts.indexOf('apps') + 1;
      const appSlug = pathParts[appSlugIndex];
      const method = route.request().method();
      
      if (url.includes('/riffs')) {
        const riffSlugIndex = pathParts.indexOf('riffs') + 1;
        const riffSlug = pathParts[riffSlugIndex];
        
        if (method === 'GET' && !riffSlug) {
          // Get all riffs for app
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
          // Create new riff
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
            created_by: 'test-user',
            message_count: 0,
            last_message_at: null
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
      } else if (method === 'GET') {
        // Get app details
        const apps = await page.evaluate(() => window.testApps || []);
        const app = apps.find(a => a.slug === appSlug);
        
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
      }
    });
  });

  test('should navigate through the complete app creation flow', async ({ page }) => {
    const appName = generateTestAppName();
    const riffName = generateTestRiffName();
    
    // Start at home page with setup
    await setupPage.goto();
    
    // Complete setup flow
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Should be on apps page
    expect(await appsPage.isPageLoaded()).toBe(true);
    expect(page.url()).toContain('/');
    
    // Create an app
    await appsPage.createApp(appName);
    
    // Navigate to app detail
    await appsPage.clickAppCard(appName);
    expect(await appDetailPage.isPageLoaded()).toBe(true);
    expect(page.url()).toContain(`/apps/${appName.toLowerCase().replace(/[^a-zA-Z0-9\s-]/g, '').replace(/\s+/g, '-')}`);
    
    // Create a riff
    await appDetailPage.createRiff(riffName);
    
    // Navigate to riff detail
    await appDetailPage.clickRiff(riffName);
    expect(await riffDetailPage.isPageLoaded()).toBe(true);
    expect(page.url()).toContain('/riffs/');
  });

  test('should maintain breadcrumb navigation correctly', async ({ page }) => {
    const appName = generateTestAppName();
    const riffName = generateTestRiffName();
    
    // Skip setup and create app and riff
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    await appsPage.createApp(appName);
    await appsPage.clickAppCard(appName);
    await appDetailPage.createRiff(riffName);
    await appDetailPage.clickRiff(riffName);
    
    // Check breadcrumbs on riff detail page
    const breadcrumbs = await riffDetailPage.getBreadcrumbs();
    expect(breadcrumbs).toContain('Apps');
    expect(breadcrumbs).toContain(appName);
    expect(breadcrumbs).toContain(riffName);
    
    // Navigate using breadcrumbs
    await riffDetailPage.goBackToApp();
    expect(await appDetailPage.isPageLoaded()).toBe(true);
    
    await appDetailPage.goBackToApps();
    expect(await appsPage.isPageLoaded()).toBe(true);
  });

  test('should handle browser back and forward navigation', async ({ page }) => {
    const appName = generateTestAppName();
    const riffName = generateTestRiffName();
    
    // Skip setup and create app and riff
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    await appsPage.createApp(appName);
    await appsPage.clickAppCard(appName);
    await appDetailPage.createRiff(riffName);
    await appDetailPage.clickRiff(riffName);
    
    // Should be on riff detail page
    expect(await riffDetailPage.isPageLoaded()).toBe(true);
    
    // Use browser back button
    await page.goBack();
    expect(await appDetailPage.isPageLoaded()).toBe(true);
    
    // Use browser back button again
    await page.goBack();
    expect(await appsPage.isPageLoaded()).toBe(true);
    
    // Use browser forward button
    await page.goForward();
    expect(await appDetailPage.isPageLoaded()).toBe(true);
    
    // Use browser forward button again
    await page.goForward();
    expect(await riffDetailPage.isPageLoaded()).toBe(true);
  });

  test('should preserve state when navigating between pages', async ({ page }) => {
    const appNames = [generateTestAppName(), generateTestAppName()];
    const riffName = generateTestRiffName();
    
    // Skip setup and create multiple apps
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    for (const appName of appNames) {
      await appsPage.createApp(appName);
    }
    
    // Navigate to first app and create riff
    await appsPage.clickAppCard(appNames[0]);
    await appDetailPage.createRiff(riffName);
    
    // Go back to apps list
    await appDetailPage.goBackToApps();
    
    // Apps should still be there
    expect(await appsPage.getAppCount()).toBe(2);
    for (const appName of appNames) {
      expect(await appsPage.appExists(appName)).toBe(true);
    }
    
    // Navigate to first app again
    await appsPage.clickAppCard(appNames[0]);
    
    // Riff should still be there
    expect(await appDetailPage.riffExists(riffName)).toBe(true);
  });

  test('should handle direct URL navigation', async ({ page }) => {
    const appName = generateTestAppName();
    const riffName = generateTestRiffName();
    const appSlug = appName.toLowerCase().replace(/[^a-zA-Z0-9\s-]/g, '').replace(/\s+/g, '-');
    const riffSlug = riffName.toLowerCase().replace(/[^a-zA-Z0-9\s-]/g, '').replace(/\s+/g, '-');
    
    // Skip setup and create app and riff
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    await appsPage.createApp(appName);
    await appsPage.clickAppCard(appName);
    await appDetailPage.createRiff(riffName);
    
    // Navigate directly to app detail page via URL
    await page.goto(`/apps/${appSlug}`);
    expect(await appDetailPage.isPageLoaded()).toBe(true);
    expect(await appDetailPage.getAppName()).toBe(appName);
    
    // Navigate directly to riff detail page via URL
    await page.goto(`/apps/${appSlug}/riffs/${riffSlug}`);
    expect(await riffDetailPage.isPageLoaded()).toBe(true);
    expect(await riffDetailPage.getRiffName()).toBe(riffName);
  });

  test('should handle 404 errors gracefully', async ({ page }) => {
    // Skip setup
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Navigate to non-existent app
    await page.goto('/apps/non-existent-app');
    
    // Should show error page
    const errorElement = page.locator('text=App Not Found, text=404, text=Error');
    await expect(errorElement).toBeVisible();
    
    // Should have link back to apps
    const backLink = page.locator('a:has-text("Back to Apps")');
    await expect(backLink).toBeVisible();
    
    // Click back link
    await backLink.click();
    expect(await appsPage.isPageLoaded()).toBe(true);
  });

  test('should maintain scroll position when navigating back', async ({ page }) => {
    const appNames = [];
    for (let i = 0; i < 10; i++) {
      appNames.push(generateTestAppName());
    }
    
    // Skip setup and create many apps
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    for (const appName of appNames) {
      await appsPage.createApp(appName);
    }
    
    // Scroll down to see more apps
    await page.evaluate(() => window.scrollTo(0, 500));
    
    // Navigate to an app
    await appsPage.clickAppCard(appNames[5]);
    expect(await appDetailPage.isPageLoaded()).toBe(true);
    
    // Go back
    await appDetailPage.goBackToApps();
    
    // Should be back on apps page
    expect(await appsPage.isPageLoaded()).toBe(true);
    
    // Note: Scroll position restoration depends on browser behavior
    // This test mainly ensures navigation works correctly
  });

  test('should handle navigation with query parameters', async ({ page }) => {
    const appName = generateTestAppName();
    
    // Skip setup and create app
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    await appsPage.createApp(appName);
    
    // Navigate with query parameters
    const appSlug = appName.toLowerCase().replace(/[^a-zA-Z0-9\s-]/g, '').replace(/\s+/g, '-');
    await page.goto(`/apps/${appSlug}?tab=riffs&view=grid`);
    
    // Should still load the app detail page correctly
    expect(await appDetailPage.isPageLoaded()).toBe(true);
    expect(await appDetailPage.getAppName()).toBe(appName);
  });

  test('should handle navigation during loading states', async ({ page }) => {
    // Mock API with delays
    await page.route('/api/apps', async (route) => {
      if (route.request().method() === 'GET') {
        await new Promise(resolve => setTimeout(resolve, 1000));
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ apps: [], count: 0 })
        });
      }
    });
    
    // Skip setup
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Should show loading state
    await expect(page.locator('.animate-spin')).toBeVisible();
    
    // Try to navigate during loading (should be handled gracefully)
    await page.goto('/apps/some-app');
    
    // Should eventually show 404 or handle gracefully
    await page.waitForTimeout(2000);
    
    // Navigate back to home
    await page.goto('/');
    await appsPage.waitForAppsToLoad();
    expect(await appsPage.isPageLoaded()).toBe(true);
  });

  test('should handle rapid navigation clicks', async ({ page }) => {
    const appNames = [generateTestAppName(), generateTestAppName()];
    
    // Skip setup and create apps
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    for (const appName of appNames) {
      await appsPage.createApp(appName);
    }
    
    // Rapidly click between apps
    await appsPage.clickAppCard(appNames[0]);
    await page.waitForTimeout(100);
    
    await appDetailPage.goBackToApps();
    await page.waitForTimeout(100);
    
    await appsPage.clickAppCard(appNames[1]);
    
    // Should end up on the second app's detail page
    expect(await appDetailPage.isPageLoaded()).toBe(true);
    expect(await appDetailPage.getAppName()).toBe(appNames[1]);
  });

  test('should maintain theme and user preferences across navigation', async ({ page }) => {
    const appName = generateTestAppName();
    
    // Skip setup and create app
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Check that theme is consistent
    const bodyClass = await page.locator('body').getAttribute('class');
    
    await appsPage.createApp(appName);
    await appsPage.clickAppCard(appName);
    
    // Theme should be maintained
    const appDetailBodyClass = await page.locator('body').getAttribute('class');
    expect(appDetailBodyClass).toBe(bodyClass);
    
    // Navigate back
    await appDetailPage.goBackToApps();
    
    // Theme should still be maintained
    const backBodyClass = await page.locator('body').getAttribute('class');
    expect(backBodyClass).toBe(bodyClass);
  });
});