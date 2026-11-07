"""Build the read-only merged catalog data quality report.

Run from repository root:
  python Noemorph/research/audit_data_quality.py --output data-quality.json
  python Noemorph/research/audit_data_quality.py --output data-quality.json --check

This report identifies editorial work. It never modifies the research corpus.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from backend.catalog import CatalogRepository  # noqa: E402
from backend.data_quality import data_quality_report  # noqa: E402

CATALOG = APP_DIR / "data" / "catalog.json"


def build(catalog_path: Path = CATALOG) -> dict:
    snapshot = CatalogRepository(catalog_path)._load_if_changed()
    metadata = snapshot.metadata
    return data_quality_report(
        snapshot.records,
        catalog_version=str(metadata.get("version", "unknown")),
        corpus_date=str(metadata.get("generated_at", "unknown")),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--output", type=Path, help="Write report here; default is stdout.")
    parser.add_argument("--check", action="store_true", help="Compare with a previously written report.")
    args = parser.parse_args(argv)
    report = build(args.catalog)
    if args.check:
        if not args.output or not args.output.is_file():
            print("A pre-existing --output report is required for --check.", file=sys.stderr)
            return 1
        try:
            previous = json.loads(args.output.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Could not read quality report: {exc}", file=sys.stderr)
            return 1
        if previous != report:
            print("Data-quality report differs from the current merged catalog.", file=sys.stderr)
            return 1
    elif args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
