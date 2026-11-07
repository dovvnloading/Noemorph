import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';

const GWT = 'seed-026-global-workspace-theory-gwt';
const mergedCatalog = JSON.parse(await readFile(new URL('../../dist/catalog.json', import.meta.url), 'utf8'));
const catalogRecordCount = mergedCatalog.records.length;

test('search-first homepage responds to real text entry and filters', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#hero-record-count')).toHaveText(String(catalogRecordCount));
  await expect(page.locator('#results-status')).toContainText(`${catalogRecordCount} records`);

  await page.getByRole('searchbox', { name: 'Search the collection' }).fill('global workspace');
  await page.locator('#hero-search-form button[type="submit"]').click();
  await expect(page.locator('#records details.record').first()).toBeVisible();
  await expect(page.locator('#results-status')).toContainText('record');
  await expect(page.locator('#records')).toContainText(/global.*workspace/i);

  await page.locator('#kind').selectOption({ label: 'Scientific theory' });
  await expect(page.locator('#records details.record').first()).toBeVisible();
  await page.locator('#reset-filters').click();
  await expect(page.locator('#results-status')).toContainText(`${catalogRecordCount} records`);
});

test('permalink opens real source-rich record and citation export downloads', async ({ page }) => {
  await page.goto('/?record=' + GWT + '#catalog');
  const record = page.locator('details.record[data-record-id="' + GWT + '"]');
  await expect(record).toHaveAttribute('open', '');
  await expect(record).toContainText(/global workspace/i);
  await record.locator('details.record-depth > summary').click();
  await expect(record.getByText(/Retained citations/)).toBeVisible();
  await expect(record.locator('a[href^="https://"]').first()).toBeVisible();

  const fileEvent = page.waitForEvent('download');
  await record.getByRole('button', { name: /Export citations/ }).click();
  const download = await fileEvent;
  expect(download.suggestedFilename()).toMatch(/\.csl\.json$/);
  const filename = await download.path();
  expect(filename).not.toBeNull();
  const exported = JSON.parse(await readFile(filename, 'utf8'));
  expect(exported.length).toBeGreaterThanOrEqual(2);
  expect(exported.every((item) => item.note.includes('not proof of claim support'))).toBe(true);
});

test('comparison stays explicitly read-only, navigable, and reversible', async ({ page }) => {
  await page.goto('/?record=' + GWT + '#catalog');
  const gwt = page.locator('details.record[data-record-id="' + GWT + '"]');
  await expect(gwt).toHaveAttribute('open', '');
  await gwt.getByRole('button', { name: 'Compare this record' }).click();

  await page.locator('#search').fill('panpsychism');
  await expect(page.locator('#records details.record').first()).toBeVisible();
  const second = page.locator('#records details.record').first();
  await second.locator(':scope > summary').click();
  await second.getByRole('button', { name: 'Compare this record' }).click();
  await expect(page.locator('#comparison')).toBeVisible();
  await expect(page.locator('#comparison .comparison-card')).toHaveCount(2);
  await expect(page.locator('#comparison')).toContainText(/independent catalog entries/i);
  await expect(page.locator('#comparison a.comparison-link')).toHaveAttribute('href', /compare=/);
  await page.locator('#clear-comparison').click();
  await expect(page.locator('#comparison')).toBeHidden();
});

test('optional reading and taxonomy tools open from valid deep links', async ({ page }) => {
  await page.goto('/?journey=awareness&step=2#discover');
  await expect(page.locator('#discovery-disclosure')).toHaveAttribute('open', '');
  await expect(page.locator('#discovery-stage')).toBeVisible();
  await expect(page.locator('#discovery-stage')).toContainText(/source|research|question/i);

  await page.goto('/?atlasKind=Scientific+theory#atlas');
  await expect(page.locator('#atlas-disclosure')).toHaveAttribute('open', '');
  await expect(page.locator('#atlas-svg')).toBeVisible();
  await expect(page.locator('#atlas-node-list button').first()).toBeVisible();
});

test('failed catalog download shows a recoverable error instead of blank content', async ({ page }) => {
  await page.route('**/catalog.json', (route) =>
    route.fulfill({ status: 503, contentType: 'text/plain', body: 'temporarily unavailable' }));
  await page.goto('/');
  await expect(page.locator('#results-status')).toHaveText('The collection could not be loaded.');
  await expect(page.locator('#records')).toContainText(/reload/i);
});
