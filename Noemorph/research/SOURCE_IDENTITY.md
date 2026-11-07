# Source work-identity review — first additive tranche

This tranche preserves every raw citation, legacy `source_id` and stable
`source_uid`. It **does not** normalize DOI identifiers or merge source work
identities, since the local review ledger relies on existing IDs.

For a shared source key, the source register now exposes:

- `work_identity_review_state: unreviewed | needs-review`
- `metadata_conflict_fields` (currently title/year)
- `metadata_variants` with the original bibliographic fields and citing IDs

The existing display title, author, and year come from the first occurrence for
backward compatibility. **They are not canonical or certified.** Conflicts are
review prompts, not automatic corrections or proof that a record is erroneous.

Run `python Noemorph/research/audit_data_quality.py` and compare the
`potential_work_metadata_conflicts` group count to the same-source-key
`needs-review` rows returned by `/api/sources`.

Next steps, requiring editorial decisions: normalize DOI strings into a
versioned work registry, adjudicate each conflict (including living scholarly
entries and publication-year conventions), add stable curated domain-family IDs,
then implement a reversible migration preserving all research claims and
public permalinks.
