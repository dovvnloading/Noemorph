"""Audit catalog coverage against Kuhn's numbered consciousness landscape.

This is a discovery audit, not a completeness score.  It extracts the named
entries in sections 9--18 of Robert Lawrence Kuhn's landscape paper and finds
likely catalog matches by name or alias.  Unmatched headings are candidates for
human screening; fuzzy matches are never written back to the corpus.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass
from datetime import date
from difflib import SequenceMatcher
from io import BytesIO
from pathlib import Path
from typing import Iterable
from urllib.request import Request, urlopen

from pypdf import PdfReader


APP_DIR = Path(__file__).resolve().parents[1]
CATALOG_PATH = APP_DIR / "data" / "catalog.json"
KUHN_PDF_URL = (
    "https://rlkuhn.com/wp-content/uploads/2024/11/"
    "A-Landscape-of-Consciousness-%E2%80%94-Robert-Lawrence-Kuhn-%E2%80%94-"
    "Progress-in-Biophysics-and-Molecular-Biology-%E2%80%94-August-2024r.pdf"
)
KUHN_DOI_URL = "https://doi.org/10.1016/j.pbiomolbio.2023.12.003"
LANDSCAPE_CATEGORIES = {
    "9": "Materialist and physicalist theories",
    "10": "Non-reductive physicalism",
    "11": "Quantum theories",
    "12": "Integrated information theory",
    "13": "Panpsychisms",
    "14": "Monisms",
    "15": "Dualisms",
    "16": "Idealisms",
    "17": "Anomalous and altered-state theories",
    "18": "Challenge theories",
}
SECTION_PATTERN = re.compile(
    r"(?m)^\s*((?:9|1[0-8])\.\d+(?:\.\d+)?\.)\s+([^\n]{3,180})\s*$"
)
LEADER_PATTERN = re.compile(r"^(?:theories?|theory|models?|frameworks?)\s+(?:of\s+)?")
PUNCTUATION_PATTERN = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class Match:
    section: str
    heading: str
    status: str
    catalog_id: str | None
    catalog_name: str | None
    score: float


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = value.casefold().replace("&", " and ")
    value = value.replace("consciousness theories", "consciousness")
    value = value.replace("theories of consciousness", "consciousness")
    value = PUNCTUATION_PATTERN.sub(" ", value)
    value = LEADER_PATTERN.sub("", value.strip())
    return " ".join(value.split())


def load_records(catalog_path: Path) -> list[dict]:
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    records = list(payload.get("records", []))
    for filename in payload.get("supplements", []):
        supplement_path = catalog_path.parent / filename
        supplement = json.loads(supplement_path.read_text(encoding="utf-8"))
        records.extend(supplement.get("records", []))
    return records


def fetch_pdf_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Noemorph/0.3 taxonomy-audit"})
    with urlopen(request, timeout=90) as response:
        payload = response.read()
    return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(payload)).pages)


def clean_heading(value: str) -> str:
    value = value.replace("�", "-")
    value = re.sub(r"\s+", " ", value).strip(" .")
    # Exclude prose accidentally captured from a numbered measurement or citation.
    value = re.split(r"\s{2,}|\t", value, maxsplit=1)[0]
    return value


def extract_headings(text: str) -> list[tuple[str, str]]:
    headings: list[tuple[str, str]] = []
    seen: set[str] = set()
    for section, raw_heading in SECTION_PATTERN.findall(text):
        heading = clean_heading(raw_heading)
        section_number = section.rstrip(".")
        # The landscape's theory entries are nested three levels deep.  A small
        # number of second-level entries are themselves named positions and are
        # retained as discovery-frame headings.
        if not heading or len(heading) > 150 or heading.endswith(":"):
            continue
        if not re.match(r"^(?:9|1[0-8])\.", section_number):
            continue
        key = f"{section_number}:{normalize(heading)}"
        if key not in seen:
            seen.add(key)
            headings.append((section_number, heading))
    return headings


def candidate_names(record: dict) -> Iterable[tuple[str, str]]:
    yield normalize(str(record.get("name", ""))), str(record.get("name", ""))
    for alias in record.get("aliases", []):
        yield normalize(str(alias)), str(record.get("name", ""))


def compare(headings: list[tuple[str, str]], records: list[dict]) -> list[Match]:
    indexed: list[tuple[str, str, str]] = []
    for record in records:
        for normalized_name, display_name in candidate_names(record):
            if normalized_name:
                indexed.append((normalized_name, str(record["id"]), display_name))

    results: list[Match] = []
    for section, heading in headings:
        needle = normalize(heading)
        best: tuple[float, str, str] = (0.0, "", "")
        for candidate, record_id, display_name in indexed:
            if needle == candidate:
                best = (1.0, record_id, display_name)
                break
            containment = min(len(needle), len(candidate)) / max(len(needle), len(candidate))
            if needle in candidate or candidate in needle:
                score = 0.9 * containment + 0.1
            else:
                score = SequenceMatcher(None, needle, candidate).ratio()
            if score > best[0]:
                best = (score, record_id, display_name)

        score, record_id, display_name = best
        if score >= 0.93:
            status = "matched"
        elif score >= 0.68:
            status = "review"
        else:
            status = "unmatched"
        results.append(
            Match(
                section=section,
                heading=heading,
                status=status,
                catalog_id=record_id or None,
                catalog_name=display_name or None,
                score=round(score, 3),
            )
        )
    return results


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--pdf-url", default=KUHN_PDF_URL)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--output", type=Path, help="Write machine-readable JSON to this path")
    args = parser.parse_args()

    records = load_records(args.catalog)
    headings = extract_headings(fetch_pdf_text(args.pdf_url))
    matches = compare(headings, records)
    counts = {status: sum(item.status == status for item in matches) for status in ("matched", "review", "unmatched")}

    if args.json:
        sections = {item.section: item.heading for item in matches}
        entries: list[dict[str, object]] = []
        for item in matches:
            is_overview = any(
                section.startswith(f"{item.section}.") for section in sections
            )
            parent_section = item.section.rsplit(".", 1)[0]
            status = {
                "matched": "likely-present",
                "review": "possible-match",
                "unmatched": "not-matched",
            }[item.status]
            if is_overview:
                status = "not-applicable"
            entries.append(
                {
                    "id": f"kuhn-{item.section.replace('.', '-')}",
                    "section": item.section,
                    "name": item.heading,
                    "entry_type": "section-overview" if is_overview else "named-position",
                    "category": LANDSCAPE_CATEGORIES[item.section.split(".", 1)[0]],
                    "subcategory": sections.get(parent_section),
                    "source": KUHN_DOI_URL,
                    "catalog_match": {
                        "status": status,
                        "record_id": None if is_overview else item.catalog_id,
                        "record_name": None if is_overview else item.catalog_name,
                        "score": 0.0 if is_overview else item.score,
                    },
                }
            )
        payload = {
                "collection": {
                    "name": "Kuhn 2024 landscape headings",
                    "source": KUHN_DOI_URL,
                    "source_pdf": args.pdf_url,
                    "retrieved": date.today().isoformat(),
                    "role": "Inclusive discovery frame; headings require identity and source screening before catalog promotion",
                    "entry_count": len(entries),
                    "named_position_count": sum(item["entry_type"] == "named-position" for item in entries),
                    "overview_count": sum(item["entry_type"] == "section-overview" for item in entries),
                },
                "discovery_frame": "Kuhn landscape sections 9-18",
                "source": args.pdf_url,
                "catalog_records": len(records),
                "heading_count": len(headings),
                "counts": counts,
                "matches": [asdict(item) for item in matches],
                "entries": entries,
            }
        serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(serialized, encoding="utf-8")
            print(f"Wrote {len(entries)} landscape entries to {args.output}")
        else:
            print(serialized, end="")
        return 0

    print(f"Catalog records: {len(records)}")
    print(f"Landscape headings: {len(headings)}")
    print(" | ".join(f"{key}: {value}" for key, value in counts.items()))
    print("\nUNMATCHED / HUMAN SCREENING REQUIRED")
    for item in matches:
        if item.status == "unmatched":
            print(f"{item.section:<8} {item.heading}")
    print("\nFUZZY MATCHES / HUMAN CONFIRMATION REQUIRED")
    for item in matches:
        if item.status == "review":
            print(f"{item.section:<8} {item.heading} -> {item.catalog_name} ({item.score:.3f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
