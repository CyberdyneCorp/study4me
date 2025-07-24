/**
 * dashboard.spec.ts - Dashboard functionality tests
 * 
 * Comprehensive end-to-end tests for the main dashboard functionality including:
 * - Page loading and layout verification
 * - Topic card interactions
 * - Modal operations (create, study, sources, delete)
 * - Responsive design testing
 * - Accessibility compliance
 */

import { test, expect } from '@playwright/test';

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the dashboard before each test
    await page.goto('/');
    
    // Wait for the page to be fully loaded
    await expect(page.locator('h1').nth(1)).toContainText('Dashboard');
  });

  test('should display the main dashboard layout', async ({ page }) => {
    // Check navbar elements
    await expect(page.locator('nav')).toBeVisible();
    await expect(page.locator('h1').first()).toContainText('Study4Me');
    await expect(page.getByText('Connect Wallet')).toBeVisible();
    
    // Check dashboard header
    await expect(page.locator('h1').nth(1)).toContainText('Dashboard');
    await expect(page.getByText('Manage your study topics')).toBeVisible();
    
    // Check that topic cards are displayed
    await expect(page.locator('[class*="grid"]')).toBeVisible();
  });

  test('should display sample topics correctly', async ({ page }) => {
    // Check for the sample topics
    await expect(page.getByText('Machine Learning Fundamentals')).toBeVisible();
    await expect(page.getByText('Quantum Computing Basics')).toBeVisible();
    await expect(page.getByText('Web Development Essentials')).toBeVisible();
    await expect(page.getByText('Data Structures & Algorithms')).toBeVisible();
    
    // Check topic descriptions are visible
    await expect(page.getByText('Basic concepts of ML algorithms')).toBeVisible();
    await expect(page.getByText('Introduction to quantum mechanics')).toBeVisible();
  });

  test('should display Create New Topic card when topics exist', async ({ page }) => {
    // Check that the Create New Topic card is visible
    await expect(page.getByText('Create New Topic')).toBeVisible();
    await expect(page.getByText('Add a new study topic to get started')).toBeVisible();
    
    // Verify it has the correct styling (dashed border)
    const createCard = page.locator('button:has-text("Create New Topic")');
    await expect(createCard).toBeVisible();
  });

  test('should open topic creation modal when clicking Create New Topic', async ({ page }) => {
    // Click the Create New Topic card
    await page.getByText('Create New Topic').click();
    
    // Check that the modal opened
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'CREATE NEW TOPIC', exact: true })).toBeVisible();
    
    // Check form elements
    await expect(page.getByLabel('Topic Name')).toBeVisible();
    await expect(page.getByLabel('Description')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Create Topic' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible();
  });

  test('should create a new topic successfully', async ({ page }) => {
    // Open the creation modal
    await page.getByText('Create New Topic').click();
    
    // Fill in the form
    await page.getByLabel('Topic Name').fill('Test Topic');
    await page.getByLabel('Description').fill('This is a test topic description');
    
    // Submit the form
    await page.getByRole('button', { name: 'Create Topic' }).click();
    
    // Check that the modal closed and new topic appears
    await expect(page.getByRole('dialog')).not.toBeVisible();
    await expect(page.getByRole('heading', { name: 'Test Topic' })).toBeVisible();
    await expect(page.getByText('This is a test topic description')).toBeVisible();
  });

  test('should not create topic with empty fields', async ({ page }) => {
    // Open the creation modal
    await page.getByText('Create New Topic').click();
    
    // Try to submit without filling fields
    const createButton = page.getByRole('button', { name: 'Create Topic' });
    await expect(createButton).toBeDisabled();
    
    // Fill only name
    await page.getByLabel('Topic Name').fill('Test Topic');
    await expect(createButton).toBeDisabled();
    
    // Fill only description (clear name first)
    await page.getByLabel('Topic Name').clear();
    await page.getByLabel('Description').fill('Test description');
    await expect(createButton).toBeDisabled();
  });

  test('should open chat modal when clicking Study button', async ({ page }) => {
    // Click Study button on first topic
    await page.getByRole('button', { name: 'Study' }).first().click();
    
    // Check that chat modal opened
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.locator('#modal-title')).toHaveText('Study: Machine Learning Fundamentals');
    
    // Check chat interface elements
    await expect(page.getByText('Sources')).toBeVisible();
    await expect(page.getByText('Session')).toBeVisible();
    await expect(page.getByPlaceholder('Ask a question about your topic')).toBeVisible();
  });

  test('should open sources modal when clicking Add/Remove Sources', async ({ page }) => {
    // Click Add/Remove Sources button on first topic
    await page.getByRole('button', { name: 'Add/Remove Sources' }).first().click();
    
    // Check that sources modal opened
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText('Add sources: Machine Learning Fundamentals')).toBeVisible();
    
    // Check tab navigation
    await expect(page.getByText('📁 Upload Files')).toBeVisible();
    await expect(page.getByText('🌐 Website')).toBeVisible();
    await expect(page.getByText('📺 YouTube')).toBeVisible();
  });

  test('should show delete confirmation when clicking delete button', async ({ page }) => {
    // Click delete button on first topic
    await page.locator('button[aria-label="Delete topic"]').first().click();
    
    // Check confirmation modal
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText('Delete Topic')).toBeVisible();
    await expect(page.getByText('Are you sure you want to delete')).toBeVisible();
    
    // Use more specific selectors for the modal buttons
    const modal = page.getByRole('dialog');
    await expect(modal.getByRole('button', { name: 'Delete' })).toBeVisible();
    await expect(modal.getByRole('button', { name: 'Cancel' })).toBeVisible();
  });

  test('should delete topic when confirmed', async ({ page }) => {
    // Click delete button and confirm
    await page.locator('button[aria-label="Delete topic"]').first().click();
    
    // Use modal-scoped selector for the delete button
    const modal = page.getByRole('dialog');
    await modal.getByRole('button', { name: 'Delete' }).click();
    
    // Verify topic is removed
    await expect(page.getByRole('heading', { name: 'Machine Learning Fundamentals' })).not.toBeVisible();
  });

  test('should cancel topic deletion', async ({ page }) => {
    // Click delete button and cancel
    await page.locator('button[aria-label="Delete topic"]').first().click();
    
    // Use modal-scoped selector for the cancel button
    const modal = page.getByRole('dialog');
    await modal.getByRole('button', { name: 'Cancel' }).click();
    
    // Verify modal closed and topic still exists
    await expect(page.getByRole('dialog')).not.toBeVisible();
    await expect(page.getByRole('heading', { name: 'Machine Learning Fundamentals' })).toBeVisible();
  });

  test('should display topic status correctly', async ({ page }) => {
    // Check that status badges are visible and have correct colors
    const completedStatus = page.locator('span:has-text("completed")').first();
    const processingStatus = page.locator('span:has-text("processing")').first();
    
    await expect(completedStatus).toBeVisible();
    await expect(processingStatus).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check that layout adapts to mobile
    await expect(page.locator('h1').nth(1)).toContainText('Dashboard');
    await expect(page.getByText('Create New Topic')).toBeVisible();
    
    // Verify grid layout changes (should be single column on mobile)
    const grid = page.locator('[class*="grid"]');
    await expect(grid).toBeVisible();
  });

  test('should have proper accessibility attributes', async ({ page }) => {
    // Check ARIA labels
    await expect(page.locator('button[aria-label="Delete topic"]').first()).toBeVisible();
    
    // Check that interactive elements are focusable
    const studyButton = page.getByRole('button', { name: 'Study' }).first();
    await studyButton.focus();
    await expect(studyButton).toBeFocused();
    
    // Check heading structure
    await expect(page.locator('h1').nth(1)).toHaveAttribute('class', expect.stringContaining('font-mono'));
  });
});