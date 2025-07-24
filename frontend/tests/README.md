# Playwright Testing Guide for Study4Me

This directory contains comprehensive end-to-end tests for the Study4Me frontend application using Playwright.

## 🧪 Test Structure

### Test Files

- **`dashboard.spec.ts`** - Main dashboard functionality tests
  - Topic card interactions
  - Modal operations (create, study, sources, delete)
  - CRUD operations for topics
  - Layout and responsive behavior

- **`modals.spec.ts`** - Modal component tests
  - Topic creation modal
  - Chat modal (study interface)
  - Sources modal (upload, website, YouTube tabs)
  - Confirmation modal
  - Wallet modal
  - Modal accessibility and keyboard navigation

- **`navbar.spec.ts`** - Navigation bar tests
  - Brand display and layout
  - MCP toggle functionality
  - Wallet connection button
  - Responsive behavior

- **`responsive.spec.ts`** - Responsive design tests
  - Mobile layouts (320px - 768px)
  - Tablet layouts (768px - 1024px)
  - Desktop layouts (1024px+)
  - Grid system responsiveness
  - Typography scaling

- **`accessibility.spec.ts`** - Accessibility compliance tests
  - Keyboard navigation
  - Screen reader compatibility
  - Focus management
  - ARIA attributes
  - WCAG 2.1 compliance

### Utility Files

- **`test-utils.ts`** - Reusable test utilities and helpers
  - Modal interaction helpers
  - Form filling utilities
  - Accessibility testing helpers
  - Common element selectors
  - Test data generators

## 🚀 Getting Started

### Prerequisites

Make sure you have installed the dependencies:

```bash
npm install
```

Install Playwright browsers:

```bash
npx playwright install
```

### Running Tests

```bash
# Run all tests
npm run test

# Run tests with browser UI visible
npm run test:headed

# Run tests with Playwright UI mode
npm run test:ui

# Run tests in debug mode
npm run test:debug

# Generate and show test report
npm run test:report
```

### Running Specific Tests

```bash
# Run specific test file
npm run test tests/dashboard.spec.ts

# Run specific test by name
npm run test -- --grep "should display the main dashboard layout"

# Run tests for specific browser
npm run test -- --project=chromium
```

## 🏗️ Test Architecture

### Browser Coverage

Tests run across multiple browsers and device configurations:

- **Desktop Browsers**: Chromium, Firefox, WebKit
- **Mobile Devices**: Mobile Chrome (Pixel 5), Mobile Safari (iPhone 12)
- **Tablets**: iPad Pro

### Test Organization

Tests are organized using Playwright's `test.describe()` blocks:

```typescript
test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    // Setup code runs before each test
  });

  test.describe('Topic Management', () => {
    // Nested test groups for better organization
  });
});
```

### Page Object Pattern

We use helper classes in `test-utils.ts` for reusable functionality:

```typescript
const { modal, form, accessibility } = createTestHelpers(page);

// Clean, readable test actions
await modal.openTopicCreation();
await form.createTopic({ name: 'Test', description: 'Test desc' });
await accessibility.checkModalAccessibility(modal);
```

## 📋 Writing Tests

### Test Best Practices

1. **Use Descriptive Names**: Test names should clearly describe what is being tested
2. **Single Responsibility**: Each test should verify one specific behavior
3. **Proper Setup/Teardown**: Use `beforeEach`/`afterEach` for consistent test state
4. **Stable Selectors**: Use semantic selectors (`getByRole`, `getByText`) over CSS selectors
5. **Wait for Elements**: Always wait for elements to be visible before interacting

### Example Test Structure

```typescript
test('should create a new topic successfully', async ({ page }) => {
  const { modal, form, wait } = createTestHelpers(page);
  
  // Arrange
  await modal.openTopicCreation();
  const newTopic = testData.randomTopic();
  
  // Act
  await form.createTopic(newTopic);
  
  // Assert
  await wait.waitForTopicToAppear(newTopic.name);
  await expect(page.getByText(newTopic.name)).toBeVisible();
});
```

### Common Patterns

