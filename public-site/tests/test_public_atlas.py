"""The public visual atlas is a taxonomic rendering, never a theory relationship graph."""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import unittest
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Noemorph"))

from backend.catalog import CatalogRepository  # noqa: E402


class PublicAtlasIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = CatalogRepository(ROOT / "Noemorph/data/catalog.json")
        cls.snapshot = cls.repo._load_if_changed()

    def test_catalog_has_reversible_kind_domain_record_classification(self) -> None:
        kinds: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
        for record in self.snapshot.records:
            self.assertTrue(record["kind"].strip())
            self.assertTrue(record["domain"].strip())
            self.assertRegex(record["id"], r"^[A-Za-z0-9_-]{1,160}$")
            self.assertNotIn(record["id"], kinds[record["kind"]][record["domain"]])
            kinds[record["kind"]][record["domain"]].add(record["id"])
        self.assertEqual(len(self.snapshot.records), 595)
        self.assertEqual(len(kinds), 8)
        self.assertEqual(
            sum(len(entries) for domains in kinds.values() for entries in domains.values()),
            len(self.snapshot.records),
        )
        self.assertGreater(
            max(len(domains) for domains in kinds.values()), 16,
            "Atlas domain pagination must support taxonomy fragmentation",
        )

    def test_existing_backend_graph_exposes_only_organizational_edges(self) -> None:
        graph = self.repo.taxonomy_graph()
        self.assertIn("Theory-to-theory synthesis is locked", graph["edge_policy"])
        record_ids = set(self.snapshot.by_id)
        for edge in graph["links"]:
            self.assertIn(edge["kind"], {"organizational", "classification"})
            if edge["source"] in record_ids:
                self.fail("No record may link to another record as a conceptual edge")
        self.assertEqual(
            len([edge for edge in graph["links"] if edge["target"] in record_ids]),
            len(record_ids),
        )
        self.assertEqual(self.snapshot.metadata["coverage_gate"], "locked")

    def test_static_site_reuses_validated_catalog_and_offers_accessible_fallback(self) -> None:
        page = (ROOT / "public-site/dist/index.html").read_text(encoding="utf-8")
        script = (ROOT / "public-site/dist/atlas.js").read_text(encoding="utf-8")
        app = (ROOT / "public-site/dist/app.js").read_text(encoding="utf-8")
        self.assertLess(page.index('src="atlas.js"'), page.index('src="app.js"'))
        self.assertIn('id="atlas-svg"', page)
        self.assertIn('id="atlas-node-list"', page)
        self.assertIn('id="atlas-status"', page)
        self.assertIn('id="atlas-kind-filter"', page)
        self.assertIn('id="atlas-search"', page)
        self.assertIn('href="#catalog"', page)
        self.assertIn("window.NoemorphAtlas?.mount(records)", app)
        self.assertIn("No theory-to-theory links", page)
        self.assertNotIn("semantic_similarity", script)
        self.assertNotIn("/api/graph/relationships", script)
        self.assertIn("The research-synthesis gate remains locked.", page)


if __name__ == "__main__":
    unittest.main()
