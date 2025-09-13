import { BasePage } from './BasePage.js';

/**
 * Page object for the App Detail page
 */
export class AppDetailPage extends BasePage {
  constructor(page) {
    super(page);
    
    // Selectors
    this.appTitle = 'h1';
    this.appSlug = '.text-cyber-muted';
    this.createRiffButton = 'button:has-text("Create New Riff")';
    this.riffNameInput = 'input[placeholder*="riff name"]';
    this.riffDescriptionInput = 'textarea[placeholder*="description"]';
    this.createRiffSubmitButton = 'button[type="submit"]:has-text("Create Riff")';
    this.riffsSection = 'section:has(h2:has-text("Riffs"))';
    this.riffCards = '.riff-card, .hacker-card';
    this.noRiffsMessage = 'text=No riffs yet';
    this.backToAppsLink = 'a:has-text("← Back to Apps")';
  }

  /**
   * Navigate to app detail page
   */
  async goto(appSlug) {
    await super.goto(`/apps/${appSlug}`);
  }

  /**
   * Check if page is loaded
   */
  async isPageLoaded() {
    await this.waitForElement(this.appTitle);
    return true;
  }

  /**
   * Get app name from title
   */
  async getAppName() {
    return await this.getTextContent(this.appTitle);
  }

  /**
   * Get app slug
   */
  async getAppSlug() {
    return await this.getTextContent(this.appSlug);
  }

  /**
   * Create a new riff
   */
  async createRiff(riffName, description = '') {
    // Click create riff button
    await this.page.locator(this.createRiffButton).click();
    
    // Fill riff details
    await this.fillInput(this.riffNameInput, riffName);
    if (description) {
      await this.fillInput(this.riffDescriptionInput, description);
    }
    
    // Submit form
    await this.page.locator(this.createRiffSubmitButton).click();
    
    // Wait for success message
    await this.waitForSuccessMessage();
  }

  /**
   * Get list of riff cards
   */
  async getRiffCards() {
    await this.waitForElement(this.riffsSection);
    return await this.page.locator(this.riffCards).all();
  }

  /**
   * Get riff names from the list
   */
  async getRiffNames() {
    const cards = await this.getRiffCards();
    const names = [];
    
    for (const card of cards) {
      const nameElement = card.locator('h3, .riff-name');
      if (await nameElement.count() > 0) {
        const name = await nameElement.textContent();
        names.push(name.trim());
      }
    }
    
    return names;
  }

  /**
   * Click on a riff to view details
   */
  async clickRiff(riffName) {
    const card = this.page.locator(this.riffCards).filter({ hasText: riffName });
    const viewLink = card.locator('a').first();
    await viewLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Check if no riffs message is visible
   */
  async isNoRiffsMessageVisible() {
    return await this.elementExists(this.noRiffsMessage);
  }

  /**
   * Get riff count
   */
  async getRiffCount() {
    const cards = await this.getRiffCards();
    return cards.length;
  }

  /**
   * Check if riff exists
   */
  async riffExists(riffName) {
    const names = await this.getRiffNames();
    return names.includes(riffName);
  }

  /**
   * Go back to apps list
   */
  async goBackToApps() {
    await this.clickAndWait(this.backToAppsLink);
  }

  /**
   * Delete a riff
   */
  async deleteRiff(riffName) {
    const card = this.page.locator(this.riffCards).filter({ hasText: riffName });
    const deleteButton = card.locator('button[title*="Delete"], button:has-text("Delete")');
    
    if (await deleteButton.count() > 0) {
      await deleteButton.click();
      
      // Wait for confirmation modal and confirm
      const confirmButton = this.page.locator('button:has-text("Delete"), button:has-text("Confirm")');
      if (await confirmButton.count() > 0) {
        await confirmButton.click();
      }
      
      // Wait for success message
      await this.waitForSuccessMessage();
    }
  }

  /**
   * Get riff details from card
   */
  async getRiffDetails(riffName) {
    const card = this.page.locator(this.riffCards).filter({ hasText: riffName });
    
    const name = await card.locator('h3, .riff-name').textContent();
    const description = await card.locator('.riff-description, p').textContent();
    
    return {
      name: name?.trim() || '',
      description: description?.trim() || ''
    };
  }
}