import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import vm from 'node:vm';

const dist = resolve(dirname(fileURLToPath(import.meta.url)), '../dist');
const script = readFileSync(resolve(dist, 'app.js'), 'utf8');
const discoveryScript = readFileSync(resolve(dist, 'discovery.js'), 'utf8');
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
    '#domain', '#tradition', '#review', '#verification', '#reset-filters', '#pagination',
    '#comparison', '#comparison-status', '#clear-comparison',
    '#discover', '#discovery-choices', '#discovery-stage', '#discovery-status'];
  const elements = Object.fromEntries(ids.map(id => [id, new FakeElement()]));
  const selectedSummary = new FakeElement();
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
  const availableRecords = options.discovery ? [...records, ...curatedRecords] : records;
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
  vm.runInNewContext(script, context, { filename: 'public-site/dist/app.js' });
  await new Promise(resolve => setImmediate(resolve));
  return { elements, selectedSummary, downloaded, links, FakeElement, window };
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
