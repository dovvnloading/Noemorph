# Reproducible semantic candidate evaluation — preliminary framework

Issue #20 requires a **real independently reviewed benchmark**. The included
`fixtures/semantic_eval_synthetic_v1.json` is deliberately **invented software
test data**, not Noemorph research evidence or a measured model result.

## Run the portable CI smoke fixture

From the repository root with Python 3.14 (no local Ollama model and no
private SQLite index required):

```sh
python Noemorph/research/evaluate_semantic_candidates.py --input Noemorph/research/fixtures/semantic_eval_synthetic_v1.json --k 3
cd Noemorph && python -m unittest tests.test_semantic_evaluation -v
```

Expected invented-fixture output: full precision@3 = 2/3, full false-discovery
fraction@3 = 1/3, reviewer observed agreement = 3/4, Cohen's kappa = 1/2.
This proves the metric calculation runs in CI, **not** that a real ranking is
accurate.

## Contract for actual evidence

Freeze a versioned candidate ordering with exact record identifiers and
`review_priority` scores, using the schema in the synthetic fixture. Create
a **separate** reviewer-adjudicated label set with known related/unrelated,
near-duplicate, and cross-tradition cases, source justifications and
disagreement resolution. Record model digests, recipe/catalog fingerprints,
license permissions, sample selection, reviewer provenance and dates in the
reviewed fixture's accompanying protocol. `fixture_kind: reviewed` is a
self-declared field, **not** independent authentication by this script.

The evaluator sorts ties by canonical pair IDs and rejects duplicate
unordered pairs, non-finite scores, invalid labels and impossible K values.
It reports top-K label coverage separately. **Full precision and the
false-discovery fraction are `null` whenever the selected top K has any
unjudged pair**. The judged-only precision is explicitly labeled and
must never be presented as population precision. Reviewer observed agreement
and Cohen's kappa are calculated from two explicit label columns but the
software cannot verify reviewer identity or independence.

This does **not** estimate general-population false-positive rates or model
rank stability from the synthetic fixture. For that, freeze independent
reviewer labels and model runs, estimate selection bias and stratify
performance by domain and pair category. Never infer conceptual relationships
or originality from semantic similarity. The publication graph remains locked.
