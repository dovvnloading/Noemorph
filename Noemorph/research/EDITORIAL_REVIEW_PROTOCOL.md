# Editorial source and claim review protocol (v0.1)

**Status:** proposed workflow for research contributors and editors. The
current catalog and local review ledger do **not** implement the publication
approval states described below. This document does not certify any existing
record, citation, theory or relationship.

## Purpose and boundaries

Noemorph indexes open-world perspectives across neuroscience, cognitive
science, clinical assessment, philosophy, history and living traditions.
Every inclusion is a *research lead*, never an endorsement or fixed
completeness claim. A verified DOI, a complete research profile, a published
source, or a machine-generated semantic candidate must **never** be
represented as proof of claim support or conceptual relationships.

Keep four states explicitly separate:

1. **Bibliographic identity:** Did we find the intended work/edition and
   correctly transcribe authors, title, date, venue, DOI and locator?
2. **Claim interpretation:** What exact claim or limitation does the record
   assert, and what source passage actually speaks to it?
3. **Independent review:** Did a qualified, distinct reviewer inspect the
   primary work and assess the interpretation and its limits?
4. **Publication decision:** Has the maintainer/editor explicitly approved
   a revision with provenance and a public correction path?

No software field currently grants stage 3 or 4 automatically.

## Work identity and citation review

A reviewer should capture the source's stable locator (DOI, official edition
or authoritative URL), author(s), original title, edition or translation,
publication year as presented by the source, and the access date for a living
resource. Check that DOI resolution reaches the **intended work**, not merely
a resolvable destination. Different preprint/journal dates, living
encyclopedia editions and translations may legitimately differ; record
the reason instead of silently overwriting variants.

The [read-only data quality audit](audit_data_quality.py) and the desktop
Source register surface potential same-work title/year discrepancies as
**review-needed** leads. Resolve each by documenting whether it is a
metadata error, edition distinction, author/title formatting convention,
or an unresolved identification question. Do not merge source identities or
change stable `source_uid` values until existing claim-review references
have been migrated and checked.

Source `authority` and `verification` are properties of **each citation
use**, not universal scores for the work or scientific merit.

## Claim-level review entry

Before a substantive claim can be proposed for editorial approval, record:

- Exact record ID, claim ID, field/path, current claim text and its hash.
- Source `source_uid`, original citation URL, and verified bibliographic
  identity or an explicit unresolved-identity warning.
- Exact **in-source** page/section/paragraph/figure/table/line/timestamp,
  tied to the reviewed edition or translation. A URL alone is not a passage
  locator.
- A short reviewer-supplied excerpt when the review decision asserts
  support or challenge, respecting rights restrictions (current local ledger
  permits at most 280 characters).
- One determination: `supports`, `challenges`, `contextualizes`,
  `inconclusive`, or `not-relevant`.
- Justification describing the inference, scope mismatch, methodological
  caveats, and what the passage **does not** establish.
- Conflicts of interest, relevant expertise and unresolved objections.

Prefer a primary formulation and an independent critical source where
appropriate. A source can **contextualize** an idea without supporting the
specific claim; disputes must not be collapsed into a binary verdict.

The current CLI is `python Noemorph/research/review_claim_evidence.py`.
It writes to a private local append-only SQLite ledger. Reviewer labels
are self-declared; its `recorded-concordance` status is **not** authenticated
independent review and may **not** automatically promote claims. Keep
review passages and private notes out of Git.

## Distinct record-kind review considerations

| Kind | Required interpretation checks |
| --- | --- |
| Scientific theory or model | Identify its formal/empirical target, test type, competing explanations, negative evidence and whether a cited paper is a proposal or independent test |
| Clinical/state model or measure | Separate observation, instrument validation and diagnosis; note population, sensitivity, limitations and non-clinical use boundaries |
| Philosophical position or argument | Distinguish the original author's thesis from exegesis, logical reconstruction, objections and contested readings; avoid treating philosophical claims as experiments |
| Phenomenological construct | Distinguish first-person description, operational measurement and causal explanation |
| Historical or living tradition | Identify original language, edition/translation and historical context; retain community attribution, contested interpretation and the perspective's own vocabulary |
| Theory of mind/social cognition | Define target population, task, inference limits and social/cultural generalizability |
| Non-consensus proposals and challenges | Record clearly that inclusion is not endorsement; distinguish methodologically testable assertions from interpretive or metaphysical claims |

For historical, Indigenous and living community traditions, seek relevant
subject specialists and, where possible and appropriate, qualified
community-informed input. Do not silently impose equivalence to a modern
neuroscientific construct or use a translation as an original-language quote.

## Independence and disagreement

A future **independent** review requires separately authenticated identities
and a documented expertise/conflict-of-interest check. The proposing author
must not serve as their own independent approval. A second reviewer reads
the actual work; agreement on a short summary or shared source link is
insufficient. Retain each decision and record disagreements explicitly.
The editor can request an additional expert review or mark the claim
`inconclusive`; editorial ambiguity should remain visible.

Current GitHub PR approvals can record code/editorial discussion but are
not themselves a full authenticated scientific peer-review mechanism. Do not
expose an "independently approved" UI state until a reviewed, auditable
publication path exists.

## Change management and correction

Propose one narrowly scoped claim/metadata correction per PR or research
issue, retaining the old value, exact proposed new value, source locator,
review note, reviewer identity and unresolved uncertainties. Required
acceptance checks are catalog validation, stable identifiers, current
public export and explicit confirmation that the relationship graph remains
locked. Material changes to a claim invalidate earlier claim-hash snapshots;
retain those decisions as stale history rather than deleting them.

If an error is reported after publication, record the correction and
public rationale, distinguish substantive changes from bibliographic
formatting updates, and provide a reversible patch. Do not cite the absence
of a candidate from the current corpus as proof of scientific novelty.

## First review pilot and measurements

Start with the **20 unreviewed claim–source leads across 10 priority
records**, plus an editorially selected tranche of incomplete profiles.
For each lead, report whether its bibliographic identity was checked, a
passage was inspected, a review was recorded, and a distinct authenticated
reviewer signed off. Record inconclusive outcomes rather than forcing
support. Maintain separate denominators for source occurrences, distinct
works, claims, records, and reviewers; never roll them into a single
"truth score."

**Publication rule:** This document, a source audit, or two entries in the
local ledger do not unlock `/api/graph/relationships`. A future independent
governance process must approve the evidence protocol and coverage gate
before relationship synthesis is considered.
