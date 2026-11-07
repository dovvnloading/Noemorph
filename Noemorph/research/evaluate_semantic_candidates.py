"""Portable semantic ranking evaluation; never generates reviewer labels."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from backend.semantic_evaluation import (  # noqa: E402
    SemanticEvaluationInputError,
    evaluate_semantic_fixture,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Frozen ranking and adjudication JSON")
    parser.add_argument("--k", required=True, type=int, help="Top-K cut-off, 1 to number of candidates")
    args = parser.parse_args()
    try:
        fixture = json.loads(args.input.read_text(encoding="utf-8"))
        report = evaluate_semantic_fixture(fixture, k=args.k)
    except (OSError, ValueError, TypeError, SemanticEvaluationInputError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
