# Desktop workspace loading failure isolation

The desktop starts with **one required request**: the validated catalog. The
taxonomic atlas and record comparison use those records directly and never
require source register, audit, methods metadata, or taxonomy API requests
to return before they can be used.

Opening the Source register, Collection audit, or Research method pane triggers
only the endpoint needed for that pane. Each shows its own loading, failure and
retry state. A transient failure cannot replace the catalog with a whole-app
service error. Previously successful optional data can remain visible after
switching panes.

The Chromium browser test mocks `/api/catalog` with the real public catalog
fixture and deliberately returns HTTP 503 from optional endpoints, then tests
recovery after the source register starts succeeding. This tests the React
frontend only; Windows WebView2 clean-install and packaging tests remain open
in issue #19.

To run in the repo root (Node 24, Python, Chromium installed):

```sh
cd Noemorph/frontend
npm ci
npm run build
npm install --no-save @playwright/test@1.65.0
npx playwright install chromium
npx playwright test --config=playwright.config.mjs
```
