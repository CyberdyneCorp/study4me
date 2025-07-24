/**
 * navbar.spec.ts - Navigation bar tests
 * 
 * Tests for the top navigation bar including:
 * - Brand display and layout
 * - MCP toggle functionality
 * - Wallet connection button
 * - Responsive behavior
 * - Accessibility features
 */

import { test, expect } from '@playwright/test';

test.describe('Navigation Bar', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('nav')).toBeVisible();
  });

  test('should display brand and navigation elements', async ({ page }) => {
    // Check brand name
    await expect(page.locator('h1').first()).toContainText('Study4Me');
    
    // Check current page indicator
    await expect(page.getByText('Dashboard')).toBeVisible();
    
    // Check wallet connection button
    await expect(page.getByRole('button', { name: 'Connect Wallet' })).toBeVisible();
  });

  test('should display MCP toggle', async ({ page }) => {
    // Check MCP label and toggle
    await expect(page.getByText('MCP:')).toBeVisible();
    
    // MCP should be enabled by default
    const mcpToggle = page.locator('button:has-text("Enabled")');
    await expect(mcpToggle).toBeVisible();
    await expect(mcpToggle).toHaveClass(/bg-green-500/);
  });

  test('should toggle MCP status', async ({ page }) => {
    // Initial state should be enabled
    await expect(page.getByText('Enabled')).toBeVisible();
    
    // Click to disable
    await page.getByText('Enabled').click();
    
    // Should now show disabled with red background
    await expect(page.getByText('Disabled')).toBeVisible();
    const disabledToggle = page.locator('button:has-text("Disabled")');
    await expect(disabledToggle).toHaveClass(/bg-red-500/);
    
    // Click to enable again
    await page.getByText('Disabled').click();
    await expect(page.getByText('Enabled')).toBeVisible();
  });

  test('should open wallet modal when clicking Connect Wallet', async ({ page }) => {
    // Click Connect Wallet button
    await page.getByRole('button', { name: 'Connect Wallet' }).click();
    
    // Check that wallet modal opened
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText('CONNECT WALLET')).toBeVisible();
    await expect(page.getByText('Wallet Connect')).toBeVisible();
    await expect(page.getByText('Social Connect')).toBeVisible();
  });

  test('should have proper layout structure', async ({ page }) => {
    const nav = page.locator('nav');
    
    // Navigation should have white background and bottom border
    await expect(nav).toHaveClass(/bg-white/);
    await expect(nav).toHaveClass(/border-b-4/);
    await expect(nav).toHaveClass(/border-black/);
    
    // Check responsive container
    const container = nav.locator('div').first();
    await expect(container).toHaveClass(/max-w-7xl/);
    await expect(container).toHaveClass(/mx-auto/);
  });

  test('should display correctly on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // All elements should still be visible and properly arranged
    await expect(page.locator('h1').first()).toContainText('Study4Me');
    await expect(page.getByText('MCP:')).toBeVisible();
    await expect(page.getByText('Dashboard')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Connect Wallet' })).toBeVisible();
  });

  test('should display correctly on tablet', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    
    // Check layout adapts properly
    await expect(page.locator('nav')).toBeVisible();
    await expect(page.locator('h1').first()).toContainText('Study4Me');
    await expect(page.getByRole('button', { name: 'Connect Wallet' })).toBeVisible();
  });

  test('should have proper accessibility attributes', async ({ page }) => {
    // Check that interactive elements are focusable
    const connectWalletButton = page.getByRole('button', { name: 'Connect Wallet' });
    await connectWalletButton.focus();
    await expect(connectWalletButton).toBeFocused();
    
    const mcpToggle = page.locator('button:has-text("Enabled")');
    await mcpToggle.focus();
    await expect(mcpToggle).toBeFocused();
  });

  test('should maintain consistent styling', async ({ page }) => {
    // Check brand typography
    const brandTitle = page.locator('h1').first();
    await expect(brandTitle).toHaveClass(/font-mono/);
    await expect(brandTitle).toHaveClass(/font-bold/);
    
    // Check Connect Wallet button styling
    const connectButton = page.getByRole('button', { name: 'Connect Wallet' });
    await expect(connectButton).toHaveClass(/bg-brand-blue/);
    await expect(connectButton).toHaveClass(/border-4/);
    await expect(connectButton).toHaveClass(/border-black/);
    await expect(connectButton).toHaveClass(/font-mono/);
  });

  test('should support keyboard navigation', async ({ page }) => {
    // Tab through navigation elements
    await page.keyboard.press('Tab');
    await expect(page.locator('button:has-text("Enabled")')).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', { name: 'Connect Wallet' })).toBeFocused();
    
    // Test MCP toggle with keyboard
    await page.keyboard.press('Shift+Tab'); // Go back to MCP toggle
    await page.keyboard.press('Enter');
    await expect(page.getByText('Disabled')).toBeVisible();
  });

  test('should handle hover states', async ({ page }) => {
    const connectButton = page.getByRole('button', { name: 'Connect Wallet' });
    
    // Hover over Connect Wallet button
    await connectButton.hover();
    
    // Button should have hover effect (opacity change)
    // Note: We can't easily test CSS hover states, but we can verify the element is hoverable
    await expect(connectButton).toBeVisible();
  });
});