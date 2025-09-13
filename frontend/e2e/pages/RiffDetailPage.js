import { BasePage } from './BasePage.js';

/**
 * Page object for the Riff Detail page
 */
export class RiffDetailPage extends BasePage {
  constructor(page) {
    super(page);
    
    // Selectors
    this.riffTitle = 'h1';
    this.riffSlug = '.text-cyber-muted';
    this.breadcrumbs = 'nav';
    this.backToAppsLink = 'a:has-text("← Apps")';
    this.backToAppLink = 'a[href*="/apps/"]';
    this.branchStatus = '.branch-status, .hacker-card';
    this.chatWindow = '.chat-window, [class*="chat"]';
    this.messageInput = 'input[placeholder*="message"], textarea[placeholder*="message"]';
    this.sendButton = 'button:has-text("Send")';
    this.messageList = '.message-list, .messages';
    this.loadingIndicator = '.animate-spin';
  }

  /**
   * Navigate to riff detail page
   */
  async goto(appSlug, riffSlug) {
    await super.goto(`/apps/${appSlug}/riffs/${riffSlug}`);
  }

  /**
   * Check if page is loaded
   */
  async isPageLoaded() {
    await this.waitForElement(this.riffTitle);
    return true;
  }

  /**
   * Get riff name from title
   */
  async getRiffName() {
    return await this.getTextContent(this.riffTitle);
  }

  /**
   * Get riff slug
   */
  async getRiffSlug() {
    return await this.getTextContent(this.riffSlug);
  }

  /**
   * Check if chat window is visible
   */
  async isChatWindowVisible() {
    return await this.elementExists(this.chatWindow);
  }

  /**
   * Send a message in the chat
   */
  async sendMessage(message) {
    if (await this.elementExists(this.messageInput)) {
      await this.fillInput(this.messageInput, message);
      await this.page.locator(this.sendButton).click();
      
      // Wait for message to be sent
      await this.page.waitForTimeout(1000);
    }
  }

  /**
   * Get messages from chat
   */
  async getMessages() {
    if (await this.elementExists(this.messageList)) {
      const messageElements = await this.page.locator(`${this.messageList} .message, .chat-message`).all();
      const messages = [];
      
      for (const element of messageElements) {
        const text = await element.textContent();
        messages.push(text.trim());
      }
      
      return messages;
    }
    return [];
  }

  /**
   * Check if branch status is visible
   */
  async isBranchStatusVisible() {
    return await this.elementExists(this.branchStatus);
  }

  /**
   * Go back to apps list
   */
  async goBackToApps() {
    await this.clickAndWait(this.backToAppsLink);
  }

  /**
   * Go back to app detail
   */
  async goBackToApp() {
    await this.clickAndWait(this.backToAppLink);
  }

  /**
   * Get breadcrumb navigation
   */
  async getBreadcrumbs() {
    const breadcrumbElement = this.page.locator(this.breadcrumbs);
    return await breadcrumbElement.textContent();
  }

  /**
   * Check if loading indicator is visible
   */
  async isLoadingVisible() {
    return await this.elementExists(this.loadingIndicator);
  }

  /**
   * Wait for chat to initialize
   */
  async waitForChatToInitialize() {
    // Wait for loading to complete
    await this.page.waitForFunction(() => {
      const loadingElements = document.querySelectorAll('.animate-spin');
      const initializingText = document.querySelector('text=Initializing chat');
      return loadingElements.length === 0 && !initializingText;
    }, { timeout: 30000 });
  }

  /**
   * Get riff metadata
   */
  async getRiffMetadata() {
    const metadata = {};
    
    // Try to extract creation date
    const createdElement = this.page.locator('text=Created:');
    if (await createdElement.count() > 0) {
      metadata.created = await createdElement.textContent();
    }
    
    // Try to extract last activity
    const activityElement = this.page.locator('text=Last activity:');
    if (await activityElement.count() > 0) {
      metadata.lastActivity = await activityElement.textContent();
    }
    
    // Try to extract message count
    const messagesElement = this.page.locator('text=Messages:');
    if (await messagesElement.count() > 0) {
      metadata.messageCount = await messagesElement.textContent();
    }
    
    return metadata;
  }
}