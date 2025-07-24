/**
 * modals.spec.ts - Modal functionality tests
 * 
 * Comprehensive tests for all modal components including:
 * - Topic creation modal
 * - Chat modal
 * - Sources modal (upload, website, YouTube tabs)
 * - Confirmation modal
 * - Wallet modal
 * - Modal accessibility and keyboard navigation
 */

import { test, expect } from '@playwright/test';

test.describe('Modal Components', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1').nth(1)).toContainText('Dashboard');
  });

  test.describe('Topic Creation Modal', () => {
    test('should open and close properly', async ({ page }) => {
      // Open modal
      await page.getByText('Create New Topic').click();
      await expect(page.getByRole('dialog')).toBeVisible();
      
      // Close with X button
      await page.getByRole('button', { name: '×' }).click();
      await expect(page.getByRole('dialog')).not.toBeVisible();
      
      // Open again and close with Cancel
      await page.getByText('Create New Topic').click();
      await page.getByRole('button', { name: 'Cancel' }).click();
      await expect(page.getByRole('dialog')).not.toBeVisible();
    });

    test('should close on backdrop click', async ({ page }) => {
      await page.getByText('Create New Topic').click();
      
      // Click outside the modal
      await page.locator('[role="dialog"]').click({ position: { x: 10, y: 10 } });
      await expect(page.getByRole('dialog')).not.toBeVisible();
    });

    test('should close on Escape key', async ({ page }) => {
      await page.getByText('Create New Topic').click();
      await page.keyboard.press('Escape');
      await expect(page.getByRole('dialog')).not.toBeVisible();
    });

    test('should validate form fields', async ({ page }) => {
      await page.getByText('Create New Topic').click();
      
      const createButton = page.getByRole('button', { name: 'Create Topic' });
      
      // Button should be disabled initially
      await expect(createButton).toBeDisabled();
      
      // Fill name only
      await page.getByLabel('Topic Name').fill('Test');
      await expect(createButton).toBeDisabled();
      
      // Fill description only (clear name first)
      await page.getByLabel('Topic Name').clear();
      await page.getByLabel('Description').fill('Test description');
      await expect(createButton).toBeDisabled();
      
      // Fill both fields
      await page.getByLabel('Topic Name').fill('Test Topic');
      await expect(createButton).toBeEnabled();
    });

    test('should show loading state during creation', async ({ page }) => {
      await page.getByText('Create New Topic').click();
      
      // Fill form
      await page.getByLabel('Topic Name').fill('Test Topic');
      await page.getByLabel('Description').fill('Test description');
      
      // Click create and check loading state
      await page.getByRole('button', { name: 'Create Topic' }).click();
      
      // Should show loading text temporarily
      await expect(page.getByText('Creating...')).toBeVisible();
    });
  });

  test.describe('Chat Modal', () => {
    test.beforeEach(async ({ page }) => {
      // Open chat modal
      await page.getByRole('button', { name: 'Study' }).first().click();
      await expect(page.getByRole('dialog')).toBeVisible();
    });

    test('should display chat interface correctly', async ({ page }) => {
      // Check header
      await expect(page.locator('#modal-title')).toHaveText('Study: Machine Learning Fundamentals');
      
      // Check three-column layout
      await expect(page.getByText('Sources')).toBeVisible();
      await expect(page.getByText('Start a conversation')).toBeVisible();
      await expect(page.getByText('Session')).toBeVisible();
      
      // Check input area
      await expect(page.getByPlaceholder('Ask a question about your topic')).toBeVisible();
      await expect(page.getByRole('button', { name: 'Send' })).toBeVisible();
    });

    test('should display sources in sidebar', async ({ page }) => {
      // Check that sources are listed
      await expect(page.getByText('Introduction to ML')).toBeVisible();
      await expect(page.getByText('Neural Networks Basics')).toBeVisible();
      await expect(page.getByText('PDF')).toBeVisible();
      await expect(page.getByText('Video')).toBeVisible();
    });

    test('should handle message sending', async ({ page }) => {
      const messageInput = page.getByPlaceholder('Ask a question about your topic');
      await expect(messageInput).toBeVisible();
      const sendButton = page.getByRole('button', { name: 'Send' });
      
      // Send button should be disabled initially
      await expect(sendButton).toBeDisabled();
      
      // Type message
      await messageInput.fill('What is machine learning?');
      await expect(sendButton).toBeEnabled();
      
      // Send message
      await sendButton.click();
      
      // Check message appears
      await expect(page.getByText('What is machine learning?')).toBeVisible();
      await expect(page.getByText('You')).toBeVisible();
      
      // Check loading state
      await expect(page.getByText('Thinking...')).toBeVisible();
    });

    test('should support keyboard shortcuts', async ({ page }) => {
      const messageInput = page.getByPlaceholder('Ask a question about your topic');
      await expect(messageInput).toBeVisible();
      
      // Type message and press Enter
      await messageInput.fill('Test message');
      await messageInput.press('Enter');
      
      // Message should be sent
      await expect(page.getByText('Test message')).toBeVisible();
    });

    test('should have session action buttons', async ({ page }) => {
      await expect(page.getByText('Create Podcast')).toBeVisible();
      await expect(page.getByText('Create Mindmap')).toBeVisible();
      await expect(page.getByText('Summarize Content')).toBeVisible();
    });
  });

  test.describe('Sources Modal', () => {
    test.beforeEach(async ({ page }) => {
      // Open sources modal
      await page.getByRole('button', { name: 'Add/Remove Sources' }).first().click();
      await expect(page.getByRole('dialog')).toBeVisible();
    });

    test('should display tab navigation', async ({ page }) => {
      // Check all tabs are visible
      await expect(page.getByText('📁 Upload Files')).toBeVisible();
      await expect(page.getByText('🌐 Website')).toBeVisible();
      await expect(page.getByText('📺 YouTube')).toBeVisible();
      
      // Upload tab should be active by default
      const uploadTab = page.locator('button:has-text("📁 Upload Files")');
      await expect(uploadTab).toHaveClass(/bg-white/);
    });

    test('should switch between tabs', async ({ page }) => {
      // Click Website tab
      await page.getByText('🌐 Website').click();
      await expect(page.getByText('Scrape Website')).toBeVisible();
      await expect(page.getByLabel('Website URL')).toBeVisible();
      
      // Click YouTube tab
      await page.getByText('📺 YouTube').click();
      await expect(page.getByText('YouTube Video')).toBeVisible();
      await expect(page.getByLabel('YouTube URL')).toBeVisible();
      
      // Back to Upload tab
      await page.getByText('📁 Upload Files').click();
      await expect(page.getByText('Upload sources')).toBeVisible();
    });

    test('should display upload interface in upload tab', async ({ page }) => {
      // Check drag and drop area
      await expect(page.getByText('Upload sources')).toBeVisible();
      await expect(page.getByText('Drag & drop or choose file to upload')).toBeVisible();
      await expect(page.getByText('Supported file types: PDF, .txt, Markdown, Audio')).toBeVisible();
    });

    test('should display website scraping interface', async ({ page }) => {
      await page.getByText('🌐 Website').click();
      
      // Check URL input
      await expect(page.getByLabel('Website URL')).toBeVisible();
      await expect(page.getByRole('button', { name: 'Scrape' })).toBeVisible();
      
      // Check quick actions
      await expect(page.getByText('📄 Article/Blog')).toBeVisible();
      await expect(page.getByText('📚 Documentation')).toBeVisible();
      await expect(page.getByText('📰 News Article')).toBeVisible();
      await expect(page.getByText('🏢 Company Page')).toBeVisible();
    });

    test('should display YouTube interface', async ({ page }) => {
      await page.getByText('📺 YouTube').click();
      
      // Check URL input
      await expect(page.getByLabel('YouTube URL')).toBeVisible();
      await expect(page.getByRole('button', { name: 'Add Video' })).toBeVisible();
      
      // Check features list
      await expect(page.getByText('Transcript extraction')).toBeVisible();
      await expect(page.getByText('Metadata analysis')).toBeVisible();
      await expect(page.getByText('Chapter detection')).toBeVisible();
      await expect(page.getByText('Multi-language')).toBeVisible();
    });

    test('should show source limit and action buttons', async ({ page }) => {
      // Check footer elements
      await expect(page.getByText('Source limit: 79 / 300')).toBeVisible();
      await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible();
      await expect(page.getByRole('button', { name: 'Save Sources' })).toBeVisible();
    });
  });

  test.describe('Confirmation Modal', () => {
    test.beforeEach(async ({ page }) => {
      // Open confirmation modal by trying to delete a topic
      await page.locator('button[aria-label="Delete topic"]').first().click();
      await expect(page.getByRole('dialog')).toBeVisible();
    });

    test('should display confirmation message', async ({ page }) => {
      await expect(page.getByText('Delete Topic')).toBeVisible();
      await expect(page.getByText('Are you sure you want to delete')).toBeVisible();
      await expect(page.getByText('This action cannot be undone')).toBeVisible();
    });

    test('should have proper button styling for dangerous action', async ({ page }) => {
      const deleteButton = page.getByRole('button', { name: 'Delete' });
      const cancelButton = page.getByRole('button', { name: 'Cancel' });
      
      await expect(deleteButton).toBeVisible();
      await expect(cancelButton).toBeVisible();
      
      // Delete button should have red background (dangerous action)
      await expect(deleteButton).toHaveClass(/bg-brand-red/);
    });

    test('should handle confirmation and cancellation', async ({ page }) => {
      // Test cancellation
      await page.getByRole('button', { name: 'Cancel' }).click();
      await expect(page.getByRole('dialog')).not.toBeVisible();
      
      // Topic should still exist
      await expect(page.getByText('Machine Learning Fundamentals')).toBeVisible();
    });
  });

  test.describe('Wallet Modal', () => {
    test.beforeEach(async ({ page }) => {
      // Open wallet modal
      await page.getByText('Connect Wallet').click();
      await expect(page.getByRole('dialog')).toBeVisible();
    });

    test('should display wallet connection options', async ({ page }) => {
      await expect(page.getByText('CONNECT WALLET')).toBeVisible();
      await expect(page.getByText('Wallet Connect')).toBeVisible();
      await expect(page.getByText('Connect with your mobile wallet')).toBeVisible();
      await expect(page.getByText('Social Connect')).toBeVisible();
      await expect(page.getByText('Connect with Google, Twitter, or email')).toBeVisible();
    });

    test('should have interactive connection buttons', async ({ page }) => {
      const walletConnectButton = page.locator('button:has-text("Wallet Connect")');
      const socialConnectButton = page.locator('button:has-text("Social Connect")');
      
      await expect(walletConnectButton).toBeVisible();
      await expect(socialConnectButton).toBeVisible();
      
      // Buttons should be clickable
      await walletConnectButton.hover();
      await socialConnectButton.hover();
    });
  });

  test.describe('Modal Accessibility', () => {
    test('should trap focus within modals', async ({ page }) => {
      // Open topic creation modal
      await page.getByText('Create New Topic').click();
      
      // Tab through modal elements
      await page.keyboard.press('Tab');
      await expect(page.getByLabel('Topic Name')).toBeFocused();
      
      await page.keyboard.press('Tab');
      await expect(page.getByLabel('Description')).toBeFocused();
      
      await page.keyboard.press('Tab');
      await expect(page.getByRole('button', { name: 'Cancel' })).toBeFocused();
      
      await page.keyboard.press('Tab');
      await expect(page.getByRole('button', { name: 'Create Topic' })).toBeFocused();
    });

    test('should have proper ARIA attributes', async ({ page }) => {
      await page.getByText('Create New Topic').click();
      
      const dialog = page.getByRole('dialog');
      await expect(dialog).toHaveAttribute('aria-modal', 'true');
      await expect(dialog).toHaveAttribute('aria-labelledby');
    });

    test('should restore focus after modal closes', async ({ page }) => {
      const createButton = page.getByText('Create New Topic');
      
      // Focus and open modal
      await createButton.focus();
      await createButton.click();
      
      // Close modal
      await page.keyboard.press('Escape');
      
      // Focus should return to the create button
      await expect(createButton).toBeFocused();
    });
  });
});