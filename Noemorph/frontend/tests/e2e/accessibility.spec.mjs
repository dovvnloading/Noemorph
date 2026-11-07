import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { readFile } from 'node:fs/promises';

const catalog = JSON.parse(
  await readFile(new URL('../../../../public-site/dist/catalog.json', import.meta.url), 'utf8')
);

async function mockCatalog(page) {
  await page.route('**/api/**', (route) => {
    const pathname = new URL(route.request().url()).pathname;
    if (pathname === '/api/catalog') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: catalog.records,
          total: catalog.records.length,
          offset: 0,
          limit: catalog.records.length,
        }),
      });
    }
    return route.fulfill({ status: 503, body: 'Optional service unavailable' });
  });
}

async function checkSeriousWcagViolations(page) {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();
  const failures = results.violations
    .filter((violation) => ['critical', 'serious'].includes(violation.impact))
    .map((violation) => ({
      rule: violation.id,
      impact: violation.impact,
      targets: violation.nodes.slice(0, 4).map((node) => node.target),
    }));
  expect(failures).toEqual([]);
}

test('desktop record catalog and comparison have no serious/critical automated WCAG violations', async ({ page }) => {
  test.setTimeout(90_000);
  await mockCatalog(page);
  await page.goto('/?compare=seed-026-global-workspace-theory-gwt%2Cseed-027-global-neuronal-workspace-theory-gnwt');
  await expect(page.locator('.catalog-view')).toBeVisible();
  await checkSeriousWcagViolations(page);
});

test('desktop taxonomic atlas has no serious/critical automated WCAG violations', async ({ page }) => {
  test.setTimeout(90_000);
  await mockCatalog(page);
  await page.goto('/');
  await expect(page.locator('.atlas-field-sigma canvas').first()).toBeAttached();
  await checkSeriousWcagViolations(page);
});
