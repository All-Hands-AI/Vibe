import { BasePage } from './BasePage.js';

/**
 * Page object for the Setup Window
 */
export class SetupPage extends BasePage {
  constructor(page) {
    super(page);
    
    // Selectors
    this.setupWindow = '.terminal-window';
    this.setupTitle = '.terminal-header';
    this.githubTokenInput = 'input[placeholder*="GitHub"]';
    this.flyTokenInput = 'input[placeholder*="Fly.io"]';
    this.openaiKeyInput = 'input[placeholder*="OpenAI"]';
    this.anthropicKeyInput = 'input[placeholder*="Anthropic"]';
    this.completeSetupButton = 'button:has-text("Complete Setup")';
    this.skipSetupButton = 'button:has-text("Skip Setup")';
  }

  /**
   * Check if setup window is visible
   */
  async isSetupWindowVisible() {
    return await this.elementExists(this.setupWindow);
  }

  /**
   * Fill GitHub token
   */
  async fillGitHubToken(token) {
    await this.fillInput(this.githubTokenInput, token);
  }

  /**
   * Fill Fly.io token
   */
  async fillFlyToken(token) {
    await this.fillInput(this.flyTokenInput, token);
  }

  /**
   * Fill OpenAI API key
   */
  async fillOpenAIKey(key) {
    await this.fillInput(this.openaiKeyInput, key);
  }

  /**
   * Fill Anthropic API key
   */
  async fillAnthropicKey(key) {
    await this.fillInput(this.anthropicKeyInput, key);
  }

  /**
   * Complete setup with all required fields
   */
  async completeSetup(credentials = {}) {
    const {
      githubToken = 'test-github-token',
      flyToken = 'test-fly-token',
      openaiKey = 'test-openai-key',
      anthropicKey = 'test-anthropic-key'
    } = credentials;

    await this.fillGitHubToken(githubToken);
    await this.fillFlyToken(flyToken);
    await this.fillOpenAIKey(openaiKey);
    await this.fillAnthropicKey(anthropicKey);
    
    await this.clickAndWait(this.completeSetupButton);
  }

  /**
   * Skip setup
   */
  async skipSetup() {
    await this.clickAndWait(this.skipSetupButton);
  }

  /**
   * Get setup window title
   */
  async getSetupTitle() {
    return await this.getTextContent(this.setupTitle);
  }

  /**
   * Check if complete setup button is enabled
   */
  async isCompleteSetupButtonEnabled() {
    const button = this.page.locator(this.completeSetupButton);
    return await button.isEnabled();
  }

  /**
   * Wait for setup to complete (window to disappear)
   */
  async waitForSetupComplete() {
    await this.page.waitForFunction(() => {
      const setupWindow = document.querySelector('.terminal-window');
      return !setupWindow || setupWindow.style.display === 'none';
    }, { timeout: 10000 });
  }
}