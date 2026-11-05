(() => {
  const recordsEl = document.querySelector('#records');
  const status = document.querySelector('#results-status');
  const search = document.querySelector('#search');
  const kind = document.querySelector('#kind');
  const pagination = document.querySelector('#pagination');
  const pageSize = 12;
  let records = [], page = 1;
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const flatten = value => Array.isArray(value) ? value.flatMap(flatten) : value && typeof value === 'object' ? Object.values(value).flatMap(flatten) : value == null ? [] : [String(value)];
  const list = value => Array.isArray(value) ? value : value == null ? [] : [value];
  const safeUrl = value => { try { const u = new URL(value); return ['https:', 'http:'].includes(u.protocol) ? u.href : ''; } catch { return ''; } };
  function detail(label, value) {
    if (value == null || value === '' || (Array.isArray(value) && !value.length)) return '';
    let content;
    if (Array.isArray(value)) content = `<ul>${value.map(item => `<li>${esc(flatten(item).join('; '))}</li>`).join('')}</ul>`;
    else if (typeof value === 'object') content = `<dl>${Object.entries(value).map(([key, item]) => `<dt>${esc(key)}</dt><dd>${esc(flatten(item).join('; '))}</dd>`).join('')}</dl>`;
    else content = `<p>${esc(value)}</p>`;
    return `<h4>${esc(label)}</h4>${content}`;
  }
  function recordHtml(r) {
    const citations = (r.citations || []).map(c => { const url = safeUrl(c.url); const title = esc(c.title || 'Source'); return `<li>${url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${title} ↗</a>` : title}<div class="citation-meta">${esc([c.authors, c.year, c.venue].filter(Boolean).join(' · '))}${c.verification ? ` · ${esc(c.verification)}` : ''}${c.authority ? ` · ${esc(c.authority)}` : ''}</div></li>`; }).join('');
    return `<details class="record"><summary><span class="record-name">${esc(r.name)}</span><span class="record-kind">${esc(r.kind)}</span><span class="record-toggle" aria-hidden="true">+</span></summary><div class="record-content">${detail('Overview', r.summary)}${detail('Scope', r.claim_scope || r.scope)}${detail('Boundaries', r.boundary_note || r.status_note)}${detail('Evidence profile', r.evidence_profile)}${detail('Open questions', r.open_questions)}${detail('People associated', r.proponents)}${detail('Review state', r.review_state)}${citations ? `<h4>Retained citations</h4><ul>${citations}</ul>` : ''}</div></details>`;
  }
  function draw() {
    const query = search.value.trim().toLocaleLowerCase();
    const filtered = records.filter(r => (!kind.value || r.kind === kind.value) && (!query || [r.name, r.summary, r.domain, r.tradition, r.kind, ...list(r.aliases), ...list(r.proponents), ...list(r.keywords)].flatMap(flatten).join(' ').toLocaleLowerCase().includes(query)));
    const pages = Math.max(1, Math.ceil(filtered.length / pageSize)); page = Math.min(page, pages);
    const start = (page - 1) * pageSize;
    status.textContent = `${filtered.length} ${filtered.length === 1 ? 'record' : 'records'}${filtered.length ? ` · showing ${start + 1}–${Math.min(start + pageSize, filtered.length)}` : ''}`;
    recordsEl.innerHTML = filtered.length ? filtered.slice(start, start + pageSize).map(recordHtml).join('') : '<p class="empty">No records match this search. Try a broader term or another record type.</p>';
    pagination.innerHTML = pages > 1 ? `<button type="button" id="previous" ${page === 1 ? 'disabled' : ''}>← Previous</button><span>Page ${page} of ${pages}</span><button type="button" id="next" ${page === pages ? 'disabled' : ''}>Next →</button>` : '';
    document.querySelector('#previous')?.addEventListener('click', () => { page--; draw(); status.focus(); });
    document.querySelector('#next')?.addEventListener('click', () => { page++; draw(); status.focus(); });
  }
  search.addEventListener('input', () => { page = 1; draw(); });
  kind.addEventListener('change', () => { page = 1; draw(); });
  fetch('catalog.json').then(response => { if (!response.ok) throw new Error('Could not load catalog'); return response.json(); }).then(data => {
    records = data.records.slice().sort((a,b) => a.name.localeCompare(b.name));
    [...new Set(records.map(r => r.kind).filter(Boolean))].sort().forEach(label => { const option = document.createElement('option'); option.value = label; option.textContent = label; kind.appendChild(option); });
    draw();
  }).catch(() => { status.textContent = 'The collection could not be loaded.'; recordsEl.innerHTML = '<p class="empty">Please reload the page, or visit the repository to explore the source data.</p>'; });
})();
