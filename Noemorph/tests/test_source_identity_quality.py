"""Non-destructive source-work metadata identity diagnostics."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.catalog import CatalogRepository
from backend.data_quality import data_quality_report


def make_record(record_id: str, title: str, year: int) -> dict:
    return {
        "id": record_id, "name": record_id, "kind": "Scientific theory",
        "domain": "Test", "tradition": "Test", "status": "provisional",
        "summary": "A research example.", "proponents": [],
        "citations": [
            {
                "title": title, "authors": "A. Researcher", "year": year,
                "url": "https://doi.org/10.1000/shared-work", "doi": "10.1000/shared-work",
                "authority": "primary-original" if record_id == "a" else "scholarly-secondary",
                "verification": "doi-resolved",
            },
            {
                "title": "Distinct work for " + record_id,
                "authors": "B. Researcher", "year": 2024,
                "url": "https://example.org/unique-" + record_id,
                "authority": "scholarly-secondary",
                "verification": "locator-recorded",
            },
        ],
    }


class SourceIdentityVariantTests(unittest.TestCase):
    def test_review_leads_preserve_source_id_and_per_use_roles(self) -> None:
        records = [make_record("a", "Proposed title", 2025), make_record("b", "Revised title", 2026)]
        report = CatalogRepository._validate({"metadata": {"version": "test"}, "records": records})
        self.assertEqual(report.metadata, {"version": "test"})
        shared = next(source for source in report.sources if source["doi"] == "10.1000/shared-work")
        self.assertEqual(shared["id"], "src-0001")
        self.assertEqual(shared["metadata_conflict_fields"], ["title", "year"])
        self.assertEqual(shared["work_identity_review_state"], "needs-review")
        self.assertEqual(len(shared["metadata_variants"]), 2)
        self.assertEqual({v["title"] for v in shared["metadata_variants"]}, {"Proposed title", "Revised title"})
        self.assertEqual({tuple(v["record_ids"]) for v in shared["metadata_variants"]}, {("a",), ("b",)})
        self.assertEqual(shared["authority_roles"], ["primary-original", "scholarly-secondary"])
        self.assertEqual(shared["verification_states"], ["doi-resolved"])
        self.assertNotIn("authority", shared)
        self.assertNotIn("verification", shared)
        self.assertTrue(all("metadata_conflict_fields" in source for source in report.sources))
        self.assertEqual(
            [source["source_uid"] for source in report.sources if source["doi"]],
            [report.by_id["a"]["citations"][0]["source_uid"]],
        )
        self.assertFalse(any(source["metadata_conflict_fields"] for source in report.sources if source["doi"] is None))

        audit = data_quality_report(report.records, catalog_version="test", corpus_date="test")
        self.assertEqual(audit["summary"]["potential_work_metadata_conflict_groups"], 1)

    def test_variant_order_is_independent_of_catalog_order(self) -> None:
        records = [make_record("a", "A title", 2025), make_record("b", "B title", 2026)]
        originals = [
            CatalogRepository._validate({"metadata": {}, "records": order})
            for order in (records, list(reversed(records)))
        ]
        variant_sets = [
            next(source for source in snap.sources if source["doi"])["metadata_variants"]
            for snap in originals
        ]
        self.assertEqual(variant_sets[0], variant_sets[1])
        self.assertEqual(
            originals[0].by_id["a"]["citations"][0]["source_uid"],
            originals[1].by_id["a"]["citations"][0]["source_uid"],
        )
        # Historical display metadata remains first-use based until human review.
        self.assertNotEqual(
            next(source for source in originals[0].sources if source["doi"])["title"],
            next(source for source in originals[1].sources if source["doi"])["title"],
        )

    def test_complete_catalog_flags_all_potential_work_conflicts(self) -> None:
        root = Path(__file__).resolve().parents[1]
        repo = CatalogRepository(root / "data" / "catalog.json")
        catalog = repo._load_if_changed()
        conflicts = [source for source in catalog.sources if source["work_identity_review_state"] == "needs-review"]
        audit = data_quality_report(
            catalog.records,
            catalog_version=str(catalog.metadata["version"]),
            corpus_date=str(catalog.metadata["generated_at"]),
        )
        self.assertEqual(len(conflicts), audit["summary"]["potential_work_metadata_conflict_groups"])
        self.assertTrue(all(source["metadata_variants"] for source in conflicts))
        self.assertTrue(all(source["metadata_conflict_fields"] for source in conflicts))


if __name__ == "__main__":
    unittest.main()
