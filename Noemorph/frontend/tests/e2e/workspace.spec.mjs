import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';

const catalog = JSON.parse(
  await readFile(new URL('../../../../public-site/dist/catalog.json', import.meta.url), 'utf8')
);

async function chooseWorkspace(page, name) {
  const mobileSelector = page.locator('.mobile-workspace-switcher select');
  if (await mobileSelector.isVisible()) {
    await mobileSelector.selectOption({ label: name });
  } else {
    await page.locator('.folio-navigation').getByRole('button', { name }).click();
  }
}

test('catalog remains usable when optional workspaces fail and can be retried', async ({ page }) => {
  let sourcesAvailable = false;
  const requested = [];
  await page.route('**/api/**', (route) => {
    const path = new URL(route.request().url()).pathname;
    requested.push(path);
    if (path === '/api/catalog') {
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
    if (path === '/api/sources' && sourcesAvailable) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0 }),
      });
    }
    return route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Intentional optional service failure' }),
    });
  });

  // A validated comparison deep link starts in the catalog instead of the
  // WebGL-backed atlas, which is tested separately by the public browser suite.
  await page.goto('/?compare=seed-026-global-workspace-theory-gwt%2Cseed-027-global-neuronal-workspace-theory-gnwt');
  await expect(page.locator('.catalog-view')).toBeVisible();
  await expect(page.locator('.catalog-table tbody tr').first()).toBeVisible();
  expect(requested).toContain('/api/catalog');
  expect(requested).not.toContain('/api/sources');
  expect(requested).not.toContain('/api/coverage');
  expect(requested).not.toContain('/api/meta');
  expect(requested).not.toContain('/api/graph/taxonomy');

  await chooseWorkspace(page, 'Source register');
  await expect(page.getByText('Source register unavailable')).toBeVisible();
  await expect(page.getByText('Intentional optional service failure')).toBeVisible();

  sourcesAvailable = true;
  await page.getByRole('button', { name: 'Retry source register' }).click();
  await expect(page.locator('.sources-view')).toBeVisible();
  await expect(page.locator('.sources-view')).toContainText('0 of 0 works');

  await chooseWorkspace(page, 'Collection audit');
  await expect(page.getByText('Collection audit unavailable')).toBeVisible();

  await chooseWorkspace(page, 'Research method');
  await expect(page.getByText('Research method unavailable')).toBeVisible();

  await chooseWorkspace(page, 'Record catalog');
  await expect(page.locator('.catalog-table tbody tr').first()).toBeVisible();
  expect(requested.filter((path) => path === '/api/catalog')).toHaveLength(1);
});

test('failed required catalog request presents a clear service error', async ({ page }) => {
  await page.route('**/api/**', (route) =>
    route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Catalog unavailable in integration test' }),
    })
  );
  await page.goto('/');
  await expect(page.getByText('Research service unavailable')).toBeVisible();
  await expect(page.getByText('Catalog unavailable in integration test')).toBeVisible();
});

test('taxonomic atlas renders; record inspection works on mobile and trace opens on desktop', async ({ page }, testInfo) => {
  const pageErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));

  await page.route('**/api/**', (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === '/api/catalog') {
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

  await page.goto('/');
  await expect(page.locator('.atlas-instrument')).toBeVisible();
  await expect(page.locator('.atlas-field-sigma canvas').first()).toBeAttached();
  await page.getByRole('button', { name: 'Open record index' }).click();
  const firstRecord = page.locator('.atlas-result-list button').first();
  await expect(firstRecord).toBeVisible();
  await firstRecord.click();
  await expect(page.getByRole('heading', { name: 'Aberrant Salience Hypothesis' })).toBeVisible();
  if (testInfo.project.name === 'mobile-chromium') {
    // Mobile intentionally opens a full-screen inspector that covers the atlas
    // projection switch. Verify the usable inspection flow, not a hidden control.
    await expect(page.getByRole('button', { name: 'Close record details' })).toBeVisible();
  } else {
    const trace = page.locator('.atlas-projection-switch').getByRole('button', { name: 'Trace' });
    await expect(trace).toBeEnabled();
    await trace.click();
    await expect(page.locator('.atlas-trace')).toBeVisible();
  }
  expect(pageErrors).toEqual([]);
});
