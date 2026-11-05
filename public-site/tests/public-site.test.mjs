import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import vm from 'node:vm';

const dist = resolve(dirname(fileURLToPath(import.meta.url)), '../dist');
const script = readFileSync(resolve(dist, 'app.js'), 'utf8');
const discoveryScript = readFileSync(resolve(dist, 'discovery.js'), 'utf8');
const atlasScript = readFileSync(resolve(dist, 'atlas.js'), 'utf8');
const curated = JSON.parse(readFileSync(resolve(dist, 'discovery-journeys.json'), 'utf8'));
const curatedIds = [...new Set([
  ...curated.journeys.flatMap(path => path.steps.map(step => step.record_id)),
  ...curated.surprise.record_ids,
])];
const curatedRecords = curatedIds.map(id => ({
  id, name: 'Catalog record ' + id, kind: 'Model or framework',
  domain: 'Research', tradition: 'Various', review_state: 'provisional',
  summary: 'A provisional catalog summary for ' + id + '.',
  claim_scope: { target: 'A narrower research question.' },
  boundary_note: 'This explanation does not establish claim verification.',
  open_questions: ['What evidence would discriminate this interpretation?'],
  proponents: [],
  citations: [{
    title: 'Research source', authors: 'Researcher', year: 2024,
    url: 'https://example.org/research', authority: 'primary-original',
    verification: 'doi-resolved',
  }],
}));
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

async function boot(locationHref = 'https://example.org/Noemorph/', options = {}) {
  class FakeElement {
    constructor() {
      this.value = '';
      this.innerHTML = '';
      this.textContent = '';
      this.dataset = {};
      this.listeners = {};
      this.children = [];
      this.attributes = {};
      this.disabled = false;
    }
    addEventListener(type, callback) { this.listeners[type] = callback; }
    append(child) { this.children.push(child); }
    click() { this.clicked = true; }
    remove() {}
    setAttribute(name, value) { this.attributes[name] = String(value); }
    getAttribute(name) { return this.attributes[name] ?? null; }
    getBoundingClientRect() { return { width: 1000, height: 600 }; }
    setPointerCapture() {}
    releasePointerCapture() {}
    closest() { return this; }
    focus() { this.focused = true; }
    scrollIntoView() { this.scrolled = true; }
    querySelector(selector) {
      if (selector === 'details[open] summary' && this.innerHTML.includes(' open>')) {
        return selectedSummary;
      }
      if (selector === '#atlas-viewport-transform') return atlasTransform;
      return null;
    }
  }
  const ids = ['#records', '#results-status', '#search', '#kind',
    '#domain', '#tradition', '#review', '#verification', '#reset-filters', '#pagination',
    '#comparison', '#comparison-status', '#clear-comparison',
    '#discover', '#discovery-choices', '#discovery-stage', '#discovery-status',
    '#atlas-svg', '#atlas-node-list', '#atlas-status', '#atlas-kind-filter',
    '#atlas-search', '#atlas-record-detail', '#atlas-back', '#atlas-home',
    '#atlas-previous', '#atlas-next', '#atlas-page-label',
    '#atlas-zoom-in', '#atlas-zoom-out', '#atlas-zoom-reset',
    '#atlas-record-total', '#hero-search-form', '#hero-record-count',
    '#catalog', '#comparison-tools'];
  const elements = Object.fromEntries(ids.map(id => [id, new FakeElement()]));
  const selectedSummary = new FakeElement();
  const atlasTransform = new FakeElement();
  const downloaded = [];
  const links = [];
  class FakeURL extends URL {}
  FakeURL.createObjectURL = blob => { downloaded.push(blob); return 'blob:test'; };
  FakeURL.revokeObjectURL = () => {};

  const listeners = {};
  const window = {
    location: { href: locationHref },
    history: {
      replaceState: (_state, _title, url) => { window.location.href = url; },
      pushState: (_state, _title, url) => { window.location.href = url; },
    },
    requestAnimationFrame: fn => fn(),
    setTimeout: fn => fn(),
    addEventListener: (name, fn) => { listeners[name] = fn; },
    listeners,
  };
  const document = {
    querySelector: selector => elements[selector] || null,
    createElement: () => new FakeElement(),
    body: { append: link => links.push(link) },
  };
  const atlasExtra = options.atlasMany
    ? Array.from({ length: 34 }, (_, index) => ({
      ...records[0],
      id: 'atlas-extra-' + index,
      name: 'Atlas entry ' + index,
      domain: 'Synthetic domain ' + index,
    }))
    : [];
  const availableRecords = [...records, ...(options.discovery ? curatedRecords : []), ...atlasExtra];
  const context = {
    document, window, URL: FakeURL, URLSearchParams, Blob, Element: FakeElement,
    fetch: path => {
      if (path === 'catalog.json' && options.catalogFailure) {
        return Promise.resolve({ ok: false });
      }
      if (path === 'discovery-journeys.json') {
        return Promise.resolve(options.discoveryFailure
          ? { ok: false }
          : { ok: true, json: () => Promise.resolve(curated) });
      }
      return Promise.resolve({
        ok: true, json: () => Promise.resolve({ records: availableRecords }),
      });
    },
  };
  vm.runInNewContext(discoveryScript, context, { filename: 'public-site/dist/discovery.js' });
  vm.runInNewContext(atlasScript, context, { filename: 'public-site/dist/atlas.js' });
  vm.runInNewContext(script, context, { filename: 'public-site/dist/app.js' });
  await new Promise(resolve => setImmediate(resolve));
  return { elements, selectedSummary, atlasTransform, downloaded, links, FakeElement, window };
}

