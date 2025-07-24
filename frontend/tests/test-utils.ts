/**
 * test-utils.ts - Utility functions and helpers for Playwright tests
 * 
 * This file contains reusable test utilities, custom matchers, and helper functions
 * to make writing and maintaining tests easier and more consistent.
 * 
 * Features:
 * - Modal interaction helpers
 * - Form filling utilities
 * - Accessibility testing helpers
 * - Common element selectors
 * - Test data generators
 */

import { Page, expect, Locator } from '@playwright/test';

/**
 * Common selectors used across multiple tests
 * Centralized to make maintenance easier
 */
export const selectors = {
  // Navigation elements
  navbar: 'nav',
  brandTitle: 'h1:first-child',
  dashboardTitle: 'h1:nth-child(2)',
  connectWalletButton: 'button:has-text("Connect Wallet")',
  mcpToggle: 'button:has-text("Enabled"), button:has-text("Disabled")',
  
  // Dashboard elements
  dashboard: 'main',
  topicGrid: '[class*="grid"]',
  createNewTopicCard: 'button:has-text("Create New Topic")',
  topicCard: '.bg-white.border-4.border-black.rounded',
  studyButton: 'button:has-text("Study")',
  sourcesButton: 'button:has-text("Add/Remove Sources")',
  deleteButton: 'button[aria-label="Delete topic"]',
  
  // Modal elements
  modal: '[role="dialog"]',
  modalBackdrop: '.fixed.inset-0.bg-black',
  closeButton: 'button:has-text("×")',
  
  // Form elements
  topicNameInput: 'input[id="topic-name"]',
  topicDescriptionInput: 'textarea[id="topic-description"]',
  createTopicButton: 'button:has-text("Create Topic")',
  cancelButton: 'button:has-text("Cancel")',
};

/**
 * Test data generators for consistent test data
 */
export const testData = {
  /**
   * Generate a random topic for testing
   */
  randomTopic: () => ({
    name: `Test Topic ${Math.random().toString(36).substr(2, 9)}`,
    description: `Test description for topic ${Math.random().toString(36).substr(2, 9)}`,
  }),

  /**
   * Sample topics that match the application's demo data
   */
  sampleTopics: [
    {
      name: 'Machine Learning Fundamentals',
      description: 'Basic concepts of ML algorithms and applications',
      status: 'completed'
    },
    {
      name: 'Quantum Computing Basics',
      description: 'Introduction to quantum mechanics and quantum algorithms',
      status: 'processing'
    },
    {
      name: 'Web Development Essentials',
      description: 'Modern web technologies including React, Node.js, and database design',
      status: 'completed'
    },
    {
      name: 'Data Structures & Algorithms',
      description: 'Core computer science concepts for technical interviews and problem solving',
      status: 'processing'
    }
  ],

  /**
   * Sample URLs for testing website and YouTube features
   */
  sampleUrls: {
    website: 'https://example.com/article',
    youtube: 'https://youtube.com/watch?v=dQw4w9WgXcQ',
    invalidUrl: 'not-a-valid-url'
  }
};

/**
 * Modal interaction helpers
 */
export class ModalHelper {
  constructor(private page: Page) {}

  /**
   * Wait for any modal to open and be visible
   */
  async waitForModalOpen(): Promise<Locator> {
    const modal = this.page.locator(selectors.modal);
    await expect(modal).toBeVisible();
    return modal;
  }

  /**
   * Wait for modal to close and be hidden
   */
  async waitForModalClose(): Promise<void> {
    await expect(this.page.locator(selectors.modal)).not.toBeVisible({ timeout: 10000 });
  }

  /**
   * Close modal by clicking the X button
   */
  async closeWithButton(): Promise<void> {
    await this.page.locator(selectors.closeButton).click();
    await this.waitForModalClose();
  }

  /**
   * Close modal by pressing Escape key
   */
  async closeWithEscape(): Promise<void> {
    await this.page.keyboard.press('Escape');
    await this.waitForModalClose();
  }

  /**
   * Close modal by clicking backdrop
   */
  async closeWithBackdrop(): Promise<void> {
    await this.page.locator(selectors.modal).click({ position: { x: 10, y: 10 } });
    await this.waitForModalClose();
  }

  /**
   * Open topic creation modal
   */
  async openTopicCreation(): Promise<void> {
    await this.page.locator(selectors.createNewTopicCard).click();
    await this.waitForModalOpen();
  }

  /**
   * Open chat modal for first topic
   */
  async openChatModal(): Promise<void> {
    await this.page.locator(selectors.studyButton).first().click();
    await this.waitForModalOpen();
  }

  /**
   * Open sources modal for first topic
   */
  async openSourcesModal(): Promise<void> {
    await this.page.locator(selectors.sourcesButton).first().click();
    await this.waitForModalOpen();
  }

  /**
   * Open wallet modal
   */
  async openWalletModal(): Promise<void> {
    await this.page.locator(selectors.connectWalletButton).click();
    await this.waitForModalOpen();
  }
}

/**
 * Form interaction helpers
 */
export class FormHelper {
  constructor(private page: Page) {}

  /**
   * Fill topic creation form
   */
  async fillTopicCreationForm(topic: { name: string; description: string }): Promise<void> {
    await this.page.locator(selectors.topicNameInput).fill(topic.name);
    await this.page.locator(selectors.topicDescriptionInput).fill(topic.description);
  }

