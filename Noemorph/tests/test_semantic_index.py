from __future__ import annotations

import json
import unittest
from pathlib import Path

from backend.catalog import CatalogRepository
from backend.semantic import SemanticRepository
from research.build_semantic_index import (
    build_text_units,
    identity_label_similarity,
    relation_type_for,
)


APP_DIR = Path(__file__).resolve().parents[1]


class SemanticIndexRecipeTests(unittest.TestCase):
    def test_conceptual_view_excludes_identity_taxonomy_and_citations(self) -> None:
        record = {
            "id": "recipe-test",
            "name": "Identity marker must stay out",
            "aliases": ["Alias marker must stay out"],
            "kind": "Scientific theory",
            "domain": "Taxonomy marker must stay out",
            "tradition": "Tradition marker must stay out",
            "status": "Status marker must stay out",
            "summary": "Conscious access depends on recurrent integration.",
            "scope": "Access and report.",
            "claim_scope": {
                "target": "Recurrent integration of conscious contents.",
                "does_not_establish": "This does not establish metaphysical identity.",
            },
            "evidence_profile": {
                "basis": ["Perturbation and report paradigms."],
                "limitations": ["Report is not experience."],
            },
            "open_questions": ["Can no-report measures isolate recurrence?"],
            "boundary_note": "Not a complete theory of phenomenal character.",
            "status_note": "Provisional.",
            "proponents": ["Author Marker"],
            "citations": [
                {"title": "Citation Marker", "authors": "Author Marker"}
            ],
        }
        views = build_text_units([record])
        core = views["core_claim"][0].text
        limits = views["limits"][0].text
        identity = views["identity"][0].text

        self.assertIn("recurrent integration", core.casefold())
        self.assertNotIn("identity marker", core.casefold())
        self.assertNotIn("taxonomy marker", core.casefold())
        self.assertNotIn("author marker", core.casefold())
        self.assertNotIn("citation marker", core.casefold())
        self.assertNotIn("does not establish", core.casefold())
        self.assertIn("does not establish", limits.casefold())
        self.assertIn("identity marker", identity.casefold())
        self.assertIn("citation marker", identity.casefold())

    def test_duplicate_typing_requires_label_similarity_not_vector_proximity(self) -> None:
        unrelated = identity_label_similarity(
            {"name": "Perturbational Complexity Index", "aliases": []},
            {"name": "Weighted Symbolic Mutual Information", "aliases": []},
        )
        alias_match = identity_label_similarity(
            {"name": "Global Workspace Theory", "aliases": ["GWT"]},
            {"name": "GWT", "aliases": []},
        )
        self.assertLess(unrelated, 0.74)
        self.assertEqual(alias_match, 1.0)
        self.assertNotEqual(
            relation_type_for(
                percentiles={"core_claim": 0.999, "target": 0.99, "evidence": 0.99},
                question_percentile=0.2,
                cross_tradition=True,
                identity_percentile=0.999,
                identity_name_similarity=unrelated,
            ),
            "possible_duplicate",
        )
        self.assertEqual(
            relation_type_for(
                percentiles={"core_claim": 0.999, "target": 0.99, "evidence": 0.99},
                question_percentile=0.2,
                cross_tradition=True,
                identity_percentile=0.999,
                identity_name_similarity=alias_match,
            ),
            "possible_duplicate",
        )


class GeneratedSemanticArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not (APP_DIR / "data" / "semantic" / "semantic.sqlite3").exists():
            raise unittest.SkipTest("Generated semantic artifact is not distributed; build it locally to test it")
        cls.catalog = CatalogRepository(APP_DIR / "data" / "catalog.json")
        cls.repository = SemanticRepository(
            APP_DIR / "data" / "semantic" / "semantic.sqlite3",
            cls.catalog,
        )

    def all_candidates(self) -> tuple[list[dict], int]:
        items: list[dict] = []
        offset = 0
        total = 0
        while True:
            page, total, _ = self.repository.list_candidates(
                offset=offset,
                limit=500,
            )
            items.extend(page)
            if not page or len(items) >= total:
                return items, total
            offset += len(page)

    def test_generated_artifact_is_current_sparse_and_review_only(self) -> None:
        status = self.repository.status()
        self.assertTrue(status["ready"], status.get("detail"))
        self.assertTrue(status["relationship_synthesis_locked"])
        record_count = self.catalog.coverage()["record_count"]
        self.assertEqual(status["catalog"]["record_count"], record_count)
        self.assertEqual(status["run"]["recipe"]["comparison"], "exact all-pairs")
        self.assertEqual(
            status["run"]["recipe"]["pair_count"],
            record_count * (record_count - 1) // 2,
        )
        candidate_count = status["counts"]["total"]
        self.assertGreaterEqual(candidate_count, 150)
        self.assertLess(candidate_count, status["run"]["recipe"]["pair_count"])
        self.assertEqual(
            status["counts"]["by_disposition"],
            {"unreviewed": candidate_count},
        )

    def test_generated_candidates_retain_inputs_controls_and_no_publication_claim(self) -> None:
        items, total = self.all_candidates()
        self.assertGreaterEqual(total, 150)
        self.assertEqual(len(items), total)
        self.assertTrue(any(item["cross_domain"] for item in items))
        self.assertTrue(any("scope-barrier-signal" in item["flags"] for item in items))
        priorities = [item["review_priority"] for item in items]
        self.assertEqual(priorities, sorted(priorities, reverse=True))
        self.assertGreater(len(set(priorities)), int(total * 0.9))

        for item in items:
            self.assertEqual(item["disposition"], "unreviewed")
            self.assertEqual(set(item["input_hashes"]), {item["record_a_id"], item["record_b_id"]})
            contribution = item["contributions"]
            self.assertFalse(contribution["publication_eligible"])
            self.assertIn(contribution["confidence_tier"], {"T0", "T1"})
            self.assertIn(
                contribution["selection_phase"],
                {"prior-art", "priority", "coverage", "priority-fill"},
            )
            self.assertEqual(
                contribution["novelty"]["literature_search_status"],
                "not-run",
            )
            self.assertIsInstance(contribution["field_contributions"], list)
            self.assertTrue(contribution["field_contributions"])
            for field_signal in contribution["field_contributions"]:
                self.assertIn("attribution_note", field_signal)
                self.assertIn("representative", field_signal["attribution_note"].casefold())

    def test_manifest_matches_database_run(self) -> None:
        manifest = json.loads(
            (APP_DIR / "data" / "semantic" / "semantic-run.json").read_text(
                encoding="utf-8"
            )
        )
        status = self.repository.status()
        self.assertEqual(manifest["run_id"], status["run"]["id"])
        self.assertEqual(manifest["catalog_hash"], status["run"]["catalog_hash"])
        self.assertEqual(manifest["candidate_count"], status["counts"]["total"])
        prior_art = json.loads(
            (APP_DIR / "data" / "semantic" / "prior-art-screen.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            manifest["screened_candidate_count"],
            prior_art["metadata"]["entry_count"],
        )

    def test_focused_prior_art_is_separate_cited_and_non_novelty_claiming(self) -> None:
        items, _ = self.all_candidates()
        screened = [
            item for item in items if "prior_art" in item["contributions"]
        ]
        prior_art = json.loads(
            (APP_DIR / "data" / "semantic" / "prior-art-screen.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(len(screened), prior_art["metadata"]["entry_count"])
        for item in screened:
            self.assertEqual(item["contributions"]["selection_phase"], "prior-art")
            prior_art = item["contributions"]["prior_art"]
            self.assertTrue(prior_art["sources"])
            self.assertTrue(
                all(source["url"].startswith("https://") for source in prior_art["sources"])
            )
            combined = " ".join(
                (
                    prior_art["direct_comparison"],
                    prior_art["assessment"],
                    prior_art["caution"],
                )
            ).casefold()
            self.assertNotIn("never previously", combined)
            self.assertNotIn("groundbreaking", combined)


if __name__ == "__main__":
    unittest.main()
