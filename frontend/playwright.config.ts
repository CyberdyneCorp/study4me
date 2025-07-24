/**
 * playwright.config.ts - Playwright configuration for Study4Me frontend testing
 * 
 * This configuration sets up end-to-end testing for the Study4Me application
 * with proper browser support, test directories, and development server integration.
 * 
 * Features:
 * - Multi-browser testing (Chromium, Firefox, WebKit)
 * - Automatic dev server startup for testing
 * - Visual regression testing setup
 * - Mobile viewport testing
 * - Test artifacts collection (screenshots, videos)
 */

import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright Test Configuration
 * Comprehensive setup for end-to-end testing of the Study4Me application
 */
export default defineConfig({
  // Test directory containing all test files
  testDir: './tests',
  
  /**
   * Test Execution Settings
   * Controls how tests are run and reported
   */
  // Run tests in files in parallel
  fullyParallel: true,
  
  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,
  
  // Retry on CI only
  retries: process.env.CI ? 2 : 0,
  
  // Opt out of parallel tests on CI
  workers: process.env.CI ? 1 : undefined,
  
  /**
   * Test Reporting
   * Multiple reporters for different environments
   */
  reporter: [
    ['html'],           // HTML report for local development
    ['line'],           // Line reporter for CI
    ['json', { outputFile: 'test-results.json' }]  // JSON for integration
  ],
  
  /**
   * Global Test Configuration
   * Settings applied to all tests
   */
  use: {
    // Base URL for all tests - points to local dev server
    baseURL: 'http://localhost:3001',
    
    // Collect trace when retrying the failed test
    trace: 'on-first-retry',
    
    // Take screenshot on failure
    screenshot: 'only-on-failure',
    
    // Record video on failure
    video: 'retain-on-failure',
    
    // Global timeout for actions (clicks, fills, etc.)
    actionTimeout: 10000,
    
    // Global timeout for navigation
    navigationTimeout: 30000,
  },

  /**
   * Browser Projects Configuration
   * Tests will run across multiple browsers and devices
   */
  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        // Additional Chromium-specific settings
        launchOptions: {
          args: ['--disable-dev-shm-usage'] // Useful for CI environments
        }
      },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    /**
     * Mobile Testing
     * Test responsive design on mobile devices
     */
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },

    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },

    /**
     * Tablet Testing
     * Test tablet-specific layouts and interactions
     */
    {
      name: 'Tablet',
      use: { ...devices['iPad Pro'] },
    },
  ],

  /**
   * Development Server Configuration
   * Automatically starts the dev server before running tests
   */
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3001',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000, // 2 minutes timeout for server startup
    stdout: 'ignore',
    stderr: 'pipe',
  },
});