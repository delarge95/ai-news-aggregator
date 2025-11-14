import { Page, Locator } from '@playwright/test';

export class E2EHelpers {
  constructor(protected page: Page) {}

  // Navigation helpers
  async navigateTo(path: string): Promise<void> {
    await this.page.goto(path);
    await this.page.waitForLoadState('networkidle');
  }

  // Element interaction helpers
  async clickElement(selector: string): Promise<void> {
    await this.page.click(selector);
  }

  async fillInput(selector: string, text: string): Promise<void> {
    await this.page.fill(selector, text);
    await this.page.waitForTimeout(100); // Small delay for UI updates
  }

  async typeInInput(selector: string, text: string): Promise<void> {
    await this.page.type(selector, text);
    await this.page.waitForTimeout(100);
  }

  async clearInput(selector: string): Promise<void> {
    await this.page.click(selector);
    await this.page.keyboard.press('Control+a');
    await this.page.keyboard.press('Delete');
  }

  // Assertion helpers
  async expectElementToBeVisible(selector: string): Promise<void> {
    await this.page.waitForSelector(selector, { state: 'visible' });
  }

  async expectElementToHaveText(selector: string, text: string): Promise<void> {
    await this.page.waitForSelector(selector, { state: 'visible' });
    const element = this.page.locator(selector);
    await expect(element).toContainText(text);
  }

  async expectUrlToContain(path: string): Promise<void> {
    await this.page.waitForURL(`**${path}**`);
  }

  // Wait helpers
  async waitForNetworkIdle(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }

  async waitForElementGone(selector: string): Promise<void> {
    await this.page.waitForSelector(selector, { state: 'detached' });
  }

  // Screenshot helper
  async takeScreenshot(name: string, fullPage: boolean = false): Promise<void> {
    await this.page.screenshot({
      path: `test-results/screenshots/${name}-${Date.now()}.png`,
      fullPage,
    });
  }

  // Mock data helpers
  async mockAPIResponse(endpoint: string, response: any): Promise<void> {
    await this.page.route(`**${endpoint}**`, route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(response)
      });
    });
  }

  // Keyboard shortcuts
  async pressEscape(): Promise<void> {
    await this.page.keyboard.press('Escape');
  }

  async pressEnter(): Promise<void> {
    await this.page.keyboard.press('Enter');
  }

  async pressTab(): Promise<void> {
    await this.page.keyboard.press('Tab');
  }

  // Scroll helpers
  async scrollToTop(): Promise<void> {
    await this.page.evaluate(() => window.scrollTo(0, 0));
  }

  async scrollToBottom(): Promise<void> {
    await this.page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  }

  async scrollToElement(selector: string): Promise<void> {
    const element = this.page.locator(selector);
    await element.scrollIntoViewIfNeeded();
  }

  // Mobile helpers
  async setMobileViewport(): Promise<void> {
    await this.page.setViewportSize({ width: 375, height: 667 });
  }

  async setDesktopViewport(): Promise<void> {
    await this.page.setViewportSize({ width: 1280, height: 720 });
  }

  // Wait for specific conditions
  async waitForText(selector: string, text: string, timeout: number = 5000): Promise<void> {
    await this.page.waitForFunction(
      (args) => {
        const element = document.querySelector(args.selector);
        return element && element.textContent && element.textContent.includes(args.text);
      },
      { selector, text },
      { timeout }
    );
  }

  async waitForElementAttribute(selector: string, attribute: string, value: string): Promise<void> {
    await this.page.waitForFunction(
      (args) => {
        const element = document.querySelector(args.selector);
        return element && element.getAttribute(args.attribute) === args.value;
      },
      { selector, attribute, value }
    );
  }
}

// Import expect from playwright
const { expect } = await import('@playwright/test');
export { expect };