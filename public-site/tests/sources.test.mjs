import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import vm from 'node:vm';

const dist = resolve(dirname(fileURLToPath(import.meta.url)), '../dist');
const script = readFileSync(resolve(dist, 'sources.js'), 'utf8');
const html = readFileSync(resolve(dist, 'index.html'), 'utf8');

const shared = {
  source_uid: 'work-shared',
  title: 'Shared Study',
  authors: 'First Author',
  year: 2024,
  url: 'https://doi.org/10.7777/shared',
  doi: '10.7777/shared',
  authority: 'primary-original',
  verification: 'doi-resolved',
};
const records = [
  {
    id: 'record-one',
    name: 'First Record',
    citations: [
      shared,
      {
        source_uid: 'work-unique',
        title: 'Unique Review',
        authors: 'Second Author',
        year: 2025,
        url: 'https://example.org/review',
        authority: 'scholarly-secondary',
        verification: 'human-verified',
      },
    ],
  },
  {
    id: 'record-two',
    name: 'Second Record',
    citations: [
      {
        ...shared,
        title: 'Shared Study — alternative title',
        authors: 'Alternate Author',
        year: 2026,
        authority: 'scholarly-secondary',
        verification: 'human-verified',
      },
    ],
  },
  {
    id: 'record-three',
    name: 'Third Record',
    citations: [
      {
        source_uid: 'work-malicious',
        title: '<img src=x onerror=alert(1)>',
        authors: 'Unsafe Test',
        year: '',
        url: 'javascript:alert(1)',
        authority: 'independent-test',
      },
    ],
  },
];

function boot(url = 'https://example.org/Noemorph/', input = records) {
  class FakeElement {
    constructor() {
      this.value = '';
      this.innerHTML = '';
      this.textContent = '';
      this.children = [];
      this.listeners = {};
      this.dataset = {};
      this.disabled = false;
    }
    append(node) { this.children.push(node); }
    addEventListener(type, callback) { this.listeners[type] = callback; }
    focus() { this.focused = true; }
    scrollIntoView() { this.scrolled = true; }
    querySelector(selector) {
      if (selector === 'details[open] summary' && this.innerHTML.includes(' open>')) return selected;
      return null;
    }
    closest() { return this; }
  }
  const ids = ['#source-search', '#source-role', '#source-verification', '#source-reset',
    '#source-results', '#source-status', '#source-pagination'];
  const elements = Object.fromEntries(ids.map(id => [id, new FakeElement()]));
  const selected = new FakeElement();
  const window = {
    location: { href: url },
    history: { replaceState: (_state, _title, href) => { window.location.href = href; } },
    requestAnimationFrame: callback => callback(),
  };
  const document = {
    querySelector: key => elements[key] || null,
    createElement: () => new FakeElement(),
  };
  vm.runInNewContext(script, { document, window, URL, Element: FakeElement },
    { filename: 'public-site/dist/sources.js' });
  window.NoemorphSources.mount(input);
  return { elements, window, selected, FakeElement };
}

test('source explorer is a real navigable feature of the public website', () => {
  assert.match(html, /href="#sources"/);
  assert.match(html, /src="sources.js"/);
  assert.match(html, /href="sources.css"/);
  for (const id of ['source-search', 'source-role', 'source-verification',
    'source-results', 'source-status', 'source-pagination']) {
    assert.ok(html.includes('id="' + id + '"'), id);
  }
  const app = boot();
  assert.match(app.elements['#source-status'].textContent, /^3 source locators/);
  assert.match(app.elements['#source-results'].innerHTML, /Shared Study/);
  assert.match(app.elements['#source-results'].innerHTML, /2 citation uses/);
  assert.match(app.elements['#source-results'].innerHTML, /2 recorded bibliographic variants/);
  assert.match(app.elements['#source-results'].innerHTML, /First Record/);
  assert.match(app.elements['#source-results'].innerHTML, /Second Record/);
  assert.match(app.elements['#source-results'].innerHTML, /Role: primary-original/);
  assert.match(app.elements['#source-results'].innerHTML, /Role: scholarly-secondary/);
  assert.match(app.elements['#source-results'].innerHTML, /not verified evidence of support/);
});

