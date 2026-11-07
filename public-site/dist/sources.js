(() => {
  // One read-only bibliography index, built from the validated catalog already in memory.
  // Grouping by a retained DOI/URL is a locator match, not a reviewed work identity.
  const search = document.querySelector('#source-search');
  const role = document.querySelector('#source-role');
  const verification = document.querySelector('#source-verification');
  const reset = document.querySelector('#source-reset');
  const results = document.querySelector('#source-results');
  const status = document.querySelector('#source-status');
  const pagination = document.querySelector('#source-pagination');
  const pageSize = 8;
  let sources = [];
  let page = 1;
  let requestedId = null;

  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
  const safeUrl = value => {
    try {
      const url = new URL(value);
      return url.protocol === 'https:' ? url.href : '';
    } catch { return ''; }
  };
  const sourceId = citation => {
    if (!citation || typeof citation !== 'object') return '';
    return String(citation.source_uid || citation.source_id || '');
  };
  function href(citation) {
    const id = sourceId(citation);
    if (!id) return '';
    const url = new URL(window.location.href);
    url.search = '';
    url.searchParams.set('source', id);
    url.hash = 'sources';
    return url.href;
  }

  function buildIndex(records) {
    const byLocator = new Map();
    for (const record of records) {
      for (const citation of record.citations || []) {
        if (!citation || !citation.url) continue;
        const key = String(citation.doi || citation.url).toLocaleLowerCase();
        let source = byLocator.get(key);
        if (!source) {
          source = {
            id: sourceId(citation) || 'local-source-' + (byLocator.size + 1),
            variants: [], variantKeys: new Set(), uses: []
          };
          byLocator.set(key, source);
        }
        const variant = {
          title: citation.title || 'Untitled citation',
          authors: citation.authors || '',
          year: citation.year ?? '',
          venue: citation.venue || '',
          doi: citation.doi || '',
          url: citation.url || ''
        };
        const signature = JSON.stringify(variant);
        if (!source.variantKeys.has(signature)) {
          source.variantKeys.add(signature);
          source.variants.push(variant);
        }
        source.uses.push({ record, citation });
      }
    }
    return [...byLocator.values()].map(source => {
      source.searchText = [
        ...source.variants.flatMap(v => Object.values(v)),
        ...source.uses.map(use => use.record.name)
      ].join(' ').toLocaleLowerCase();
      delete source.variantKeys;
      return source;
    }).sort((a, b) =>
      a.variants[0].title.localeCompare(b.variants[0].title)
      || a.id.localeCompare(b.id)
    );
  }

  function populate(select, values) {
    [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b))
      .forEach(value => {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = value;
        select.append(option);
      });
  }

  function variantHtml(variant) {
    const link = safeUrl(variant.url);
    return '<li><strong>' + esc(variant.title) + '</strong>'
      + '<span>' + esc([variant.authors, variant.year, variant.venue].filter(Boolean).join(' · ')) + '</span>'
      + (link ? '<a href="' + esc(link) + '" target="_blank" rel="noopener noreferrer">Citation locator ↗</a>' : '')
      + '</li>';
  }

  function sourceHtml(source) {
    const first = source.variants[0];
    const url = safeUrl(first.url);
    const uses = source.uses.map(use => {
      const recordUrl = new URL(window.location.href);
      recordUrl.search = '';
      recordUrl.searchParams.set('record', use.record.id);
      recordUrl.hash = 'catalog';
      return '<li><a href="' + esc(recordUrl.href) + '">' + esc(use.record.name) + '</a>'
        + '<small>Role: ' + esc(use.citation.authority || 'unspecified')
        + ' · Citation metadata: ' + esc(use.citation.verification || 'pending-metadata-review') + '</small></li>';
    }).join('');
    const variants = source.variants.length > 1
      ? '<details class="source-variants"><summary>' + source.variants.length
        + ' recorded bibliographic variants — review differences</summary><ul>'
        + source.variants.map(variantHtml).join('') + '</ul></details>'
      : '';
    return '<details class="source-entry" data-source-id="' + esc(source.id) + '"'
      + (requestedId === source.id ? ' open' : '') + '>'
      + '<summary><span class="source-entry-main"><strong>' + esc(first.title) + '</strong>'
      + '<small>' + esc([first.authors, first.year, first.venue].filter(Boolean).join(' · ')) + '</small></span>'
      + '<span class="source-use-count">' + source.uses.length + ' citation '
      + (source.uses.length === 1 ? 'use' : 'uses') + '</span>'
      + '<span class="source-toggle" aria-hidden="true">+</span></summary>'
      + '<div class="source-entry-detail">'
      + '<p>These are retained bibliography uses, not verified evidence of support for any claim.</p>'
      + (url ? '<p><a class="source-external" href="' + esc(url)
        + '" target="_blank" rel="noopener noreferrer">Open cited locator ↗</a></p>' : '')
      + (first.doi ? '<p class="source-doi">DOI: ' + esc(first.doi) + '</p>' : '')
      + variants
      + '<h3>Where this locator is cited</h3><ol class="source-record-links">' + uses + '</ol>'
      + '</div></details>';
  }

  function filteredSources() {
    const query = search.value.trim().toLocaleLowerCase();
    const terms = query.split(/\s+/).filter(Boolean);
    // Facets apply to the same citation use, not an invented source-wide status.
    const candidates = sources.filter(source => source.uses.some(use =>
      (!role.value || use.citation.authority === role.value)
      && (!verification.value || (use.citation.verification || 'pending-metadata-review') === verification.value)
    ));
    // Prefer a real phrase when one exists; otherwise accept terms across fields.
    // This avoids matching "Second Record" merely from "Second Author" + "First Record".
    if (query.includes(' ')) {
      const exactPhrase = candidates.filter(source => source.searchText.includes(query));
      if (exactPhrase.length) return exactPhrase;
    }
    return candidates.filter(source => terms.every(term => source.searchText.includes(term)));
  }

  function draw() {
    const matched = filteredSources();
    if (requestedId) {
      const position = matched.findIndex(source => source.id === requestedId);
      if (position >= 0) page = Math.floor(position / pageSize) + 1;
    }
    const pages = Math.max(1, Math.ceil(matched.length / pageSize));
    page = Math.min(page, pages);
    const start = (page - 1) * pageSize;
    status.textContent = matched.length + ' source ' + (matched.length === 1 ? 'locator' : 'locators')
      + (matched.length ? ' · showing ' + (start + 1) + '–' + Math.min(start + pageSize, matched.length) : '');
    results.innerHTML = matched.length
      ? matched.slice(start, start + pageSize).map(sourceHtml).join('')
      : '<p class="source-empty">No matching sources. Try an author, a DOI, or a broader search.</p>';
    pagination.innerHTML = pages > 1
      ? '<button type="button" data-source-page="' + (page - 1)
        + '"' + (page === 1 ? ' disabled' : '') + '>← Previous</button>'
        + '<span>Page ' + page + ' of ' + pages + '</span>'
        + '<button type="button" data-source-page="' + (page + 1)
        + '"' + (page === pages ? ' disabled' : '') + '>Next →</button>'
      : '';
  }

  function clearSelection() {
    requestedId = null;
    const url = new URL(window.location.href);
    if (url.searchParams.has('source')) {
      url.searchParams.delete('source');
      window.history.replaceState(null, '', url.href);
    }
  }

  function mount(records) {
    if (!results || !status || !search || !role || !verification || !reset || !pagination) return;
    sources = buildIndex(records);
    populate(role, sources.flatMap(source => source.uses.map(use => use.citation.authority)));
    populate(verification, sources.flatMap(source => source.uses.map(use => use.citation.verification || 'pending-metadata-review')));
    const url = new URL(window.location.href);
    const ids = url.searchParams.getAll('source');
    requestedId = ids.length === 1 && !url.searchParams.has('record')
      && !url.searchParams.has('compare')
      && sources.some(source => source.id === ids[0]) ? ids[0] : null;
    draw();
    if (requestedId) window.requestAnimationFrame(() => {
      const selected = results.querySelector('details[open] summary');
      if (selected) {
        selected.scrollIntoView({ block: 'center' });
        selected.focus({ preventScroll: true });
      }
    });
    for (const element of [search, role, verification]) {
      element.addEventListener(element === search ? 'input' : 'change', () => {
        clearSelection();
        page = 1;
        draw();
      });
    }
    reset.addEventListener('click', () => {
      search.value = '';
      role.value = '';
      verification.value = '';
      clearSelection();
      page = 1;
      draw();
      search.focus();
    });
    pagination.addEventListener('click', event => {
      const button = event.target instanceof Element
        ? event.target.closest('button[data-source-page]') : null;
      if (!button || button.disabled) return;
      const requestedPage = Number(button.dataset.sourcePage);
      if (!Number.isInteger(requestedPage) || requestedPage < 1) return;
      clearSelection();
      page = requestedPage;
      draw();
      status.focus({ preventScroll: true });
    });
  }

  window.NoemorphSources = { mount, href };
})();
