from __future__ import annotations

import json
import threading
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .profile_quality import profile_quality_report

from .claim_evidence import (
    ClaimReviewIntegrityError,
    apply_claim_review_supplement,
    stable_source_uid,
)


class CatalogIntegrityError(RuntimeError):
    """Raised when the curated corpus violates a publication invariant."""


RECORD_KINDS = {
    "Scientific theory",
    "Model or framework",
    "Clinical / state model",
    "Theory of mind / social cognition",
    "Phenomenological construct",
    "Philosophical position",
    "Argument / challenge",
    "Historical tradition",
}
VERIFICATION_STATES = {
    "doi-resolved",
    "locator-recorded",
    "human-verified",
    "pending-metadata-review",
}


def _identity_text(value: Any) -> str:
    """Normalize comparison text, never overwrite the original bibliography."""
    return " ".join(str(value or "").casefold().split())


DISCOVERY_MATCH_STATES = {
    "likely-present",
    "possible-match",
    "not-matched",
    "not-applicable",
}
PROFILE_ENRICHMENT_FIELDS = {
    "status_note",
    "scope",
    "keywords",
    "boundary_note",
    "claim_scope",
    "evidence_profile",
    "open_questions",
    "review_state",
}


@dataclass(frozen=True)
class CatalogSnapshot:
    metadata: dict[str, Any]
    records: tuple[dict[str, Any], ...]
    by_id: dict[str, dict[str, Any]]
    sources: tuple[dict[str, Any], ...]


