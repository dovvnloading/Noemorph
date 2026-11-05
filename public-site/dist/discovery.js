/* Read-only, question-led discovery. No theory relationship edges are inferred. */
(() => {
  'use strict';

  const THEMES = new Set(['orbit', 'signal', 'focus', 'mirror']);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch])
  );
  function compact(value, max = 210) {
    const str = String(value ?? '').trim();
    if (str.length <= max) return str;
    const head = str.slice(0, max);
    const split = head.lastIndexOf(' ');
    return head.slice(0, split > 80 ? split : max) + '…';
  }
  function recordHref(id) {
    const url = new URL(window.location.href);
    url.search = '';
    url.searchParams.set('record', id);
    url.hash = 'catalog';
    return url.href;
  }
  function sourceHref(value) {
    try {
      const url = new URL(value);
      return url.protocol === 'https:' ? url.href : '';
    } catch {
      return '';
    }
  }
  function valueHtml(value) {
    if (value === null || value === undefined || value === ''
        || (Array.isArray(value) && !value.length)) {
      return '<p class="discovery-missing">Not profiled yet</p>';
    }
    if (typeof value === 'string' || typeof value === 'number') {
      return '<p>' + esc(value) + '</p>';
    }
    if (Array.isArray(value)) {
      return '<ul>' + value.map(item => '<li>' + esc(item) + '</li>').join('') + '</ul>';
    }
    if (typeof value === 'object') {
      return '<dl>' + Object.entries(value).map(([key, item]) =>
        '<div><dt>' + esc(key.replaceAll('_', ' ')) + '</dt><dd>' +
        valueHtml(item) + '</dd></div>'
      ).join('') + '</dl>';
    }
    return '<p class="discovery-missing">Not profiled yet</p>';
  }
  function checkPaths(config, byId) {
    if (config?.version !== 1 || !Array.isArray(config.journeys) ||
        !config.journeys.length || !Array.isArray(config.surprise?.record_ids)) {
      throw new Error('Missing discovery configuration');
    }
    const known = new Set();
    for (const path of config.journeys) {
      if (typeof path.id !== 'string' || !/^[a-z-]{2,40}$/.test(path.id) ||
          known.has(path.id) || !THEMES.has(path.theme) || !path.title ||
          !path.subtitle || !Array.isArray(path.steps) || path.steps.length < 2) {
        throw new Error('Invalid curated reading pathway');
      }
      known.add(path.id);
      const stepIds = new Set();
      for (const step of path.steps) {
        if (!byId.has(step.record_id) || stepIds.has(step.record_id) ||
            !step.prompt || !step.orientation || !step.reflection) {
          throw new Error('Discovery step references a missing catalog entry');
        }
        stepIds.add(step.record_id);
      }
    }
    const pool = config.surprise.record_ids;
    if (pool.length < 2 || new Set(pool).size !== pool.length ||
        pool.some(id => !byId.has(id))) {
      throw new Error('Surprise pool includes a missing catalog entry');
    }
  }

  function mount(records) {
    const choices = document.querySelector('#discovery-choices');
    const stage = document.querySelector('#discovery-stage');
    const status = document.querySelector('#discovery-status');
    const disclosure = document.querySelector('#discovery-disclosure');
    if (!choices || !stage || !status) return Promise.resolve();
    const byId = new Map(records.map(record => [record.id, record]));

    return fetch('discovery-journeys.json')
      .then(response => {
        if (!response.ok) throw new Error('The discovery collection is unavailable');
        return response.json();
      })
      .then(config => {
        checkPaths(config, byId);
        const byPath = new Map(config.journeys.map(path => [path.id, path]));
        let active = null;

        function readLink() {
          const params = new URL(window.location.href).searchParams;
          if (params.has('record') || params.has('compare')) return null;
          const journey = params.getAll('journey');
          const step = params.getAll('step');
          const surprise = params.getAll('surprise');
          if (journey.length === 1 && step.length <= 1 && !surprise.length) {
            const path = byPath.get(journey[0]);
            const rawStep = step.length ? step[0] : '1';
            if (!path || !/^[1-9][0-9]*$/.test(rawStep)) return null;
            const index = Number(rawStep) - 1;
            if (!Number.isSafeInteger(index) || index >= path.steps.length) return null;
            return { mode: 'journey', id: path.id, index };
          }
          if (surprise.length === 1 && !journey.length && !step.length &&
              config.surprise.record_ids.includes(surprise[0])) {
            return { mode: 'surprise', id: surprise[0], index: 0 };
          }
          return null;
        }
        function updateLink() {
          const url = new URL(window.location.href);
          for (const key of ['journey', 'step', 'surprise', 'record', 'compare']) {
            url.searchParams.delete(key);
          }
          if (active?.mode === 'journey') {
            url.searchParams.set('journey', active.id);
            url.searchParams.set('step', String(active.index + 1));
            url.hash = 'discover';
          } else if (active?.mode === 'surprise') {
            url.searchParams.set('surprise', active.id);
            url.hash = 'discover';
          }
          window.history.pushState(null, '', url.href);
        }
        function focusStage() {
          window.requestAnimationFrame(() => {
            stage.scrollIntoView({ block: 'start' });
            stage.focus({ preventScroll: true });
          });
        }
        function choiceHtml(path) {
          const pressed = active?.mode === 'journey' && active.id === path.id;
          return '<button type="button" class="discovery-choice discovery-choice-' +
            path.theme + '" data-discovery-journey="' + esc(path.id) +
            '" aria-pressed="' + pressed + '">' +
            '<span class="discovery-choice-number">' + esc(path.number) +
            ' / QUESTION</span><span class="discovery-choice-glyph" aria-hidden="true">✳</span>' +
            '<strong>' + esc(path.title) + '</strong>' +
            '<span class="discovery-choice-description">' + esc(path.subtitle) + '</span>' +
            '<span class="discovery-choice-action">Explore ' + path.steps.length +
            ' perspectives <span aria-hidden="true">↗</span></span></button>';
        }
        function drawChoices() {
          choices.innerHTML = '<div class="discovery-grid">' +
            config.journeys.map(choiceHtml).join('') +
            '<button type="button" class="discovery-choice discovery-choice-wild" ' +
            'data-discovery-action="surprise">' +
            '<span class="discovery-choice-number">05 / UNEXPECTED</span>' +
            '<span class="discovery-choice-glyph" aria-hidden="true">✺</span>' +
            '<strong>Surprise me.</strong>' +
            '<span class="discovery-choice-description">A doorway into a less familiar part of the collection.</span>' +
            '<span class="discovery-choice-action">Reveal an idea <span aria-hidden="true">↗</span></span>' +
            '</button></div>';
        }
        function retainedSources(record) {
          return (record.citations || []).slice(0, 2).map(citation => {
            const href = sourceHref(citation.url);
            const title = esc(citation.title || 'Retained source');
            return '<li>' + (href
              ? '<a target="_blank" rel="noopener noreferrer" href="' + esc(href) + '">' + title + ' ↗</a>'
              : title) +
              '<span class="discovery-citation-meta">' +
              esc(String(citation.authority || 'unspecified').replaceAll('-', ' ')) +
              ' · locator state: ' +
              esc(String(citation.verification || 'pending-metadata-review').replaceAll('-', ' ')) +
              '</span></li>';
          }).join('');
        }
        function researchNotes(record) {
          return '<details class="discovery-notes"><summary>Unfold research notes ' +
            '<span aria-hidden="true">+</span></summary>' +
            '<div class="discovery-note-columns">' +
            '<section><h5>Scope and boundaries</h5>' +
            valueHtml(record.claim_scope || record.scope) +
            valueHtml(record.boundary_note || record.status_note) + '</section>' +
            '<section><h5>Still open</h5>' + valueHtml(record.open_questions) + '</section>' +
            '<section><h5>Retained source trail</h5><ul class="discovery-citations">' +
            retainedSources(record) + '</ul>' +
            '<p>Recorded citations do not verify claim support. Check the original works.</p></section>' +
            '</div></details>';
        }
        function drawStage() {
          drawChoices();
          if (!active) {
            stage.hidden = true;
            stage.innerHTML = '';
            status.textContent = 'Choose a question or try Surprise me.';
            return;
          }
          const path = active.mode === 'journey' ? byPath.get(active.id) : null;
          const item = path?.steps[active.index];
          const record = byId.get(item?.record_id || active.id);
          if (!record) {
            active = null;
            drawStage();
            return;
          }
          const count = path?.steps.length ?? 1;
          const current = active.index + 1;
          const theme = path?.theme || 'wild';
          const prompt = item?.prompt || config.surprise.prompt;
          const orientation = item?.orientation ||
            'A documented idea from a different corner of the catalog. Its inclusion is not endorsement.';
          const reflection = item?.reflection ||
            'What is unresolved, and which source would you consult next?';
          const progress = Array.from({ length: count }, (_, index) =>
            '<span class="' + (index <= active.index ? 'filled' : '') + '"></span>'
          ).join('');
          let navigation;
          if (path) {
            navigation = '<button type="button" data-discovery-action="previous" ' +
              (active.index === 0 ? 'disabled' : '') + '>← Previous</button>' +
              (current < count
                ? '<button type="button" data-discovery-action="next">Reveal next perspective →</button>'
                : '<button type="button" data-discovery-action="reset">Explore another question ↗</button>');
          } else {
            navigation = '<button type="button" data-discovery-action="surprise">Another surprise ↗</button>';
          }
          if (disclosure) disclosure.open = true;
          stage.hidden = false;
          stage.innerHTML = '<div class="discovery-stage-top"><span class="discovery-overline">' +
            esc(path ? path.title : 'Unscripted discovery') + '</span>' +
            '<button type="button" data-discovery-action="reset">Choose another question</button></div>' +
            '<div class="discovery-progress" role="progressbar" aria-label="Reading progress" ' +
            'aria-valuemin="0" aria-valuemax="' + count + '" aria-valuenow="' + current + '">' +
            progress + '</div>' +
            '<div class="discovery-stage-grid discovery-stage-' + theme + '">' +
              '<div class="discovery-scene" aria-hidden="true">' +
                '<span class="discovery-scene-ring discovery-ring-one"></span>' +
                '<span class="discovery-scene-ring discovery-ring-two"></span>' +
                '<span class="discovery-scene-ring discovery-ring-three"></span>' +
                '<span class="discovery-scene-star">✳</span>' +
                '<span class="discovery-scene-caption">NOEMORPH / RESEARCH LENS</span>' +
                '<strong>' + String(current).padStart(2, '0') +
                ' <small>/ ' + String(count).padStart(2, '0') + '</small></strong>' +
              '</div>' +
              '<article class="discovery-reveal">' +
                '<span class="discovery-step-label">' +
                (path ? 'PERSPECTIVE ' + current + ' / ' + count : 'AN UNEXPECTED ENTRY') +
                ' · ' + esc(record.kind) + '</span>' +
                '<h3>' + esc(prompt) + '</h3>' +
                '<p class="discovery-orientation">' + esc(orientation) + '</p>' +
                '<div class="discovery-entry"><span>FROM THE CATALOG · ' +
                esc(record.review_state || 'review pending') + '</span>' +
                '<h4>' + esc(record.name) + '</h4>' +
                '<p>' + esc(compact(record.summary)) + '</p>' +
                '<a href="' + esc(recordHref(record.id)) + '">Explore the full record ' +
                '<span aria-hidden="true">↗</span></a></div>' +
                '<p class="discovery-reflection"><span>CONSIDER</span>' +
                esc(reflection) + '</p>' + researchNotes(record) +
                '<nav class="discovery-navigation" aria-label="Move through this reading journey">' +
                navigation + '</nav>' +
              '</article></div>' +
            '<p class="discovery-policy">These are curated reading perspectives, not verified ' +
            'connections between theories. Citation resolution does not establish claim support. ' +
            'No conceptual relationships are generated.</p>';
          status.textContent = path
            ? path.title + ', perspective ' + current + ' of ' + count + '.'
            : 'Unexpected entry: ' + record.name + '.';
        }
        function chooseSurprise() {
          const candidates = config.surprise.record_ids.filter(id => !(
            active?.mode === 'surprise' && active.id === id
          ));
          active = { mode: 'surprise', id: candidates[Math.floor(Math.random() * candidates.length)], index: 0 };
          updateLink();
          drawStage();
          focusStage();
        }
        function handleClick(event) {
          const button = event.target instanceof Element
            ? event.target.closest('button[data-discovery-journey], button[data-discovery-action]')
            : null;
          if (!button || button.disabled) return;
          if (button.dataset.discoveryJourney) {
            const path = byPath.get(button.dataset.discoveryJourney);
            if (!path) return;
            active = { mode: 'journey', id: path.id, index: 0 };
          } else {
            switch (button.dataset.discoveryAction) {
              case 'surprise':
                chooseSurprise();
                return;
              case 'reset':
                active = null;
                break;
              case 'previous':
                if (active?.mode !== 'journey' || active.index === 0) return;
                active = { ...active, index: active.index - 1 };
                break;
              case 'next':
                if (active?.mode !== 'journey' ||
                    active.index + 1 >= byPath.get(active.id).steps.length) return;
                active = { ...active, index: active.index + 1 };
                break;
              default:
                return;
            }
          }
          updateLink();
          drawStage();
          if (active) focusStage();
          else window.requestAnimationFrame(() => choices.focus({ preventScroll: true }));
        }
        choices.addEventListener('click', handleClick);
        stage.addEventListener('click', handleClick);
        window.addEventListener('popstate', () => {
          active = readLink();
          drawStage();
          if (active) focusStage();
        });
        active = readLink();
        if (disclosure && new URL(window.location.href).hash === '#discover') {
          disclosure.open = true;
        }
        drawStage();
        if (active) focusStage();
        window.addEventListener('hashchange', () => {
          if (disclosure && new URL(window.location.href).hash === '#discover') {
            disclosure.open = true;
          }
        });
      })
      .catch(() => {
        choices.innerHTML = '';
        stage.hidden = true;
        stage.innerHTML = '';
        status.textContent = 'Guided discovery is unavailable right now. The full catalog remains accessible below.';
      });
  }

  window.NoemorphDiscovery = { mount };
})();
