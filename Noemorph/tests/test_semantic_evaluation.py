from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from backend.semantic_evaluation import (
    SemanticEvaluationInputError,
    evaluate_semantic_fixture,
)

FIXTURE = Path(__file__).resolve().parents[1] / "research" / "fixtures" / "semantic_eval_synthetic_v1.json"


class SemanticEvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_known_synthetic_scores_and_reviewer_agreement(self) -> None:
        report = evaluate_semantic_fixture(self.fixture, k=3)
        self.assertTrue(report["synthetic_smoke_only"])
        self.assertFalse(report["labels_authenticated_by_software"])
        self.assertTrue(report["relationship_synthesis_locked"])
        self.assertEqual(report["precision_at_k"], 0.666667)
        self.assertEqual(report["false_discovery_fraction_at_k"], 0.333333)
        self.assertEqual(report["coverage_at_k"], 1.0)
        self.assertEqual(report["cross_domain_at_k"], 2)
        self.assertEqual(report["observed_reviewer_agreement"], 0.75)
        self.assertEqual(report["cohens_kappa"], 0.5)

    def test_unjudged_candidates_are_never_assumed_negative(self) -> None:
        report = evaluate_semantic_fixture(self.fixture, k=4)
        self.assertEqual(report["unjudged_at_k"], 1)
        self.assertEqual(report["coverage_at_k"], 0.75)
        self.assertIsNone(report["precision_at_k"])
        self.assertIsNone(report["false_discovery_fraction_at_k"])
        self.assertEqual(report["judged_only_precision_at_k"], 0.666667)

    def test_candidate_and_label_order_does_not_change_results(self) -> None:
        shuffled = copy.deepcopy(self.fixture)
        shuffled["candidates"].reverse()
        shuffled["adjudications"].reverse()
        self.assertEqual(
            evaluate_semantic_fixture(self.fixture, k=3),
            evaluate_semantic_fixture(shuffled, k=3),
        )

    def test_duplicate_unordered_pairs_rejected(self) -> None:
        broken = copy.deepcopy(self.fixture)
        duplicate = copy.deepcopy(broken["candidates"][0])
        duplicate["record_a_id"], duplicate["record_b_id"] = (
            duplicate["record_b_id"], duplicate["record_a_id"]
        )
        broken["candidates"].append(duplicate)
        with self.assertRaises(SemanticEvaluationInputError):
            evaluate_semantic_fixture(broken, k=3)

    def test_rejects_invalid_labels_scores_and_cutoff(self) -> None:
        broken = copy.deepcopy(self.fixture)
        broken["adjudications"][0]["reviewer_b"] = "unknown"
        with self.assertRaises(SemanticEvaluationInputError):
            evaluate_semantic_fixture(broken, k=3)

        broken = copy.deepcopy(self.fixture)
        broken["candidates"][0]["review_priority"] = float("nan")
        with self.assertRaises(SemanticEvaluationInputError):
            evaluate_semantic_fixture(broken, k=3)

        with self.assertRaises(SemanticEvaluationInputError):
            evaluate_semantic_fixture(self.fixture, k=5)

    def test_requires_explicit_fixture_provenance(self) -> None:
        broken = copy.deepcopy(self.fixture)
        broken["fixture_kind"] = "verified_by_ai"
        with self.assertRaises(SemanticEvaluationInputError):
            evaluate_semantic_fixture(broken, k=3)


if __name__ == "__main__":
    unittest.main()