test('public HTML exposes every filter and labeled results', () => {
  for (const id of ['search', 'kind', 'domain', 'tradition', 'review',
    'verification', 'reset-filters', 'records', 'results-status',
    'comparison', 'comparison-status', 'clear-comparison']) {
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


test('valid comparison permalinks render both independent records and preserve citation caveats', async () => {
  const app = await boot('https://example.org/Noemorph/?compare=record-one%2Crecord-two#catalog');
  const html = app.elements['#comparison'].innerHTML;
  assert.equal(app.elements['#comparison'].hidden, false);
  assert.equal(app.elements['#comparison'].focused, true);
  assert.match(html, /Global Neuronal Workspace/);
  assert.match(html, /Panpsychism/);
  assert.match(html, /Citation status: human-verified/);
  assert.match(html, /Citation status: doi-resolved/);
  assert.match(html, /not evidence of convergence/);
  assert.match(html, /Open shareable comparison permalink/);
  assert.match(app.elements['#comparison-status'].textContent, /2 of 2 selected/);
});

test('comparison selections are explicit, reversible, and reflected in the address', async () => {
  const app = await boot();
  const select = id => {
    const target = new app.FakeElement();
    target.dataset.compare = id;
    app.elements['#records'].listeners.click({ target });
  };
  select('record-one');
  assert.match(app.elements['#comparison-status'].textContent, /1 of 2 selected/);
  assert.equal(app.elements['#comparison'].hidden, true);
  select('record-two');
  assert.equal(app.elements['#comparison'].hidden, false);
  assert.equal(new URL(app.window.location.href).searchParams.get('compare'), 'record-one,record-two');
  assert.match(app.elements['#records'].innerHTML, /aria-pressed="true"/);
  app.elements['#clear-comparison'].listeners.click();
  assert.equal(app.elements['#comparison'].hidden, true);
  assert.equal(new URL(app.window.location.href).searchParams.has('compare'), false);
  assert.equal(app.elements['#clear-comparison'].hidden, true);
});

test('invalid, repeated or unknown comparison IDs never render a misleading pair', async () => {
  for (const query of [
    '?compare=record-one%2Crecord-one',
    '?compare=record-one%2Cmissing',
    '?compare=record-one%2Crecord-two%2Cthird',
    '?compare=%3Cscript%3E%2Crecord-two',
    '?compare=record-one%2Crecord-two&compare=record-one%2Crecord-two',
  ]) {
    const app = await boot('https://example.org/Noemorph/' + query);
    assert.equal(app.elements['#comparison'].hidden, true, query);
    assert.equal(app.elements['#comparison'].innerHTML, '', query);
  }
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


test('discovery cards lead with questions while leaving the full catalog available', async () => {
  const app = await boot('https://example.org/Noemorph/', { discovery: true });
  const panel = app.elements['#discovery-choices'].innerHTML;
  for (const label of [
    'What makes us conscious?', 'Could AI be conscious?',
    'What is awareness?', 'What makes a self?', 'Surprise me.',
  ]) {
    assert.ok(panel.includes(label), label);
  }
  assert.equal(app.elements['#discovery-stage'].hidden, true);
  assert.match(app.elements['#discovery-status'].textContent, /Choose a question/);
  assert.match(app.elements['#results-status'].textContent, /records/);
  assert.match(app.elements['#records'].innerHTML, /data-record-id="breadth-neuro-021-insect-subjective-experience"/);
  assert.match(html, /id="discover"/);
  assert.match(html, /src="discovery.js"/);
});

test('a question reveals three progressive, source-bounded steps with a full-record exit', async () => {
  const app = await boot('https://example.org/Noemorph/', { discovery: true });
  const activate = (where, dataset) => {
    const button = new app.FakeElement();
    Object.assign(button.dataset, dataset);
    app.elements[where].listeners.click({ target: button });
  };
  activate('#discovery-choices', { discoveryJourney: 'experience' });
  let stage = app.elements['#discovery-stage'];
  assert.equal(stage.hidden, false);
  assert.equal(stage.focused, true);
  assert.match(stage.innerHTML, /What are we trying to explain?/);
  assert.match(stage.innerHTML, /Phenomenological construct|Model or framework/);
  assert.match(stage.innerHTML, /Unfold research notes/);
  assert.match(stage.innerHTML, /Citation resolution does not establish claim support/);
  assert.match(stage.innerHTML, /Explore the full record/);
  assert.match(new URL(app.window.location.href).searchParams.get('journey'), /experience/);
  assert.equal(new URL(app.window.location.href).searchParams.get('step'), '1');

  activate('#discovery-stage', { discoveryAction: 'next' });
  assert.match(stage.innerHTML, /Could access be the key?/);
  assert.match(stage.innerHTML, /aria-valuenow="2"/);
  assert.equal(new URL(app.window.location.href).searchParams.get('step'), '2');

  activate('#discovery-stage', { discoveryAction: 'next' });
  assert.match(stage.innerHTML, /What if structure matters?/);
  assert.match(stage.innerHTML, /aria-valuenow="3"/);
  assert.match(stage.innerHTML, /Explore another question/);
  activate('#discovery-stage', { discoveryAction: 'previous' });
  assert.match(stage.innerHTML, /Could access be the key?/);
  activate('#discovery-stage', { discoveryAction: 'reset' });
  assert.equal(stage.hidden, true);
  assert.equal(new URL(app.window.location.href).searchParams.has('journey'), false);
});

test('a shared discovery URL reopens a precise step and respects browser navigation', async () => {
  const app = await boot(
    'https://example.org/Noemorph/?journey=awareness&step=3#discover',
    { discovery: true },
  );
  const stage = app.elements['#discovery-stage'];
  assert.equal(stage.hidden, false);
  assert.equal(stage.focused, true);
  assert.match(stage.innerHTML, /What if someone cannot respond?/);
  assert.match(stage.innerHTML, /seed-192-cognitive-motor-dissociation/);
  const moved = new URL('https://example.org/Noemorph/?journey=awareness&step=1#discover');
  app.window.location.href = moved.href;
  app.window.listeners.popstate();
  assert.match(stage.innerHTML, /Is attention the same as awareness?/);
  assert.match(stage.innerHTML, /aria-valuenow="1"/);
});

test('Surprise me draws from real curated entries and does not repeat immediately', async () => {
  const app = await boot('https://example.org/Noemorph/', { discovery: true });
  const button = new app.FakeElement();
  button.dataset.discoveryAction = 'surprise';
  app.elements['#discovery-choices'].listeners.click({ target: button });
  const first = new URL(app.window.location.href).searchParams.get('surprise');
  assert.ok(curated.surprise.record_ids.includes(first));
  assert.equal(app.elements['#discovery-stage'].hidden, false);
  assert.match(app.elements['#discovery-stage'].innerHTML, /AN UNEXPECTED ENTRY/);
  app.elements['#discovery-stage'].listeners.click({ target: button });
  const next = new URL(app.window.location.href).searchParams.get('surprise');
  assert.ok(curated.surprise.record_ids.includes(next));
  assert.notEqual(next, first);
  const reopened = await boot(
    'https://example.org/Noemorph/?surprise=' + encodeURIComponent(next) + '#discover',
    { discovery: true },
  );
  assert.equal(reopened.elements['#discovery-stage'].hidden, false);
  assert.match(reopened.elements['#discovery-stage'].innerHTML, new RegExp(next));
});

test('malformed and conflicting discovery links never misrepresent a research journey', async () => {
  for (const query of [
    '?journey=experience&step=99',
    '?journey=not-a-journey&step=1',
    '?surprise=not-a-record',
    '?journey=experience&step=1&journey=machines',
    '?journey=experience&step=%3Cscript%3E',
    '?record=record-one&journey=experience&step=2',
    '?compare=record-one%2Crecord-two&journey=experience&step=2',
  ]) {
    const app = await boot('https://example.org/Noemorph/' + query, { discovery: true });
    assert.equal(app.elements['#discovery-stage'].hidden, true, query);
    assert.match(app.elements['#discovery-choices'].innerHTML, /What makes us conscious?/);
  }
});

test('broken discovery data fails independently without breaking catalog search', async () => {
  const app = await boot('https://example.org/Noemorph/', {
    discovery: true, discoveryFailure: true,
  });
  assert.equal(app.elements['#discovery-stage'].hidden, true);
  assert.match(app.elements['#discovery-status'].textContent, /full catalog remains accessible/);
  assert.match(app.elements['#records'].innerHTML, /data-record-id="breadth-neuro-021-insect-subjective-experience"/);
  assert.match(app.elements['#results-status'].textContent, /records/);
});


function atlasTarget(app, type, value) {
  const target = new app.FakeElement();
  target.dataset.atlasType = type;
  target.dataset.atlasValue = value;
  return target;
}

test('visual atlas groups the same catalog records by type and domain, without theory edges', async () => {
  const app = await boot();
  const svg = app.elements['#atlas-svg'].innerHTML;
  const text = app.elements['#atlas-status'].textContent;
  assert.match(text, /2 types/);
  assert.equal(app.elements['#atlas-record-total'].textContent, '2');
  assert.match(text, /no theory-to-theory links/i);
  assert.match(svg, /atlas-membership-spoke/);
  assert.doesNotMatch(svg, /data-edge-type="theory-relationship"/);
  assert.match(app.elements['#atlas-node-list'].innerHTML, /Scientific theory/);
  assert.match(app.elements['#atlas-node-list'].innerHTML, /Philosophical position/);
  assert.match(html, /id="atlas"/);
  assert.match(html, /src="atlas.js"/);
  assert.match(html, /href="#atlas"/);
});

test('atlas drills from kind to domain to record using both the map and accessible list', async () => {
  const app = await boot();
  app.elements['#atlas-node-list'].listeners.click({
    target: atlasTarget(app, 'kind', 'Scientific theory'),
  });
  assert.match(app.elements['#atlas-status'].textContent, /1 domains/);
  assert.match(app.elements['#atlas-node-list'].innerHTML, /Neuroscience/);

  app.elements['#atlas-svg'].listeners.keydown({
    target: atlasTarget(app, 'domain', 'Neuroscience'),
    key: 'Enter', preventDefault() {},
  });
  assert.match(app.elements['#atlas-status'].textContent, /1 records/);
  assert.match(app.elements['#atlas-node-list'].innerHTML, /Global Neuronal Workspace/);
  app.elements['#atlas-node-list'].listeners.click({
    target: atlasTarget(app, 'record', 'record-one'),
  });
  assert.match(app.elements['#atlas-record-detail'].innerHTML, /Original model/);
  assert.match(app.elements['#atlas-record-detail'].innerHTML, /human-verified/);
  assert.match(app.elements['#atlas-record-detail'].innerHTML, /do not verify claim-level support/);
  assert.match(app.elements['#atlas-record-detail'].innerHTML, /Read the full cited record/);
  assert.equal(new URL(app.window.location.href).searchParams.get('atlasRecord'), 'record-one');
  assert.equal(app.elements['#atlas-status'].focused, true);

  app.elements['#atlas-back'].listeners.click();
  assert.match(app.elements['#atlas-status'].textContent, /1 domains/);
  app.elements['#atlas-home'].listeners.click();
  assert.match(app.elements['#atlas-status'].textContent, /2 types/);
  assert.equal(new URL(app.window.location.href).searchParams.has('atlasKind'), false);
});

test('atlas paging prevents unreadable maps for highly fragmented domains', async () => {
  const app = await boot('https://example.org/Noemorph/', { atlasMany: true });
  app.elements['#atlas-kind-filter'].value = 'Scientific theory';
  app.elements['#atlas-kind-filter'].listeners.change();
  assert.match(app.elements['#atlas-status'].textContent, /35 domains/);
  assert.equal(app.elements['#atlas-page-label'].textContent, 'Page 1 of 3');
  assert.equal(app.elements['#atlas-previous'].disabled, true);
  app.elements['#atlas-next'].listeners.click();
  assert.equal(app.elements['#atlas-page-label'].textContent, 'Page 2 of 3');
  assert.equal(app.elements['#atlas-previous'].disabled, false);
  assert.match(app.elements['#atlas-svg'].innerHTML, /atlas-node-domain/);
});

test('atlas global record search, zoom and pointer pan stay independent of catalog search', async () => {
  const app = await boot();
  const search = app.elements['#atlas-search'];
  search.value = 'panpsychism';
  search.listeners.input();
  assert.match(app.elements['#atlas-status'].textContent, /1 matching records/);
  assert.match(app.elements['#atlas-node-list'].innerHTML, /Panpsychism/);
  app.elements['#atlas-node-list'].listeners.click({
    target: atlasTarget(app, 'record', 'record-two'),
  });
  assert.equal(new URL(app.window.location.href).searchParams.get('atlasKind'), 'Philosophical position');
  assert.equal(new URL(app.window.location.href).searchParams.get('atlasRecord'), 'record-two');
  assert.match(app.elements['#atlas-record-detail'].innerHTML, /Citation locators/);

  app.elements['#atlas-zoom-in'].listeners.click();
  assert.match(app.elements['#atlas-zoom-reset'].textContent, /120%/);
  assert.match(app.atlasTransform.attributes.transform, /scale\(1.2\)/);
  const svg = app.elements['#atlas-svg'];
  svg.listeners.pointerdown({
    button: 0, pointerId: 2, clientX: 100, clientY: 100,
  });
  svg.listeners.pointermove({
    pointerId: 2, clientX: 120, clientY: 110,
  });
  svg.listeners.pointerup({ pointerId: 2 });
  assert.match(app.atlasTransform.attributes.transform, /translate\(20 10\)/);
  app.elements['#atlas-zoom-reset'].listeners.click();
  assert.match(app.elements['#atlas-zoom-reset'].textContent, /100%/);
  assert.match(app.elements['#results-status'].textContent, /2 records/);
});

test('atlas deep links restore a valid record and ignore malformed or conflicting claims', async () => {
  const url = 'https://example.org/Noemorph/?atlasKind=Scientific+theory' +
    '&atlasDomain=Neuroscience&atlasRecord=record-one#atlas';
  const app = await boot(url);
  assert.match(app.elements['#atlas-record-detail'].innerHTML, /Global Neuronal Workspace/);
  assert.match(app.elements['#atlas-status'].textContent, /Neuroscience/);
  assert.equal(app.elements['#atlas-status'].focused, true);
  for (const query of [
    '?atlasKind=not-a-type',
    '?atlasKind=Scientific+theory&atlasDomain=Philosophy',
    '?atlasKind=Scientific+theory&atlasDomain=Neuroscience&atlasRecord=record-two',
    '?atlasKind=Scientific+theory&atlasKind=Philosophical+position',
    '?atlasRecord=%3Cscript%3E',
    '?record=record-two&atlasKind=Scientific+theory',
    '?compare=record-one%2Crecord-two&atlasKind=Scientific+theory',
  ]) {
    const invalid = await boot('https://example.org/Noemorph/' + query);
    assert.match(invalid.elements['#atlas-status'].textContent, /2 types/, query);
    assert.doesNotMatch(invalid.elements['#atlas-record-detail'].innerHTML, /Original model/, query);
  }
});

test('missing atlas is optional, and a separate discovery journey still functions', async () => {
  const app = await boot('https://example.org/Noemorph/?journey=awareness&step=1#discover',
    { discovery: true });
  assert.match(app.elements['#discovery-stage'].innerHTML, /Is attention the same as awareness?/);
  assert.match(app.elements['#atlas-status'].textContent, /types/);
  assert.match(app.elements['#results-status'].textContent, /records/);
});


test('subtractive homepage puts real catalog search before optional experiences', async () => {
  const index = html;
  const start = index.indexOf('id="top"');
  const catalog = index.indexOf('id="catalog"');
  const secondary = index.indexOf('class="secondary-tools');
  assert.ok(start >= 0 && start < catalog && catalog < secondary);
  assert.match(index, /id="hero-search-form"/);
  assert.match(index, /id="search"/);
  assert.match(index, /id="discovery-disclosure"/);
  assert.match(index, /id="atlas-disclosure"/);
  assert.doesNotMatch(index, /class="hero-art"/);
  assert.doesNotMatch(index, /class="principles"/);
  const app = await boot();
  assert.equal(app.elements['#hero-record-count'].textContent, '2');
  assert.equal(app.elements['#comparison-tools'].hidden, true);
  assert.match(app.elements['#records'].innerHTML, /record-summary-text/);
  assert.match(app.elements['#records'].innerHTML, /Explore research notes and sources/);
});

test('prominent hero search updates the real catalog and jumps to its results on submit', async () => {
  const app = await boot();
  const { elements } = app;
  elements['#search'].value = 'Panpsychism';
  elements['#search'].listeners.input();
  assert.match(elements['#results-status'].textContent, /^1 record/);
  assert.match(elements['#records'].innerHTML, /Panpsychism/);
  let prevented = false;
  elements['#hero-search-form'].listeners.submit({
    preventDefault() { prevented = true; },
  });
  assert.equal(prevented, true);
  assert.equal(elements['#catalog'].scrolled, true);
  assert.equal(elements['#results-status'].focused, true);
});
