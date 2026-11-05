"""Review-only, claim-level citation leads for the research collection.

A bibliographic link is *not* an assertion that a source supports a claim.
The initial registry is deliberately restricted to unreviewed source-URL leads.
In-source passage review must be implemented independently before promotion.
"""
from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any


class ClaimReviewIntegrityError(ValueError):
    """A claim-review lead is malformed or references the wrong catalog record."""


CLAIM_FIELDS = {
    "claim_scope.target": "scope",
    "claim_scope.does_not_establish": "boundary",
    "boundary_note": "boundary",
    "summary": "scope",
}


def stable_source_uid(citation: Mapping[str, Any]) -> str:
    """Order-independent identifier; legacy sequential source IDs stay unchanged."""
    source_key = citation.get("doi") or citation.get("url")
    if not isinstance(source_key, str) or not source_key.strip():
        raise ClaimReviewIntegrityError("Citation needs a DOI or URL for source identity")
    digest = hashlib.sha256(source_key.casefold().encode("utf-8")).hexdigest()
    return f"work-{digest[:24]}"


def _field_value(record: Mapping[str, Any], path: str) -> str:
    if path not in CLAIM_FIELDS:
        raise ClaimReviewIntegrityError(f"Unsupported claim field: {path}")
    value: Any = record
    for part in path.split("."):
        if not isinstance(value, dict):
            raise ClaimReviewIntegrityError(f"Claim field {path} is not an object path")
        value = value.get(part)
    if not isinstance(value, str) or not value.strip():
        raise ClaimReviewIntegrityError(f"Claim field {path} must have nonempty text")
    return value


def apply_claim_review_supplement(
    records_by_id: dict[str, dict[str, Any]], payload: Any
) -> dict[str, Any]:
    """Attach validated, never-promoted review leads to an existing merged catalog.

    The caller loads this after profile enrichments, so source URLs and field
    values reflect the fully merged record. No canonical catalog claims change.
    """
    if not isinstance(payload, dict) or set(payload) != {"collection", "records"}:
        raise ClaimReviewIntegrityError(
            "Claim review supplement must contain only collection and records"
        )
    collection = payload.get("collection")
    items = payload.get("records")
    if not isinstance(collection, dict) or not isinstance(items, list):
        raise ClaimReviewIntegrityError("Claim review needs collection and records")
    required_metadata = {"name", "created", "review_state", "method", "limits"}
    if set(collection) != required_metadata or any(
        not isinstance(collection[key], str) or not collection[key].strip()
        for key in required_metadata
    ):
        raise ClaimReviewIntegrityError(
            "Claim review metadata must contain only complete descriptive fields"
        )
    if collection.get("review_state") != "unreviewed-source-leads":
        raise ClaimReviewIntegrityError(
            "Claim review supplement must explicitly remain unreviewed-source-leads"
        )

    seen_records: set[str] = set()
    claim_count = 0
    lead_count = 0
    for item in items:
        if not isinstance(item, dict) or set(item) != {"id", "claims"}:
            raise ClaimReviewIntegrityError("Each claim-review record needs id and claims")
        record_id = item["id"]
        if not isinstance(record_id, str) or record_id not in records_by_id:
            raise ClaimReviewIntegrityError(f"Unknown claim-review record: {record_id}")
        if record_id in seen_records or "claim_reviews" in records_by_id[record_id]:
            raise ClaimReviewIntegrityError(f"Duplicate claim-review record: {record_id}")
        seen_records.add(record_id)
        record = records_by_id[record_id]
        citations_by_url = {
            citation["url"]: citation for citation in record["citations"]
        }
        claims = item["claims"]
        if not isinstance(claims, list) or not claims:
            raise ClaimReviewIntegrityError(f"Record {record_id} needs nonempty claims")

        seen_claims: set[str] = set()
        normalized_claims: list[dict[str, Any]] = []
        for claim in claims:
            if not isinstance(claim, dict) or set(claim) != {
                "id", "field", "kind", "citations"
            }:
                raise ClaimReviewIntegrityError(
                    f"Claim for {record_id} needs id, field, kind, and citations"
                )
            claim_id = claim["id"]
            if (
                not isinstance(claim_id, str)
                or not claim_id.startswith(f"{record_id}:")
                or len(claim_id) > 180
                or claim_id in seen_claims
            ):
                raise ClaimReviewIntegrityError(
                    f"Claim ID must be unique and scoped to {record_id}: {claim_id}"
                )
            seen_claims.add(claim_id)
            field = claim["field"]
            if not isinstance(field, str) or claim["kind"] != CLAIM_FIELDS.get(field):
                raise ClaimReviewIntegrityError(
                    f"Claim {claim_id} has an unsupported field/kind pairing"
                )
            text = _field_value(record, field)
            leads = claim["citations"]
            if not isinstance(leads, list) or not leads:
                raise ClaimReviewIntegrityError(f"Claim {claim_id} needs citation leads")
            normalized_leads: list[dict[str, str]] = []
            used_urls: set[str] = set()
            for lead in leads:
                if not isinstance(lead, dict) or set(lead) != {
                    "citation_url", "locator_kind", "review_state"
                }:
                    raise ClaimReviewIntegrityError(
                        f"Claim {claim_id} has an invalid citation lead"
                    )
                url = lead["citation_url"]
                if not isinstance(url, str) or url not in citations_by_url:
                    raise ClaimReviewIntegrityError(
                        f"Claim {claim_id} references a citation absent from its record"
                    )
                if url in used_urls:
                    raise ClaimReviewIntegrityError(
                        f"Claim {claim_id} repeats citation {url}"
                    )
                used_urls.add(url)
                if (
                    lead["locator_kind"] != "source-url-only"
                    or lead["review_state"] != "unreviewed"
                ):
                    raise ClaimReviewIntegrityError(
                        f"Claim {claim_id} cannot assert passage verification or support"
                    )
                normalized_leads.append(
                    {
                        **lead,
                        "source_uid": stable_source_uid(citations_by_url[url]),
                    }
                )
                lead_count += 1
            normalized_claims.append(
                {
                    "id": claim_id,
                    "field": field,
                    "kind": claim["kind"],
                    "text": text,
                    "citations": normalized_leads,
                    "review_state": "unreviewed",
                }
            )
            claim_count += 1
        records_by_id[record_id] = {
            **record,
            "claim_reviews": normalized_claims,
        }
    return {
        **collection,
        "record_count": len(seen_records),
        "claim_count": claim_count,
        "source_lead_count": lead_count,
    }
