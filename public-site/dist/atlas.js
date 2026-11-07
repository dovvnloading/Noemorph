/* Noemorph public atlas: organizational taxonomy only, no theory-to-theory edges. */
(() => {
  'use strict';

  const PAGE_SIZE = 16;
  const MIN_ZOOM = 0.65;
  const MAX_ZOOM = 3;
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch])
  );
  const order = (a, b) => String(a).localeCompare(String(b));
  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
  const isSafeId = value => typeof value === 'string' && /^[A-Za-z0-9_-]{1,160}$/.test(value);
  function model(records) {
    if (!Array.isArray(records) || !records.length) throw new Error('Atlas needs catalog records');
    const byId = new Map();
    const kindMap = new Map();
    for (const record of records) {
      if (!isSafeId(record.id) || byId.has(record.id) ||
          typeof record.kind !== 'string' || !record.kind.trim() ||
          typeof record.domain !== 'string' || !record.domain.trim() ||
          typeof record.name !== 'string' || !record.name.trim()) {
        throw new Error('Invalid catalog record for the public atlas');
      }
      byId.set(record.id, record);
      if (!kindMap.has(record.kind)) kindMap.set(record.kind, new Map());
      const domainMap = kindMap.get(record.kind);
      if (!domainMap.has(record.domain)) domainMap.set(record.domain, []);
      domainMap.get(record.domain).push(record);
    }
    const kinds = [...kindMap].map(([name, domains]) => ({
      type: 'kind', value: name, label: name,
      count: [...domains.values()].reduce((sum, entries) => sum + entries.length, 0),
      domains: [...domains].map(([domain, entries]) => ({
        type: 'domain', value: domain, label: domain,
        count: entries.length,
        records: entries.slice().sort((a, b) => order(a.name, b.name)),
      })).sort((a, b) => order(a.label, b.label)),
    })).sort((a, b) => b.count - a.count || order(a.label, b.label));
    return { kinds, byId, records: records.slice().sort((a, b) => order(a.name, b.name)) };
  }
  function mount(records) {
    const svg = document.querySelector('#atlas-svg');
    const list = document.querySelector('#atlas-node-list');
    const status = document.querySelector('#atlas-status');
    const disclosure = document.querySelector('#atlas-disclosure');
    const kindSelect = document.querySelector('#atlas-kind-filter');
    const search = document.querySelector('#atlas-search');
    const detail = document.querySelector('#atlas-record-detail');
    const back = document.querySelector('#atlas-back');
    const previous = document.querySelector('#atlas-previous');
    const next = document.querySelector('#atlas-next');
    const paging = document.querySelector('#atlas-page-label');
    const zoomIn = document.querySelector('#atlas-zoom-in');
    const zoomOut = document.querySelector('#atlas-zoom-out');
    const resetZoom = document.querySelector('#atlas-zoom-reset');
    if ([svg, list, status, kindSelect, search, detail, back,
      previous, next, paging, zoomIn, zoomOut, resetZoom].some(value => !value)) return;

    let catalog;
    try { catalog = model(records); }
    catch {
      status.textContent = 'The interactive map is unavailable. The full catalog remains accessible below.';
      return;
    }
    const state = {
      kind: null, domain: null, record: null, query: '', page: 0,
      zoom: 1, panX: 0, panY: 0,
    };
    const kindByName = new Map(catalog.kinds.map(kind => [kind.value, kind]));
    const count = document.querySelector('#atlas-record-total');
    if (count) count.textContent = String(catalog.records.length);

    function recordHref(record) {
      const url = new URL(window.location.href);
      url.search = '';
      url.searchParams.set('record', record.id);
      url.hash = 'catalog';
      return url.href;
    }
    function validRoute() {
      const url = new URL(window.location.href);
      const params = url.searchParams;
      if (['record', 'compare', 'journey', 'surprise'].some(key => params.has(key))) {
        return null;
      }
      const k = params.getAll('atlasKind');
      const d = params.getAll('atlasDomain');
      const r = params.getAll('atlasRecord');
      if (k.length > 1 || d.length > 1 || r.length > 1) return null;
      const kind = k[0] || null;
      const domain = d[0] || null;
      const record = r[0] || null;
      if (!kind && (domain || record)) return null;
      const group = kind ? kindByName.get(kind) : null;
      if (kind && !group) return null;
      if (domain && !group.domains.some(item => item.value === domain)) return null;
      if (record) {
        const entry = catalog.byId.get(record);
        if (!domain || !entry || entry.kind !== kind || entry.domain !== domain) {
          return null;
        }
      }
      return { kind, domain, record };
    }
    function syncUrl() {
      const url = new URL(window.location.href);
      for (const key of ['atlasKind', 'atlasDomain', 'atlasRecord', 'record',
        'compare', 'journey', 'step', 'surprise']) {
        url.searchParams.delete(key);
      }
      if (state.kind) url.searchParams.set('atlasKind', state.kind);
      if (state.domain) url.searchParams.set('atlasDomain', state.domain);
      if (state.record) url.searchParams.set('atlasRecord', state.record);
      url.hash = 'atlas';
      window.history.pushState(null, '', url.href);
    }
    function resetViewport() {
      state.zoom = 1;
      state.panX = 0;
      state.panY = 0;
    }
    function visibleItems() {
      let candidates = [];
      let label = 'Catalog record types';
      if (state.query.trim()) {
        const terms = state.query.toLocaleLowerCase().trim().split(/\s+/);
        candidates = catalog.records.filter(record => {
          const haystack = [record.name, record.summary, record.kind, record.domain,
            ...(record.aliases || [])].join(' ').toLocaleLowerCase();
          return terms.every(term => haystack.includes(term));
        }).map(record => ({
          type: 'record', value: record.id, label: record.name, count: 1,
          kind: record.kind, domain: record.domain,
        }));
        label = 'Search results across the whole catalog';
      } else if (state.kind && state.domain) {
        const domain = kindByName.get(state.kind)?.domains.find(item => item.value === state.domain);
        candidates = (domain?.records || []).map(record => ({
          type: 'record', value: record.id, label: record.name, count: 1,
          kind: record.kind, domain: record.domain,
        }));
        label = state.domain;
      } else if (state.kind) {
        candidates = kindByName.get(state.kind)?.domains || [];
        label = state.kind;
      } else {
        candidates = catalog.kinds;
      }
      const pages = Math.max(1, Math.ceil(candidates.length / PAGE_SIZE));
      state.page = clamp(state.page, 0, pages - 1);
      return {
        items: candidates.slice(state.page * PAGE_SIZE, (state.page + 1) * PAGE_SIZE),
        total: candidates.length, pages, label,
      };
    }
    function svgTransform() {
      return 'translate(' + state.panX + ' ' + state.panY +
        ') translate(500 300) scale(' + state.zoom +
        ') translate(-500 -300)';
    }
    function updateTransform() {
      const layer = svg.querySelector('#atlas-viewport-transform');
      if (layer) layer.setAttribute('transform', svgTransform());
      zoomIn.disabled = state.zoom >= MAX_ZOOM;
      zoomOut.disabled = state.zoom <= MIN_ZOOM;
      resetZoom.textContent = Math.round(state.zoom * 100) + '% · Reset view';
    }
    function mapHtml(visible) {
      const radius = visible.items.length < 5 ? 185 : 235;
      const center = visible.label.length > 29 ? visible.label.slice(0, 28) + '…' : visible.label;
      const points = visible.items.map((item, i) => {
        const angle = -Math.PI / 2 + i * 2 * Math.PI / visible.items.length;
        return { ...item, x: Math.round(500 + Math.cos(angle) * radius),
          y: Math.round(300 + Math.sin(angle) * radius) };
      });
      const lines = points.map(point =>
        '<line x1="500" y1="300" x2="' + point.x + '" y2="' + point.y +
        '" class="atlas-membership-spoke"></line>'
      ).join('');
      const nodes = points.map(point => {
        const size = point.type === 'record' ? 15 : 22 + Math.min(13, Math.sqrt(point.count));
        const nodeLabel = point.label.length > 28
          ? point.label.slice(0, 26) + '…' : point.label;
        const selected = point.type === 'record' && state.record === point.value;
        return '<g class="atlas-visual-node atlas-node-' + point.type +
          (selected ? ' atlas-node-selected' : '') +
          '" role="button" tabindex="0" data-atlas-type="' + esc(point.type) +
          '" data-atlas-value="' + esc(point.value) +
          '" aria-label="' + esc(nodeLabel + (point.type === 'record' ? '' : ' ' + point.count)) + '">' +
          '<circle cx="' + point.x + '" cy="' + point.y +
          '" r="' + size + '"></circle>' +
          '<text x="' + point.x + '" y="' + (point.y + size + 18) +
          '" text-anchor="middle">' + esc(nodeLabel) + '</text>' +
          (point.type === 'record' ? '' :
            '<text class="atlas-node-count" x="' + point.x + '" y="' +
            (point.y + 4) + '" text-anchor="middle">' + point.count + '</text>') +
          '</g>';
      }).join('');
      return '<g id="atlas-viewport-transform" transform="' + svgTransform() + '">' +
        '<circle class="atlas-orbit" cx="500" cy="300" r="' + radius + '"></circle>' +
        lines +
        '<circle class="atlas-center" cx="500" cy="300" r="64"></circle>' +
        '<text class="atlas-center-heading" x="500" y="294" text-anchor="middle">' +
        esc(center) + '</text>' +
        '<text class="atlas-center-sub" x="500" y="318" text-anchor="middle">' +
        (state.query ? 'MATCHING RECORDS' : state.domain ? 'RECORDS' :
          state.kind ? 'DOMAINS' : 'RECORD TYPES') + '</text>' +
        nodes + '</g>';
    }
    function detailHtml() {
      const record = state.record ? catalog.byId.get(state.record) : null;
      if (!record) {
        detail.innerHTML = '<div class="atlas-record-empty"><span>SELECT A RECORD</span>' +
          '<p>Choose a node or a list item to reveal its catalog context and sources.</p></div>';
        return;
      }
      const sourceHtml = (record.citations || []).slice(0, 2).map(citation => {
        let url = '';
        try {
          const candidate = new URL(citation.url);
          if (candidate.protocol === 'https:') url = candidate.href;
        } catch { /* Invalid URLs stay unlinked. */ }
        return '<li>' + (url ? '<a href="' + esc(url) +
          '" target="_blank" rel="noopener noreferrer">' +
          esc(citation.title) + ' ↗</a>' : esc(citation.title)) +
          '<small>' + esc(citation.authority || 'role unknown') +
          ' · ' + esc(citation.verification || 'pending-metadata-review') +
          ' (locator state)</small></li>';
      }).join('');
      detail.innerHTML = '<div class="atlas-record-card">' +
        '<span class="atlas-detail-eyebrow">CURATED RECORD · ' +
        esc(record.review_state || 'not reviewed') + '</span>' +
        '<h3>' + esc(record.name) + '</h3>' +
        '<p class="atlas-kind-label">' + esc(record.kind) +
        ' / ' + esc(record.domain) + '</p>' +
        '<p>' + esc(record.summary) + '</p>' +
        (record.boundary_note ? '<p class="atlas-boundary"><strong>Boundary:</strong> ' +
          esc(record.boundary_note) + '</p>' : '') +
        '<h4>Retained sources</h4><ul>' + sourceHtml + '</ul>' +
        '<a class="atlas-full-record" href="' + esc(recordHref(record)) +
        '">Read the full cited record ↗</a>' +
        '<p class="atlas-evidence-caution">Citation locators and DOI resolution do not verify claim-level support.</p>' +
        '</div>';
    }
    function render() {
      const visible = visibleItems();
      const hasParent = Boolean(state.kind || state.query);
      back.disabled = !hasParent;
      kindSelect.value = state.kind || '';
      search.value = state.query;
      status.textContent = (state.query
        ? 'Search'
        : state.domain ? state.domain : state.kind ? state.kind : 'Research types') +
        ': ' + visible.total + ' ' + (state.query ? 'matching records' :
          state.domain ? 'records' : state.kind ? 'domains' : 'types') +
        '. Organizational classification only; no theory-to-theory links.';
      paging.textContent = 'Page ' + (state.page + 1) + ' of ' + visible.pages;
      previous.disabled = state.page <= 0;
      next.disabled = state.page + 1 >= visible.pages;
      svg.innerHTML = mapHtml(visible);
      list.innerHTML = visible.items.map(item =>
        '<li><button type="button" data-atlas-type="' + esc(item.type) +
        '" data-atlas-value="' + esc(item.value) + '" ' +
        (item.type === 'record' && state.record === item.value ?
          'aria-current="true"' : '') + '>' +
        '<span>' + esc(item.label) + '</span>' +
        '<small>' + (item.type === 'record' ? esc(item.kind) :
          item.count + ' record' + (item.count === 1 ? '' : 's')) +
        '</small></button></li>'
      ).join('') || '<li class="atlas-no-results">No matches. Try another search.</li>';
      detailHtml();
      updateTransform();
    }
    function focusStatus() {
      window.requestAnimationFrame(() => status.focus({ preventScroll: true }));
    }
    function selectNode(type, value) {
      if (type === 'kind') {
        if (!kindByName.has(value)) return;
        state.kind = value;
        state.domain = null;
        state.record = null;
        state.query = '';
      } else if (type === 'domain') {
        if (!state.kind || !kindByName.get(state.kind)?.domains.some(x => x.value === value)) return;
        state.domain = value;
        state.record = null;
        state.query = '';
      } else if (type === 'record') {
        const record = catalog.byId.get(value);
        if (!record) return;
        if (!state.query && (record.kind !== state.kind || record.domain !== state.domain)) {
          return;
        }
        state.record = value;
        if (state.query) {
          state.kind = record.kind;
          state.domain = record.domain;
          state.query = '';
        }
        const domainGroup = kindByName.get(record.kind)?.domains.find(x => x.value === record.domain);
        state.page = Math.max(0, Math.floor(
          (domainGroup?.records.findIndex(item => item.id === value) ?? 0) / PAGE_SIZE
        ));
      } else return;
      if (type !== 'record') state.page = 0;
      resetViewport();
      syncUrl();
      render();
      focusStatus();
    }
    function goBack() {
      if (state.query) {
        state.query = '';
      } else if (state.domain) {
        state.domain = null;
        state.record = null;
      } else if (state.kind) {
        state.kind = null;
        state.record = null;
      } else return;
      state.page = 0;
      resetViewport();
      syncUrl();
      render();
      focusStatus();
    }
    function goOverview() {
      state.kind = null;
      state.domain = null;
      state.record = null;
      state.query = '';
      state.page = 0;
      resetViewport();
      syncUrl();
      render();
      focusStatus();
    }
    function zoomBy(factor) {
      state.zoom = Math.round(clamp(state.zoom * factor, MIN_ZOOM, MAX_ZOOM) * 100) / 100;
      updateTransform();
    }
    function handleNodeClick(event) {
      if (suppressClick) {
        suppressClick = false;
        return;
      }
      const node = event.target instanceof Element
        ? event.target.closest('[data-atlas-type][data-atlas-value]') : null;
      if (!node) return;
      selectNode(node.dataset.atlasType, node.dataset.atlasValue);
    }
    svg.addEventListener('click', handleNodeClick);
    svg.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') {
        const node = event.target instanceof Element
          ? event.target.closest('[data-atlas-type][data-atlas-value]') : null;
        if (node) {
          event.preventDefault();
          selectNode(node.dataset.atlasType, node.dataset.atlasValue);
        }
      } else if (event.key === '+' || event.key === '=') {
        event.preventDefault(); zoomBy(1.2);
      } else if (event.key === '-') {
        event.preventDefault(); zoomBy(1 / 1.2);
      } else if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) {
        event.preventDefault();
        state.panX += event.key === 'ArrowLeft' ? -32 : event.key === 'ArrowRight' ? 32 : 0;
        state.panY += event.key === 'ArrowUp' ? -32 : event.key === 'ArrowDown' ? 32 : 0;
        updateTransform();
      }
    });
    list.addEventListener('click', event => {
      const node = event.target instanceof Element
        ? event.target.closest('[data-atlas-type][data-atlas-value]') : null;
      if (node) selectNode(node.dataset.atlasType, node.dataset.atlasValue);
    });
    let gesture = null;
    let suppressClick = false;
    svg.addEventListener('pointerdown', event => {
      if (event.button !== 0) return;
      gesture = { id: event.pointerId, x: event.clientX, y: event.clientY, moved: false };
      svg.setPointerCapture?.(event.pointerId);
    });
    svg.addEventListener('pointermove', event => {
      if (!gesture || event.pointerId !== gesture.id) return;
      const bounds = svg.getBoundingClientRect();
      const width = bounds.width || 1000;
      const height = bounds.height || 600;
      const dx = event.clientX - gesture.x;
      const dy = event.clientY - gesture.y;
      if (Math.abs(dx) + Math.abs(dy) > 2) gesture.moved = true;
      if (!gesture.moved) return;
      state.panX += dx * 1000 / width;
      state.panY += dy * 600 / height;
      gesture.x = event.clientX;
      gesture.y = event.clientY;
      updateTransform();
    });
    svg.addEventListener('pointerup', event => {
      if (gesture && gesture.id === event.pointerId) {
        suppressClick = gesture.moved;
        gesture = null;
        svg.releasePointerCapture?.(event.pointerId);
      }
    });
    svg.addEventListener('pointercancel', () => { gesture = null; });
    svg.addEventListener('wheel', event => {
      event.preventDefault();
      zoomBy(event.deltaY < 0 ? 1.12 : 1 / 1.12);
    }, { passive: false });
    back.addEventListener('click', goBack);
    document.querySelector('#atlas-home').addEventListener('click', goOverview);
    previous.addEventListener('click', () => {
      state.page -= 1;
      resetViewport();
      render();
      focusStatus();
    });
    next.addEventListener('click', () => {
      state.page += 1;
      resetViewport();
      render();
      focusStatus();
    });
    zoomIn.addEventListener('click', () => zoomBy(1.2));
    zoomOut.addEventListener('click', () => zoomBy(1 / 1.2));
    resetZoom.addEventListener('click', () => { resetViewport(); updateTransform(); });
    kindSelect.innerHTML = '<option value="">All record types</option>' +
      catalog.kinds.map(kind => '<option value="' + esc(kind.value) + '">' +
        esc(kind.label) + ' (' + kind.count + ')</option>').join('');
    kindSelect.addEventListener('change', () => {
      state.kind = kindSelect.value || null;
      state.domain = null;
      state.record = null;
      state.query = '';
      state.page = 0;
      resetViewport();
      syncUrl();
      render();
    });
    search.addEventListener('input', () => {
      state.query = search.value.slice(0, 120);
      state.record = null;
      state.page = 0;
      resetViewport();
      render();
    });
    window.addEventListener('popstate', () => {
      const route = validRoute();
      state.kind = route?.kind || null;
      state.domain = route?.domain || null;
      state.record = route?.record || null;
      state.query = '';
      state.page = 0;
      if (state.record) {
        const group = kindByName.get(state.kind)?.domains.find(x => x.value === state.domain);
        state.page = Math.max(0, Math.floor(
          (group?.records.findIndex(item => item.id === state.record) ?? 0) / PAGE_SIZE
        ));
      }
      resetViewport();
      render();
    });
    const initial = validRoute();
    if (disclosure && new URL(window.location.href).hash === '#atlas') {
      disclosure.open = true;
    }
    window.addEventListener('hashchange', () => {
      if (disclosure && new URL(window.location.href).hash === '#atlas') {
        disclosure.open = true;
      }
    });
    state.kind = initial?.kind || null;
    state.domain = initial?.domain || null;
    state.record = initial?.record || null;
    if (state.record) {
      const group = kindByName.get(state.kind)?.domains.find(x => x.value === state.domain);
      state.page = Math.max(0, Math.floor(
        (group?.records.findIndex(item => item.id === state.record) ?? 0) / PAGE_SIZE
      ));
    }
    render();
    if (initial?.kind) {
      window.requestAnimationFrame(() => status.focus({ preventScroll: true }));
    }
  }

  window.NoemorphAtlas = { mount, model };
})();
