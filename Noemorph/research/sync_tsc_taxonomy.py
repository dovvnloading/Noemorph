"""Index the University of Arizona TSC 2024 research-topic taxonomy.

The taxonomy is a scope-control frame, not a list of consciousness theories.
Keeping it separate prevents topics such as anesthesia or dance from being
misrepresented as explanatory theories while still making blind spots visible.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

from pypdf import PdfReader


APP_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = APP_DIR / "data" / "scope-tsc-taxonomy.json"
SOURCE_URL = (
    "https://consciousness.arizona.edu/sites/consciousness.arizona.edu/files/"
    "2024-02/NEW%20TAXONOMY%20for%20TSC_2024.pdf"
)
GROUP_PATTERN = re.compile(r"^\[([^\d][^\]]+)\]\s*$")
ITEM_PATTERN = re.compile(r"^\[(\d{2}\.\d{2})\]?\s*\.{2,}\s*(.+?)\s*$")


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Noemorph/0.4 scope-index"})
    with urlopen(request, timeout=90) as response:
        payload = response.read()
    return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(payload)).pages)


def normalize_line(line: str) -> str:
    return (
        line.replace("………", "........")
        .replace("……", "........")
        .replace("…", ".")
        .replace("[02.05.........", "[02.05]........")
        .strip()
    )


def parse(text: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    current_group = ""
    for raw_line in text.splitlines():
        line = normalize_line(raw_line)
        group_match = GROUP_PATTERN.match(line)
        if group_match:
            current_group = group_match.group(1).strip()
            continue
        item_match = ITEM_PATTERN.match(line)
        if not item_match or not current_group:
            continue
        code, label = item_match.groups()
        items.append(
            {
                "id": f"tsc-{code.replace('.', '-')}",
                "code": code,
                "group": current_group,
                "label": " ".join(label.split()),
            }
        )
    if len(items) != 102:
        raise RuntimeError(f"Expected 102 TSC topic areas, parsed {len(items)}")
    if len({item["code"] for item in items}) != len(items):
        raise RuntimeError("TSC taxonomy contains duplicate topic codes")
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=SOURCE_URL)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    items = parse(fetch_text(args.source))
    groups: dict[str, int] = {}
    for item in items:
        groups[item["group"]] = groups.get(item["group"], 0) + 1
    payload = {
        "collection": {
            "name": "The Science of Consciousness 2024 topic taxonomy",
            "source": args.source,
            "publisher": "University of Arizona Center for Consciousness Studies",
            "retrieved": date.today().isoformat(),
            "role": "Research-scope control frame; not a theory catalog or completeness denominator",
            "item_count": len(items),
            "group_counts": groups,
        },
        "items": items,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Indexed {len(items)} topic areas across {len(groups)} TSC groups")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
