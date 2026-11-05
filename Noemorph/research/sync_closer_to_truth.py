"""Build a reproducible discovery registry from Closer to Truth's theory index.

The output is deliberately separate from the reviewed Noemorph catalog.  It is
an acquisition queue: exact source pages, attributed authors, key takeaways,
and reference locators are retained, but no page is promoted to a catalog
record automatically.  Promotion requires identity, boundary, and citation
review.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


APP_DIR = Path(__file__).resolve().parents[1]
INDEX_URL = "https://loc.closertotruth.com/theory"
OUTPUT_PATH = APP_DIR / "data" / "discovery-closer-to-truth.json"
CATALOG_PATH = APP_DIR / "data" / "catalog.json"
USER_AGENT = "Noemorph/0.3 citation-first discovery registry"


def fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = value.casefold().replace("&", " and ")
    value = re.sub(r"\b(theory|theories|model|models|framework|frameworks|hypothesis)\b", " ", value)
    value = re.sub(r"\b(?:s|of|the|and|a|an)\b", " ", value)
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value).split())


def title_variants(value: str) -> list[tuple[str, str]]:
    """Return conservative title forms for lexical screening.

    Many source titles prefix an author's possessive name (for example,
    ``Carhart-Harris's Entropic Brain Hypothesis``).  Comparing only that full
    label creates avoidable false negatives.  The stripped form remains merely
    a title candidate and never establishes record identity.
    """
    variants = [(normalize(value), "full-title")]
    possessive = re.split(r"[’']s?\s+", value, maxsplit=1)
    if len(possessive) == 2:
        stripped = normalize(possessive[1])
        if stripped and stripped != variants[0][0]:
            variants.append((stripped, "possessive-prefix-stripped"))
    return variants


def load_catalog_names(path: Path) -> list[tuple[str, str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = list(payload.get("records", []))
    for filename in payload.get("supplements", []):
        supplement = json.loads((path.parent / filename).read_text(encoding="utf-8"))
        records.extend(supplement.get("records", []))

    names: list[tuple[str, str, str]] = []
    for record in records:
        record_id = str(record["id"])
        display_name = str(record["name"])
        for value in (display_name, *record.get("aliases", [])):
            normalized = normalize(str(value))
            if normalized:
                names.append((normalized, record_id, display_name))
    return names


def match_catalog(name: str, catalog_names: list[tuple[str, str, str]]) -> dict[str, Any]:
    best: tuple[float, str, str, str] = (0.0, "", "", "full-title")
    for needle, basis in title_variants(name):
        for candidate, record_id, display_name in catalog_names:
            if candidate == needle:
                current = (1.0, record_id, display_name, basis)
            else:
                score = SequenceMatcher(None, needle, candidate).ratio()
                if needle in candidate or candidate in needle:
                    score = max(score, 0.78 + 0.2 * min(len(needle), len(candidate)) / max(len(needle), len(candidate)))
                current = (score, record_id, display_name, basis)
            if current[0] > best[0]:
                best = current
    score, record_id, display_name, basis = best
    if score >= 0.92:
        status = "likely-present"
    # Precision is intentionally favored over recall: this label is visible in
    # the acquisition queue and must not imply identity from a vague topical
    # resemblance.  Lower-scoring candidates remain searchable as unmatched.
    elif score >= 0.88:
        status = "possible-match"
    else:
        status = "not-matched"
    return {
        "status": status,
        "record_id": record_id or None,
        "record_name": display_name or None,
        "score": round(score, 3),
        "basis": basis,
    }


def catalog_screen(
    name: str,
    entry_type: str,
    catalog_names: list[tuple[str, str, str]],
) -> dict[str, Any]:
    if entry_type != "theory":
        return {
            "status": "not-applicable",
            "record_id": None,
            "record_name": None,
            "score": 0.0,
            "basis": "not-applicable",
        }
    return match_catalog(name, catalog_names)


def json_ld_graph(soup: BeautifulSoup) -> list[dict[str, Any]]:
    graph: list[dict[str, Any]] = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            payload = json.loads(script.get_text())
        except (TypeError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and isinstance(payload.get("@graph"), list):
            graph.extend(item for item in payload["@graph"] if isinstance(item, dict))
        elif isinstance(payload, dict):
            graph.append(payload)
    return graph


def get_type(graph: list[dict[str, Any]], item_type: str) -> list[dict[str, Any]]:
    return [item for item in graph if item.get("@type") == item_type]


def clean_locators(value: str) -> list[str]:
    """Split malformed combined hrefs and remove non-identifying tracking data."""
    cleaned: list[str] = []
    for candidate in re.split(r",\s*(?=https://)", value.strip()):
        if not candidate.startswith("https://"):
            continue
        parts = urlsplit(candidate)
        query = urlencode(
            [
                (key, item)
                for key, item in parse_qsl(parts.query, keep_blank_values=True)
                if not key.casefold().startswith("utm_")
            ],
            doseq=True,
        )
        locator = urlunsplit(parts._replace(query=query))
        if locator not in cleaned:
            cleaned.append(locator)
    return cleaned


def parse_references(soup: BeautifulSoup) -> list[dict[str, Any]]:
    section = soup.select_one("#reference-section")
    if section is None:
        return []
    references: list[dict[str, Any]] = []
    for label in section.select('span[id^="ref-"]'):
        block = label.parent
        if block is None:
            continue
        detail = block.find("div")
        title_node = detail.select_one(".font-semibold") if detail else None
        title = title_node.get_text(" ", strip=True) if title_node else ""
        container = ""
        if title_node is not None:
            sibling = title_node.find_next_sibling("div")
            if sibling is not None:
                container = sibling.get_text(" ", strip=True)
        author_node = label.find_next_sibling("span")
        links = []
        for anchor in block.select("a[href]"):
            href = str(anchor.get("href", "")).strip()
            for locator in clean_locators(href):
                if locator not in links:
                    links.append(locator)
        references.append(
            {
                "label": label.get_text(" ", strip=True),
                "authors": author_node.get_text(" ", strip=True) if author_node else "",
                "title": title,
                "container": container,
                "locators": links,
            }
        )
    return references


def parse_page(slug: str, index_name: str, catalog_names: list[tuple[str, str, str]]) -> dict[str, Any]:
    url = urljoin(INDEX_URL + "/", slug)
    soup = BeautifulSoup(fetch(url), "html.parser")
    graph = json_ld_graph(soup)
    terms = get_type(graph, "DefinedTerm")
    articles = get_type(graph, "Article")
    people = get_type(graph, "Person")
    takeaways = get_type(graph, "ItemList")
    term = terms[0] if terms else {}
    article = articles[0] if articles else {}

    category = "Unclassified"
    breadcrumb_links = soup.select("header a[href]")
    if len(breadcrumb_links) >= 2:
        category = breadcrumb_links[-1].get_text(" ", strip=True)

    key_takeaways: list[dict[str, str]] = []
    if takeaways:
        for element in takeaways[0].get("itemListElement", []):
            item = element.get("item", {}) if isinstance(element, dict) else {}
            if isinstance(item, dict):
                key_takeaways.append(
                    {"label": str(item.get("name", "")), "text": str(item.get("text", ""))}
                )

    name = str(term.get("name") or article.get("headline") or index_name).strip()
    entry_type = "theory"
    if slug.endswith("-overview"):
        entry_type = "overview"
    elif "additional-theories" in slug:
        entry_type = "collection"

    return {
        "slug": slug,
        "name": name,
        "url": url,
        "entry_type": entry_type,
        "category": category,
        "description": str(term.get("description") or article.get("description") or "").strip(),
        "term_code": term.get("termCode"),
        "modified_at": article.get("dateModified"),
        "verified_by_source": soup.select_one('img[alt="Verified"]') is not None,
        "proponents": [
            {
                "name": str(person.get("name", "")).strip(),
                "role": str(person.get("jobTitle", "")).strip(),
                "same_as": person.get("sameAs", []),
            }
            for person in people
        ],
        "key_takeaways": key_takeaways,
        "references": parse_references(soup),
        "catalog_match": catalog_screen(name, entry_type, catalog_names),
    }


def index_entries() -> list[tuple[str, str]]:
    soup = BeautifulSoup(fetch(INDEX_URL), "html.parser")
    nav = soup.select_one('nav[aria-label="All consciousness theories"]')
    if nav is None:
        raise RuntimeError("Closer to Truth theory index did not expose its accessible theory list")
    entries: list[tuple[str, str]] = []
    seen: set[str] = set()
    for anchor in nav.select('a[href^="/theory/"]'):
        href = str(anchor.get("href", ""))
        slug = href.removeprefix("/theory/").strip("/")
        if slug and slug not in seen:
            seen.add(slug)
            entries.append((slug, anchor.get_text(" ", strip=True)))
    return entries


def write_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--limit", type=int, help="Development-only page limit")
    parser.add_argument(
        "--reconcile-only",
        action="store_true",
        help="Recompute catalog matches in an existing registry without fetching pages",
    )
    args = parser.parse_args()

    catalog_names = load_catalog_names(args.catalog)
    if args.reconcile_only:
        payload = json.loads(args.output.read_text(encoding="utf-8"))
        records = payload.get("entries", [])
        for record in records:
            record["catalog_match"] = catalog_screen(
                str(record.get("name", "")),
                str(record.get("entry_type", "theory")),
                catalog_names,
            )
        counts = {
            status: sum(item["catalog_match"]["status"] == status for item in records)
            for status in ("likely-present", "possible-match", "not-matched", "not-applicable")
        }
        payload.setdefault("collection", {})["catalog_match_counts"] = counts
        write_atomic(args.output, payload)
        print(f"Reconciled {len(records)} entries against the current catalog")
        return 0

    entries = index_entries()
    if args.limit:
        entries = entries[: max(1, args.limit)]

    records: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 12))) as executor:
        futures = {
            executor.submit(parse_page, slug, name, catalog_names): (slug, name)
            for slug, name in entries
        }
        for completed, future in enumerate(as_completed(futures), start=1):
            slug, name = futures[future]
            try:
                records.append(future.result())
            except Exception as exc:  # Preserve the failed locator for retry/audit.
                errors.append({"slug": slug, "name": name, "error": str(exc)})
            if completed % 25 == 0 or completed == len(futures):
                print(f"Fetched {completed}/{len(futures)}", flush=True)

    records.sort(key=lambda item: item["name"].casefold())
    counts: dict[str, int] = {}
    for status in ("likely-present", "possible-match", "not-matched", "not-applicable"):
        counts[status] = sum(item["catalog_match"]["status"] == status for item in records)
    payload = {
        "collection": {
            "name": "Closer to Truth Landscape of Consciousness discovery registry",
            "source": INDEX_URL,
            "retrieved": date.today().isoformat(),
            "role": "discovery-frame; not automatically promoted to reviewed catalog",
            "source_verification_note": "verified_by_source records only the presence of the source site's Verified badge; it is not Noemorph verification",
            "people_note": "proponents contains Person nodes exposed by the source page and must be treated as people named on that page, not independent attribution",
            "catalog_match_note": "automated lexical title screening only; statuses are review candidates, not identity or inclusion decisions",
            "reference_note": "references and locators are transcribed from source pages and are not automatically authoritative or independently validated",
            "entry_count": len(records),
            "error_count": len(errors),
            "catalog_match_counts": counts,
        },
        "entries": records,
        "errors": sorted(errors, key=lambda item: item["slug"]),
    }
    write_atomic(args.output, payload)
    print(f"Wrote {len(records)} entries to {args.output}")
    if errors:
        print(f"Retained {len(errors)} fetch errors for retry")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
