import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const GWT = 'seed-026-global-workspace-theory-gwt';
const GNWT = 'seed-027-global-neuronal-workspace-theory-gnwt';

async function checkSeriousWcagViolations(page) {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();
  // Report rule, impact, and actionable element targets in failing CI logs.
  const failures = results.violations
    .filter((violation) => ['critical', 'serious'].includes(violation.impact))
    .map((violation) => ({
      rule: violation.id,
      impact: violation.impact,
      targets: violation.nodes.slice(0, 4).map((node) => ({ target: node.target, summary: node.failureSummary, html: node.html.slice(0, 500) })),
    }));
  expect(failures).toEqual([]);
}

test('public search-first homepage has no serious/critical automated WCAG violations', async ({ page }) => {
  test.setTimeout(90_000);
  await page.goto('/');
  await expect(page.locator('#results-status')).toContainText('records');
  await checkSeriousWcagViolations(page);
});

test('public record, citations and comparison remain accessible', async ({ page }) => {
  test.setTimeout(90_000);
  await page.goto('/?compare=' + GWT + ',' + GNWT + '#catalog');
  await expect(page.locator('#comparison .comparison-card')).toHaveCount(2);
  await checkSeriousWcagViolations(page);
});

test('public taxonomy atlas expanded state has no serious/critical automated WCAG violations', async ({ page }) => {
  test.setTimeout(90_000);
  await page.goto('/?atlasKind=Scientific+theory#atlas');
  await expect(page.locator('#atlas-svg')).toBeVisible();
  await checkSeriousWcagViolations(page);
});
