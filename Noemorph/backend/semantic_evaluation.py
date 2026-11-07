"""Deterministic metrics for a separately reviewed semantic candidate fixture.

This module does not label pairs, authenticate reviewers, interpret claims, or
unlock conceptual relationships. Missing labels are never treated as negatives.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

LABELS = frozenset({"related", "unrelated"})
FIXTURE_KINDS = frozenset({"synthetic_ci_smoke", "reviewed"})


class SemanticEvaluationInputError(ValueError):
    """Invalid or misleading semantic evaluation fixture."""


def _pair(row: Any) -> tuple[str, str]:
    if not isinstance(row, Mapping):
        raise SemanticEvaluationInputError("Each pair must be an object")
    left = row.get("record_a_id")
    right = row.get("record_b_id")
    if not isinstance(left, str) or not left.strip():
        raise SemanticEvaluationInputError("record_a_id must be a non-empty string")
    if not isinstance(right, str) or not right.strip():
        raise SemanticEvaluationInputError("record_b_id must be a non-empty string")
    if left != left.strip() or right != right.strip() or left == right:
        raise SemanticEvaluationInputError("Pair IDs must be trimmed and distinct")
    return tuple(sorted((left, right)))


def _rows(fixture: Mapping[str, Any], key: str) -> list[Any]:
    rows = fixture.get(key)
    if not isinstance(rows, list) or not rows:
        raise SemanticEvaluationInputError(f"{key} must be a non-empty list")
    return rows


def evaluate_semantic_fixture(fixture: Mapping[str, Any], *, k: int) -> dict[str, Any]:
    """Score a frozen ranking against adjudicated labels, with explicit coverage.

    `precision_at_k` and `false_discovery_fraction_at_k` are null unless all
    top-K candidates have an adjudicated label. An additional judged-only
    precision is provided with the denominator and coverage clearly exposed.
    """
    if not isinstance(fixture, Mapping) or fixture.get("schema_version") != 1:
        raise SemanticEvaluationInputError("Expected semantic evaluation schema_version 1")
    kind = fixture.get("fixture_kind")
    if kind not in FIXTURE_KINDS:
        raise SemanticEvaluationInputError("fixture_kind must be synthetic_ci_smoke or reviewed")

    ranked: list[tuple[float, tuple[str, str], bool]] = []
    seen_ranked: set[tuple[str, str]] = set()
    for row in _rows(fixture, "candidates"):
        pair = _pair(row)
        if pair in seen_ranked:
            raise SemanticEvaluationInputError(f"Duplicate candidate pair: {pair}")
        seen_ranked.add(pair)
        score = row.get("review_priority")
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise SemanticEvaluationInputError("review_priority must be numeric")
        if not math.isfinite(score) or not 0.0 <= score <= 1.0:
            raise SemanticEvaluationInputError("review_priority must be finite and in [0,1]")
        cross_domain = row.get("cross_domain")
        if not isinstance(cross_domain, bool):
            raise SemanticEvaluationInputError("cross_domain must be boolean")
        ranked.append((float(score), pair, cross_domain))

    if isinstance(k, bool) or not isinstance(k, int) or not 1 <= k <= len(ranked):
        raise SemanticEvaluationInputError("k must be an integer within the ranked list")
    # Stable tie-breaking makes the report independent of input iteration order.
    ranked.sort(key=lambda item: (-item[0], item[1]))

    adjudications: dict[tuple[str, str], dict[str, str]] = {}
    for row in _rows(fixture, "adjudications"):
        pair = _pair(row)
        if pair in adjudications:
            raise SemanticEvaluationInputError(f"Duplicate adjudicated pair: {pair}")
        labels = {}
        for field in ("adjudicated_label", "reviewer_a", "reviewer_b"):
            value = row.get(field)
            if value not in LABELS:
                raise SemanticEvaluationInputError(f"{field} must be related or unrelated")
            labels[field] = value
        adjudications[pair] = labels

    top = ranked[:k]
    judged = [adjudications[pair] for _, pair, _ in top if pair in adjudications]
    related = sum(item["adjudicated_label"] == "related" for item in judged)
    unrelated = len(judged) - related
    coverage = len(judged) / k

    annotations = list(adjudications.values())
    observed_agreement = sum(
        item["reviewer_a"] == item["reviewer_b"] for item in annotations
    ) / len(annotations)
    a_related = sum(item["reviewer_a"] == "related" for item in annotations) / len(annotations)
    b_related = sum(item["reviewer_b"] == "related" for item in annotations) / len(annotations)
    chance_agreement = a_related * b_related + (1 - a_related) * (1 - b_related)
    kappa = (
        (observed_agreement - chance_agreement) / (1 - chance_agreement)
        if not math.isclose(chance_agreement, 1.0)
        else None
    )

    def rounded(value: float | None) -> float | None:
        return round(value, 6) if value is not None else None

    return {
        "schema_version": 1,
        "fixture_kind": kind,
        "synthetic_smoke_only": kind == "synthetic_ci_smoke",
        "labels_authenticated_by_software": False,
        "relationship_synthesis_locked": True,
        "ranked_candidates": len(ranked),
        "adjudicated_pairs": len(adjudications),
        "k": k,
        "judged_at_k": len(judged),
        "unjudged_at_k": k - len(judged),
        "coverage_at_k": rounded(coverage),
        "related_at_k": related,
        "unrelated_at_k": unrelated,
        "precision_at_k": rounded(related / k) if len(judged) == k else None,
        "false_discovery_fraction_at_k": (
            rounded(unrelated / k) if len(judged) == k else None
        ),
        "judged_only_precision_at_k": rounded(related / len(judged)) if judged else None,
        "cross_domain_at_k": sum(cross_domain for _, _, cross_domain in top),
        "reviewer_pair_count": len(annotations),
        "observed_reviewer_agreement": rounded(observed_agreement),
        "cohens_kappa": rounded(kappa),
    }