class CatalogRepository:
    """Thread-safe reader for the versioned, citation-first research corpus.

    The JSON corpus is intentionally the auditable publication artifact for this
    collection phase. A claim-centric relational ingestion store can be introduced
    without changing this read API once the review workflow grows.
    """

    def __init__(self, catalog_path: Path) -> None:
        self.catalog_path = catalog_path
        self.discovery_path = catalog_path.parent / "discovery-closer-to-truth.json"
        self._lock = threading.RLock()
        self._source_mtimes: tuple[tuple[str, int], ...] = ()
        self._supplement_paths: tuple[Path, ...] = ()
        self._profile_paths: tuple[Path, ...] = ()
        self._claim_review_paths: tuple[Path, ...] = ()
        self._snapshot: CatalogSnapshot | None = None
        self._discovery_mtime: int | None = None
        self._discovery_payload: dict[str, Any] | None = None

    def _load_if_changed(self) -> CatalogSnapshot:
        with self._lock:
            known_paths = (
                self.catalog_path,
                *self._supplement_paths,
                *self._profile_paths,
                *self._claim_review_paths,
            )
            try:
                known_mtimes = tuple(
                    (str(path), path.stat().st_mtime_ns) for path in known_paths
                )
            except FileNotFoundError as exc:
                raise CatalogIntegrityError(
                    f"Catalog data is missing: {exc.filename or self.catalog_path}"
                ) from exc

            if self._snapshot is not None and self._source_mtimes == known_mtimes:
                return self._snapshot

            payload = json.loads(self.catalog_path.read_text(encoding="utf-8"))
            supplement_names = payload.get("supplements", [])
            if not isinstance(supplement_names, list) or not all(
                isinstance(name, str) for name in supplement_names
            ):
                raise CatalogIntegrityError("Catalog supplements must be a list of filenames")
            profile_names = payload.get("profile_enrichments", [])
            if not isinstance(profile_names, list) or not all(
                isinstance(name, str) for name in profile_names
            ):
                raise CatalogIntegrityError(
                    "Catalog profile_enrichments must be a list of filenames"
                )

            claim_review_names = payload.get("claim_review_supplements", [])
            if not isinstance(claim_review_names, list) or not all(
                isinstance(name, str) for name in claim_review_names
            ):
                raise CatalogIntegrityError(
                    "Catalog claim_review_supplements must be a list of filenames"
                )

            catalog_directory = self.catalog_path.parent.resolve()
            supplement_paths: list[Path] = []
            for name in supplement_names:
                candidate = (self.catalog_path.parent / name).resolve()
                if candidate.parent != catalog_directory or candidate.suffix.lower() != ".json":
                    raise CatalogIntegrityError(
                        f"Catalog supplement must be a sibling JSON file: {name}"
                    )
                supplement_paths.append(candidate)

            profile_paths: list[Path] = []
            for name in profile_names:
                candidate = (self.catalog_path.parent / name).resolve()
                if candidate.parent != catalog_directory or candidate.suffix.lower() != ".json":
                    raise CatalogIntegrityError(
                        f"Catalog profile enrichment must be a sibling JSON file: {name}"
                    )
                profile_paths.append(candidate)

            claim_review_paths: list[Path] = []
            for name in claim_review_names:
                candidate = (self.catalog_path.parent / name).resolve()
                if candidate.parent != catalog_directory or candidate.suffix.lower() != ".json":
                    raise CatalogIntegrityError(
                        f"Claim review supplement must be a sibling JSON file: {name}"
                    )
                claim_review_paths.append(candidate)

            merged_records = list(payload.get("records", []))
            collection_manifests: list[dict[str, Any]] = []
            for path in supplement_paths:
                try:
                    supplement = json.loads(path.read_text(encoding="utf-8"))
                except FileNotFoundError as exc:
                    raise CatalogIntegrityError(
                        f"Catalog supplement is missing: {path}"
                    ) from exc
                if not isinstance(supplement, dict) or not isinstance(
                    supplement.get("records"), list
                ):
                    raise CatalogIntegrityError(
                        f"Catalog supplement needs a records array: {path.name}"
                    )
                merged_records.extend(supplement["records"])
                manifest = supplement.get("collection", {})
                if not isinstance(manifest, dict):
                    raise CatalogIntegrityError(
                        f"Catalog supplement collection must be an object: {path.name}"
                    )
                collection_manifests.append(
                    {
                        **manifest,
                        "file": path.name,
                        "record_count": len(supplement["records"]),
                    }
                )

            if any(
                isinstance(record, dict) and "claim_reviews" in record
                for record in merged_records
            ):
                raise CatalogIntegrityError(
                    "Claim reviews may only be added through validated claim_review_supplements"
                )

            profile_manifests: list[dict[str, Any]] = []
            record_by_id = {str(record.get("id")): record for record in merged_records}
            enriched_ids: set[str] = set()
            for path in profile_paths:
                try:
                    enrichment = json.loads(path.read_text(encoding="utf-8"))
                except FileNotFoundError as exc:
                    raise CatalogIntegrityError(
                        f"Catalog profile enrichment is missing: {path}"
                    ) from exc
                profiles = enrichment.get("profiles") if isinstance(enrichment, dict) else None
                if not isinstance(profiles, list):
                    raise CatalogIntegrityError(
                        f"Catalog profile enrichment needs a profiles array: {path.name}"
                    )
                manifest = enrichment.get("collection", {})
                if not isinstance(manifest, dict):
                    raise CatalogIntegrityError(
                        f"Catalog profile enrichment collection must be an object: {path.name}"
                    )
                profile_manifests.append(
                    {
                        **manifest,
                        "file": path.name,
                        "profile_count": len(profiles),
                    }
                )
                for index, profile in enumerate(profiles):
                    if not isinstance(profile, dict) or not isinstance(profile.get("id"), str):
                        raise CatalogIntegrityError(
                            f"Profile {index} in {path.name} needs a string id"
                        )
                    record_id = profile["id"]
                    if record_id not in record_by_id:
                        raise CatalogIntegrityError(
                            f"Profile enrichment targets unknown record: {record_id}"
                        )
                    if record_id in enriched_ids:
                        raise CatalogIntegrityError(
                            f"Record has more than one profile enrichment: {record_id}"
                        )
                    enriched_ids.add(record_id)
                    unsupported = set(profile) - PROFILE_ENRICHMENT_FIELDS - {
                        "id",
                        "citation_additions",
                    }
                    if unsupported:
                        raise CatalogIntegrityError(
                            f"Profile enrichment {record_id} changes unsupported fields: "
                            f"{', '.join(sorted(unsupported))}"
                        )
                    citation_additions = profile.get("citation_additions", [])
                    if not isinstance(citation_additions, list):
                        raise CatalogIntegrityError(
                            f"Profile enrichment {record_id} citation_additions must be a list"
                        )
                    current = record_by_id[record_id]
                    patched = {
                        **current,
                        **{
                            key: value
                            for key, value in profile.items()
                            if key in PROFILE_ENRICHMENT_FIELDS
                        },
                        "citations": [
                            *current.get("citations", []),
                            *citation_additions,
                        ],
                    }
                    record_by_id[record_id] = patched
            if profile_paths:
                merged_records = [record_by_id[str(record.get("id"))] for record in merged_records]

            claim_review_manifests: list[dict[str, Any]] = []
            for path in claim_review_paths:
                try:
                    review_payload = json.loads(path.read_text(encoding="utf-8"))
                except FileNotFoundError as exc:
                    raise CatalogIntegrityError(
                        f"Claim review supplement is missing: {path}"
                    ) from exc
                try:
                    manifest = apply_claim_review_supplement(
                        record_by_id, review_payload
                    )
                except ClaimReviewIntegrityError as exc:
                    raise CatalogIntegrityError(
                        f"Invalid claim review supplement {path.name}: {exc}"
                    ) from exc
                claim_review_manifests.append({**manifest, "file": path.name})
            if claim_review_paths:
                merged_records = [
                    record_by_id[str(record.get("id"))] for record in merged_records
                ]

            metadata = payload.get("metadata")
            if isinstance(metadata, dict):
                metadata = {
                    **metadata,
                    "collections": collection_manifests,
                    "profile_collections": profile_manifests,
                    "claim_review_collections": claim_review_manifests,
                }
            merged_payload = {"metadata": metadata, "records": merged_records}
            snapshot = self._validate(merged_payload)
            self._snapshot = snapshot
            self._supplement_paths = tuple(supplement_paths)
            self._profile_paths = tuple(profile_paths)
            self._claim_review_paths = tuple(claim_review_paths)
            self._source_mtimes = tuple(
                (str(path), path.stat().st_mtime_ns)
                for path in (
                    self.catalog_path,
                    *self._supplement_paths,
                    *self._profile_paths,
                    *self._claim_review_paths,
                )
            )
            return snapshot

    @staticmethod
    def _validate(payload: dict[str, Any]) -> CatalogSnapshot:
        if not isinstance(payload, dict):
            raise CatalogIntegrityError("Catalog root must be an object")

        metadata = payload.get("metadata")
        records = payload.get("records")
        if not isinstance(metadata, dict) or not isinstance(records, list):
            raise CatalogIntegrityError("Catalog needs metadata and records")

        required_record_fields = {
            "id",
            "name",
            "kind",
            "domain",
            "tradition",
            "status",
            "summary",
            "proponents",
            "citations",
        }
        by_id: dict[str, dict[str, Any]] = {}
        id_by_name: dict[str, str] = {}
        source_by_key: dict[str, dict[str, Any]] = {}

        for index, record in enumerate(records):
            if not isinstance(record, dict):
                raise CatalogIntegrityError(f"Record {index} is not an object")
            missing = sorted(required_record_fields - record.keys())
            if missing:
                raise CatalogIntegrityError(
                    f"Record {index} is missing required fields: {', '.join(missing)}"
                )
            record_id = str(record["id"])
            if record_id in by_id:
                raise CatalogIntegrityError(f"Duplicate record id: {record_id}")
            normalized_name = " ".join(str(record["name"]).casefold().split())
            if normalized_name in id_by_name:
                raise CatalogIntegrityError(
                    f"Duplicate record name: {record['name']} ({id_by_name[normalized_name]}, {record_id})"
                )
            id_by_name[normalized_name] = record_id
            if record["kind"] not in RECORD_KINDS:
                raise CatalogIntegrityError(
                    f"Record {record_id} has unsupported kind: {record['kind']}"
                )
            citations = record.get("citations")
            if not isinstance(citations, list) or len(citations) < 2:
                raise CatalogIntegrityError(
                    f"Record {record_id} needs at least two citation locators"
                )

            normalized_citations: list[dict[str, Any]] = []
            citation_keys: set[str] = set()
            for citation_index, citation in enumerate(citations):
                if not isinstance(citation, dict):
                    raise CatalogIntegrityError(
                        f"Citation {citation_index} on {record_id} is not an object"
                    )
                for field in ("title", "authors", "year", "url", "authority"):
                    if field not in citation:
                        raise CatalogIntegrityError(
                            f"Citation {citation_index} on {record_id} lacks {field}"
                        )
                if not str(citation["url"]).startswith("https://"):
                    raise CatalogIntegrityError(
                        f"Citation {citation_index} on {record_id} is not HTTPS"
                    )
                verification = citation.get("verification", "pending-metadata-review")
                if verification not in VERIFICATION_STATES:
                    raise CatalogIntegrityError(
                        f"Citation {citation_index} on {record_id} has unsupported verification: {verification}"
                    )
                source_key = str(citation.get("doi") or citation["url"]).lower()
                source_uid = stable_source_uid(citation)
                if source_key in citation_keys:
                    raise CatalogIntegrityError(
                        f"Record {record_id} repeats citation locator {citation['url']}"
                    )
                citation_keys.add(source_key)
                source_id = f"src-{len(source_by_key) + 1:04d}"
                if source_key in source_by_key:
                    source_id = source_by_key[source_key]["id"]
                else:
                    source = {
                        "id": source_id,
                        "source_uid": source_uid,
                        "title": citation["title"],
                        "authors": citation["authors"],
                        "year": citation["year"],
                        "url": citation["url"],
                        "doi": citation.get("doi"),
                        "venue": citation.get("venue"),
                        "retrieved": citation.get("retrieved"),
                        "used_by": [],
                        "uses": [],
                        "authority_roles": [],
                        "verification_states": [],
                        "_bibliographic_uses": [],
                    }
                    source_by_key[source_key] = source
                source_by_key[source_key]["used_by"].append(record_id)
                source_by_key[source_key]["_bibliographic_uses"].append(
                    {
                        "record_id": record_id,
                        "title": citation["title"],
                        "authors": citation["authors"],
                        "year": citation["year"],
                        "url": citation["url"],
                        "doi": citation.get("doi"),
                        "venue": citation.get("venue"),
                        "retrieved": citation.get("retrieved"),
                    }
                )
                source_by_key[source_key]["uses"].append(
                    {
                        "record_id": record_id,
                        "authority": citation["authority"],
                        "verification": verification,
                        "url": citation["url"],
                    }
                )
                normalized_citations.append(
                    {**citation, "source_id": source_id, "source_uid": source_uid}
                )

            normalized = {**record, "id": record_id, "citations": normalized_citations}
            by_id[record_id] = normalized

        # Authority and verification belong to a citation use, not the work.
        # Preserve all roles/states rather than inheriting the first citation's values.
        for source in source_by_key.values():
            source["authority_roles"] = sorted(
                {use["authority"] for use in source["uses"]}
            )
            source["verification_states"] = sorted(
                {use["verification"] for use in source["uses"]}
            )
            bibliographic_uses = source.pop("_bibliographic_uses")
            conflict_fields = [
                field
                for field in ("title", "year")
                if len({_identity_text(use[field]) for use in bibliographic_uses}) > 1
            ]
            source["metadata_conflict_fields"] = conflict_fields
            source["work_identity_review_state"] = (
                "needs-review" if conflict_fields else "unreviewed"
            )
            # Keep legacy first-use display metadata and source IDs unchanged.
            # Record every conflicting variant so a scholar can reconcile it;
            # no variant is silently promoted to canonical or human-verified.
            variants: dict[str, dict[str, Any]] = {}
            if conflict_fields:
                for use in bibliographic_uses:
                    bibliographic_metadata = {
                        field: use[field]
                        for field in ("title", "authors", "year", "url", "doi", "venue", "retrieved")
                    }
                    signature = json.dumps(
                        bibliographic_metadata, sort_keys=True, ensure_ascii=False
                    )
                    if signature not in variants:
                        variants[signature] = {
                            **bibliographic_metadata, "record_ids": []
                        }
                    variants[signature]["record_ids"].append(use["record_id"])
            source["metadata_variants"] = sorted(
                [
                    {**variant, "record_ids": sorted(set(variant["record_ids"]))}
                    for variant in variants.values()
                ],
                key=lambda variant: (
                    _identity_text(variant["title"]),
                    _identity_text(variant["year"]),
                    _identity_text(variant["authors"]),
                    variant["url"],
                ),
            )

        normalized_records = tuple(by_id.values())
        return CatalogSnapshot(
            metadata=metadata,
            records=normalized_records,
            by_id=by_id,
            sources=tuple(source_by_key.values()),
        )

    def metadata(self) -> dict[str, Any]:
        return dict(self._load_if_changed().metadata)

    def _load_discovery(self) -> dict[str, Any]:
        """Load the acquisition registry without conflating it with reviewed records."""
        with self._lock:
            try:
                mtime = self.discovery_path.stat().st_mtime_ns
            except FileNotFoundError:
                return {
                    "collection": {
                        "availability": "unavailable",
                        "entry_count": 0,
                        "notice": "The optional third-party discovery registry is not included in this installation.",
                    },
                    "entries": [],
                    "errors": [],
                }
            if self._discovery_payload is not None and self._discovery_mtime == mtime:
                return self._discovery_payload

            payload = json.loads(self.discovery_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or not isinstance(payload.get("entries"), list):
                raise CatalogIntegrityError(
                    "Closer to Truth discovery registry needs an entries array"
                )
            collection = payload.get("collection")
            errors = payload.get("errors")
            if not isinstance(collection, dict) or not isinstance(errors, list):
                raise CatalogIntegrityError(
                    "Closer to Truth discovery registry needs collection metadata and an errors array"
                )
            if collection.get("entry_count") != len(payload["entries"]):
                raise CatalogIntegrityError("Discovery entry count does not match its manifest")
            if collection.get("error_count") != len(errors):
                raise CatalogIntegrityError("Discovery error count does not match its manifest")

            required = {
                "slug",
                "name",
                "url",
                "entry_type",
                "category",
                "description",
                "verified_by_source",
                "proponents",
                "key_takeaways",
                "references",
                "catalog_match",
            }
            seen_slugs: set[str] = set()
            match_counts: Counter[str] = Counter()
            catalog_ids = set(self._load_if_changed().by_id)
            for index, entry in enumerate(payload["entries"]):
                if not isinstance(entry, dict):
                    raise CatalogIntegrityError(f"Discovery entry {index} is not an object")
                missing = required - entry.keys()
                if missing:
                    raise CatalogIntegrityError(
                        f"Discovery entry {index} is missing: {', '.join(sorted(missing))}"
                    )
                slug = entry["slug"]
                if not isinstance(slug, str) or not slug:
                    raise CatalogIntegrityError(f"Discovery entry {index} has no slug")
                if slug in seen_slugs:
                    raise CatalogIntegrityError(f"Duplicate discovery slug: {slug}")
                seen_slugs.add(slug)
                if entry["url"] != f"https://loc.closertotruth.com/theory/{slug}":
                    raise CatalogIntegrityError(f"Unexpected discovery locator on {slug}")
                if entry["entry_type"] not in {"theory", "overview", "collection"}:
                    raise CatalogIntegrityError(f"Unexpected discovery entry type on {slug}")
                if not isinstance(entry["verified_by_source"], bool):
                    raise CatalogIntegrityError(f"Invalid source verification badge on {slug}")
                for field in ("proponents", "key_takeaways", "references"):
                    if not isinstance(entry[field], list):
                        raise CatalogIntegrityError(f"Discovery {field} must be an array on {slug}")

                match = entry["catalog_match"]
                if not isinstance(match, dict) or match.get("status") not in DISCOVERY_MATCH_STATES:
                    raise CatalogIntegrityError(f"Invalid discovery title screen on {slug}")
                score = match.get("score")
                if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 1:
                    raise CatalogIntegrityError(f"Invalid discovery title-screen score on {slug}")
                match_counts[str(match["status"])] += 1
                record_id = match.get("record_id")
                if record_id is not None and record_id not in catalog_ids:
                    raise CatalogIntegrityError(
                        f"Discovery title screen on {slug} points to missing record {record_id}"
                    )
                if match["status"] == "not-applicable" and (
                    record_id is not None or match.get("record_name") is not None or score != 0
                ):
                    raise CatalogIntegrityError(
                        f"Non-applicable discovery screen retains an identity candidate on {slug}"
                    )

                for reference in entry["references"]:
                    if not isinstance(reference, dict) or not isinstance(reference.get("locators"), list):
                        raise CatalogIntegrityError(f"Invalid discovery reference on {slug}")
                    for locator in reference["locators"]:
                        if (
                            not isinstance(locator, str)
                            or not locator.startswith("https://")
                            or ", https://" in locator
                            or "utm_" in locator.casefold()
                        ):
                            raise CatalogIntegrityError(
                                f"Malformed discovery reference locator on {slug}"
                            )

            declared_match_counts = collection.get("catalog_match_counts")
            actual_match_counts = {
                state: match_counts.get(state, 0) for state in DISCOVERY_MATCH_STATES
            }
            if declared_match_counts != actual_match_counts:
                raise CatalogIntegrityError(
                    "Discovery title-screen counts do not match the registry entries"
                )

            self._discovery_payload = payload
            self._discovery_mtime = mtime
            return payload

    def discovery_metadata(self) -> dict[str, Any]:
        return dict(self._load_discovery().get("collection", {}))

    def list_discovery_entries(
        self,
        *,
        query: str | None = None,
        categories: Iterable[str] = (),
        match_statuses: Iterable[str] = (),
        offset: int = 0,
        limit: int = 500,
    ) -> tuple[list[dict[str, Any]], int]:
        payload = self._load_discovery()
        query_terms = tuple((query or "").casefold().split())
        category_set = {value.casefold() for value in categories if value}
        status_set = {value.casefold() for value in match_statuses if value}

        def text(value: Any) -> str:
            if isinstance(value, dict):
                return " ".join(text(item) for item in value.values())
            if isinstance(value, list):
                return " ".join(text(item) for item in value)
            return str(value or "")

        def matches(entry: dict[str, Any]) -> bool:
            if category_set and str(entry.get("category", "")).casefold() not in category_set:
                return False
            match_status = str(entry.get("catalog_match", {}).get("status", ""))
            if status_set and match_status.casefold() not in status_set:
                return False
            if not query_terms:
                return True
            haystack = " ".join(
                (
                    str(entry.get("name", "")),
                    str(entry.get("description", "")),
                    str(entry.get("category", "")),
                    text(entry.get("proponents", [])),
                    text(entry.get("key_takeaways", [])),
                    text(entry.get("references", [])),
                )
            ).casefold()
            return all(term in haystack for term in query_terms)

        filtered = [entry for entry in payload["entries"] if matches(entry)]
        filtered.sort(key=lambda entry: str(entry["name"]).casefold())
        total = len(filtered)
        safe_offset = max(offset, 0)
        safe_limit = min(max(limit, 1), 1000)
        return filtered[safe_offset : safe_offset + safe_limit], total

    def get(self, record_id: str) -> dict[str, Any] | None:
        return self._load_if_changed().by_id.get(record_id)

    def list_records(
        self,
        *,
        query: str | None = None,
        kinds: Iterable[str] = (),
        domains: Iterable[str] = (),
        statuses: Iterable[str] = (),
        traditions: Iterable[str] = (),
        offset: int = 0,
        limit: int = 500,
    ) -> tuple[list[dict[str, Any]], int]:
        snapshot = self._load_if_changed()
        query_terms = tuple((query or "").casefold().split())
        kind_set = {item.casefold() for item in kinds if item}
        domain_set = {item.casefold() for item in domains if item}
        status_set = {item.casefold() for item in statuses if item}
        tradition_set = {item.casefold() for item in traditions if item}

        def research_text(value: Any) -> str:
            if isinstance(value, dict):
                return " ".join(
                    f"{key} {research_text(item)}" for key, item in value.items()
                )
            if isinstance(value, (list, tuple)):
                return " ".join(research_text(item) for item in value)
            return str(value or "")

        def matches(record: dict[str, Any]) -> bool:
            if kind_set and str(record["kind"]).casefold() not in kind_set:
                return False
            if domain_set and str(record["domain"]).casefold() not in domain_set:
                return False
            if status_set and str(record["status"]).casefold() not in status_set:
                return False
            if tradition_set and str(record["tradition"]).casefold() not in tradition_set:
                return False
            if query_terms:
                haystack = " ".join(
                    [
                        str(record.get("name", "")),
                        str(record.get("summary", "")),
                        " ".join(record.get("aliases", [])),
                        " ".join(record.get("proponents", [])),
                        " ".join(record.get("keywords", [])),
                        research_text(record.get("claim_scope", "")),
                        str(record.get("boundary_note", "")),
                        research_text(record.get("evidence_profile", "")),
                        research_text(record.get("open_questions", "")),
                    ]
                ).casefold()
                if not all(term in haystack for term in query_terms):
                    return False
            return True

        filtered = [record for record in snapshot.records if matches(record)]
        filtered.sort(key=lambda record: str(record["name"]).casefold())
        total = len(filtered)
        safe_offset = max(offset, 0)
        safe_limit = min(max(limit, 1), 1000)
        return filtered[safe_offset : safe_offset + safe_limit], total

    def list_sources(
        self,
        *,
        query: str | None = None,
        authority: str | None = None,
    ) -> list[dict[str, Any]]:
        sources = list(self._load_if_changed().sources)
        query_terms = tuple((query or "").casefold().split())
        if authority:
            sources = [
                item
                for item in sources
                if any(
                    str(role).casefold() == authority.casefold()
                    for role in item["authority_roles"]
                )
            ]
        if query_terms:
            sources = [
                item
                for item in sources
                if all(
                    term
                    in f"{item['title']} {item['authors']} {item.get('venue', '')}".casefold()
                    for term in query_terms
                )
            ]
        def sortable_year(source: dict[str, Any]) -> int:
            value = source.get("year")
            try:
                return int(value)
            except (TypeError, ValueError):
                return 0

        sources.sort(key=lambda source: (-sortable_year(source), source["title"]))
        return sources

    def profile_quality(self) -> dict[str, Any]:
        """Current profile-depth audit; completeness is not evidence verification."""
        snapshot = self._load_if_changed()
        return profile_quality_report(
            snapshot.records,
            catalog_version=str(snapshot.metadata.get("version", "unknown")),
            corpus_date=str(snapshot.metadata.get("generated_at", "unknown")),
        )

    def coverage(self) -> dict[str, Any]:
        snapshot = self._load_if_changed()
        records = snapshot.records
        sources = snapshot.sources
        metadata = snapshot.metadata

        def counts(field: str) -> list[dict[str, Any]]:
            values = Counter(str(record.get(field, "Unclassified")) for record in records)
            return [
                {"name": name, "value": value}
                for name, value in sorted(values.items(), key=lambda pair: (-pair[1], pair[0]))
            ]

        records_with_primary = sum(
            1
            for record in records
            if any(
                str(citation.get("authority", "")).startswith("primary-")
                for citation in record["citations"]
            )
        )
        citation_count = sum(len(record["citations"]) for record in records)
        human_verified_count = sum(
            1
            for record in records
            for citation in record["citations"]
            if citation.get("verification") == "human-verified"
        )
        locator_count = sum(
            1
            for record in records
            for citation in record["citations"]
            if str(citation.get("url", "")).startswith(("https://", "http://"))
        )
        full_profile_count = sum(
            all(
                record.get(field)
                for field in (
                    "claim_scope",
                    "boundary_note",
                    "evidence_profile",
                    "open_questions",
                )
            )
            for record in records
        )
        readiness = int(metadata.get("readiness_percent", 0))
        discovery = self.discovery_metadata()
        return {
            "phase": metadata.get("phase", "collection"),
            "gate_state": metadata.get("coverage_gate", "locked"),
            "readiness_percent": readiness,
            "record_count": len(records),
            "source_count": len(sources),
            "citation_count": citation_count,
            "full_research_profile_count": full_profile_count,
            "research_profile_gap_count": len(records) - full_profile_count,
            "human_verified_percent": round(
                100 * human_verified_count / citation_count, 1
            )
            if citation_count
            else 0,
            "locator_coverage_percent": round(
                100 * locator_count / citation_count, 1
            )
            if citation_count
            else 0,
            "primary_source_percent": round(100 * records_with_primary / len(records), 1)
            if records
            else 0,
            "by_kind": counts("kind"),
            "by_domain": counts("domain"),
            "by_status": counts("status"),
            "by_tradition": counts("tradition"),
            "discovery_frames": metadata.get("discovery_frames", []),
            "discovery_registry": discovery,
            "gate_requirements": metadata.get("gate_requirements", []),
            "notice": metadata.get(
                "coverage_notice",
                "This is an open-world catalog. Readiness measures the protocol, not completeness.",
            ),
        }

    def taxonomy_graph(self) -> dict[str, Any]:
        """Return organizational edges only; no conceptual theory relationships."""
        snapshot = self._load_if_changed()
        category_ids: dict[tuple[str, str], str] = {}
        nodes: list[dict[str, Any]] = []
        links: list[dict[str, str]] = []

        nodes.append(
            {
                "id": "phenomenon-consciousness",
                "name": "Consciousness",
                "node_type": "phenomenon",
                "group": "Target phenomenon",
                "size": 13,
            }
        )

        for record in snapshot.records:
            group = str(record["domain"])
            category_key = ("domain", group)
            if category_key not in category_ids:
                category_id = f"domain-{len(category_ids) + 1}"
                category_ids[category_key] = category_id
                nodes.append(
                    {
                        "id": category_id,
                        "name": group,
                        "node_type": "domain",
                        "group": group,
                        "size": 8,
                    }
                )
                links.append(
                    {
                        "source": "phenomenon-consciousness",
                        "target": category_id,
                        "kind": "organizational",
                    }
                )
            nodes.append(
                {
                    "id": record["id"],
                    "name": record["name"],
                    "node_type": "record",
                    "group": group,
                    "kind": record["kind"],
                    "status": record["status"],
                    "size": 4 + min(len(record["citations"]), 4),
                }
            )
            links.append(
                {
                    "source": category_ids[category_key],
                    "target": record["id"],
                    "kind": "classification",
                }
            )

        return {
            "nodes": nodes,
            "links": links,
            "edge_policy": "Taxonomic classification only. Theory-to-theory synthesis is locked.",
        }
