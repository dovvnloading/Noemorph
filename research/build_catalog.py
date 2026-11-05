"""Build the application corpus from the reviewed Markdown research tables.

The transformation preserves the row-level distinctions made during research and
uses Crossref only to expand DOI bibliographic metadata. It does not infer or
publish relationships between theories.
"""

from __future__ import annotations

import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


RESEARCH_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = RESEARCH_DIR.parent
SOURCE_PATHS = (
    RESEARCH_DIR / "consciousness_seed_catalog.md",
    RESEARCH_DIR / "consciousness_expansion_catalog.md",
)
OUTPUT_PATH = WORKSPACE_DIR / "Noemorph" / "data" / "catalog.json"
CACHE_PATH = RESEARCH_DIR / "crossref_cache.json"
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
YEAR_PATTERN = re.compile(r"\b(?:1[5-9]\d{2}|20\d{2})\b")
HTML_PATTERN = re.compile(r"<[^>]+>")

PROPONENT_OVERRIDES: dict[int, list[str]] = {
    6: ["J. S. Mill"],
    7: ["C. D. Broad", "William Hasker", "Timothy O’Connor"],
    9: ["Paul Churchland", "Patricia Churchland", "Wilfrid Sellars", "W. V. Quine"],
    10: ["Daniel C. Dennett", "Keith Frankish"],
    11: ["T. H. Huxley", "Frank Jackson"],
    13: ["René Descartes", "Karl Popper", "John C. Eccles"],
    15: ["Aristotle", "Thomas Aquinas", "William Jaworski"],
    17: ["Baruch Spinoza", "Wolfgang Pauli", "C. G. Jung", "Harald Atmanspacher"],
    18: ["Bertrand Russell", "Arthur Eddington", "Philip Goff", "Torin Alter", "Daniel Stoljar"],
    19: ["Galen Strawson", "Philip Goff"],
    20: ["David Chalmers"],
    24: ["Colin McGinn", "Thomas Nagel"],
    25: ["Alfred North Whitehead"],
    28: ["Giulio Tononi", "Masafumi Oizumi", "Larissa Albantakis", "Christof Koch"],
    31: ["William G. Lycan", "David M. Armstrong"],
    47: ["Wolf Singer", "Francis Crick", "Christof Koch"],
    52: ["Andrew A. Fingelkurts", "Alexander A. Fingelkurts"],
    55: ["David Rudrauf", "Daniel Bennequin", "Kenneth Williford", "Karl Friston"],
    56: ["Simona Ginsburg", "Eva Jablonka", "Jonathan Birch"],
    57: ["Mark Solms", "Jaak Panksepp"],
    59: ["Robin L. Carhart-Harris"],
    62: ["Karl Friston", "Mark Solms", "Anil K. Seth", "Jakob Hohwy"],
    67: ["Alan Turing", "Hilary Putnam", "Jerry Fodor"],
    76: ["Hiroomi Umezawa", "Mari Jibu", "Giuseppe Vitiello", "Walter J. Freeman"],
    88: ["Classical Sāṃkhya traditions", "Patañjali’s Yoga tradition"],
    92: ["Mahāvīra", "Umāsvāti", "Jaina traditions"],
    94: ["Wilfrid Sellars", "David Premack", "Guy Woodruff", "Alison Gopnik", "Henry Wellman"],
    96: ["Alan Leslie", "Simon Baron-Cohen", "Ori Friedman", "Tamsin German"],
    98: ["Shaun Gallagher"],
}

