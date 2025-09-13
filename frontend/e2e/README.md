# End-to-End Tests with Playwright

This directory contains comprehensive end-to-end tests for the OpenVibe frontend application using Playwright.

## Test Structure

### Test Files

- **`setup-flow.spec.js`** - Tests the initial setup window flow
- **`app-creation-flow.spec.js`** - Tests creating new apps
- **`app-management-flow.spec.js`** - Tests app viewing, navigation, and deletion
- **`riff-creation-flow.spec.js`** - Tests creating and managing riffs within apps
- **`navigation-flow.spec.js`** - Tests navigation between pages and state management
- **`error-handling.spec.js`** - Tests error scenarios and user feedback

### Page Objects

- **`pages/BasePage.js`** - Base page object with common functionality
- **`pages/SetupPage.js`** - Setup window interactions
- **`pages/AppsPage.js`** - Apps list page interactions
- **`pages/AppDetailPage.js`** - App detail page interactions
- **`pages/RiffDetailPage.js`** - Riff detail page interactions

### Utilities

- **`utils/test-helpers.js`** - Common test utilities and helper functions

## Running Tests

### Prerequisites

1. Install dependencies:
   ```bash
   npm install
   ```

2. Install Playwright browsers:
   ```bash
   npx playwright install
   ```

### Running Tests Locally

```bash
# Run all e2e tests
npm run test:e2e

# Run tests in headed mode (see browser)
npm run test:e2e:headed

# Run tests with UI mode (interactive)
npm run test:e2e:ui

# Run tests in debug mode
npm run test:e2e:debug

# Run specific test file
npx playwright test setup-flow.spec.js

# Run tests on specific browser
npx playwright test --project=chromium
```

### Test Configuration

The tests are configured in `playwright.config.js` with the following settings:

- **Browsers**: Chromium, Firefox, WebKit
- **Viewports**: Desktop and Mobile
- **Base URL**: `http://localhost:5173`
- **Retries**: 2 on CI, 0 locally
- **Timeout**: Default Playwright timeouts
- **Screenshots**: On failure only
- **Videos**: Retained on failure
- **Traces**: On first retry

## Test Features

### Comprehensive Flow Testing

The tests cover complete user journeys:

1. **Setup Flow**: Initial application setup with API keys
2. **App Creation**: Creating new apps with validation
3. **App Management**: Viewing, navigating, and deleting apps
4. **Riff Creation**: Creating riffs within apps
5. **Navigation**: Browser navigation and state management
6. **Error Handling**: Network errors, validation errors, and edge cases

### API Mocking

Tests use comprehensive API mocking to:
- Simulate backend responses
- Test error scenarios
- Ensure consistent test data
- Avoid external dependencies

### Cross-Browser Testing

Tests run on multiple browsers:
- **Chromium** (Chrome/Edge)
- **Firefox**
- **WebKit** (Safari)

### Mobile Testing

Tests include mobile viewport testing:
- **Pixel 5** (Android)
- **iPhone 12** (iOS)

### Visual Testing

- Screenshots on test failures
- Video recordings for debugging
- Trace files for detailed analysis

## Test Data Management

### Dynamic Test Data

Tests use dynamically generated test data:
- Unique app names with timestamps
- Unique riff names with random IDs
- Isolated test environments per test

### State Management

- Tests clean up after themselves
- Each test starts with a clean state
- No test dependencies or ordering requirements

## Debugging Tests

### Local Debugging

1. **Headed Mode**: See tests run in real browser
   ```bash
   npm run test:e2e:headed
   ```

2. **Debug Mode**: Step through tests with debugger
   ```bash
   npm run test:e2e:debug
   ```

3. **UI Mode**: Interactive test runner
   ```bash
   npm run test:e2e:ui
   ```

### CI Debugging

When tests fail in CI:

1. Check the **Playwright Report** artifact
2. Review **Test Results** artifact for screenshots
3. Look at console logs in the workflow output

### Common Issues

1. **Timing Issues**: Tests wait for elements and loading states
2. **API Mocking**: Ensure mocks match actual API behavior
3. **Selectors**: Use stable selectors that won't change frequently
4. **State Cleanup**: Each test starts with clean state

## Best Practices

### Writing Tests

1. **Use Page Objects**: Encapsulate page interactions
2. **Wait for Elements**: Always wait for elements to be ready
3. **Descriptive Names**: Use clear, descriptive test names
4. **Independent Tests**: Each test should be independent
5. **Error Scenarios**: Test both happy path and error cases

### Selectors

1. **Stable Selectors**: Use data-testid or stable CSS selectors
2. **Avoid Brittle Selectors**: Don't rely on styling classes
3. **Semantic Selectors**: Use role-based selectors when possible

### Assertions

1. **Meaningful Assertions**: Assert on user-visible behavior
2. **Multiple Assertions**: Test various aspects of functionality
3. **Error Messages**: Include helpful error messages

## CI/CD Integration

Tests are integrated into the CI/CD pipeline:

- **Trigger**: Run on frontend changes
- **Environment**: Ubuntu with Node.js 20
- **Browsers**: All supported browsers installed
- **Artifacts**: Test reports and screenshots uploaded
- **PR Comments**: Results posted to pull requests

## Maintenance

### Updating Tests

When updating the application:

1. Update page objects if UI changes
2. Update selectors if elements change
3. Update API mocks if backend changes
4. Add new tests for new features

### Performance

- Tests run in parallel for speed
- API mocking reduces external dependencies
- Selective test running based on file changes

## Troubleshooting

### Common Errors

1. **Element not found**: Check if selector is correct and element exists
2. **Timeout errors**: Increase timeout or improve waiting logic
3. **API mock issues**: Verify mock responses match expected format
4. **Browser issues**: Ensure browsers are installed correctly

### Getting Help

1. Check Playwright documentation
2. Review test logs and screenshots
3. Use debug mode to step through tests
4. Check CI artifacts for detailed failure information