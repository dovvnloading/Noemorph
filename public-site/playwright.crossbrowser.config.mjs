import { defineConfig } from '@playwright/test';
import chromiumConfig from './playwright.config.mjs';

// Keep the established Chromium gating suite unchanged. This separate config
// exercises identical journeys in independent browser engines while failures
// are being triaged before promotion to a required repository check.
export default defineConfig({
  ...chromiumConfig,
  projects: [
    { name: 'desktop-firefox', use: { browserName: 'firefox', viewport: { width: 1440, height: 900 } } },
    { name: 'desktop-webkit', use: { browserName: 'webkit', viewport: { width: 1440, height: 900 } } },
    { name: 'mobile-webkit', use: { browserName: 'webkit', viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } },
  ],
});
