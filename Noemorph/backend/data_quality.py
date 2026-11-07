"""Deterministic research data quality diagnostics; no source is auto-corrected.

Conflicting metadata is a *review lead*, not a conclusion that a source is
wrong. Citation metadata verification never establishes claim-level support.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from typing import Any

PROFILE_FIELDS = ("claim_scope", "boundary_note", "evidence_profile", "open_questions")


def _has_material(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return any(_has_material(part) for part in value.values())
    if isinstance(value, (tuple, list)):
        return any(_has_material(part) for part in value)
    return value is not None and bool(value)


def _categories(values: Iterable[str], *, limit: int = 12) -> dict[str, Any]:
    counter = Counter(values)
    ordered = sorted(counter.items(), key=lambda row: (-row[1], row[0].casefold()))
    return {
        "distinct": len(counter),
        "singletons": sum(count == 1 for count in counter.values()),
        "most_common": [
            {"label": label, "count": count} for label, count in ordered[:limit]
        ],
    }


def _normalized_text(value: Any) -> str:
    return " ".join(str(value or "").casefold().split())


def data_quality_report(
    records: Iterable[Mapping[str, Any]],
    *,
    catalog_version: str,
    corpus_date: str,
) -> dict[str, Any]:
    """Create a stable, order-independent report from merged canonical records."""
    items = sorted(records, key=lambda item: str(item["id"]))
    if len({str(item["id"]) for item in items}) != len(items):
        raise ValueError("Data quality audit requires unique record IDs")

    citations: list[tuple[str, Mapping[str, Any]]] = []
    citation_uses: dict[str, list[tuple[str, Mapping[str, Any]]]] = defaultdict(list)
    missing_profiles: list[str] = []
    no_primary: list[str] = []
    no_human_metadata: list[str] = []
    claim_leads = 0

    for record in items:
        record_id = str(record["id"])
        record_citations = record["citations"]
        if not all(_has_material(record.get(field)) for field in PROFILE_FIELDS):
            missing_profiles.append(record_id)
        if not any(
            str(citation.get("authority", "")).startswith("primary-")
            for citation in record_citations
        ):
            no_primary.append(record_id)
        if not any(
            citation.get("verification") == "human-verified"
            for citation in record_citations
        ):
            no_human_metadata.append(record_id)
        for claim in record.get("claim_reviews", []):
            claim_leads += len(claim.get("citations", []))
        for citation in record_citations:
            citations.append((record_id, citation))
            source_key = str(citation.get("doi") or citation["url"]).casefold()
            citation_uses[source_key].append((record_id, citation))

    conflicts: list[dict[str, Any]] = []
    for key, uses in sorted(citation_uses.items()):
        titles = {
            _normalized_text(citation.get("title")): str(citation.get("title", ""))
            for _, citation in uses
        }
        years = {str(citation.get("year", "")) for _, citation in uses}
        if len(titles) <= 1 and len(years) <= 1:
            continue
        conflicts.append({
            "source_key": key,
            "title_variants": sorted(set(titles.values()), key=str.casefold),
            "year_variants": sorted(years),
            "record_ids": sorted({record_id for record_id, _ in uses}),
            "disposition": "review-needed",
        })

    states = Counter(
        str(citation.get("verification") or "pending-metadata-review")
        for _, citation in citations
    )
    summary = {
        "record_count": len(items),
        "citation_occurrences": len(citations),
        "unique_source_keys": len(citation_uses),
        "incomplete_profile_count": len(missing_profiles),
        "records_without_primary_anchor": len(no_primary),
        "records_without_human_verified_metadata": len(no_human_metadata),
        "pending_metadata_citation_occurrences": states["pending-metadata-review"],
        "unreviewed_claim_source_leads": claim_leads,
        "potential_work_metadata_conflict_groups": len(conflicts),
    }
    return {
        "schema_version": 1,
        "catalog_version": catalog_version,
        "corpus_date": corpus_date,
        "scope": "Merged catalog; local semantic and claim evidence databases excluded",
        "limitations": (
            "A source metadata conflict is a human review lead, not proof of an error. "
            "A complete profile, primary-source role, DOI resolution, or metadata "
            "verification does not establish support for a research claim."
        ),
        "summary": summary,
        "classification_fragmentation": {
            "domains": _categories(str(record["domain"]) for record in items),
            "status_phrases": _categories(str(record["status"]) for record in items),
            "citation_authority_roles": _categories(
                str(citation["authority"]) for _, citation in citations
            ),
        },
        "citation_verification_counts": dict(sorted(states.items())),
        "editorial_queues": {
            "incomplete_profile_record_ids": missing_profiles,
            "no_primary_anchor_record_ids": no_primary,
            "no_human_verified_metadata_record_ids": no_human_metadata,
        },
        "potential_work_metadata_conflicts": conflicts,
    }
