# Noemorph

Noemorph is a citation-first research atlas for theories, constructs, clinical state models, and positions concerning mind and consciousness. The current release remains in **collection phase**, not finished synthesis: it publishes typed records and their provenance while keeping theory-to-theory relationship claims locked until the coverage protocol passes independent review.

## Run the desktop application

From the repository root on Windows, with Python installed, run:

```powershell
python Noemorph\Noemorph.py
```

The entry point creates a project-local Python environment, installs the pinned Python packages, obtains a verified portable Node.js runtime if the machine has no compatible Node installation, runs `npm ci`, builds the Vite interface, starts FastAPI on an ephemeral loopback port, and opens the result in an application-owned WebView2 frame. It does not use Qt/PySide, Chrome, or an external browser. Citation destinations open in a second contained WebView window.

The normal production launch leaves no Vite or Node process running after the frontend has been built. Subsequent launches reuse unchanged dependencies and build artifacts.

Useful development modes:

```powershell
python Noemorph\Noemorph.py --server-only
python Noemorph\Noemorph.py --api-only --port 8765 --skip-python-bootstrap
cd Noemorph\frontend
npm run dev
```

## Research corpus

- `Noemorph/data/catalog.json` is the versioned base artifact and declares the dated supplement files loaded by the backend.
- `Noemorph/data/catalog-2026-08-30-neuroscience.json` adds computational, neural-dynamics, anesthesia, sleep, and clinical-state gaps.
- `Noemorph/data/catalog-2026-08-30-awareness-social.json` adds awareness, metacognition, selfhood, developmental, comparative, and machine-mind gaps.
- `Noemorph/data/catalog-2026-08-30-philosophy-history.json` adds arguments, explanatory challenges, and source-bounded historical and living traditions.
- `Noemorph/data/catalog-2026-08-30-anomalous-challenge.json` adds 22 explicitly bounded non-consensus proposals and challenge positions from Kuhn sections 17–18; inclusion is not endorsement.
- The six `*-breadth.json` shards add 306 records across neuroscience, cognition, self/agency/affect, analytic philosophy, recent formal proposals, clinical and state measurement, cross-cultural history, and living traditions.
- `Noemorph/data/catalog-2026-08-30-states-clinical-breadth.json` contributes 56 sharply bounded state constructs, assessment instruments, experimental paradigms, and neural measures; it does not relabel every measure as a causal theory.
- `Noemorph/data/catalog-2026-08-30-cross-cultural-breadth.json` contributes 65 source-bounded positions across South Asian, Buddhist, Sikh, Jaina, East Asian, Arabic-Islamic, Jewish, African, Indigenous American, Pacific, and ancient traditions with explicit translation and community-attribution limits.
- `Noemorph/data/catalog-2026-08-30-emerging-breadth.json` contributes 35 recent scientific, formal, methodological, and artificial-consciousness proposals; 24 date from 2024–2026.
- The optional local `Noemorph/data/discovery-closer-to-truth.json` is a separate 474-entry acquisition registry crawled from the Closer To Truth Landscape index. It is excluded from the public repository because it contains third-party source text. It retains categories, people named on each page, exact source pages, 1,489 key-takeaway statements, 1,499 reference entries, and 1,909 clean reference locators without automatically promoting candidates into the reviewed catalog.
- `Noemorph/data/discovery-kuhn-landscape.json` retains all 219 named headings from Kuhn's landscape audit (209 named positions and 10 section overviews) with conservative title-screen results.
- `Noemorph/data/scope-tsc-taxonomy.json` indexes the University of Arizona TSC 2024 taxonomy's 102 research topics across six groups. These are scope controls, not theories, and are never added to the theory count.
- `Noemorph/data/coverage-report.json` is a regenerated machine-readable rollup across reviewed records, citations, research-profile depth, acquisition frames, and scope controls.
- `research/consciousness_seed_catalog.md` is the human-readable seed inventory.
- `research/consciousness_expansion_catalog.md` is the first audited expansion tranche.
- `research/build_catalog.py` regenerates the JSON artifact and enriches DOI metadata through Crossref.
- The merged reviewed collection currently contains 595 uniquely named and identified records, 1,256 retained citations, and 1,045 unique source records. It distinguishes scientific theories, philosophical positions, historical traditions, phenomenological constructs, clinical/state models, methodological frameworks, social-cognition accounts, and arguments or challenges.

