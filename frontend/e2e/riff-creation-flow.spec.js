import { test, expect } from '@playwright/test';
import { SetupPage } from './pages/SetupPage.js';
import { AppsPage } from './pages/AppsPage.js';
import { AppDetailPage } from './pages/AppDetailPage.js';
import { RiffDetailPage } from './pages/RiffDetailPage.js';
import { setupTestEnvironment, generateTestAppName, generateTestRiffName } from './utils/test-helpers.js';

test.describe('Riff Creation Flow', () => {
  let setupPage;
  let appsPage;
  let appDetailPage;
  let riffDetailPage;

  test.beforeEach(async ({ page }) => {
    setupPage = new SetupPage(page);
    appsPage = new AppsPage(page);
    appDetailPage = new AppDetailPage(page);
    riffDetailPage = new RiffDetailPage(page);
    
    // Set up test environment with comprehensive riff mocking
    await setupTestEnvironment(page);
    
    // Enhanced API mocking for riff creation flow
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
      const appSlugIndex = pathParts.indexOf('apps') + 1;
      const appSlug = pathParts[appSlugIndex];
      const method = route.request().method();
      
      // Handle riff-related endpoints
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
        } else if (method === 'GET' && riffSlug) {
          // Get specific riff
          const apps = await page.evaluate(() => window.testApps || []);
          const app = apps.find(a => a.slug === appSlug);
          const riff = app?.riffs?.find(r => r.slug === riffSlug);
          
          if (riff) {
            await route.fulfill({
              status: 200,
              contentType: 'application/json',
              body: JSON.stringify(riff)
            });
          } else {
            await route.fulfill({
              status: 404,
              contentType: 'application/json',
              body: JSON.stringify({ error: 'Riff not found' })
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
    
    // Mock chat/message endpoints
    await page.route('/api/apps/*/riffs/*/messages', async (route) => {
      const method = route.request().method();
      
      if (method === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            messages: [],
            count: 0
          })
        });
      } else if (method === 'POST') {
        const requestBody = route.request().postDataJSON();
        const newMessage = {
          id: Date.now(),
          content: requestBody.content,
          role: 'user',
          created_at: new Date().toISOString()
        };
        
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            message: 'Message sent successfully',
            data: newMessage
          })
        });
      }
    });
  });

  test('should create a riff in an app successfully', async ({ page }) => {
    const appName = generateTestAppName();
    const riffName = generateTestRiffName();
    
    // Skip setup and create app
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    await appsPage.createApp(appName);
    await appsPage.clickAppCard(appName);
    
    // Should be on app detail page
    expect(await appDetailPage.isPageLoaded()).toBe(true);
    expect(await appDetailPage.isNoRiffsMessageVisible()).toBe(true);
    
    // Create a riff
    await appDetailPage.createRiff(riffName, 'Test riff description');
    
    // Riff should appear in the list
    expect(await appDetailPage.riffExists(riffName)).toBe(true);
    expect(await appDetailPage.getRiffCount()).toBe(1);
    expect(await appDetailPage.isNoRiffsMessageVisible()).toBe(false);
  });

  test('should navigate to riff detail page after creation', async ({ page }) => {
    const appName = generateTestAppName();
    const riffName = generateTestRiffName();
    
    // Skip setup and create app
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    await appsPage.createApp(appName);
    await appsPage.clickAppCard(appName);
    
    // Create a riff
    await appDetailPage.createRiff(riffName);
    
    // Click on the riff to view details
    await appDetailPage.clickRiff(riffName);
    
    // Should be on riff detail page
    expect(await riffDetailPage.isPageLoaded()).toBe(true);
    expect(await riffDetailPage.getRiffName()).toBe(riffName);
  });

  test('should show riff detail page with chat interface', async ({ page }) => {
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
    
    // Should show riff details
    expect(await riffDetailPage.getRiffName()).toBe(riffName);
    
    // Should show chat interface
    expect(await riffDetailPage.isChatWindowVisible()).toBe(true);
    
    // Should show branch status
    expect(await riffDetailPage.isBranchStatusVisible()).toBe(true);
    
    // Should show proper breadcrumbs
    const breadcrumbs = await riffDetailPage.getBreadcrumbs();
    expect(breadcrumbs).toContain('Apps');
    expect(breadcrumbs).toContain(appName);
    expect(breadcrumbs).toContain(riffName);
  });

  test('should validate riff name input', async ({ page }) => {
    const appName = generateTestAppName();
    
    // Skip setup and create app
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    await appsPage.createApp(appName);
    await appsPage.clickAppCard(appName);
    
    // Try to create riff with empty name
    await page.locator(appDetailPage.createRiffButton).click();
    await page.locator(appDetailPage.createRiffSubmitButton).click();
    
    // Should show error message
    await appDetailPage.waitForErrorMessage('Riff name is required');
    
    // Fill valid name
    await appDetailPage.fillInput(appDetailPage.riffNameInput, 'Valid Riff Name');
    await page.locator(appDetailPage.createRiffSubmitButton).click();
    
    // Should create successfully
    await appDetailPage.waitForSuccessMessage();
  });

  test('should handle riff creation errors gracefully', async ({ page }) => {
    // Mock API to return error
    await page.route('/api/apps/*/riffs', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Riff name already exists'
          })
        });
      }
    });
    
    const appName = generateTestAppName();
    const riffName = generateTestRiffName();
    
    // Skip setup and create app
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    await appsPage.createApp(appName);
    await appsPage.clickAppCard(appName);
    
    // Try to create riff
    await appDetailPage.createRiff(riffName);
    
    // Should show error message
    await appDetailPage.waitForErrorMessage('Riff name already exists');
    
    // Riff should not appear in list
    expect(await appDetailPage.riffExists(riffName)).toBe(false);
  });

  test('should create multiple riffs in an app', async ({ page }) => {
    const appName = generateTestAppName();
    const riffNames = [
      generateTestRiffName(),
      generateTestRiffName(),
      generateTestRiffName()
    ];
    
    // Skip setup and create app
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    await appsPage.createApp(appName);
    await appsPage.clickAppCard(appName);
    
    // Create multiple riffs
    for (const riffName of riffNames) {
      await appDetailPage.createRiff(riffName);
    }
    
    // All riffs should be displayed
    expect(await appDetailPage.getRiffCount()).toBe(3);
    
    for (const riffName of riffNames) {
      expect(await appDetailPage.riffExists(riffName)).toBe(true);
    }
  });

  test('should show loading state during riff creation', async ({ page }) => {
    // Mock API with delay
    await page.route('/api/apps/*/riffs', async (route) => {
      if (route.request().method() === 'POST') {
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const requestBody = route.request().postDataJSON();
        const riffSlug = requestBody.name.toLowerCase().replace(/[^a-zA-Z0-9\s-]/g, '').replace(/\s+/g, '-');
        
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            message: 'Riff created successfully',
            riff: {
              name: requestBody.name,
              slug: riffSlug,
              created_at: new Date().toISOString(),
              created_by: 'test-user'
            }
          })
        });
      }
    });
    
    const appName = generateTestAppName();
    const riffName = generateTestRiffName();
    
    // Skip setup and create app
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    await appsPage.createApp(appName);
    await appsPage.clickAppCard(appName);
    
    // Start creating riff
    await page.locator(appDetailPage.createRiffButton).click();
    await appDetailPage.fillInput(appDetailPage.riffNameInput, riffName);
    await page.locator(appDetailPage.createRiffSubmitButton).click();
    
    // Should show loading state
    await expect(page.locator('button:has-text("Creating..."), .animate-spin')).toBeVisible();
    
    // Wait for completion
    await appDetailPage.waitForSuccessMessage();
  });

  test('should clear form after successful riff creation', async ({ page }) => {
    const appName = generateTestAppName();
    const riffName = generateTestRiffName();
    
    // Skip setup and create app
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    await appsPage.createApp(appName);
    await appsPage.clickAppCard(appName);
    
    // Create riff
    await appDetailPage.createRiff(riffName, 'Test description');
    
    // Form should be cleared
    const nameInput = page.locator(appDetailPage.riffNameInput);
    const descInput = page.locator(appDetailPage.riffDescriptionInput);
    
    if (await nameInput.count() > 0) {
      expect(await nameInput.inputValue()).toBe('');
    }
    if (await descInput.count() > 0) {
      expect(await descInput.inputValue()).toBe('');
    }
  });

  test('should navigate between riff detail and app detail pages', async ({ page }) => {
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
    
    // Go back to app detail
    await riffDetailPage.goBackToApp();
    
    // Should be back on app detail page
    expect(await appDetailPage.isPageLoaded()).toBe(true);
    expect(await appDetailPage.getAppName()).toBe(appName);
    
    // Riff should still be in the list
    expect(await appDetailPage.riffExists(riffName)).toBe(true);
  });

  test('should handle special characters in riff names', async ({ page }) => {
    const appName = generateTestAppName();
    
    // Skip setup and create app
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    await appsPage.createApp(appName);
    await appsPage.clickAppCard(appName);
    
    const testCases = [
      { name: 'Riff with Spaces', expectedSlug: 'riff-with-spaces' },
      { name: 'Riff-With-Hyphens', expectedSlug: 'riff-with-hyphens' },
      { name: 'Riff_With_Underscores', expectedSlug: 'riffwithunderscores' },
      { name: 'Riff123 With Numbers', expectedSlug: 'riff123-with-numbers' },
      { name: 'Riff!@# With Special', expectedSlug: 'riff-with-special' }
    ];
    
    for (const testCase of testCases) {
      // Create riff
      await appDetailPage.createRiff(testCase.name);
      
      // Verify riff was created
      expect(await appDetailPage.riffExists(testCase.name)).toBe(true);
      
      // Click on riff to verify slug
      await appDetailPage.clickRiff(testCase.name);
      
      // Check that we're on the correct riff page
      expect(await riffDetailPage.getRiffName()).toBe(testCase.name);
      
      // Go back to app detail for next test
      await riffDetailPage.goBackToApp();
    }
  });
});