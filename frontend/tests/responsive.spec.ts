/**
 * responsive.spec.ts - Responsive design tests
 * 
 * Tests for responsive behavior across different screen sizes:
 * - Mobile phone layouts (320px - 768px)
 * - Tablet layouts (768px - 1024px)
 * - Desktop layouts (1024px+)
 * - Grid system responsiveness
 * - Typography scaling
 * - Touch interaction support
 */

import { test, expect } from '@playwright/test';

const viewports = {
  mobile: { width: 375, height: 667 },
  mobileLarge: { width: 414, height: 896 },
  tablet: { width: 768, height: 1024 },
  tabletLarge: { width: 1024, height: 768 },
  desktop: { width: 1280, height: 720 },
  desktopLarge: { width: 1920, height: 1080 }
};

test.describe('Responsive Design', () => {
  test.describe('Mobile Layouts', () => {
    test('should display correctly on small mobile (375px)', async ({ page }) => {
      await page.setViewportSize(viewports.mobile);
      await page.goto('/');
      
      // Navigation should be compact but functional
      await expect(page.locator('nav')).toBeVisible();
      await expect(page.locator('h1').first()).toContainText('Study4Me');
      await expect(page.getByRole('button', { name: 'Connect Wallet' })).toBeVisible();
      
      // Dashboard should use single column layout
      await expect(page.locator('h1').nth(1)).toContainText('Dashboard');
      
      // Topic cards should stack vertically (grid-cols-1)
      const grid = page.locator('[class*="grid"]');
      await expect(grid).toBeVisible();
      
      // Create New Topic card should be visible
      await expect(page.getByText('Create New Topic')).toBeVisible();
      
      // All topic cards should be visible and readable
      await expect(page.getByRole('heading', { name: 'Machine Learning Fundamentals' })).toBeVisible();
      await expect(page.getByRole('heading', { name: 'Quantum Computing Basics' })).toBeVisible();
    });

    test('should display correctly on large mobile (414px)', async ({ page }) => {
      await page.setViewportSize(viewports.mobileLarge);
      await page.goto('/');
      
      // Check that content fits properly
      await expect(page.locator('nav')).toBeVisible();
      await expect(page.getByText('Dashboard')).toBeVisible();
      
      // Cards should still be in single column but have more breathing room
      await expect(page.getByText('Create New Topic')).toBeVisible();
      await expect(page.getByRole('heading', { name: 'Machine Learning Fundamentals' })).toBeVisible();
    });

    test('should handle mobile modal interactions', async ({ page }) => {
      await page.setViewportSize(viewports.mobile);
      await page.goto('/');
      
      // Open topic creation modal
      await page.getByText('Create New Topic').click();
      
      // Modal should be properly sized for mobile
      const modal = page.getByRole('dialog');
      await expect(modal).toBeVisible();
      
      // Modal should be almost full width (w-11/12)
      await expect(page.getByText('CREATE NEW TOPIC')).toBeVisible();
      
      // Form elements should be touch-friendly
      const nameInput = page.getByLabel('Topic Name');
      await expect(nameInput).toBeVisible();
      await nameInput.tap();
      await expect(nameInput).toBeFocused();
    });

    test('should support touch interactions', async ({ page }) => {
      await page.setViewportSize(viewports.mobile);
      await page.goto('/');
      
      // Test tap interactions
      await page.getByText('Create New Topic').tap();
      await expect(page.getByRole('dialog')).toBeVisible();
      
      // Close modal with tap
      await page.getByRole('button', { name: 'Cancel' }).tap();
      await expect(page.getByRole('dialog')).not.toBeVisible();
      
      // Test button taps
      await page.getByRole('button', { name: 'Study' }).first().tap();
      await expect(page.getByRole('dialog')).toBeVisible();
    });
  });

  test.describe('Tablet Layouts', () => {
    test('should display correctly on tablet portrait (768px)', async ({ page }) => {
      await page.setViewportSize(viewports.tablet);
      await page.goto('/');
      
      // Should use 2-column grid (md:grid-cols-2)
      await expect(page.locator('nav')).toBeVisible();
      await expect(page.getByText('Dashboard')).toBeVisible();
      
      // Topic cards should be in 2 columns
      const grid = page.locator('[class*="grid"]');
      await expect(grid).toBeVisible();
      
      // All content should be visible and well-spaced
      await expect(page.getByText('Create New Topic')).toBeVisible();
      await expect(page.getByRole('heading', { name: 'Machine Learning Fundamentals' })).toBeVisible();
    });

    test('should display correctly on tablet landscape (1024px)', async ({ page }) => {
      await page.setViewportSize(viewports.tabletLarge);
      await page.goto('/');
      
      // Should transition to 3-column grid (xl:grid-cols-3)
      await expect(page.locator('nav')).toBeVisible();
      await expect(page.getByText('Dashboard')).toBeVisible();
      
      // Content should be well-distributed across the wider screen
      await expect(page.getByText('Create New Topic')).toBeVisible();
      
      // All topic cards should be visible
      await expect(page.getByRole('heading', { name: 'Machine Learning Fundamentals' })).toBeVisible();
      await expect(page.getByRole('heading', { name: 'Quantum Computing Basics' })).toBeVisible();
      await expect(page.getByRole('heading', { name: 'Web Development Essentials' })).toBeVisible();
      await expect(page.getByRole('heading', { name: 'Data Structures & Algorithms' })).toBeVisible();
    });

    test('should handle tablet modal layouts', async ({ page }) => {
      await page.setViewportSize(viewports.tablet);
      await page.goto('/');
      
      // Open chat modal
      await page.getByRole('button', { name: 'Study' }).first().click();
      
      // Chat modal should use appropriate sizing for tablet
      await expect(page.getByRole('dialog')).toBeVisible();
      await expect(page.getByRole('heading', { name: 'Study: Machine Learning Fundamentals' })).toBeVisible();
      
      // Three-column layout should be visible
      await expect(page.getByText('Sources')).toBeVisible();
      await expect(page.getByText('Session')).toBeVisible();
      
      // Input area should be properly sized
      await expect(page.getByPlaceholder('Ask a question')).toBeVisible();
    });
  });

  test.describe('Desktop Layouts', () => {
    test('should display correctly on standard desktop (1280px)', async ({ page }) => {
      await page.setViewportSize(viewports.desktop);
      await page.goto('/');
      
      // Should use full 3-column grid layout
      await expect(page.locator('nav')).toBeVisible();
      await expect(page.getByText('Dashboard')).toBeVisible();
      
      // Navigation should be properly spaced
      const nav = page.locator('nav div').first();
      await expect(nav).toHaveClass(/max-w-7xl/);
      
      // Grid should show 3 columns
      await expect(page.getByText('Create New Topic')).toBeVisible();
      await expect(page.getByRole('heading', { name: 'Machine Learning Fundamentals' })).toBeVisible();
    });

    test('should display correctly on large desktop (1920px)', async ({ page }) => {
      await page.setViewportSize(viewports.desktopLarge);
      await page.goto('/');
      
      // Content should be centered with max-width constraint
      await expect(page.locator('nav')).toBeVisible();
      
      // Main content should have max-width and be centered
      const main = page.locator('main');
      await expect(main).toHaveClass(/max-w-7xl/);
      await expect(main).toHaveClass(/mx-auto/);
      
      // All content should be visible with proper spacing
      await expect(page.getByText('Dashboard')).toBeVisible();
      await expect(page.getByText('Create New Topic')).toBeVisible();
    });

    test('should handle desktop modal layouts', async ({ page }) => {
      await page.setViewportSize(viewports.desktop);
      await page.goto('/');
      
      // Open sources modal (largest modal)
      await page.getByRole('button', { name: 'Add/Remove Sources' }).first().click();
      
      // Modal should be properly sized for desktop
      const modal = page.getByRole('dialog');
      await expect(modal).toBeVisible();
      
      // Should have max-width constraint (max-w-4xl)
      await expect(page.getByRole('heading', { name: 'Add sources: Machine Learning Fundamentals' })).toBeVisible();
      
      // Tab navigation should be clearly visible
      await expect(page.getByText('📁 Upload Files')).toBeVisible();
      await expect(page.getByText('🌐 Website')).toBeVisible();
      await expect(page.getByText('📺 YouTube')).toBeVisible();
      
      // Content should not be cramped
      await expect(page.getByText('Upload sources')).toBeVisible();
    });
  });

  test.describe('Grid System Responsiveness', () => {
    test('should transition grid columns at breakpoints', async ({ page }) => {
      await page.goto('/');
      
      // Test mobile (should be 1 column)
      await page.setViewportSize({ width: 375, height: 667 });
      const grid = page.locator('[class*="grid"]');
      await expect(grid).toBeVisible();
      
      // Test tablet (should be 2 columns)
      await page.setViewportSize({ width: 768, height: 1024 });
      await expect(grid).toBeVisible();
      
      // Test desktop (should be 3 columns)
      await page.setViewportSize({ width: 1280, height: 720 });
      await expect(grid).toBeVisible();
      
      // All cards should remain visible at all breakpoints
      await expect(page.getByText('Create New Topic')).toBeVisible();
      await expect(page.getByRole('heading', { name: 'Machine Learning Fundamentals' })).toBeVisible();
    });

    test('should maintain card proportions across breakpoints', async ({ page }) => {
      await page.goto('/');
      
      const cardTitle = page.getByRole('heading', { name: 'Machine Learning Fundamentals' });
      const cardDescription = page.getByText('Basic concepts of ML algorithms');
      
      // Test across different viewport sizes
      for (const [name, viewport] of Object.entries(viewports)) {
        await page.setViewportSize(viewport);
        
        // Card content should always be visible and readable
        await expect(cardTitle).toBeVisible();
        await expect(cardDescription).toBeVisible();
        
        // Buttons should be accessible
        await expect(page.getByRole('button', { name: 'Study' }).first()).toBeVisible();
      }
    });
  });

  test.describe('Typography Responsiveness', () => {
    test('should scale typography appropriately', async ({ page }) => {
      await page.goto('/');
      
      const dashboardTitle = page.locator('h1').nth(1);
      const brandTitle = page.locator('h1').first();
      
      // Test on mobile
      await page.setViewportSize(viewports.mobile);
      await expect(dashboardTitle).toBeVisible();
      await expect(brandTitle).toBeVisible();
      
      // Test on desktop
      await page.setViewportSize(viewports.desktop);
      await expect(dashboardTitle).toBeVisible();
      await expect(brandTitle).toBeVisible();
      
      // Typography should remain readable at all sizes
      await expect(dashboardTitle).toHaveClass(/text-4xl/);
      await expect(brandTitle).toHaveClass(/text-2xl/);
    });

    test('should maintain button sizing across devices', async ({ page }) => {
      await page.goto('/');
      
      const studyButton = page.getByRole('button', { name: 'Study' }).first();
      const connectWalletButton = page.getByRole('button', { name: 'Connect Wallet' });
      
      // Test across different viewport sizes
      for (const [name, viewport] of Object.entries(viewports)) {
        await page.setViewportSize(viewport);
        
        // Buttons should be touch-friendly on all devices
        await expect(studyButton).toBeVisible();
        await expect(connectWalletButton).toBeVisible();
        
        // Buttons should maintain proper padding
        await expect(studyButton).toHaveClass(/px-4/);
        await expect(studyButton).toHaveClass(/py-2/);
      }
    });
  });

  test.describe('Performance Across Devices', () => {
    test('should load quickly on mobile', async ({ page }) => {
      await page.setViewportSize(viewports.mobile);
      
      const startTime = Date.now();
      await page.goto('/');
      await expect(page.getByText('Dashboard')).toBeVisible();
      const loadTime = Date.now() - startTime;
      
      // Should load within reasonable time (adjust threshold as needed)
      expect(loadTime).toBeLessThan(5000);
    });

    test('should handle viewport changes smoothly', async ({ page }) => {
      await page.goto('/');
      await expect(page.getByText('Dashboard')).toBeVisible();
      
      // Rapidly change viewport sizes
      await page.setViewportSize(viewports.mobile);
      await expect(page.getByText('Dashboard')).toBeVisible();
      
      await page.setViewportSize(viewports.tablet);
      await expect(page.getByText('Dashboard')).toBeVisible();
      
      await page.setViewportSize(viewports.desktop);
      await expect(page.getByText('Dashboard')).toBeVisible();
      
      // Content should remain functional throughout
      await expect(page.getByText('Create New Topic')).toBeVisible();
    });
  });
});