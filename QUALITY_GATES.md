# Noemorph — quality acceptance gates after issue queue clearance

**November 7, 2026.** The maintainer requested **zero open GitHub issues**.
The historical issue tickets are being closed as an **administrative decision**,
not because every acceptance criterion passed. Closing a ticket is not
scientific review, WCAG certification, or a completed Windows GUI release.

This is the durable record of work that still requires evidence. **Reopen an
issue or create a new one before claiming these gates are complete.**

| Issue | Verified foundation | Still required; NOT certified |
| --- | --- | --- |
| [#16](https://github.com/dovvnloading/Noemorph/issues/16) source identities and taxonomy | Read-only quality audit (#13) and citation title/year variants (#39) | Human decisions on work/edition conflicts; reviewed work IDs, taxonomy mapping and reversible migration preserving all stable links |
| [#17](https://github.com/dovvnloading/Noemorph/issues/17) source/claim review | Proposed editorial review protocol (#41) and deterministic **unreviewed** triage export | Qualified independent scientific/historical/community-aware reviewers; exact passages, identities/conflicts, dispute resolution, 20-lead pilot and approved correction process |
| [#18](https://github.com/dovvnloading/Noemorph/issues/18) a11y, search and performance | Automated serious/critical WCAG checks (#63), public Firefox/WebKit exploratory coverage (#67), and cross-surface alias/keyword/taxonomy search regressions (functionality only) | Manual screen reader/keyboard/200% zoom/focus/motion/touch audit, all desktop workspaces, reviewed search benchmark, mobile performance budgets and CSL metadata improvements |
| [#19](https://github.com/dovvnloading/Noemorph/issues/19) Windows/WebView2 | Launcher and API recovery (#38/#40), offline portable ZIP smoke (#64) | Real interactive Windows WebView2 clean install, missing-runtime and restart/recovery tests, controlled offline bootstrap, upgrade/rollback and native GUI acceptance |
| [#20](https://github.com/dovvnloading/Noemorph/issues/20) semantic model evaluation | Reproducible metric harness with **synthetic**, not empirical, fixture (#68) | License-compliant real cases, independent adjudicated reviewer labels, frozen model digests, rank stability, domain-stratified measured utility |
| [#21](https://github.com/dovvnloading/Noemorph/issues/21) foundation roadmap | Historical coordination of #11–#68 | These five unverified gates survive outside the issue queue |

## Reproduce outstanding human-work queue (never a certificate)

Run from repository root:

```sh
python Noemorph/research/build_editorial_triage.py --output editorial-triage.json
python Noemorph/research/audit_data_quality.py --output data-quality.json
python Noemorph/research/evaluate_semantic_candidates.py --input Noemorph/research/fixtures/semantic_eval_synthetic_v1.json --k 3
cd Noemorph && python -m unittest discover -s tests -v
```

The exported profile tranche, pending citation uses, title/year conflicts
and unreviewed claim/source leads are **review proposals**, not decisions.
Keep raw private reviewer notes and SQLite ledgers out of Git.

## Nonnegotiable release boundaries

- Keep `/api/graph/relationships` locked until independent evidence review
  and an explicit publication decision actually happen.
- A profile, bibliographic match, citation role or semantic score does
  **not** establish support for a scientific/philosophical claim.
- Never silently merge stable source IDs or change public deep links.
- CodeQL, browser tests and Python CI do not certify full research quality.
- This file records debt deliberately instead of marking incomplete science
  or GUI checks as completed to make a GitHub badge look clean.