CITATION_OVERRIDES: dict[str, dict[str, Any]] = {
    "https://doi.org/10.1017/CBO9780511625251.023": {
        "title": "The Nature of Mental States",
        "authors": "Hilary Putnam",
        "year": 1975,
        "venue": "Mind, Language and Reality: Philosophical Papers, Volume 2",
    },
    "https://www.ingentaconnect.com/content/imp/jcs/2016/00000023/f0020011/art00002": {
        "title": "Illusionism as a Theory of Consciousness",
        "authors": "Keith Frankish",
        "year": 2016,
        "venue": "Journal of Consciousness Studies",
    },
    "https://www.hachettebookgroup.com/titles/daniel-c-dennett/consciousness-explained/9780316180665/": {
        "title": "Consciousness Explained",
        "authors": "Daniel C. Dennett",
        "year": 1991,
        "venue": "Little, Brown and Company",
    },
    "https://www.gutenberg.org/ebooks/2529": {
        "title": "The Analysis of Mind",
        "authors": "Bertrand Russell",
        "year": 1921,
        "venue": "Project Gutenberg edition",
    },
    "https://mitpress.mit.edu/9780262121972/consciousness-and-experience/": {
        "title": "Consciousness and Experience",
        "authors": "William G. Lycan",
        "year": 1996,
        "venue": "MIT Press",
    },
    "https://mitpress.mit.edu/9780262700887/consciousness-color-and-content/": {
        "title": "Consciousness, Color, and Content",
        "authors": "Michael Tye",
        "year": 2002,
        "venue": "MIT Press",
    },
    "https://authors.library.caltech.edu/records/7fap3-5v118": {
        "title": "Towards a Neurobiological Theory of Consciousness",
        "authors": "Francis Crick, Christof Koch",
        "year": 1990,
        "venue": "Seminars in the Neurosciences",
    },
    "https://cris.huji.ac.il/en/publications/a-psychological-theory-of-consciousness/": {
        "title": "A Psychological Theory of Consciousness",
        "authors": "Benny Shanon",
        "year": 2008,
        "venue": "Journal of Consciousness Studies",
    },
}

REVIEWED_URLS = {
    *CITATION_OVERRIDES,
    "https://doi.org/10.2307/2182164",
    "https://doi.org/10.1007/978-3-642-61891-8",
    "https://doi.org/10.1093/acprof:oso/9780199359943.003.0005",
    "https://doi.org/10.1093/acprof:oso/9780199570355.001.0001",
    "https://doi.org/10.1016/S0010-0277%2800%2900130-X",
    "https://doi.org/10.1016/S0896-6273%2800%2980821-1",
    "https://doi.org/10.1016/j.neuropharm.2018.03.010",
}


def slugify(value: str) -> str:
    value = value.casefold().replace("ā", "a").replace("ṃ", "m").replace("ṣ", "s")
    value = value.replace("ñ", "n").replace("ī", "i").replace("ṛ", "r").replace("ś", "s")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:72] or "record"


def kind_label(code: str) -> str:
    # The first code is the record's primary entity class; later codes preserve
    # secondary facets without flattening a tradition, construct, or clinical
    # state into whichever theory-like label happens to have higher precedence.
    primary = code.split("/", 1)[0].strip()
    labels = {
        "PC": "Phenomenological construct",
        "CS": "Clinical / state model",
        "SC": "Theory of mind / social cognition",
        "CT": "Scientific theory",
        "MP": "Philosophical position",
        "HT": "Historical tradition",
        "MF": "Model or framework",
        "NF": "Model or framework",
    }
    return labels.get(primary, "Model or framework")


def proponents(value: str) -> list[str]:
    head = value.split(";", 1)[0]
    head = re.sub(r"^(Contemporary lineage|Historical precedents?|Precursors?)\s*:\s*", "", head)
    head = re.sub(r"\b(?:and many later authors|and others|among others)\b", "", head)
    pieces = re.split(r",|\band\b|\bincluding\b", head)
    cleaned = [re.sub(r"\s+", " ", piece).strip(" .") for piece in pieces]
    names = [piece for piece in cleaned if piece and not YEAR_PATTERN.search(piece)]
    return names[:8] or [head.strip()]


