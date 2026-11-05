"""Local CLI for claim-to-source evidence reviews (no networked review writes).

Examples (from the repository root):

  python Noemorph/research/review_claim_evidence.py init
  python Noemorph/research/review_claim_evidence.py status
  python Noemorph/research/review_claim_evidence.py show \
      --record-id seed-026-global-workspace-theory-gwt \
      --claim-id seed-026-global-workspace-theory-gwt:scope

To append an assessment, see the explicit record subcommand arguments.
All reviewer identifiers are self-asserted. No decision publishes evidence.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from backend.catalog import CatalogRepository  # noqa: E402
from backend.evidence_ledger import (  # noqa: E402
    ClaimEvidenceLedger, DECISIONS, LOCATOR_KINDS, EvidenceReviewError,
    initialize_evidence_database,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database", type=Path,
        default=APP_DIR / "data" / "reviews" / "claim-evidence.sqlite3",
        help="Local untracked review ledger path.",
    )
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("init", help="Initialize a local, untracked SQLite ledger.")
    actions.add_parser("status", help="Check the ledger and hash-chain integrity.")
    show = actions.add_parser("show", help="Inspect claim event history and review status.")
    show.add_argument("--record-id", required=True)
    show.add_argument("--claim-id", required=True)

    record = actions.add_parser(
        "record",
        help="Append an assessment; never certify a claim or publish a relationship.",
    )
    record.add_argument("--record-id", required=True)
    record.add_argument("--claim-id", required=True)
    record.add_argument("--citation-url", required=True)
    record.add_argument("--reviewer-id", required=True)
    record.add_argument("--decision", choices=sorted(DECISIONS), required=True)
    record.add_argument("--locator-kind", choices=sorted(LOCATOR_KINDS), required=True)
    record.add_argument("--locator", required=True)
    record.add_argument("--excerpt", help="Short passage, at most 280 characters.")
    record.add_argument("--note", required=True, help="Reasoned decision, 20–2000 characters.")
    args = parser.parse_args(argv)
    catalog = CatalogRepository(APP_DIR / "data" / "catalog.json")
    ledger = ClaimEvidenceLedger(args.database, catalog)
    try:
        if args.action == "init":
            initialize_evidence_database(args.database)
            result = ledger.status()
        elif args.action == "status":
            result = ledger.status()
        elif args.action == "show":
            result = ledger.history(args.record_id, args.claim_id)
        else:
            if not args.database.is_file():
                parser.error("Initialize the evidence ledger first with the init subcommand.")
            result = ledger.record(
                record_id=args.record_id, claim_id=args.claim_id,
                citation_url=args.citation_url,
                reviewer_id=args.reviewer_id, decision=args.decision,
                locator_kind=args.locator_kind, locator=args.locator,
                excerpt=args.excerpt, note=args.note,
            )
    except EvidenceReviewError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
