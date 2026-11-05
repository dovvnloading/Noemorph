"""Deterministic, provenance-conscious research-profile completeness report.

The score ranks outstanding *editorial work*, never scientific validity.
A complete prose profile and a resolvable DOI are not claim-level verification.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping

REQUIRED_PROFILE_FIELDS = (
    "claim_scope",
    "boundary_note",
    "evidence_profile",
    "open_questions",
)
REPORT_SCHEMA_VERSION = 1


def _has_content(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value) and any(_has_content(v) for v in value.values())
    if isinstance(value, (tuple, list)):
        return bool(value) and any(_has_content(v) for v in value)
    return value is not None and bool(value)


def profile_quality_report(
    records: Iterable[Mapping[str, Any]],
    *,
    catalog_version: str,
    corpus_date: str,
) -> dict[str, Any]:
    """Compute a stable report from validated merged records, without network access."""
    items = sorted(records, key=lambda r: str(r["id"]))
    if len({str(record["id"]) for record in items}) != len(items):
        raise ValueError("Cannot assess profile quality with duplicate record IDs")
    gaps_by_field: Counter[str] = Counter()
    citation_states: Counter[str] = Counter()
    by_kind: dict[str, dict[str, int | str]] = {}
    backlog: list[dict[str, Any]] = []
    complete = 0
    citation_total = 0

    for record in items:
        kind = str(record["kind"])
        kind_row = by_kind.setdefault(kind, {
            "kind": kind,
            "records": 0,
            "complete_profiles": 0,
            "incomplete_profiles": 0,
            "records_with_pending_citations": 0,
            "records_with_no_primary_anchor": 0,
        })
        kind_row["records"] += 1
        missing = [
            field for field in REQUIRED_PROFILE_FIELDS
            if not _has_content(record.get(field))
        ]
        citations = record["citations"]
        citation_total += len(citations)
        citation_states.update(
            str(citation.get("verification") or "pending-metadata-review")
            for citation in citations
        )
        pending = sum(
            (citation.get("verification") or "pending-metadata-review")
            == "pending-metadata-review" for citation in citations
        )
        has_primary = any(
            str(citation.get("authority", "")).startswith("primary-")
            for citation in citations
        )
        if pending:
            kind_row["records_with_pending_citations"] += 1
        if not has_primary:
            kind_row["records_with_no_primary_anchor"] += 1
        if not missing:
            complete += 1
            kind_row["complete_profiles"] += 1
            continue

        kind_row["incomplete_profiles"] += 1
        gaps_by_field.update(missing)
        # Review-workload triage only: four missing fields dominate the score.
        # Bibliographic risks break ties; these are not measures of truth.
        priority = (
            10 * len(missing)
            + 3 * min(pending, 3)
            + (2 if not has_primary else 0)
            + (1 if len(citations) <= 2 else 0)
        )
        backlog.append({
            "id": str(record["id"]),
            "name": str(record["name"]),
            "kind": kind,
            "domain": str(record["domain"]),
            "missing_fields": missing,
            "missing_field_count": len(missing),
            "pending_metadata_citations": pending,
            "has_primary_citation": has_primary,
            "citation_count": len(citations),
            "triage_priority": priority,
        })

    backlog.sort(
        key=lambda item: (
            -item["triage_priority"],
            item["kind"].casefold(),
            item["name"].casefold(),
            item["id"],
        )
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "catalog_version": catalog_version,
        "corpus_date": corpus_date,
        "method": (
            "Read-only profiling of merged catalog records. Four required fields "
            "must contain nonempty material; citation statuses and authority "
            "roles are descriptive metadata and do not validate claims."
        ),
        "limitations": (
            "Profile completeness measures editorial depth, not evidential "
            "support, scientific merit, coverage exhaustiveness, or verification. "
            "Triage priority ranks missing editorial work and source-metadata "
            "follow-up; it does not rank theories or patients."
        ),
        "required_profile_fields": list(REQUIRED_PROFILE_FIELDS),
        "triage_formula": (
            "10 * missing_required_fields + 3 * min(pending_metadata_citations, 3) "
            "+ (2 if no primary-authority citation else 0) "
            "+ (1 if citation_count <= 2 else 0)"
        ),
        "summary": {
            "record_count": len(items),
            "complete_profiles": complete,
            "incomplete_profiles": len(items) - complete,
            "completion_percent": round(100 * complete / len(items), 1) if items else 0,
            "citation_occurrences": citation_total,
            "citation_verification_counts": dict(sorted(citation_states.items())),
            "missing_required_field_counts": {
                field: gaps_by_field[field] for field in REQUIRED_PROFILE_FIELDS
            },
        },
        "by_kind": [by_kind[k] for k in sorted(by_kind, key=str.casefold)],
        "backlog": backlog,
    }
