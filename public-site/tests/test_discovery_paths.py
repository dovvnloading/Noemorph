"""The public discovery journey is a curated navigation overlay, never a relationship graph."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Noemorph"))

from backend.catalog import CatalogRepository  # noqa: E402


class PublicDiscoveryIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snapshot = CatalogRepository(ROOT / "Noemorph/data/catalog.json")._load_if_changed()
        cls.config = json.loads(
            (ROOT / "public-site/dist/discovery-journeys.json").read_text(encoding="utf-8")
        )

    def test_every_reading_path_uses_real_catalog_records_and_does_not_repeat_them(self) -> None:
        config = self.config
        by_id = self.snapshot.by_id
        self.assertEqual(config["version"], 1)
        self.assertGreaterEqual(len(config["journeys"]), 4)
        self.assertIn("not imply agreement", config["editorial_policy"])
        ids = [path["id"] for path in config["journeys"]]
        self.assertEqual(len(ids), len(set(ids)))

        for path in config["journeys"]:
            with self.subTest(journey=path["id"]):
                self.assertRegex(path["id"], r"^[a-z-]{2,40}$")
                self.assertGreaterEqual(len(path["steps"]), 3)
                self.assertIn(path["theme"], {"orbit", "signal", "focus", "mirror"})
                self.assertTrue(path["title"].strip())
                self.assertTrue(path["subtitle"].strip())
                record_ids = [step["record_id"] for step in path["steps"]]
                self.assertEqual(len(record_ids), len(set(record_ids)))
                self.assertTrue(set(record_ids).issubset(by_id))
                for step in path["steps"]:
                    self.assertTrue(step["prompt"].strip())
                    self.assertTrue(step["orientation"].strip())
                    self.assertTrue(step["reflection"].strip())
                    self.assertGreaterEqual(
                        len(by_id[step["record_id"]]["citations"]), 2
                    )

    def test_surprise_pool_is_real_and_spans_research_kinds(self) -> None:
        pool = self.config["surprise"]["record_ids"]
        self.assertGreaterEqual(len(pool), 5)
        self.assertEqual(len(pool), len(set(pool)))
        self.assertTrue(set(pool).issubset(self.snapshot.by_id))
        kinds = {self.snapshot.by_id[id]["kind"] for id in pool}
        self.assertGreaterEqual(len(kinds), 3)

    def test_editorial_paths_do_not_add_or_promote_relationships(self) -> None:
        self.assertEqual(self.snapshot.metadata["coverage_gate"], "locked")
        self.assertNotIn("relationship", self.config)
        self.assertNotIn("edges", self.config)
        for path in self.config["journeys"]:
            self.assertFalse(
                set(path) & {"edges", "relations", "claims_verified", "scientific_rank"}
            )
            for step in path["steps"]:
                self.assertEqual(
                    set(step), {"record_id", "prompt", "orientation", "reflection"}
                )
                self.assertNotIn("verification", step)
                self.assertNotIn("evidence_score", step)

    def test_static_page_loads_progressive_guide_before_existing_catalog_script(self) -> None:
        index = (ROOT / "public-site/dist/index.html").read_text(encoding="utf-8")
        self.assertLess(index.index('src="discovery.js"'), index.index('src="app.js"'))
        self.assertIn('href="#discover"', index)
        self.assertIn('id="discovery-stage"', index)
        self.assertIn('id="catalog"', index)


if __name__ == "__main__":
    unittest.main()
