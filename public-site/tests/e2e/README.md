# Real-browser public site regression suite

This is additional coverage, not a replacement for the dependency-free Node
smoke tests in `public-site/tests/public-site.test.mjs`.

CI generates `public-site/dist/catalog.json` from the canonical merged catalog,
then runs Playwright against a static local HTTP server in real Chromium at
1440×900 and a touch-enabled 390×844 viewport.

Tested journeys: search and filtering; a stable record deep link; source
disclosure and CSL-JSON download; explicit two-record comparison; direct
reading-path and taxonomy-map links; and a failed catalog request.

From the repository root, with Python and Node 24 installed:

```sh
python public-site/build.py
npm install --no-save --prefix public-site @playwright/test@1.65.0
./public-site/node_modules/.bin/playwright install chromium
./public-site/node_modules/.bin/playwright test --config=public-site/playwright.config.mjs
```

This initial suite does not certify WCAG compliance, screen-reader behavior,
real hardware performance, cross-browser support, or the Windows WebView2 shell.
Expand to WebKit/Firefox and manual assistive-technology testing once this baseline
is stable. The test-only Playwright version is pinned in the workflow.
