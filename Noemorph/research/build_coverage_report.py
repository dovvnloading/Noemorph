"""Build an auditable open-world coverage report across catalog and source frames."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parents[1]
CATALOG_PATH = APP_DIR / "data" / "catalog.json"
OUTPUT_PATH = APP_DIR / "data" / "coverage-report.json"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from backend.catalog import CatalogRepository  # noqa: E402


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sorted_counts(values: list[str]) -> list[dict[str, Any]]:
    return [
        {"name": name, "count": count}
        for name, count in sorted(Counter(values).items(), key=lambda item: (-item[1], item[0]))
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    base = read(args.catalog)
    repository = CatalogRepository(args.catalog)
    records, _ = repository.list_records(limit=100_000)
    supplement_counts: list[dict[str, Any]] = []
    for filename in base.get("supplements", []):
        payload = read(args.catalog.parent / filename)
        shard_records = payload["records"]
        supplement_counts.append(
            {
                "file": filename,
                "name": payload.get("collection", {}).get("name", filename),
                "record_count": len(shard_records),
            }
        )
    profile_counts: list[dict[str, Any]] = []
    for filename in base.get("profile_enrichments", []):
        payload = read(args.catalog.parent / filename)
        profiles = payload["profiles"]
        profile_counts.append(
            {
                "file": filename,
                "name": payload.get("collection", {}).get("name", filename),
                "profile_count": len(profiles),
            }
        )

    citations = [citation for record in records for citation in record["citations"]]
    source_keys = {
        str(citation.get("doi") or citation["url"]).casefold() for citation in citations
    }
    fully_profiled = [
        record
        for record in records
        if all(record.get(field) for field in ("claim_scope", "boundary_note", "evidence_profile", "open_questions"))
    ]

    ctt = read(args.catalog.parent / "discovery-closer-to-truth.json")
    ctt_entries = ctt["entries"]
    kuhn = read(args.catalog.parent / "discovery-kuhn-landscape.json")
    kuhn_entries = kuhn["entries"]
    tsc = read(args.catalog.parent / "scope-tsc-taxonomy.json")

    payload = {
        "generated_at": date.today().isoformat(),
        "phase": base["metadata"].get("phase", "collection"),
        "coverage_gate": base["metadata"].get("coverage_gate", "locked"),
        "interpretation": "Counts describe indexed and reviewed material; they are not a claim that the open world of consciousness theories is complete.",
        "reviewed_catalog": {
            "record_count": len(records),
            "citation_count": len(citations),
            "unique_source_count": len(source_keys),
            "full_research_profile_count": len(fully_profiled),
            "research_profile_gap_count": len(records) - len(fully_profiled),
            "base_record_count": len(base["records"]),
            "supplements": supplement_counts,
            "profile_enrichments": profile_counts,
            "by_kind": sorted_counts([str(record["kind"]) for record in records]),
            "by_domain": sorted_counts([str(record["domain"]) for record in records]),
            "by_status": sorted_counts([str(record["status"]) for record in records]),
            "by_source_authority": sorted_counts([str(citation["authority"]) for citation in citations]),
        },
        "discovery_frames": {
            "closer_to_truth": {
                "profile_count": len(ctt_entries),
                "category_count": len({entry["category"] for entry in ctt_entries}),
                "key_takeaway_count": sum(len(entry["key_takeaways"]) for entry in ctt_entries),
                "reference_entry_count": sum(len(entry["references"]) for entry in ctt_entries),
                "reference_locator_count": sum(
                    len(reference["locators"])
                    for entry in ctt_entries
                    for reference in entry["references"]
                ),
                "title_screen_counts": ctt["collection"]["catalog_match_counts"],
                "by_category": sorted_counts([str(entry["category"]) for entry in ctt_entries]),
            },
            "kuhn_landscape": {
                "heading_count": len(kuhn_entries),
                "named_position_count": kuhn["collection"]["named_position_count"],
                "overview_count": kuhn["collection"]["overview_count"],
                "title_screen_counts": dict(Counter(entry["catalog_match"]["status"] for entry in kuhn_entries)),
                "by_category": sorted_counts([str(entry["category"]) for entry in kuhn_entries]),
            },
            "tsc_scope_taxonomy": {
                "topic_count": len(tsc["items"]),
                "group_count": len(tsc["collection"]["group_counts"]),
                "by_group": sorted_counts([str(item["group"]) for item in tsc["items"]]),
                "role": tsc["collection"]["role"],
            },
        },
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Coverage report: {len(records)} records, {len(citations)} citations, "
        f"{len(fully_profiled)} full profiles"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
