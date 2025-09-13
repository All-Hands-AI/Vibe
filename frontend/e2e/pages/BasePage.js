/**
 * Base page object with common functionality
 */
export class BasePage {
  constructor(page) {
    this.page = page;
  }

  /**
   * Navigate to a specific path
   */
  async goto(path = '/') {
    await this.page.goto(path);
    await this.waitForPageLoad();
  }

  /**
   * Wait for page to load completely
   */
  async waitForPageLoad() {
    // Wait for DOM to be ready
    await this.page.waitForLoadState('domcontentloaded');
    
    // Wait for any loading spinners to disappear with shorter timeout
    try {
      await this.page.waitForFunction(() => {
        const spinners = document.querySelectorAll('.animate-spin');
        return spinners.length === 0;
      }, { timeout: 10000 });
    } catch (error) {
      // If spinners don't disappear, continue anyway to avoid hanging
      console.warn('Loading spinners did not disappear within timeout, continuing...');
    }
  }

  /**
   * Get page title
   */
  async getTitle() {
    return await this.page.title();
  }

  /**
   * Check if element exists
   */
  async elementExists(selector) {
    return await this.page.locator(selector).count() > 0;
  }

  /**
   * Wait for element to be visible
   */
  async waitForElement(selector, options = {}) {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible', ...options });
    return element;
  }

  /**
   * Click element and wait for navigation if needed
   */
  async clickAndWait(selector, options = {}) {
    const element = this.page.locator(selector);
    await element.click(options);
    await this.waitForPageLoad();
  }

  /**
   * Fill input field
   */
  async fillInput(selector, value) {
    const input = this.page.locator(selector);
    await input.fill(value);
  }

  /**
   * Get text content of element
   */
  async getTextContent(selector) {
    const element = this.page.locator(selector);
    return await element.textContent();
  }

  /**
   * Wait for success message
   */
  async waitForSuccessMessage(expectedMessage = null) {
    const successSelector = '.bg-green-900\\/20';
    await this.waitForElement(successSelector);
    
    if (expectedMessage) {
      await this.page.waitForFunction(
        (message) => {
          const successElement = document.querySelector('.bg-green-900\\/20');
          return successElement && successElement.textContent.includes(message);
        },
        expectedMessage,
        { timeout: 10000 }
      );
    }
  }

  /**
   * Wait for error message
   */
  async waitForErrorMessage(expectedMessage = null) {
    const errorSelector = '.bg-red-900\\/20';
    await this.waitForElement(errorSelector);
    
    if (expectedMessage) {
      await this.page.waitForFunction(
        (message) => {
          const errorElement = document.querySelector('.bg-red-900\\/20');
          return errorElement && errorElement.textContent.includes(message);
        },
        expectedMessage,
        { timeout: 10000 }
      );
    }
  }

  /**
   * Take screenshot
   */
  async takeScreenshot(name) {
    return await this.page.screenshot({ path: `screenshots/${name}.png` });
  }
}