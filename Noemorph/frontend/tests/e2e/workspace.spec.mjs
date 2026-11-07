import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';

const catalog = JSON.parse(
  await readFile(new URL('../../../../public-site/dist/catalog.json', import.meta.url), 'utf8')
);

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

  await page.locator('.folio-navigation').getByRole('button', { name: 'Source register' }).click();
  await expect(page.getByText('Source register unavailable')).toBeVisible();
  await expect(page.getByText('Intentional optional service failure')).toBeVisible();

  sourcesAvailable = true;
  await page.getByRole('button', { name: 'Retry source register' }).click();
  await expect(page.locator('.sources-view')).toBeVisible();
  await expect(page.locator('.sources-view')).toContainText('0 of 0 works');

  await page.locator('.folio-navigation').getByRole('button', { name: 'Collection audit' }).click();
  await expect(page.getByText('Collection audit unavailable')).toBeVisible();

  await page.locator('.folio-navigation').getByRole('button', { name: 'Research method' }).click();
  await expect(page.getByText('Research method unavailable')).toBeVisible();

  await page.locator('.folio-navigation').getByRole('button', { name: 'Record catalog' }).click();
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
