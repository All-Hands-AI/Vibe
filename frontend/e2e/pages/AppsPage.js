import { BasePage } from './BasePage.js';

/**
 * Page object for the Apps page
 */
export class AppsPage extends BasePage {
  constructor(page) {
    super(page);
    
    // Selectors
    this.pageTitle = 'h1:has-text("Apps")';
    this.createAppSection = 'section:has(h2:has-text("Create New App"))';
    this.appNameInput = 'input#appName';
    this.createAppButton = 'button:has-text("Create App")';
    this.appsListSection = 'section:has(h2:has-text("Your Apps"))';
    this.appCards = '.hacker-card';
    this.loadingSpinner = '.animate-spin';
    this.noAppsMessage = 'text=No apps yet. Create your first app above!';
    this.deleteButtons = 'button[title*="Delete app"]';
  }

  /**
   * Navigate to Apps page
   */
  async goto() {
    await super.goto('/');
  }

  /**
   * Check if page is loaded
   */
  async isPageLoaded() {
    await this.waitForElement(this.pageTitle);
    return true;
  }

  /**
   * Create a new app
   */
  async createApp(appName) {
    // Fill app name
    await this.fillInput(this.appNameInput, appName);
    
    // Click create button
    await this.page.locator(this.createAppButton).click();
    
    // Wait for success message
    await this.waitForSuccessMessage();
  }

  /**
   * Get app name input value
   */
  async getAppNameInputValue() {
    return await this.page.locator(this.appNameInput).inputValue();
  }

  /**
   * Get slug preview
   */
  async getSlugPreview() {
    const slugElement = this.page.locator('code:near(text="Slug:")');
    if (await slugElement.count() > 0) {
      return await slugElement.textContent();
    }
    return null;
  }

  /**
   * Check if create button is enabled
   */
  async isCreateButtonEnabled() {
    const button = this.page.locator(this.createAppButton);
    return await button.isEnabled();
  }

  /**
   * Get list of app cards
   */
  async getAppCards() {
    await this.waitForElement(this.appsListSection);
    return await this.page.locator(this.appCards).all();
  }

  /**
   * Get app names from the list
   */
  async getAppNames() {
    const cards = await this.getAppCards();
    const names = [];
    
    for (const card of cards) {
      const nameElement = card.locator('h3');
      const name = await nameElement.textContent();
      names.push(name);
    }
    
    return names;
  }

  /**
   * Click on an app card to view details
   */
  async clickAppCard(appName) {
    const card = this.page.locator(this.appCards).filter({ hasText: appName });
    const viewLink = card.locator('a:has-text("View App")');
    await viewLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Delete an app
   */
  async deleteApp(appName) {
    const card = this.page.locator(this.appCards).filter({ hasText: appName });
    const deleteButton = card.locator('button[title*="Delete app"]');
    await deleteButton.click();
    
    // Wait for confirmation modal and confirm
    await this.page.locator('button:has-text("Delete App")').click();
    
    // Wait for success message
    await this.waitForSuccessMessage();
  }

  /**
   * Check if no apps message is visible
   */
  async isNoAppsMessageVisible() {
    return await this.elementExists(this.noAppsMessage);
  }

  /**
   * Wait for apps to load
   */
  async waitForAppsToLoad() {
    // Wait for loading spinner to disappear
    await this.page.waitForFunction(() => {
      const spinners = document.querySelectorAll('.animate-spin');
      return spinners.length === 0;
    }, { timeout: 30000 });
  }

  /**
   * Get app count from the list
   */
  async getAppCount() {
    await this.waitForAppsToLoad();
    const cards = await this.getAppCards();
    return cards.length;
  }

  /**
   * Check if app exists in the list
   */
  async appExists(appName) {
    const names = await this.getAppNames();
    return names.includes(appName);
  }

  /**
   * Get app details from card
   */
  async getAppDetails(appName) {
    const card = this.page.locator(this.appCards).filter({ hasText: appName });
    
    const name = await card.locator('h3').textContent();
    const slug = await card.locator('.text-cyber-muted').first().textContent();
    const createdDate = await card.locator('text=Created:').textContent();
    
    return {
      name: name.trim(),
      slug: slug.trim(),
      createdDate: createdDate.replace('Created: ', '').trim()
    };
  }
}