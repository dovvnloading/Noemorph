import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import vm from 'node:vm';

const dist = resolve(dirname(fileURLToPath(import.meta.url)), '../dist');
const script = readFileSync(resolve(dist, 'app.js'), 'utf8');
const html = readFileSync(resolve(dist, 'index.html'), 'utf8');

const records = [
  {
    id: 'record-one', name: 'Global Neuronal Workspace',
    kind: 'Scientific theory', domain: 'Neuroscience',
    tradition: 'Contemporary', review_state: 'provisional',
    summary: 'A theory of conscious access.', proponents: [],
    claim_reviews: [{
      id: 'record-one:scope', kind: 'scope', field: 'claim_scope.target',
      text: 'A theory of conscious access.', review_state: 'unreviewed',
      citations: [{
        citation_url: 'https://example.org/one', source_uid: 'work-demo',
        locator_kind: 'source-url-only', review_state: 'unreviewed',
      }],
    }],
    citations: [{
      title: 'Original model', authors: 'Researcher', year: 2024,
      authority: 'primary-original', verification: 'human-verified',
      url: 'https://example.org/one',
    }],
  },
  {
    id: 'record-two', name: 'Panpsychism',
    kind: 'Philosophical position', domain: 'Philosophy',
    tradition: 'Analytic', review_state: 'needs-review',
    summary: 'A philosophical position.', proponents: [],
    citations: [{
      title: 'Overview', authors: 'Scholar', year: 'living entry',
      authority: 'scholarly-secondary', verification: 'doi-resolved',
      doi: '10.1000/example', url: 'https://doi.org/10.1000/example',
    }],
  },
];

async function boot(locationHref = 'https://example.org/Noemorph/') {
  class FakeElement {
    constructor() {
      this.value = '';
      this.innerHTML = '';
      this.textContent = '';
      this.dataset = {};
      this.listeners = {};
      this.children = [];
    }
    addEventListener(type, callback) { this.listeners[type] = callback; }
    append(child) { this.children.push(child); }
    click() { this.clicked = true; }
    remove() {}
    closest() { return this; }
    focus() { this.focused = true; }
    scrollIntoView() { this.scrolled = true; }
    querySelector(selector) {
      if (selector === 'details[open] summary' && this.innerHTML.includes(' open>')) {
        return selectedSummary;
      }
      return null;
    }
  }
  const ids = ['#records', '#results-status', '#search', '#kind',
    '#domain', '#tradition', '#review', '#verification', '#reset-filters', '#pagination'];
  const elements = Object.fromEntries(ids.map(id => [id, new FakeElement()]));
  const selectedSummary = new FakeElement();
  const downloaded = [];
  const links = [];
  class FakeURL extends URL {}
  FakeURL.createObjectURL = blob => { downloaded.push(blob); return 'blob:test'; };
  FakeURL.revokeObjectURL = () => {};

  const window = {
    location: { href: locationHref },
    history: { replaceState: (_state, _title, url) => { window.location.href = url; } },
    requestAnimationFrame: fn => fn(),
    setTimeout: fn => fn(),
  };
  const document = {
    querySelector: selector => elements[selector] || null,
    createElement: () => new FakeElement(),
    body: { append: link => links.push(link) },
  };
  const context = {
    document, window, URL: FakeURL, Blob, Element: FakeElement,
    fetch: () => Promise.resolve({ ok: true, json: () => Promise.resolve({ records }) }),
  };
  vm.runInNewContext(script, context, { filename: 'public-site/dist/app.js' });
  await new Promise(resolve => setImmediate(resolve));
  return { elements, selectedSummary, downloaded, links, FakeElement, window };
}

test('public HTML exposes every filter and labeled results', () => {
  for (const id of ['search', 'kind', 'domain', 'tradition', 'review',
    'verification', 'reset-filters', 'records', 'results-status']) {
    assert.ok(html.includes('id="' + id + '"'), 'Missing #' + id);
  }
  assert.match(html, /aria-live="polite"/);
});

test('filters combine without confusing citation states with claim verification', async () => {
  const app = await boot();
  const { elements } = app;
  assert.match(elements['#results-status'].textContent, /^2 records/);

  elements['#domain'].value = 'Neuroscience';
  elements['#domain'].listeners.change();
  assert.match(elements['#results-status'].textContent, /^1 record/);
  assert.match(elements['#records'].innerHTML, /Global Neuronal Workspace/);
  assert.doesNotMatch(elements['#records'].innerHTML, /Panpsychism/);

  elements['#verification'].value = 'doi-resolved';
  elements['#verification'].listeners.change();
  assert.match(elements['#results-status'].textContent, /^0 records/);

  elements['#reset-filters'].listeners.click();
  assert.match(elements['#results-status'].textContent, /^2 records/);
  assert.equal(elements['#verification'].value, '');
});

test('a permanent record URL expands and focuses its entry', async () => {
  const app = await boot('https://example.org/Noemorph/?record=record-two#catalog');
  assert.match(app.elements['#records'].innerHTML, /data-record-id="record-two" open/);
  assert.equal(app.selectedSummary.focused, true);
  assert.match(app.elements['#records'].innerHTML, /Permanent link/);
});

test('claim review leads remain visibly unverified in the public catalog', async () => {
  const app = await boot();
  assert.match(app.elements['#records'].innerHTML, /Claim-level source review leads/);
  assert.match(app.elements['#records'].innerHTML, /do not verify support/);
  assert.match(app.elements['#records'].innerHTML, /source URL only/i);
});

test('citation export retains recorded provenance without inventing a publication year', async () => {
  const app = await boot();
  const target = new app.FakeElement();
  target.dataset.export = 'record-two';
  app.elements['#records'].listeners.click({ target });
  assert.equal(app.links.length, 1);
  assert.ok(app.links[0].download.endsWith('-citations.csl.json'));
  const exported = JSON.parse(await app.downloaded[0].text());
  assert.equal(exported.length, 1);
  assert.equal(exported[0].DOI, '10.1000/example');
  assert.equal(exported[0].issued, undefined);
  assert.match(exported[0].note, /not proof of claim support/);
});
