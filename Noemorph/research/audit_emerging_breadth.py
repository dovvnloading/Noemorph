"""Reproducible integrity and collision audit for the emerging-breadth packet."""

from __future__ import annotations

import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TARGET = DATA / "catalog-2026-08-30-emerging-breadth.json"
sys.path.insert(0, str(ROOT))

from backend.catalog import CatalogRepository, RECORD_KINDS, VERIFICATION_STATES


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


packet = json.loads(TARGET.read_text(encoding="utf-8"))
records = packet["records"]
assert packet["collection"]["record_count"] == len(records)
assert len(records) == 35

required_deep = {
    "aliases",
    "status_note",
    "scope",
    "keywords",
    "boundary_note",
    "claim_scope",
    "evidence_profile",
    "open_questions",
    "review_state",
}
for record in records:
    assert required_deep <= record.keys(), record["id"]
    assert record["kind"] in RECORD_KINDS, record["id"]
    assert record["review_state"] == "provisional", record["id"]
    assert set(record["claim_scope"]) == {"target", "level", "does_not_establish"}, record["id"]
    assert set(record["evidence_profile"]) == {"basis", "limitations", "independence"}, record["id"]
    assert len(record["evidence_profile"]["basis"]) >= 2, record["id"]
    assert len(record["evidence_profile"]["limitations"]) >= 2, record["id"]
    assert len(record["open_questions"]) >= 3, record["id"]
    assert len(record["citations"]) >= 2, record["id"]
    keys: set[str] = set()
    for citation in record["citations"]:
        assert citation["url"].startswith("https://"), (record["id"], citation["url"])
        assert citation["verification"] in VERIFICATION_STATES, (record["id"], citation["verification"])
        key = (citation.get("doi") or citation["url"]).casefold()
        assert key not in keys, (record["id"], key)
        keys.add(key)
        if citation.get("doi"):
            assert citation["url"].casefold() == f"https://doi.org/{citation['doi']}".casefold()
            assert citation["verification"] == "doi-resolved"

# Validate the exact merge that registration would create, without registering the file.
base = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
merged = list(base["records"])
for supplement in base.get("supplements", []):
    merged.extend(json.loads((DATA / supplement).read_text(encoding="utf-8"))["records"])
existing = list(merged)
merged.extend(records)
snapshot = CatalogRepository._validate({"metadata": base["metadata"], "records": merged})

# Compare new names and aliases against every catalog JSON currently present, including
# unregistered sibling-agent packets, while excluding this packet itself.
other_records = []
for path in DATA.glob("catalog*.json"):
    if path.resolve() == TARGET.resolve():
        continue
    payload = json.loads(path.read_text(encoding="utf-8"))
    other_records.extend(payload.get("records", []))

other_terms: dict[str, set[str]] = {}
for record in other_records:
    for term in [record.get("name", ""), *record.get("aliases", [])]:
        if term:
            other_terms.setdefault(norm(term), set()).add(record.get("id", "unknown"))

collisions = []
new_terms: dict[str, str] = {}
for record in records:
    for term in [record["name"], *record.get("aliases", [])]:
        normalized = norm(term)
        if normalized in other_terms:
            collisions.append((record["id"], term, sorted(other_terms[normalized])))
        previous = new_terms.get(normalized)
        if previous and previous != record["id"]:
            collisions.append((record["id"], term, [previous]))
        new_terms[normalized] = record["id"]
assert not collisions, collisions

citations = [citation for record in records for citation in record["citations"]]
unique_sources = {(citation.get("doi") or citation["url"]).casefold() for citation in citations}
dois = sorted({citation["doi"].lower() for citation in citations if citation.get("doi")})
locator_only = sorted({citation["url"] for citation in citations if not citation.get("doi")})


def resolve(doi: str) -> tuple[str, int]:
    response = requests.head(
        f"https://doi.org/{doi}",
        headers={"User-Agent": "Noemorph DOI integrity audit"},
        allow_redirects=False,
        timeout=30,
    )
    return doi, response.status_code


statuses = {}
with ThreadPoolExecutor(max_workers=8) as pool:
    futures = [pool.submit(resolve, doi) for doi in dois]
    for future in as_completed(futures):
        doi, status = future.result()
        statuses[doi] = status

bad_dois = {doi: status for doi, status in statuses.items() if status not in {200, 301, 302, 303, 307, 308}}
assert not bad_dois, bad_dois

years = [record["year"] for record in records]
print(json.dumps({
    "records": len(records),
    "citations": len(citations),
    "unique_sources": len(unique_sources),
    "unique_dois": len(dois),
    "locator_only_sources": len(locator_only),
    "records_2024_2026": sum(year >= 2024 for year in years),
    "records_2025_2026": sum(year >= 2025 for year in years),
    "merged_records_validated": len(snapshot.records),
    "exact_name_alias_collisions": len(collisions),
    "doi_resolver_failures": len(bad_dois),
    "doi_statuses": dict(sorted(statuses.items())),
    "locator_only_urls": locator_only,
}, indent=2))
