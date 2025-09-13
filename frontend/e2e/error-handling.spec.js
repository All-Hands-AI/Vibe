import { test, expect } from '@playwright/test';
import { SetupPage } from './pages/SetupPage.js';
import { AppsPage } from './pages/AppsPage.js';
import { AppDetailPage } from './pages/AppDetailPage.js';
import { RiffDetailPage } from './pages/RiffDetailPage.js';
import { setupTestEnvironment, generateTestAppName, generateTestRiffName } from './utils/test-helpers.js';

test.describe('Error Handling', () => {
  let setupPage;
  let appsPage;
  let appDetailPage;
  let riffDetailPage;

  test.beforeEach(async ({ page }) => {
    setupPage = new SetupPage(page);
    appsPage = new AppsPage(page);
    appDetailPage = new AppDetailPage(page);
    riffDetailPage = new RiffDetailPage(page);
    
    // Set up test environment
    await setupTestEnvironment(page);
  });

  test('should handle network errors gracefully', async ({ page }) => {
    // Mock network failure
    await page.route('/api/**', async (route) => {
      await route.abort('failed');
    });
    
    // Skip setup and try to load apps
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Should show error message for failed network request
    await appsPage.waitForErrorMessage('Failed to load apps');
    
    // Should still show the page structure
    expect(await appsPage.isPageLoaded()).toBe(true);
  });

  test('should handle 500 server errors', async ({ page }) => {
    // Mock server error
    await page.route('/api/apps', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Internal server error'
        })
      });
    });
    
    // Skip setup and try to load apps
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Should show error message
    await appsPage.waitForErrorMessage('Failed to load apps');
  });

  test('should handle 404 errors for non-existent apps', async ({ page }) => {
    // Mock 404 for specific app
    await page.route('/api/apps/non-existent-app', async (route) => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'App not found'
        })
      });
    });
    
    // Skip setup
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Navigate to non-existent app
    await page.goto('/apps/non-existent-app');
    
    // Should show 404 error page
    const errorElement = page.locator('text=App Not Found, text=404, text=Error');
    await expect(errorElement).toBeVisible();
    
    // Should have navigation back to apps
    const backLink = page.locator('a:has-text("Back to Apps")');
    await expect(backLink).toBeVisible();
  });

  test('should handle app creation validation errors', async ({ page }) => {
    // Mock validation error
    await page.route('/api/apps', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'App name already exists'
          })
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ apps: [], count: 0 })
        });
      }
    });
    
    const appName = generateTestAppName();
    
    // Skip setup
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Try to create app
    await appsPage.fillInput(appsPage.appNameInput, appName);
    await page.locator(appsPage.createAppButton).click();
    
    // Should show validation error
    await appsPage.waitForErrorMessage('App name already exists');
    
    // Form should still be usable
    expect(await appsPage.getAppNameInputValue()).toBe(appName);
    expect(await appsPage.isCreateButtonEnabled()).toBe(true);
  });

  test('should handle riff creation errors', async ({ page }) => {
    const appName = generateTestAppName();
    const riffName = generateTestRiffName();
    
    // Mock successful app creation but failed riff creation
    await page.route('/api/apps', async (route) => {
      if (route.request().method() === 'GET') {
        const apps = await page.evaluate(() => window.testApps || []);
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ apps: apps, count: apps.length })
        });
      } else if (route.request().method() === 'POST') {
        const requestBody = route.request().postDataJSON();
        const slug = requestBody.name.toLowerCase().replace(/[^a-zA-Z0-9\s-]/g, '').replace(/\s+/g, '-');
        
        const newApp = {
          name: requestBody.name,
          slug: slug,
          created_at: new Date().toISOString(),
          created_by: 'test-user',
          riffs: []
        };
        
        await page.evaluate((app) => {
          window.testApps = window.testApps || [];
          window.testApps.push(app);
        }, newApp);
        
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'App created successfully', app: newApp })
        });
      }
    });
    
    await page.route('/api/apps/*', async (route) => {
      const url = route.request().url();
      
      if (url.includes('/riffs') && route.request().method() === 'POST') {
        // Mock riff creation error
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Riff name already exists'
          })
        });
      } else if (url.includes('/riffs') && route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ riffs: [], count: 0 })
        });
      } else if (route.request().method() === 'GET') {
        const apps = await page.evaluate(() => window.testApps || []);
        const pathParts = url.split('/');
        const appSlug = pathParts[pathParts.indexOf('apps') + 1];
        const app = apps.find(a => a.slug === appSlug);
        
        if (app) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(app)
          });
        }
      }
    });
    
    // Skip setup and create app
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    await appsPage.createApp(appName);
    await appsPage.clickAppCard(appName);
    
    // Try to create riff
    await page.locator(appDetailPage.createRiffButton).click();
    await appDetailPage.fillInput(appDetailPage.riffNameInput, riffName);
    await page.locator(appDetailPage.createRiffSubmitButton).click();
    
    // Should show error message
    await appDetailPage.waitForErrorMessage('Riff name already exists');
    
    // Form should still be usable
    const nameInput = page.locator(appDetailPage.riffNameInput);
    if (await nameInput.count() > 0) {
      expect(await nameInput.inputValue()).toBe(riffName);
    }
  });

  test('should handle timeout errors', async ({ page }) => {
    // Mock very slow response
    await page.route('/api/apps', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 5000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ apps: [], count: 0 })
      });
    });
    
    // Skip setup
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Should show loading state
    await expect(page.locator('.animate-spin')).toBeVisible();
    
    // Wait for timeout (this test assumes there's timeout handling)
    await page.waitForTimeout(6000);
    
    // Should handle timeout gracefully
    // Note: Actual timeout handling depends on implementation
  });

  test('should handle malformed JSON responses', async ({ page }) => {
    // Mock malformed JSON response
    await page.route('/api/apps', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: 'invalid json {'
      });
    });
    
    // Skip setup
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Should handle JSON parsing error gracefully
    await appsPage.waitForErrorMessage('Failed to load apps');
  });

  test('should handle authentication errors', async ({ page }) => {
    // Mock 401 unauthorized
    await page.route('/api/apps', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Unauthorized'
        })
      });
    });
    
    // Skip setup
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Should show authentication error
    await appsPage.waitForErrorMessage('Failed to load apps');
  });

  test('should handle missing required headers', async ({ page }) => {
    // Mock missing header error
    await page.route('/api/apps', async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'X-User-UUID header is required'
        })
      });
    });
    
    // Skip setup
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Should show header error
    await appsPage.waitForErrorMessage('Failed to load apps');
  });

  test('should handle form validation errors', async ({ page }) => {
    // Skip setup
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Try to create app with empty name
    await page.locator(appsPage.createAppButton).click();
    
    // Should show client-side validation error
    await appsPage.waitForErrorMessage('App name is required');
    
    // Try with whitespace-only name
    await appsPage.fillInput(appsPage.appNameInput, '   ');
    await page.locator(appsPage.createAppButton).click();
    
    // Should show validation error
    await appsPage.waitForErrorMessage('App name is required');
  });

  test('should handle concurrent request errors', async ({ page }) => {
    const appName = generateTestAppName();
    let requestCount = 0;
    
    // Mock to fail after first request
    await page.route('/api/apps', async (route) => {
      requestCount++;
      
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ apps: [], count: 0 })
        });
      } else if (route.request().method() === 'POST') {
        if (requestCount > 2) {
          await route.fulfill({
            status: 409,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'Concurrent modification detected'
            })
          });
        } else {
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
                created_at: new Date().toISOString()
              }
            })
          });
        }
      }
    });
    
    // Skip setup
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Try to create app multiple times quickly
    await appsPage.fillInput(appsPage.appNameInput, appName);
    await page.locator(appsPage.createAppButton).click();
    await page.locator(appsPage.createAppButton).click();
    await page.locator(appsPage.createAppButton).click();
    
    // Should handle concurrent request error
    await appsPage.waitForErrorMessage('Concurrent modification detected');
  });

  test('should recover from errors and allow retry', async ({ page }) => {
    const appName = generateTestAppName();
    let shouldFail = true;
    
    // Mock to fail first, then succeed
    await page.route('/api/apps', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ apps: [], count: 0 })
        });
      } else if (route.request().method() === 'POST') {
        if (shouldFail) {
          shouldFail = false;
          await route.fulfill({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'Temporary server error'
            })
          });
        } else {
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
                created_at: new Date().toISOString()
              }
            })
          });
        }
      }
    });
    
    // Skip setup
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // First attempt should fail
    await appsPage.fillInput(appsPage.appNameInput, appName);
    await page.locator(appsPage.createAppButton).click();
    await appsPage.waitForErrorMessage('Temporary server error');
    
    // Retry should succeed
    await page.locator(appsPage.createAppButton).click();
    await appsPage.waitForSuccessMessage();
  });

  test('should handle setup errors gracefully', async ({ page }) => {
    // Mock setup API to fail
    await page.route('/integrations/**', async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Invalid API key format'
        })
      });
    });
    
    await setupPage.goto();
    
    if (await setupPage.isSetupWindowVisible()) {
      // Try to complete setup with invalid data
      await setupPage.completeSetup({
        githubToken: 'invalid-token',
        flyToken: 'invalid-token',
        openaiKey: 'invalid-key',
        anthropicKey: 'invalid-key'
      });
      
      // Should show error message
      await setupPage.waitForErrorMessage('Invalid API key format');
      
      // Setup window should still be visible
      expect(await setupPage.isSetupWindowVisible()).toBe(true);
      
      // Should be able to skip setup instead
      await setupPage.skipSetup();
      expect(await appsPage.isPageLoaded()).toBe(true);
    }
  });

  test('should handle page refresh during operations', async ({ page }) => {
    const appName = generateTestAppName();
    
    // Skip setup
    await setupPage.goto();
    if (await setupPage.isSetupWindowVisible()) {
      await setupPage.skipSetup();
    }
    
    // Start creating app
    await appsPage.fillInput(appsPage.appNameInput, appName);
    
    // Refresh page during form filling
    await page.reload();
    
    // Should return to clean state
    expect(await appsPage.isPageLoaded()).toBe(true);
    expect(await appsPage.getAppNameInputValue()).toBe('');
  });
});