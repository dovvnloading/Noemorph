"""Export an unapproved and read-only source/profile/claim review queue."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from backend.catalog import CatalogRepository  # noqa: E402
from backend.editorial_triage import editorial_triage_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=APP_DIR / "data" / "catalog.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--profile-limit", type=int, default=25)
    args = parser.parse_args()
    snapshot = CatalogRepository(args.catalog)._load_if_changed()
    report = editorial_triage_report(
        snapshot.records, catalog_version=str(snapshot.metadata.get("version", "unknown")),
        corpus_date=str(snapshot.metadata.get("generated_at", "unknown")),
        profile_limit=args.profile_limit,
    )
    rendered = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
