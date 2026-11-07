# Real-browser public site regression suite

This is additional coverage, not a replacement for the dependency-free Node
smoke tests in `public-site/tests/public-site.test.mjs`.

CI generates `public-site/dist/catalog.json` from the canonical merged catalog,
then runs Playwright against a static local HTTP server in real Chromium at
1440×900 and a touch-enabled 390×844 viewport. This established Chromium
suite is a **required branch quality gate**.

Tested journeys: search and filtering; a stable record deep link; source
disclosure and CSL-JSON download; explicit two-record comparison; direct
reading-path and taxonomy-map links; and a failed catalog request. Automated
serious/critical WCAG rules are also checked, but they do not replace manual
assistive-technology testing.

Issue #18 also tracks browser-engine coverage. The separate
`playwright.crossbrowser.config.mjs` runs these same public journeys and
automated accessibility checks on **desktop Firefox**, **desktop WebKit**, and
**touch-enabled mobile WebKit**. The GitHub workflow
`public-crossbrowser.yml` is intentionally **non-blocking** while failures
are triaged: check its Actions step outcome, summary and uploaded traces, not
just its green overall workflow status. Promote it to a required check only
when the run passes consistently on representative PRs.

From the repository root, with Python and Node 24 installed:

```sh
python public-site/build.py
npm install --no-save --prefix public-site @playwright/test@1.65.0 @axe-core/playwright@4.14.0
./public-site/node_modules/.bin/playwright install --with-deps chromium firefox webkit
./public-site/node_modules/.bin/playwright test --config=public-site/playwright.config.mjs
./public-site/node_modules/.bin/playwright test --config=public-site/playwright.crossbrowser.config.mjs
```

These automated checks do **not** certify WCAG compliance, screen-reader
behavior, real hardware performance, broad cross-browser support, or the
Windows WebView2 shell. Those acceptance checks remain open in issues #18
and #19. The test-only Playwright version is pinned in CI.