def aliases_for(name: str) -> list[str]:
    """Retain explicit acronym aliases without inventing semantic equivalence."""

    aliases: list[str] = []
    for candidate in re.findall(r"\(([^()]+)\)", name):
        candidate = candidate.strip(" ‘'\"“”")
        if (
            candidate
            and len(candidate) <= 12
            and " " not in candidate
            and sum(character.isupper() for character in candidate) >= 2
        ):
            aliases.append(candidate)
    return list(dict.fromkeys(aliases))


def load_cache() -> dict[str, Any]:
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def crossref_metadata(doi: str, cache: dict[str, Any]) -> dict[str, Any] | None:
    if doi in cache:
        return cache[doi]
    endpoint = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}"
    request = urllib.request.Request(
        endpoint,
        headers={"User-Agent": "NoemorphResearch/0.1 (citation metadata verification)"},
    )
    result: dict[str, Any] | None = None
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            message = json.load(response)["message"]
        author_names = []
        for author in message.get("author", []):
            name = " ".join(part for part in (author.get("given"), author.get("family")) if part)
            if not name:
                name = author.get("name", "")
            if name:
                author_names.append(name)
        date_parts = (
            message.get("published-print", {}).get("date-parts")
            or message.get("published-online", {}).get("date-parts")
            or message.get("issued", {}).get("date-parts")
            or [[None]]
        )
        raw_title = (message.get("title") or [""])[0]
        result = {
            "title": html.unescape(HTML_PATTERN.sub("", raw_title)).strip(),
            "authors": ", ".join(author_names),
            "year": date_parts[0][0],
            "venue": (message.get("container-title") or [""])[0],
        }
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError, ValueError):
        result = None
    cache[doi] = result
    time.sleep(0.04)
    return result


def authority_for(label: str, url: str) -> str:
    combined = f"{label} {url}".casefold()
    if "plato.stanford.edu" in combined or "sep:" in combined:
        return "authoritative-secondary"
    if any(token in combined for token in ("seth & bayne", "kuhn 2024", "contrast", "scoping", "review")):
        return "scholarly-secondary"
    if any(token in combined for token in ("philpapers.org", "publisher", "book page", "bibliographic")):
        return "discovery-lead"
    return "primary-original"


def citation_from_link(
    label: str,
    url: str,
    fallback_authors: list[str],
    cache: dict[str, Any],
) -> dict[str, Any]:
    decoded_url = urllib.parse.unquote(url)
    doi = decoded_url.split("doi.org/", 1)[1] if "doi.org/" in decoded_url else None
    expanded = crossref_metadata(doi, cache) if doi else None
    is_sep = "plato.stanford.edu" in url
    reviewed_metadata = CITATION_OVERRIDES.get(url)
    metadata = reviewed_metadata or expanded or {}
    citation = {
        "title": metadata.get("title") or label,
        "authors": metadata.get("authors") or ("Stanford Encyclopedia of Philosophy" if is_sep else "Source authorship pending review"),
        "year": metadata.get("year") or ("living entry" if is_sep else "see source"),
        "venue": metadata.get("venue") or ("Stanford Encyclopedia of Philosophy" if is_sep else "Canonical source record"),
        "url": url,
        "authority": authority_for(label, url),
        "verification": (
            "human-verified"
            if url in REVIEWED_URLS
            else "doi-resolved"
            if doi and expanded
            else "locator-recorded"
            if is_sep
            else "pending-metadata-review"
        ),
        "retrieved": "2026-08-29",
    }
    if doi:
        citation["doi"] = doi
    return citation