  /**
   * Submit topic creation form
   */
  async submitTopicCreation(): Promise<void> {
    await this.page.locator(selectors.createTopicButton).click();
  }

  /**
   * Create a new topic (combines fill and submit)
   */
  async createTopic(topic: { name: string; description: string }): Promise<void> {
    await this.fillTopicCreationForm(topic);
    await this.submitTopicCreation();
  }

  /**
   * Check if create button is enabled
   */
  async isCreateButtonEnabled(): Promise<boolean> {
    const button = this.page.locator(selectors.createTopicButton);
    return !(await button.isDisabled());
  }

  /**
   * Wait for form validation to complete
   */
  async waitForValidation(): Promise<void> {
    // Small delay to allow reactive validation to complete
    await this.page.waitForTimeout(100);
  }
}

/**
 * Accessibility testing helpers
 */
export class AccessibilityHelper {
  constructor(private page: Page) {}

  /**
   * Check if element has proper focus styling
   */
  async checkFocusVisibility(locator: Locator): Promise<void> {
    await locator.focus();
    await expect(locator).toBeFocused();
  }

  /**
   * Test keyboard navigation through a set of elements
   */
  async testKeyboardNavigation(elements: string[]): Promise<void> {
    for (let i = 0; i < elements.length; i++) {
      if (i > 0) {
        await this.page.keyboard.press('Tab');
      }
      await expect(this.page.locator(elements[i])).toBeFocused();
    }
  }

  /**
   * Check if modal has proper ARIA attributes
   */
  async checkModalAccessibility(modal: Locator): Promise<void> {
    await expect(modal).toHaveAttribute('role', 'dialog');
    await expect(modal).toHaveAttribute('aria-modal', 'true');
    
    // Check for aria-labelledby or aria-label
    const hasLabelledBy = await modal.getAttribute('aria-labelledby');
    const hasLabel = await modal.getAttribute('aria-label');
    
    if (!hasLabelledBy && !hasLabel) {
      throw new Error('Modal should have either aria-labelledby or aria-label');
    }
  }

  /**
   * Check form accessibility
   */
  async checkFormAccessibility(): Promise<void> {
    // Check that form inputs have associated labels
    const nameInput = this.page.locator(selectors.topicNameInput);
    const descInput = this.page.locator(selectors.topicDescriptionInput);
    
    // Check for proper label association
    await expect(nameInput).toHaveAttribute('id', 'topic-name');
    await expect(descInput).toHaveAttribute('id', 'topic-description');
    
    // Check that labels exist and point to inputs
    await expect(this.page.locator('label[for="topic-name"]')).toBeVisible();
    await expect(this.page.locator('label[for="topic-description"]')).toBeVisible();
  }
}

/**
 * Viewport and responsive testing helpers
 */
export class ResponsiveHelper {
  constructor(private page: Page) {}

  /**
   * Common viewport sizes for testing
   */
  static viewports = {
    mobile: { width: 375, height: 667 },
    tablet: { width: 768, height: 1024 },
    desktop: { width: 1280, height: 720 },
  };

  /**
   * Set viewport and verify layout adapts
   */
  async setViewportAndVerify(
    viewport: { width: number; height: number },
    expectedColumns: number
  ): Promise<void> {
    await this.page.setViewportSize(viewport);
    
    // Wait for layout to stabilize
    await this.page.waitForTimeout(100);
    
    // Verify basic layout elements are still visible
    await expect(this.page.locator(selectors.navbar)).toBeVisible();
    await expect(this.page.locator(selectors.dashboardTitle)).toBeVisible();
    await expect(this.page.locator(selectors.topicGrid)).toBeVisible();
  }

  /**
   * Test that element is visible across all viewports
   */
  async testElementAcrossViewports(selector: string): Promise<void> {
    const viewports = Object.values(ResponsiveHelper.viewports);
    
    for (const viewport of viewports) {
      await this.page.setViewportSize(viewport);
      await expect(this.page.locator(selector)).toBeVisible();
    }
  }
}

/**
 * Wait helpers for common scenarios
 */
export class WaitHelper {
  constructor(private page: Page) {}

  /**
   * Wait for page to be fully loaded
   */
  async waitForPageLoad(): Promise<void> {
    await expect(this.page.locator(selectors.dashboardTitle)).toBeVisible();
    await expect(this.page.locator(selectors.topicGrid)).toBeVisible();
  }

  /**
   * Wait for topic to appear in the list
   */
  async waitForTopicToAppear(topicName: string): Promise<void> {
    await expect(this.page.getByText(topicName)).toBeVisible();
  }

  /**
   * Wait for topic to disappear from the list
   */
  async waitForTopicToDisappear(topicName: string): Promise<void> {
    await expect(this.page.getByText(topicName)).not.toBeVisible();
  }

  /**
   * Wait for loading state to complete
   */
  async waitForLoadingComplete(): Promise<void> {
    // Wait for any loading indicators to disappear
    await expect(this.page.getByText('Creating...')).not.toBeVisible();
    await expect(this.page.getByText('Loading...')).not.toBeVisible();
  }
}

/**
 * Create all helpers for a given page
 */
export function createTestHelpers(page: Page) {
  return {
    modal: new ModalHelper(page),
    form: new FormHelper(page),
    accessibility: new AccessibilityHelper(page),
    responsive: new ResponsiveHelper(page),
    wait: new WaitHelper(page),
  };
}