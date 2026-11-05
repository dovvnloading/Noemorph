(() => {
  const recordsEl = document.querySelector('#records');
  const status = document.querySelector('#results-status');
  const search = document.querySelector('#search');
  const kind = document.querySelector('#kind');
  const domain = document.querySelector('#domain');
  const tradition = document.querySelector('#tradition');
  const review = document.querySelector('#review');
  const verification = document.querySelector('#verification');
  const reset = document.querySelector('#reset-filters');
  const pagination = document.querySelector('#pagination');
  const comparison = document.querySelector('#comparison');
  const comparisonStatus = document.querySelector('#comparison-status');
  const clearComparison = document.querySelector('#clear-comparison');
  const pageSize = 12;
  let records = [], page = 1;
  let requestedRecordId = new URL(window.location.href).searchParams.get('record');
  function parseComparisonIds(search) {
    const values = new URLSearchParams(search).getAll('compare');
    if (values.length !== 1) return [];
    const ids = values[0].split(',');
    if (ids.length !== 2 || ids[0] === ids[1]) return [];
    if (ids.some(id => !/^[A-Za-z0-9_-]{1,160}$/.test(id))) return [];
    return ids;
  }
  let comparisonIds = parseComparisonIds(new URL(window.location.href).search);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const flatten = value => Array.isArray(value) ? value.flatMap(flatten) : value && typeof value === 'object' ? Object.values(value).flatMap(flatten) : value == null ? [] : [String(value)];
  const list = value => Array.isArray(value) ? value : value == null ? [] : [value];
  const safeUrl = value => { try { const u = new URL(value); return ['https:', 'http:'].includes(u.protocol) ? u.href : ''; } catch { return ''; } };
  const recordHref = id => {
    const url = new URL(window.location.href);
    url.search = '';
    url.searchParams.set('record', id);
    url.hash = 'catalog';
    return url.href;
  };
  function clearRecordLink() {
    requestedRecordId = null;
    const url = new URL(window.location.href);
    if (!url.searchParams.has('record')) return;
    url.searchParams.delete('record');
    window.history.replaceState(null, '', url.href);
  }
  function exportCitations(record) {
    // CSL-JSON keeps incomplete author and date metadata literal rather than guessing.
    const items = (record.citations || []).map((citation, index) => {
      const year = Number(citation.year);
      return {
        id: citation.doi || `${record.id}-${index + 1}`,
        type: 'document',
        title: citation.title,
        ...(citation.authors ? { author: [{ literal: citation.authors }] } : {}),
        ...(citation.doi ? { DOI: citation.doi } : {}),
        ...(safeUrl(citation.url) ? { URL: safeUrl(citation.url) } : {}),
        ...(citation.venue ? { 'container-title': citation.venue } : {}),
        ...(Number.isInteger(year) && year >= 1000 && year <= 2100 ? { issued: { 'date-parts': [[year]] } } : {}),
        note: `Noemorph citation authority: ${citation.authority || 'unspecified'}; verification: ${citation.verification || 'pending-metadata-review'}. A citation locator is not proof of claim support.`,
      };
    });
    const url = URL.createObjectURL(new Blob([JSON.stringify(items, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = `noemorph-${String(record.id).replace(/[^a-z0-9_-]+/gi, '-')}-citations.csl.json`;
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  }
  function fillSelect(select, values) {
    [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b)).forEach(label => {
      const option = document.createElement('option');
      option.value = label;
      option.textContent = label;
      select.append(option);
    });
  }
  function detail(label, value) {
    if (value == null || value === '' || (Array.isArray(value) && !value.length)) return '';
    let content;
    if (Array.isArray(value)) content = `<ul>${value.map(item => `<li>${esc(flatten(item).join('; '))}</li>`).join('')}</ul>`;
    else if (typeof value === 'object') content = `<dl>${Object.entries(value).map(([key, item]) => `<dt>${esc(key)}</dt><dd>${esc(flatten(item).join('; '))}</dd>`).join('')}</dl>`;
    else content = `<p>${esc(value)}</p>`;
    return `<h4>${esc(label)}</h4>${content}`;
  }
  function claimReviewHtml(r) {
    if (!Array.isArray(r.claim_reviews) || !r.claim_reviews.length) return '';
    const items = r.claim_reviews.map(claim => {
      const leads = (claim.citations || []).map(lead => {
        const cited = (r.citations || []).find(citation => citation.url === lead.citation_url);
        const link = safeUrl(lead.citation_url);
        const label = esc(cited?.title || 'Retained source');
        const citationState = esc(cited?.verification || 'pending metadata review');
        return `<li>${link ? `<a href="${esc(link)}" target="_blank" rel="noopener noreferrer">${label} ↗</a>` : label}<small>Source URL only · claim match unreviewed · citation metadata: ${citationState}</small></li>`;
      }).join('');
      return `<li><strong>${esc(claim.kind === 'scope' ? 'Theory statement' : 'Boundary or limitation')}</strong><p>${esc(claim.text)}</p><ul>${leads}</ul></li>`;
    }).join('');
    return `<section class="claim-review-leads"><h4>Claim-level source review leads — unverified</h4><p>Retained bibliography links proposed for passage review. These links do not verify support, refutation, or theoretical relationships.</p><ol>${items}</ol></section>`;
  }

  function comparisonHref() {
    if (comparisonIds.length !== 2) return '';
    const url = new URL('https://dovvnloading.github.io/Noemorph/');
    url.searchParams.set('compare', comparisonIds.join(','));
    url.hash = 'catalog';
    return url.href;
  }
  function syncComparisonUrl() {
    const url = new URL(window.location.href);
    url.searchParams.delete('record');
    if (comparisonIds.length === 2) url.searchParams.set('compare', comparisonIds.join(','));
    else url.searchParams.delete('compare');
    window.history.replaceState(null, '', url.href);
  }
  function compareCard(r) {
    const citations = (r.citations || []).map(c => {
      const url = safeUrl(c.url);
      const title = esc(c.title || 'Retained source');
      return `<li>${url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${title}</a>` : title}<small>${esc(c.authors || 'Author pending')} · Role: ${esc(c.authority || 'unknown')} · Citation status: ${esc(c.verification || 'pending-metadata-review')}</small></li>`;
    }).join('');
    return `<article class="comparison-card"><h3>${esc(r.name)}</h3><p class="comparison-classification">${esc(r.kind)} · ${esc(r.domain)} · ${esc(r.tradition)}</p>${detail('Current catalog status', r.status)}${detail('Record review state', r.review_state || 'unspecified')}${detail('Overview', r.summary)}${detail('Claim scope', r.claim_scope || r.scope)}${detail('Boundaries', r.boundary_note || r.status_note)}${detail('Evidence profile', r.evidence_profile)}${detail('Open questions', r.open_questions)}<h4>Retained citations</h4><ul class="comparison-citations">${citations}</ul></article>`;
  }
  function drawComparison() {
    const selected = comparisonIds.map(id => records.find(record => record.id === id));
    comparisonStatus.textContent = comparisonIds.length
      ? `${comparisonIds.length} of 2 selected: ${selected.map(record => record?.name || 'Unavailable record').join(' / ')}${comparisonIds.length === 2 ? '. Clear a selection to choose another record.' : '. Select one more record.'}`
      : 'Open two records and choose Compare to inspect them side by side.';
    clearComparison.hidden = comparisonIds.length === 0;
    if (selected.length !== 2 || selected.some(record => !record)) {
      comparison.hidden = true;
      comparison.innerHTML = '';
      return;
    }
    comparison.hidden = false;
    comparison.innerHTML = `<h2 id="comparison-title">Read-only record comparison</h2><p>These are independent catalog entries. Shared terminology or citations are not evidence of convergence, contrast, equivalence, influence, or causation. Citation verification is not claim verification.</p><p><a href="${esc(comparisonHref())}" class="comparison-link">Open shareable comparison permalink</a></p><div class="comparison-columns">${selected.map(compareCard).join('')}</div><p class="comparison-disclaimer">All records remain source-bounded and provisional. Unreviewed claim-to-source leads and private local evidence reviews are not promoted by this view.</p>`;
  }
  function selectComparison(id) {
    if (!records.some(record => record.id === id)) return;
    if (comparisonIds.includes(id)) comparisonIds = comparisonIds.filter(item => item !== id);
    else if (comparisonIds.length < 2) comparisonIds = [...comparisonIds, id];
    else return;
    syncComparisonUrl();
    draw();
    if (comparisonIds.length === 2) {
      window.requestAnimationFrame(() => {
        comparison.scrollIntoView({ block: 'start' });
        comparison.focus({ preventScroll: true });
      });
    }
  }
  function recordHtml(r, expanded = false) {
    const citations = (r.citations || []).map(c => { const url = safeUrl(c.url); const title = esc(c.title || 'Source'); return `<li>${url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${title} ↗</a>` : title}<div class="citation-meta">${esc([c.authors, c.year, c.venue].filter(Boolean).join(' · '))}${c.verification ? ` · ${esc(c.verification)}` : ''}${c.authority ? ` · ${esc(c.authority)}` : ''}</div></li>`; }).join('');
    return `<details class="record" data-record-id="${esc(r.id)}"${expanded ? ' open' : ''}><summary><span class="record-name">${esc(r.name)}</span><span class="record-kind">${esc(r.kind)}</span><span class="record-toggle" aria-hidden="true">+</span></summary><div class="record-content"><div class="record-actions"><a href="${esc(recordHref(r.id))}">Permanent link</a><button type="button" data-compare="${esc(r.id)}" aria-pressed="${comparisonIds.includes(r.id)}" ${comparisonIds.length === 2 && !comparisonIds.includes(r.id) ? 'disabled' : ''}>${comparisonIds.includes(r.id) ? 'Remove from comparison' : 'Compare this record'}</button><button type="button" data-export="${esc(r.id)}">Export citations (CSL-JSON)</button></div>${detail('Overview', r.summary)}${detail('Scope', r.claim_scope || r.scope)}${detail('Boundaries', r.boundary_note || r.status_note)}${detail('Evidence profile', r.evidence_profile)}${detail('Open questions', r.open_questions)}${detail('People associated', r.proponents)}${detail('Review state', r.review_state)}${claimReviewHtml(r)}${citations ? `<h4>Retained citations</h4><ul>${citations}</ul>` : ''}</div></details>`;
  }
  function draw() {
    const opened = new Set(Array.from(recordsEl.querySelectorAll?.('details[open]') ?? [], element => element.dataset.recordId));
    drawComparison();
    const terms = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    const filtered = records.filter(r => {
      if (kind.value && r.kind !== kind.value) return false;
      if (domain.value && r.domain !== domain.value) return false;
      if (tradition.value && r.tradition !== tradition.value) return false;
      if (review.value && r.review_state !== review.value) return false;
      if (verification.value && !(r.citations || []).some(c => c.verification === verification.value)) return false;
      const haystack = [r.name, r.summary, r.domain, r.tradition, r.kind, ...list(r.aliases), ...list(r.proponents), ...list(r.keywords), r.claim_scope, r.boundary_note, r.evidence_profile, r.open_questions]
        .flatMap(flatten).join(' ').toLocaleLowerCase();
      return terms.every(term => haystack.includes(term));
    });
    if (requestedRecordId) {
      const index = filtered.findIndex(record => record.id === requestedRecordId);
      if (index !== -1) page = Math.floor(index / pageSize) + 1;
    }
    const pages = Math.max(1, Math.ceil(filtered.length / pageSize)); page = Math.min(page, pages);
    const start = (page - 1) * pageSize;
    status.textContent = `${filtered.length} ${filtered.length === 1 ? 'record' : 'records'}${filtered.length ? ` · showing ${start + 1}–${Math.min(start + pageSize, filtered.length)}` : ''}`;
    recordsEl.innerHTML = filtered.length ? filtered.slice(start, start + pageSize).map(r => recordHtml(r, r.id === requestedRecordId || opened.has(r.id))).join('') : '<p class="empty">No records match this search. Try a broader term or another record type.</p>';
    pagination.innerHTML = pages > 1 ? `<button type="button" id="previous" ${page === 1 ? 'disabled' : ''}>← Previous</button><span>Page ${page} of ${pages}</span><button type="button" id="next" ${page === pages ? 'disabled' : ''}>Next →</button>` : '';
    document.querySelector('#previous')?.addEventListener('click', () => { clearRecordLink(); page--; draw(); status.focus(); });
    document.querySelector('#next')?.addEventListener('click', () => { clearRecordLink(); page++; draw(); status.focus(); });
    if (requestedRecordId) {
      const selected = recordsEl.querySelector('details[open] summary');
      requestedRecordId = null;
      if (selected) window.requestAnimationFrame(() => {
        selected.scrollIntoView({ block: 'center' });
        selected.focus({ preventScroll: true });
      });
    }
  }
  const filters = [search, kind, domain, tradition, review, verification];
  filters.forEach(element => element.addEventListener(element === search ? 'input' : 'change', () => {
    clearRecordLink();
    page = 1;
    draw();
  }));
  reset.addEventListener('click', () => {
    filters.forEach(element => { element.value = ''; });
    clearRecordLink();
    page = 1;
    draw();
    search.focus();
  });
  clearComparison.addEventListener('click', () => {
    comparisonIds = [];
    syncComparisonUrl();
    draw();
    search.focus();
  });
  recordsEl.addEventListener('click', event => {
    const target = event.target instanceof Element ? event.target : null;
    if (!target) return;
    const compareButton = target.closest('button[data-compare]');
    if (compareButton?.dataset.compare && !compareButton.disabled) {
      selectComparison(compareButton.dataset.compare);
      return;
    }
    const exportButton = target.closest('button[data-export]');
    if (!exportButton?.dataset.export) return;
    const record = records.find(item => item.id === exportButton.dataset.export);
    if (record) exportCitations(record);
  });
  fetch('catalog.json').then(response => { if (!response.ok) throw new Error('Could not load catalog'); return response.json(); }).then(data => {
    records = data.records.slice().sort((a,b) => a.name.localeCompare(b.name));
    if (comparisonIds.length && (
      comparisonIds.length !== 2 || comparisonIds.some(id => !records.some(record => record.id === id))
    )) {
      comparisonIds = [];
      syncComparisonUrl();
    }
    const requestedComparison = comparisonIds.length === 2;
    fillSelect(kind, records.map(r => r.kind));
    fillSelect(domain, records.map(r => r.domain));
    fillSelect(tradition, records.map(r => r.tradition));
    fillSelect(review, records.map(r => r.review_state));
    draw();
    if (requestedComparison) window.requestAnimationFrame(() => {
      comparison.scrollIntoView({ block: 'start' });
      comparison.focus({ preventScroll: true });
    });
  }).catch(() => { status.textContent = 'The collection could not be loaded.'; recordsEl.innerHTML = '<p class="empty">Please reload the page, or visit the repository to explore the source data.</p>'; });
})();