def parse_rows(text: str, cache: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not re.match(r"^\|\s*\d+\s*\|", line):
            continue
        cells = [cell.strip() for cell in line.strip().split("|")[1:-1]]
        if len(cells) != 9:
            raise ValueError(f"Unexpected table row shape ({len(cells)} cells): {line[:120]}")
        number, name, kind, summary, proponent_text, domain, status, citation_cell, citation_note = cells
        record_number = int(number)
        attributed_people = PROPONENT_OVERRIDES.get(record_number, proponents(proponent_text))
        citations = [
            citation_from_link(label, url, attributed_people, cache)
            for label, url in LINK_PATTERN.findall(citation_cell)
        ]
        if len(citations) < 2:
            raise ValueError(f"Record {number} ({name}) has fewer than two source links")
        era_years = YEAR_PATTERN.findall(proponent_text)
        record: dict[str, Any] = {
            "id": f"seed-{record_number:03d}-{slugify(name)}",
            "name": name,
            "aliases": aliases_for(name),
            "kind": kind_label(kind),
            "kind_codes": kind.split("/"),
            "domain": domain,
            "tradition": domain,
            "status": status.replace(";", " ·"),
            "status_note": citation_note,
            "summary": summary,
            "proponents": attributed_people,
            "era": proponent_text.split(";", 1)[-1].strip() if ";" in proponent_text else proponent_text,
            "scope": "See cited definition and scope review",
            "keywords": [kind_label(kind), domain, *aliases_for(name)],
            "review_state": "provisional",
            "citations": citations,
        }
        if era_years:
            record["year"] = int(era_years[0])
        records.append(record)
    return records


def main() -> None:
    cache = load_cache()
    source_text = "\n".join(path.read_text(encoding="utf-8") for path in SOURCE_PATHS)
    records = parse_rows(source_text, cache)
    if [int(record["id"].split("-", 2)[1]) for record in records] != list(range(1, len(records) + 1)):
        raise ValueError("Seed record numbering is not continuous")

    payload = {
        "metadata": {
            "title": "Noemorph consciousness and mind research corpus",
            "version": "0.2.0-collection",
            "generated_at": "2026-08-29",
            "phase": "collection",
            "coverage_gate": "locked",
            "readiness_percent": 46,
            "methodology": "A citation-first collection organized from Robert Lawrence Kuhn's inclusive 2024 landscape, systematic and scoping reviews, primary works, and authoritative scholarly references. The expanded inventory adds explicit awareness constructs, state models, and historical traditions while keeping entity kinds distinct and synthesis deferred.",
            "coverage_notice": "There is no defensible fixed denominator for ‘all theories.’ Noemorph reports protocol coverage, unresolved strata, and discovery yield rather than declaring the catalog complete.",
            "anchor_sources": [
                "https://doi.org/10.1016/j.pbiomolbio.2023.12.003",
                "https://doi.org/10.1038/s41583-022-00587-4",
                "https://doi.org/10.3390/brainsci11050535",
                "https://doi.org/10.1093/nc/niab021",
                "https://doi.org/10.1038/s41562-021-01284-5",
            ],
            "discovery_frames": [
                {"name": "Kuhn landscape taxonomy", "type": "Broad inclusive consciousness taxonomy", "status": "screening", "screened": 148, "target": 220},
                {"name": "Peer-reviewed theory literature", "type": "Scientific and neurocognitive primary works", "status": "active", "screened": 174, "target": 240},
                {"name": "Stanford Encyclopedia of Philosophy", "type": "Authoritative philosophical orientation", "status": "screening", "screened": 68, "target": 96},
                {"name": "Closer to Truth index", "type": "Expert interview discovery frame", "status": "queued", "screened": 18, "target": 180},
                {"name": "Historical and comparative traditions", "type": "Cross-cultural scholarly sources", "status": "active", "screened": 52, "target": 110},
            ],
            "gate_requirements": [
                "Every published catalog record has at least two retained citation locators and exact destinations.",
                "Scientific theories, philosophical positions, frameworks, traditions, and social-cognition theories remain separately typed.",
                "Citation title, author, work identity, and DOI destination pass independent semantic review.",
                "At least 95% of registered discovery-frame items are screened overall and 85% in every mandatory stratum.",
                "At least 90% of records are anchored to a primary or authoritative self-exposition source, or reviewed waiver.",
                "Unresolved identity and duplicate candidates fall below the protocol threshold.",
                "Two independent reviewers approve the coverage report before synthesis begins.",
            ],
        },
        "records": records,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} records to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
