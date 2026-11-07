"""Read-only deterministic work queues: never human approval or claim evidence."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .data_quality import data_quality_report
from .profile_quality import profile_quality_report


def editorial_triage_report(records: Iterable[Mapping[str, Any]], *,
                            catalog_version: str, corpus_date: str,
                            profile_limit: int = 25) -> dict[str, Any]:
    """Select a bounded draft profile tranche; retain every unreviewed citation lead."""
    if isinstance(profile_limit, bool) or not isinstance(profile_limit, int) or profile_limit < 1:
        raise ValueError("profile_limit must be a positive integer")
    items = sorted(records, key=lambda record: str(record["id"]))
    profiles = profile_quality_report(items, catalog_version=catalog_version,
                                      corpus_date=corpus_date)
    quality = data_quality_report(items, catalog_version=catalog_version,
                                  corpus_date=corpus_date)
    pending: list[dict[str, Any]] = []
    leads: list[dict[str, str]] = []
    for record in items:
        record_id = str(record["id"])
        for citation in record["citations"]:
            if (citation.get("verification") or "pending-metadata-review") != "pending-metadata-review":
                continue
            pending.append({
                "record_id": record_id,
                "source_key": str(citation.get("doi") or citation["url"]),
                "citation_url": str(citation["url"]),
                "title_as_cited": str(citation.get("title") or ""),
                "year_as_cited": str(citation.get("year") or ""),
                "review_state": "pending-metadata-review",
            })
        for claim in record.get("claim_reviews", []):
            for lead in claim.get("citations", []):
                if lead.get("review_state") != "unreviewed":
                    continue
                leads.append({
                    "record_id": record_id,
                    "claim_id": str(claim["id"]),
                    "field": str(claim["field"]),
                    "source_uid": str(lead.get("source_uid") or ""),
                    "citation_url": str(lead["citation_url"]),
                    "review_state": "unreviewed",
                })
    pending.sort(key=lambda r: (r["record_id"], r["source_key"].casefold(), r["citation_url"]))
    leads.sort(key=lambda r: (r["record_id"], r["claim_id"], r["source_uid"], r["citation_url"]))
    tranche = profiles["backlog"][:profile_limit]
    conflicts = quality["potential_work_metadata_conflicts"]
    return {
        "schema_version": 1,
        "catalog_version": catalog_version,
        "corpus_date": corpus_date,
        "queue_state": "unreviewed-human-work",
        "independent_approvals": 0,
        "relationship_synthesis_locked": True,
        "limitations": "Read-only triage, not bibliographic or claim verification. No independent approval is granted.",
        "summary": {
            "record_count": len(items),
            "incomplete_profiles_total": len(profiles["backlog"]),
            "proposed_profile_tranche_count": len(tranche),
            "pending_citation_occurrences": len(pending),
            "potential_work_identity_conflict_groups": len(conflicts),
            "unreviewed_claim_source_leads": len(leads),
        },
        "proposed_profile_tranche": tranche,
        "pending_citation_review_queue": pending,
        "potential_work_identity_conflicts": conflicts,
        "claim_source_lead_review_queue": leads,
    }
