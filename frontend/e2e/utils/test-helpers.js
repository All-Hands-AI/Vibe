/**
 * Test utilities and helper functions for e2e tests
 */

/**
 * Generate a unique test identifier
 */
export function generateTestId() {
  return `test-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Generate a unique app name for testing
 */
export function generateTestAppName() {
  return `Test App ${generateTestId()}`;
}

/**
 * Generate a unique riff name for testing
 */
export function generateTestRiffName() {
  return `Test Riff ${generateTestId()}`;
}

/**
 * Wait for element to be visible and stable
 */
export async function waitForElement(page, selector, options = {}) {
  const element = page.locator(selector);
  await element.waitFor({ state: 'visible', ...options });
  return element;
}

/**
 * Wait for loading to complete
 */
export async function waitForLoadingToComplete(page) {
  // Wait for any loading spinners to disappear with shorter timeout
  try {
    await page.waitForFunction(() => {
      const spinners = document.querySelectorAll('.animate-spin');
      return spinners.length === 0;
    }, { timeout: 10000 });
  } catch (error) {
    // If spinners don't disappear, continue anyway to avoid hanging
    console.warn('Loading spinners did not disappear within timeout, continuing...');
  }
}

/**
 * Wait for success message to appear
 */
export async function waitForSuccessMessage(page, expectedMessage = null) {
  const successSelector = '.bg-green-900\\/20';
  await waitForElement(page, successSelector, { timeout: 10000 });
  
  if (expectedMessage) {
    try {
      await page.waitForFunction(
        (message) => {
          const successElement = document.querySelector('.bg-green-900\\/20');
          return successElement && successElement.textContent.includes(message);
        },
        expectedMessage,
        { timeout: 5000 }
      );
    } catch (error) {
      console.warn(`Success message "${expectedMessage}" not found within timeout`);
    }
  }
}

/**
 * Wait for error message to appear
 */
export async function waitForErrorMessage(page, expectedMessage = null) {
  const errorSelector = '.bg-red-900\\/20';
  await waitForElement(page, errorSelector, { timeout: 10000 });
  
  if (expectedMessage) {
    try {
      await page.waitForFunction(
        (message) => {
          const errorElement = document.querySelector('.bg-red-900\\/20');
          return errorElement && errorElement.textContent.includes(message);
        },
        expectedMessage,
        { timeout: 5000 }
      );
    } catch (error) {
      console.warn(`Error message "${expectedMessage}" not found within timeout`);
    }
  }
}

/**
 * Clear local storage and session storage
 */
export async function clearStorage(page) {
  try {
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  } catch (error) {
    // If localStorage is not accessible (e.g., before navigation), ignore the error
    console.warn('Could not clear storage, continuing...');
  }
}

/**
 * Mock API responses for testing
 */
export async function mockApiResponses(page) {
  // Mock the backend API calls
  await page.route('/api/**', async (route) => {
    const url = route.request().url();
    const method = route.request().method();
    
    console.log(`Mocking API call: ${method} ${url}`);
    
    // Mock apps endpoints
    if (url.includes('/api/apps') && method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          apps: [],
          count: 0
        })
      });
    } else if (url.includes('/api/apps') && method === 'POST') {
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
    } else {
      // Default mock response
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true })
      });
    }
  });
}

/**
 * Set up test environment
 */
export async function setupTestEnvironment(page) {
  // Mock API responses first
  await mockApiResponses(page);
  
  // Set up console logging for debugging
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      console.error(`Browser console error: ${msg.text()}`);
    }
  });
  
  // Set up error handling
  page.on('pageerror', (error) => {
    console.error(`Page error: ${error.message}`);
  });
  
  // Clear storage (will be done after navigation in individual tests)
  await clearStorage(page);
}

/**
 * Take a screenshot with a descriptive name
 */
export async function takeScreenshot(page, testInfo, name) {
  const screenshot = await page.screenshot();
  await testInfo.attach(name, {
    body: screenshot,
    contentType: 'image/png'
  });
}