"""Regression checks for source-bounded research depth and reproducible triage."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api import create_app
from backend.catalog import CatalogRepository
from backend.profile_quality import REQUIRED_PROFILE_FIELDS, profile_quality_report
from research.build_profile_quality_report import build, main

APP_DIR = Path(__file__).resolve().parents[1]
TRANCHE_FILE = "catalog-2026-11-05-profile-depth-tranche-1.json"


class ProfileQualityIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = CatalogRepository(APP_DIR / "data" / "catalog.json")
        cls.snapshot = cls.repo._load_if_changed()
        cls.base = json.loads(
            (APP_DIR / "data" / "catalog.json").read_text(encoding="utf-8")
        )
        cls.tranche = json.loads(
            (APP_DIR / "data" / TRANCHE_FILE).read_text(encoding="utf-8")
        )
        cls.report = cls.repo.profile_quality()

    def test_exactly_ten_profiles_repaired_without_new_records_or_citations(self) -> None:
        self.assertEqual(len(self.snapshot.records), 595)
        self.assertEqual(len(self.tranche["profiles"]), 10)
        self.assertEqual(self.tranche["collection"]["record_count"], 10)
        self.assertEqual(self.tranche["collection"]["review_requirement"][:3], "All")
        by_id = self.snapshot.by_id
        base_by_id = {record["id"]: record for record in self.base["records"]}
        for profile in self.tranche["profiles"]:
            with self.subTest(id=profile["id"]):
                self.assertEqual(
                    set(profile),
                    {"id", *REQUIRED_PROFILE_FIELDS},
                )
                record = by_id[profile["id"]]
                before = base_by_id[profile["id"]]
                self.assertEqual(record["name"], before["name"])
                self.assertEqual(record["kind"], before["kind"])
                self.assertEqual(record["status"], before["status"])
                self.assertEqual(record["review_state"], before["review_state"])
                self.assertEqual(
                    [
                        (c["url"], c.get("verification"), c["authority"])
                        for c in record["citations"]
                    ],
                    [
                        (c["url"], c.get("verification"), c["authority"])
                        for c in before["citations"]
                    ],
                )
                self.assertTrue(
                    all(record.get(field) for field in REQUIRED_PROFILE_FIELDS)
                )
                self.assertGreater(
                    len(profile["evidence_profile"]["independence"]), 60
                )
                self.assertFalse(record.get("claim_reviews"))
        manifests = self.snapshot.metadata["profile_collections"]
        self.assertEqual(manifests[-1]["file"], TRANCHE_FILE)
        self.assertEqual(manifests[-1]["profile_count"], 10)

    def test_report_is_current_and_committed_snapshot_is_reproducible(self) -> None:
        report = self.report
        summary = report["summary"]
        self.assertEqual(summary["record_count"], 595)
        self.assertEqual(summary["complete_profiles"], 463)
        self.assertEqual(summary["incomplete_profiles"], 132)
        self.assertEqual(summary["citation_occurrences"], 1256)
        self.assertEqual(len(report["backlog"]), 132)
        self.assertEqual(len({item["id"] for item in report["backlog"]}), 132)
        self.assertEqual(
            sum(item["records"] for item in report["by_kind"]), 595
        )
        self.assertEqual(
            sum(item["incomplete_profiles"] for item in report["by_kind"]), 132
        )
        for field in REQUIRED_PROFILE_FIELDS:
            self.assertEqual(
                summary["missing_required_field_counts"][field], 132
            )
        self.assertIn("not evidential support", report["limitations"])
        committed = json.loads(
            (APP_DIR / "data" / "profile-quality-report.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(build(), report)
        self.assertEqual(committed, report)
        self.assertEqual(main(["--check"]), 0)

    def test_coverage_report_is_in_sync_after_enrichment(self) -> None:
        report = json.loads(
            (APP_DIR / "data" / "coverage-report.json").read_text(
                encoding="utf-8"
            )
        )
        reviewed = report["reviewed_catalog"]
        self.assertEqual(reviewed["record_count"], 595)
        self.assertEqual(reviewed["citation_count"], 1256)
        self.assertEqual(reviewed["full_research_profile_count"], 463)
        self.assertEqual(reviewed["research_profile_gap_count"], 132)
        self.assertEqual(
            reviewed["profile_enrichments"][-1]["file"], TRANCHE_FILE
        )
        self.assertEqual(report["coverage_gate"], "locked")

    def test_live_api_reports_current_unverified_editorial_quality(self) -> None:
        app = create_app(APP_DIR, serve_frontend=False)
        with TestClient(app) as client:
            response = client.get("/api/profile-quality")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), self.report)
            self.assertEqual(
                client.get("/api/graph/relationships").status_code, 423
            )


class SyntheticProfileQualityTests(unittest.TestCase):
    def test_blank_profile_fields_and_pending_citations_receive_workload_priority(self) -> None:
        fixture = {
            "id": "example",
            "name": "Example",
            "kind": "Model or framework",
            "domain": "Concepts",
            "claim_scope": {"target": " "},
            "boundary_note": "",
            "evidence_profile": {},
            "open_questions": [],
            "citations": [
                {
                    "authority": "scholarly-secondary",
                    "verification": "pending-metadata-review",
                },
                {
                    "authority": "scholarly-secondary",
                    "verification": "locator-recorded",
                },
            ],
        }
        result = profile_quality_report(
            [fixture], catalog_version="test", corpus_date="test"
        )
        summary = result["summary"]
        self.assertEqual(summary["incomplete_profiles"], 1)
        gap = result["backlog"][0]
        self.assertEqual(gap["missing_field_count"], 4)
        self.assertEqual(gap["triage_priority"], 46)
        self.assertFalse(gap["has_primary_citation"])
        self.assertEqual(gap["pending_metadata_citations"], 1)
        self.assertIn("not", result["limitations"].lower())

    def test_duplicate_record_ids_rejected(self) -> None:
        row = {
            "id": "dup",
            "name": "Dup",
            "kind": "Scientific theory",
            "domain": "Test",
            "citations": [],
        }
        with self.assertRaisesRegex(ValueError, "duplicate"):
            profile_quality_report(
                [row, row], catalog_version="test", corpus_date="test"
            )


if __name__ == "__main__":
    unittest.main()
