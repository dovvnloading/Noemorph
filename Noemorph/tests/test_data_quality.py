"""Research data audit: reproducible, non-promotional, and source-specific."""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from backend.data_quality import data_quality_report
from research.audit_data_quality import build, main

APP_DIR = Path(__file__).resolve().parents[1]


class DataQualityAuditTests(unittest.TestCase):
    def test_current_corpus_is_audited_without_mutation(self) -> None:
        report = build()
        summary = report["summary"]
        self.assertEqual(summary["record_count"], 595)
        self.assertEqual(summary["citation_occurrences"], 1256)
        self.assertEqual(summary["unique_source_keys"], 1045)
        self.assertEqual(summary["incomplete_profile_count"], 132)
        self.assertEqual(summary["records_without_primary_anchor"], 131)
        self.assertEqual(summary["pending_metadata_citation_occurrences"], 79)
        self.assertEqual(summary["unreviewed_claim_source_leads"], 20)
        self.assertEqual(
            len(report["potential_work_metadata_conflicts"]),
            summary["potential_work_metadata_conflict_groups"],
        )
        self.assertGreater(summary["potential_work_metadata_conflict_groups"], 0)
        self.assertIn("not proof", report["limitations"])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "quality.json"
            self.assertEqual(main(["--output", str(output)]), 0)
            self.assertEqual(main(["--output", str(output), "--check"]), 0)
            output.write_text("{}", encoding="utf-8")
            self.assertEqual(main(["--output", str(output), "--check"]), 1)

    def test_metadata_variants_are_review_leads_not_auto_corrections(self) -> None:
        common_citation = {
            "url": "https://example.org/work",
            "title": "Original Work",
            "year": 2025,
            "authority": "primary-original",
            "verification": "doi-resolved",
        }
        first = {
            "id": "a", "kind": "Scientific theory", "domain": "Neural dynamics",
            "status": "provisional", "citations": [common_citation],
        }
        second = {
            "id": "b", "kind": "Scientific theory", "domain": "Neural dynamics",
            "status": "provisional",
            "citations": [{**common_citation, "year": 2026}],
        }
        originals = copy.deepcopy([first, second])
        result = data_quality_report(
            [second, first], catalog_version="test", corpus_date="test"
        )
        reverse = data_quality_report(
            [first, second], catalog_version="test", corpus_date="test"
        )
        self.assertEqual(result, reverse)
        self.assertEqual([first, second], originals)
        conflicts = result["potential_work_metadata_conflicts"]
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["year_variants"], ["2025", "2026"])
        self.assertEqual(conflicts[0]["disposition"], "review-needed")
        self.assertEqual(result["classification_fragmentation"]["domains"]["distinct"], 1)

    def test_duplicate_record_id_is_rejected(self) -> None:
        duplicate = {"id": "duplicate"}
        with self.assertRaisesRegex(ValueError, "unique"):
            data_quality_report(
                [duplicate, duplicate], catalog_version="test", corpus_date="test"
            )


if __name__ == "__main__":
    unittest.main()
