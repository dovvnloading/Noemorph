"""Verify that the published catalog and current coverage summary agree with source data."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Noemorph"))

from backend.catalog import CatalogRepository  # noqa: E402


class PublicExportIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snapshot = CatalogRepository(
            ROOT / "Noemorph" / "data" / "catalog.json"
        )._load_if_changed()

    def test_export_matches_validated_snapshot(self) -> None:
        export_path = ROOT / "public-site" / "dist" / "catalog.json"
        exported = json.loads(export_path.read_text(encoding="utf-8"))
        self.assertEqual(set(exported), {"metadata", "records"})
        self.assertEqual(exported["metadata"], self.snapshot.metadata)
        self.assertEqual(exported["records"], list(self.snapshot.records))

    def test_current_coverage_report_agrees_with_source_data(self) -> None:
        report_path = ROOT / "Noemorph" / "data" / "coverage-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        reviewed = report["reviewed_catalog"]
        records = self.snapshot.records

        self.assertEqual(reviewed["record_count"], len(records))
        self.assertEqual(
            reviewed["citation_count"],
            sum(len(record["citations"]) for record in records),
        )
        self.assertEqual(
            reviewed["unique_source_count"], len(self.snapshot.sources)
        )
        self.assertEqual(
            reviewed["full_research_profile_count"],
            sum(
                all(
                    record.get(field)
                    for field in (
                        "claim_scope",
                        "boundary_note",
                        "evidence_profile",
                        "open_questions",
                    )
                )
                for record in records
            ),
        )
        self.assertEqual(report["coverage_gate"], "locked")


if __name__ == "__main__":
    unittest.main()