test('source search finds titles, alternate authors, DOI and citing records', () => {
  const app = boot();
  const search = app.elements['#source-search'];
  for (const text of ['Shared Study', 'ALTERNATE AUTHOR', '10.7777/shared', 'second record']) {
    search.value = text;
    search.listeners.input();
    assert.match(app.elements['#source-status'].textContent, /^1 source locator/, text);
    assert.match(app.elements['#source-results'].innerHTML, /Shared Study/, text);
  }
  search.value = 'not in the bibliography';
  search.listeners.input();
  assert.match(app.elements['#source-status'].textContent, /^0 source locators/);
  assert.match(app.elements['#source-results'].innerHTML, /No matching sources/);
  app.elements['#source-reset'].listeners.click();
  assert.match(app.elements['#source-status'].textContent, /^3 source locators/);
  assert.equal(search.focused, true);
});

test('role and verification filters require a matching citation use together', () => {
  const app = boot();
  const role = app.elements['#source-role'];
  const verification = app.elements['#source-verification'];
  role.value = 'primary-original';
  role.listeners.change();
  assert.match(app.elements['#source-status'].textContent, /^1 source locator/);
  verification.value = 'human-verified';
  verification.listeners.change();
  // The shared locator has both statuses, but not on the same citation use.
  assert.match(app.elements['#source-status'].textContent, /^0 source locators/);
  role.value = 'scholarly-secondary';
  role.listeners.change();
  assert.match(app.elements['#source-status'].textContent, /^2 source locators/);
  verification.value = 'pending-metadata-review';
  verification.listeners.change();
  assert.match(app.elements['#source-status'].textContent, /^0 source locators/);
});

test('deep link expands one known locator and preserves distinct record permalinks', () => {
  const app = boot('https://example.org/Noemorph/?source=work-shared#sources');
  assert.match(app.elements['#source-results'].innerHTML, /data-source-id="work-shared" open/);
  assert.match(app.elements['#source-results'].innerHTML, /record=record-one/);
  assert.match(app.elements['#source-results'].innerHTML, /record=record-two/);
  assert.equal(app.selected.focused, true);
  const url = app.window.NoemorphSources.href(shared);
  assert.equal(new URL(url).searchParams.get('source'), 'work-shared');
  assert.equal(new URL(url).hash, '#sources');
  app.elements['#source-search'].value = 'Unique Review';
  app.elements['#source-search'].listeners.input();
  assert.equal(new URL(app.window.location.href).searchParams.has('source'), false);
  assert.match(app.elements['#source-status'].textContent, /^1 source locator/);
});

test('untrusted source parameters are ignored and unsafe source text is escaped', () => {
  for (const query of [
    '?source=%3Cscript%3E',
    '?source=work-shared&source=work-shared',
    '?record=record-one&source=work-shared',
  ]) {
    const app = boot('https://example.org/Noemorph/' + query);
    assert.doesNotMatch(app.elements['#source-results'].innerHTML, /data-source-id="work-shared" open/);
  }
  const app = boot();
  assert.match(app.elements['#source-results'].innerHTML, /&lt;img src=x onerror=alert\(1\)&gt;/);
  assert.doesNotMatch(app.elements['#source-results'].innerHTML, /href="javascript:/);
});

test('pagination works without inserting the full bibliography into the DOM', () => {
  const input = Array.from({ length: 20 }, (_, index) => ({
    id: 'record-' + index, name: 'Record ' + index,
    citations: [{
      source_uid: 'work-' + index, title: 'Source ' + String(index).padStart(2, '0'),
      authors: 'Author', year: 2024, url: 'https://example.org/source-' + index,
      authority: 'primary-original', verification: 'locator-recorded',
    }],
  }));
  const app = boot('https://example.org/Noemorph/', input);
  assert.match(app.elements['#source-status'].textContent, /^20 source locators · showing 1–8/);
  assert.match(app.elements['#source-pagination'].innerHTML, /Page 1 of 3/);
  assert.match(app.elements['#source-results'].innerHTML, /Source 07/);
  assert.doesNotMatch(app.elements['#source-results'].innerHTML, /Source 08/);
  const button = new app.FakeElement();
  button.dataset.sourcePage = '2';
  app.elements['#source-pagination'].listeners.click({ target: button });
  assert.match(app.elements['#source-pagination'].innerHTML, /Page 2 of 3/);
  assert.match(app.elements['#source-results'].innerHTML, /Source 08/);
  assert.equal(app.elements['#source-status'].focused, true);
});
