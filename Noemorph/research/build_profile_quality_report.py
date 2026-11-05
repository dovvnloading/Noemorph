"""Generate/check a deterministic current research-profile quality report.

Run from the repository root:
  python Noemorph/research/build_profile_quality_report.py
  python Noemorph/research/build_profile_quality_report.py --check

This is an editorial triage report, NOT a claim-evidence verification report.
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
from backend.profile_quality import profile_quality_report  # noqa: E402

CATALOG = APP_DIR / "data" / "catalog.json"
REPORT = APP_DIR / "data" / "profile-quality-report.json"


def build(catalog_path: Path = CATALOG) -> dict:
    repository = CatalogRepository(catalog_path)
    snapshot = repository._load_if_changed()
    meta = snapshot.metadata
    return profile_quality_report(
        snapshot.records,
        catalog_version=str(meta.get("version", "unknown")),
        corpus_date=str(meta.get("generated_at", "unknown")),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--output", type=Path, default=REPORT)
    parser.add_argument("--check", action="store_true", help="Fail if the committed report is absent or stale.")
    args = parser.parse_args(argv)
    report = build(args.catalog)
    if args.check:
        if not args.output.is_file():
            print(f"Missing quality report: {args.output}", file=sys.stderr)
            return 1
        try:
            committed = json.loads(args.output.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Invalid quality report: {exc}", file=sys.stderr)
            return 1
        if committed != report:
            print("Profile quality report is stale. Regenerate it.", file=sys.stderr)
            return 1
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    summary = report["summary"]
    print(
        f"Profile quality: {summary['complete_profiles']}/{summary['record_count']} "
        f"complete, {summary['incomplete_profiles']} outstanding "
        f"({summary['completion_percent']}%)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