The current corpus includes 453 deep research profiles. Each retains a claim scope, a boundary note, an evidence profile, open questions, source roles, and exact citation locators. The additions include recent active-inference and evolutionary proposals, criticality and neural-hierarchy accounts, clinical complexity and state-transition models, attention and memory architectures, agency and affect models, social and comparative cognition, explanatory arguments, and carefully bounded historical or living traditions. These additions increase coverage; they do not make a claim of exhaustiveness.

When the optional local acquisition registry is available, it is visible under **Record catalog → Discovery screening**, with match status kept separate from reviewed-record status. Each source profile can be inspected without leaving the catalog table; the inspector exposes the retained description, named people, page claims, lexical match evidence, and reference locators only on demand. Rebuild or reconcile the source frames with:

```powershell
cd Noemorph
python research\sync_closer_to_truth.py --workers 6
python research\sync_closer_to_truth.py --reconcile-only
python research\audit_kuhn_landscape.py --json --output data\discovery-kuhn-landscape.json
python research\sync_tsc_taxonomy.py
python research\build_coverage_report.py
```

DOI resolution, locator recording, and human semantic review are intentionally separate provenance states. A resolvable DOI is not represented as proof that its title, authors, or content support a catalog claim. Known misdirected citations are prohibited by automated integrity tests.

## Local semantic candidate analysis

The **Relationship review** workspace is a separate, review-only queue. It does not draw semantic edges on the Taxonomic Atlas and it does not unlock `/api/graph/relationships`. Every row is a machine-generated research lead; embedding proximity is not represented as correlation, causation, influence, equivalence, support, refutation, or novelty.

A locally generated run uses the locally installed `nomic-embed-text:latest` model at 768 dimensions for independent claim, target, evidence, limit, and question views. `mxbai-embed-large:latest` supplies a separate 1,024-dimensional neighbour-rank sensitivity check; raw scores from the two spaces are never averaged. Names, aliases, proponents, citations, domains, traditions, and status labels are excluded from the conceptual vectors. Identity text is embedded only for duplicate screening.

The generated candidate database and embedding cache are not included in a clean checkout. The checked-in run manifest may describe an earlier catalog and does not make candidates available on its own. Generate a fresh local artifact for the current catalog with:

```powershell
cd Noemorph
python research\build_semantic_index.py
```

The builder requires Ollama on `127.0.0.1:11434` with both models already installed. It uses exact all-pairs comparison, reciprocal-neighbour ranks, empirical within-stratum percentiles, CSLS hubness diagnostics, cross-model rank agreement, shared-source/proponent controls, explicit scope-barrier checks, and a content-addressed embedding cache under `data/semantic/embedding-cache`. The builder writes a run manifest at `data/semantic/semantic-run.json` and a local review ledger and sparse candidate artifact at `data/semantic/semantic.sqlite3`. Changing the catalog requires a new run.

Candidate review is deliberately staged:

1. Inspect the two record claims, evidence profiles, limits, citations, and exact input provenance.
2. Dismiss artifacts, defer uncertain pairs, or shortlist a typed research lead with a reviewer note.
3. Run and record a separate prior-art search. Absence from the current corpus is never treated as proof of novelty.
4. Only a directly supported, independently reviewed relationship can later be considered for a maintained synthesis layer.

The semantic API is exposed at `/api/semantic/status`, `/api/semantic/candidates`, and `/api/semantic/candidates/{id}`. Review writes use the candidate endpoint with `PATCH`; the canonical catalog and taxonomy remain immutable.

## Verification

```powershell
cd Noemorph
python -m pip install -r requirements.txt httpx==0.28.1
python -m unittest discover -s tests -v
cd frontend
npm ci
npm run build
```

The FastAPI route `/api/graph/relationships` returns HTTP 423 while the collection gate is locked. `/api/graph/taxonomy` exposes organizational classification edges only.

## Contribute and reuse

Contributions are welcome: see [CONTRIBUTING.md](CONTRIBUTING.md) for research, source, and development guidelines. Report a missing perspective or correction through the repository's issues, or propose a focused pull request.

Original project material is available under the [MIT license](LICENSE). Referenced research and other third-party material retain their own rights and terms; see [THIRD_PARTY.md](THIRD_PARTY.md). Local copies of the Kuhn paper, extracted text, and the scraped Closer To Truth registry are excluded from the public repository. Some acquisition scripts and related tests require those optional files and cannot run until they are obtained or generated locally under applicable terms.
