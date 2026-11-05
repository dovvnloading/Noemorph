"""Audit merged catalog shards for identifiers, aliases, profiles, and citations."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any


APP_DIR = Path(__file__).resolve().parents[1]
CATALOG_PATH = APP_DIR / "data" / "catalog.json"
KINDS = {
    "Scientific theory",
    "Model or framework",
    "Clinical / state model",
    "Theory of mind / social cognition",
    "Phenomenological construct",
    "Philosophical position",
    "Argument / challenge",
    "Historical tradition",
}
VERIFICATION = {"doi-resolved", "locator-recorded", "human-verified", "pending-metadata-review"}
PROFILE_FIELDS = {
    "id",
    "status_note",
    "scope",
    "keywords",
    "boundary_note",
    "claim_scope",
    "evidence_profile",
    "open_questions",
    "review_state",
    "citation_additions",
}


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().casefold()
    value = re.sub(r"\b(theory|model|framework|hypothesis|account|approach)\b", " ", value)
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value).split())


def collect(catalog_path: Path, candidates: list[Path]) -> list[tuple[Path, dict[str, Any]]]:
    base = read(catalog_path)
    packets = [(catalog_path, base)]
    packets.extend((catalog_path.parent / filename, read(catalog_path.parent / filename)) for filename in base.get("supplements", []))
    packets.extend((path, read(path)) for path in candidates)
    return packets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("candidates", nargs="*", type=Path)
    args = parser.parse_args()

    packets = collect(args.catalog, args.candidates)
    errors: list[str] = []
    ids: dict[str, str] = {}
    terms: defaultdict[str, list[tuple[str, str, str]]] = defaultdict(list)
    record_count = 0
    citation_count = 0
    profile_count = 0

    for path, payload in packets:
        records = payload.get("records")
        if not isinstance(records, list):
            errors.append(f"{path}: records is not an array")
            continue
        manifest = payload.get("collection")
        if path != args.catalog and isinstance(manifest, dict) and manifest.get("record_count") != len(records):
            errors.append(f"{path}: manifest record_count does not equal {len(records)}")
        for record in records:
            record_count += 1
            record_id = str(record.get("id", ""))
            if not record_id:
                errors.append(f"{path}: record without id")
                continue
            if record_id in ids:
                errors.append(f"duplicate id {record_id}: {ids[record_id]} and {path}")
            ids[record_id] = str(path)
            if record.get("kind") not in KINDS:
                errors.append(f"{record_id}: unsupported kind {record.get('kind')}")
            for term_type, term in [("name", record.get("name", "")), *(('alias', alias) for alias in record.get("aliases", []))]:
                normalized = normalize(str(term))
                if normalized:
                    terms[normalized].append((record_id, term_type, str(term)))

            for field in ("claim_scope", "boundary_note", "evidence_profile", "open_questions"):
                if path != args.catalog and not record.get(field):
                    errors.append(f"{record_id}: missing deep-profile field {field}")
            citations = record.get("citations")
            if not isinstance(citations, list) or len(citations) < 2:
                errors.append(f"{record_id}: fewer than two citations")
                continue
            citation_count += len(citations)
            local: set[str] = set()
            for citation in citations:
                url = str(citation.get("url", ""))
                key = str(citation.get("doi") or url).casefold()
                if not url.startswith("https://"):
                    errors.append(f"{record_id}: non-HTTPS citation {url}")
                if key in local:
                    errors.append(f"{record_id}: repeated citation locator {url}")
                local.add(key)
                if citation.get("verification") not in VERIFICATION:
                    errors.append(f"{record_id}: invalid verification {citation.get('verification')}")
                if not citation.get("title") or not citation.get("authors") or not citation.get("authority"):
                    errors.append(f"{record_id}: incomplete citation metadata for {url}")

    for normalized, owners in terms.items():
        record_ids = {owner[0] for owner in owners}
        if len(record_ids) > 1:
            rendered = "; ".join(f"{record_id} {term_type}={term!r}" for record_id, term_type, term in owners)
            errors.append(f"normalized term collision {normalized!r}: {rendered}")

    base = read(args.catalog)
    profiled_ids: set[str] = set()
    for filename in base.get("profile_enrichments", []):
        path = args.catalog.parent / filename
        payload = read(path)
        profiles = payload.get("profiles")
        if not isinstance(profiles, list):
            errors.append(f"{path}: profiles is not an array")
            continue
        manifest = payload.get("collection")
        if isinstance(manifest, dict) and manifest.get("profile_count") != len(profiles):
            errors.append(f"{path}: manifest profile_count does not equal {len(profiles)}")
        for profile in profiles:
            profile_count += 1
            if not isinstance(profile, dict):
                errors.append(f"{path}: profile is not an object")
                continue
            record_id = str(profile.get("id", ""))
            if record_id not in ids:
                errors.append(f"{path}: profile targets unknown id {record_id!r}")
            if record_id in profiled_ids:
                errors.append(f"duplicate profile enrichment for {record_id}")
            profiled_ids.add(record_id)
            unsupported = set(profile) - PROFILE_FIELDS
            if unsupported:
                errors.append(
                    f"{record_id}: unsupported profile field(s) {', '.join(sorted(unsupported))}"
                )
            for field in ("claim_scope", "boundary_note", "evidence_profile", "open_questions"):
                if not profile.get(field):
                    errors.append(f"{record_id}: profile enrichment lacks {field}")
            additions = profile.get("citation_additions", [])
            if not isinstance(additions, list):
                errors.append(f"{record_id}: citation_additions is not an array")
                continue
            for citation in additions:
                url = str(citation.get("url", ""))
                if not url.startswith("https://"):
                    errors.append(f"{record_id}: non-HTTPS added citation {url}")
                if citation.get("verification") not in VERIFICATION:
                    errors.append(
                        f"{record_id}: invalid added-citation verification "
                        f"{citation.get('verification')}"
                    )
                if not citation.get("title") or not citation.get("authors") or not citation.get("authority"):
                    errors.append(f"{record_id}: incomplete added citation metadata for {url}")

    if errors:
        print(f"AUDIT FAILED: {len(errors)} issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"AUDIT PASSED: {record_count} records, {citation_count} base citations, "
        f"{profile_count} profile enrichments, {len(packets)} record files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