#### Modal Testing
```typescript
// Open modal
await page.getByText('Create New Topic').click();
await expect(page.getByRole('dialog')).toBeVisible();

// Close modal with different methods
await page.keyboard.press('Escape'); // Keyboard
await page.getByRole('button', { name: '×' }).click(); // Button
await page.locator('[role="dialog"]').click({ position: { x: 10, y: 10 } }); // Backdrop
```

#### Form Testing
```typescript
// Fill form
await page.getByLabel('Topic Name').fill('Test Topic');
await page.getByLabel('Description').fill('Test description');

// Check form validation
const submitButton = page.getByRole('button', { name: 'Create Topic' });
await expect(submitButton).toBeDisabled(); // Before valid input
await expect(submitButton).toBeEnabled();  // After valid input
```

#### Responsive Testing
```typescript
// Test different viewports
await page.setViewportSize({ width: 375, height: 667 }); // Mobile
await page.setViewportSize({ width: 768, height: 1024 }); // Tablet
await page.setViewportSize({ width: 1280, height: 720 }); // Desktop
```

## 🎯 Test Coverage

### Functional Coverage

- ✅ Topic CRUD operations
- ✅ Modal interactions (all types)
- ✅ Form validation and submission
- ✅ Navigation and routing
- ✅ Responsive layout behavior
- ✅ User interaction patterns

### Accessibility Coverage

- ✅ Keyboard navigation
- ✅ Focus management
- ✅ ARIA attributes
- ✅ Screen reader support
- ✅ Color contrast validation
- ✅ Interactive element accessibility

### Browser Coverage

- ✅ Chromium (Chrome, Edge)
- ✅ Firefox
- ✅ WebKit (Safari)
- ✅ Mobile Chrome
- ✅ Mobile Safari
- ✅ Tablet layouts

## 🔧 Configuration

### Playwright Config

The main configuration is in `playwright.config.ts`:

- **Test Directory**: `./tests`
- **Base URL**: `http://localhost:3001`
- **Automatic Dev Server**: Starts before tests run
- **Multiple Reporters**: HTML, line, and JSON output
- **Parallel Execution**: Tests run in parallel for speed
- **Retry Logic**: Automatic retries on CI failures

### Environment Variables

- `CI`: Enables CI-specific settings (retries, single worker)
- Custom variables can be added for different environments

## 📊 Reporting

### HTML Report

After running tests, view the HTML report:

```bash
npm run test:report
```

The report includes:
- Test results by browser
- Screenshots of failures
- Video recordings of failed tests
- Test traces for debugging

### CI Integration

Tests automatically run on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

Reports are uploaded as GitHub Actions artifacts.

## 🐛 Debugging

### Debug Mode

Run tests in debug mode with browser developer tools:

```bash
npm run test:debug
```

### Trace Viewer

For failed tests, use Playwright's trace viewer:

```bash
npx playwright show-trace test-results/[test-name]/trace.zip
```

### Common Issues

1. **Element Not Found**: Use `page.locator().waitFor()` before interactions
2. **Timing Issues**: Add appropriate waits with `expect().toBeVisible()`
3. **Flaky Tests**: Check for race conditions and add stability waits
4. **Selector Issues**: Use semantic selectors over CSS selectors

## 📈 Performance

### Test Execution

- Tests run in parallel across multiple workers
- Average execution time: ~30-60 seconds for full suite
- Individual test files can be run for faster feedback

### Optimization Tips

1. Use `test.beforeEach()` for common setup
2. Group related tests with `test.describe()`
3. Use page object patterns for reusable actions
4. Minimize browser context switches
5. Use selective test execution during development

## 🤝 Contributing

When adding new tests:

1. Follow the existing naming conventions
2. Add tests to the appropriate spec file
3. Use the test utilities for common actions
4. Ensure tests pass across all browsers
5. Add accessibility tests for new components
6. Update this README if adding new test patterns

## 📚 Resources

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Accessibility Testing Guide](https://playwright.dev/docs/accessibility-testing)
- [Visual Testing](https://playwright.dev/docs/test-screenshots)