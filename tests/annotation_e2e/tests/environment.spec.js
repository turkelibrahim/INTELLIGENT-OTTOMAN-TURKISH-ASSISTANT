
const { test, expect } = require('@playwright/test');
test('environment check', async ({ page }) => {
  await page.setContent('<html><body><h1>ANNOTATION_E2E_ENVIRONMENT_OK</h1></body></html>');
  await expect(page.locator('h1')).toHaveText('ANNOTATION_E2E_ENVIRONMENT_OK');
  await page.screenshot({ path: 'screenshots/environment_browser_test.png' });
});
