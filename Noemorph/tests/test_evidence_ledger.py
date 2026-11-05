"""Local claim-review ledger: immutable history, provenance, and read-only API."""
from __future__ import annotations

import copy
import sqlite3
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api import create_app
from backend.catalog import CatalogRepository
from backend.evidence_ledger import (
    ClaimEvidenceLedger,
    EvidenceIntegrityError,
    EvidenceReviewError,
    initialize_evidence_database,
)


APP_DIR = Path(__file__).resolve().parents[1]


class ClaimEvidenceLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "reviews" / "local.sqlite3"
        self.catalog = CatalogRepository(APP_DIR / "data" / "catalog.json")
        self.ledger = ClaimEvidenceLedger(self.db, self.catalog)
        self.record_id = "seed-026-global-workspace-theory-gwt"
        self.record = self.catalog.get(self.record_id)
        assert self.record is not None
        self.claim = self.record["claim_reviews"][0]
        self.claim_id = self.claim["id"]
        self.lead = self.claim["citations"][0]
        self.args = {
            "record_id": self.record_id,
            "claim_id": self.claim_id,
            "citation_url": self.lead["citation_url"],
            "decision": "contextualizes",
            "locator_kind": "section",
            "locator": "Section 2, paragraph 3",
            "note": "The nominated section is relevant background; confirm claim scope.",
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def record_review(self, reviewer: str = "reviewer-a", **overrides):
        return self.ledger.record(
            reviewer_id=reviewer,
            **{**self.args, **overrides},
        )

    def test_reads_do_not_create_a_database(self) -> None:
        status = self.ledger.status()
        self.assertEqual(status["state"], "absent")
        empty = self.ledger.history(self.record_id, self.claim_id)
        self.assertEqual(empty["database_state"], "absent")
        self.assertEqual(empty["events"], [])
        self.assertEqual(empty["sources"][0]["status"], "unreviewed")
        self.assertFalse(self.db.exists())

    def test_append_only_history_and_two_reviewer_concordance(self) -> None:
        initialize_evidence_database(self.db)
        first = self.record_review()
        second = self.record_review("reviewer-b")
        self.assertNotEqual(first["event_hash"], second["event_hash"])
        self.assertEqual(second["previous_hash"], first["event_hash"])
        self.assertEqual(self.ledger.status()["event_count"], 2)
        result = self.ledger.history(self.record_id, self.claim_id)
        self.assertEqual(len(result["events"]), 2)
        self.assertTrue(all(e["current"] for e in result["events"]))
        self.assertTrue(result["relationships_locked"])
        self.assertEqual(result["publication_state"], "review-only")
        self.assertEqual(
            result["sources"][0]["status"], "independent-agreement-recorded"
        )
        self.assertEqual(result["sources"][0]["active_reviewer_count"], 2)
        self.assertTrue(result["sources"][0]["recorded_agreement_is_not_verification"])
        self.assertIn("self-declared", result["identity_note"])

    def test_conflict_and_latest_event_per_reviewer(self) -> None:
        initialize_evidence_database(self.db)
        self.record_review("reviewer-a")
        self.record_review("reviewer-b", decision="inconclusive")
        history = self.ledger.history(self.record_id, self.claim_id)
        self.assertEqual(history["sources"][0]["status"], "disagreement")
        self.record_review("reviewer-b")
        current = self.ledger.history(self.record_id, self.claim_id)
        self.assertEqual(len(current["events"]), 3)
        self.assertEqual(current["sources"][0]["active_reviewer_count"], 2)
        self.assertEqual(
            current["sources"][0]["status"], "independent-agreement-recorded"
        )

    def test_exact_locator_and_short_excerpt_required_for_strong_decisions(self) -> None:
        initialize_evidence_database(self.db)
        with self.assertRaisesRegex(EvidenceReviewError, "excerpt"):
            self.record_review(decision="supports")
        with self.assertRaisesRegex(EvidenceReviewError, "locator"):
            self.record_review(locator_kind="source-url-only")
        with self.assertRaisesRegex(EvidenceReviewError, "locator"):
            self.record_review(locator="whole source")
        with self.assertRaisesRegex(EvidenceReviewError, "reviewer_id"):
            self.record_review(reviewer="a")
        with self.assertRaisesRegex(EvidenceReviewError, "review note"):
            self.record_review(note="short")
        event = self.record_review(
            decision="supports",
            excerpt="A short, locally supplied excerpt of this example passage.",
        )
        self.assertEqual(event["decision"], "supports")
        self.assertEqual(event["publication_state"], "review-only")

    def test_rejects_non_nominated_source_or_unknown_claim(self) -> None:
        initialize_evidence_database(self.db)
        with self.assertRaisesRegex(EvidenceReviewError, "nominated"):
            self.record_review(citation_url="https://example.org/other")
        with self.assertRaisesRegex(EvidenceReviewError, "Unknown claim"):
            self.record_review(claim_id="incorrect-claim-id")
        self.assertEqual(self.ledger.status()["event_count"], 0)

    def test_database_triggers_prevent_update_and_delete(self) -> None:
        initialize_evidence_database(self.db)
        self.record_review()
        with sqlite3.connect(self.db) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("UPDATE evidence_events SET note = 'tampered'")
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("DELETE FROM evidence_events")

    def test_hash_chain_detects_manual_tampering(self) -> None:
        initialize_evidence_database(self.db)
        self.record_review()
        self.record_review("reviewer-b")
        with sqlite3.connect(self.db) as connection:
            connection.execute("DROP TRIGGER evidence_events_no_update")
            connection.execute(
                "UPDATE evidence_events SET note = ? WHERE id = 1",
                ("A falsified, untracked revision of the original evidence review.",),
            )
            connection.commit()
        with self.assertRaises(EvidenceIntegrityError):
            self.ledger.status()

    def test_changed_claim_text_makes_prior_events_stale(self) -> None:
        initialize_evidence_database(self.db)
        self.record_review()

        class ModifiedCatalog:
            def __init__(self, base):
                self.base = base

            def get(self, record_id):
                existing = self.base.get(record_id)
                if existing is None:
                    return None
                record = copy.deepcopy(existing)
                record["claim_reviews"][0]["text"] += " A revised interpretation."
                return record

        shifted = ClaimEvidenceLedger(self.db, ModifiedCatalog(self.catalog))
        history = shifted.history(self.record_id, self.claim_id)
        self.assertEqual(len(history["events"]), 1)
        self.assertFalse(history["events"][0]["current"])
        self.assertEqual(history["sources"][0]["active_reviewer_count"], 0)
        self.assertEqual(history["sources"][0]["status"], "unreviewed")

    def test_api_exposes_history_but_never_accepts_write(self) -> None:
        initialize_evidence_database(self.db)
        self.record_review()
        app = create_app(
            APP_DIR, serve_frontend=False,
            claim_evidence_db_path=self.db,
        )
        with TestClient(app, client=("127.0.0.1", 5555)) as client:
            status = client.get("/api/claim-evidence/status")
            self.assertEqual(status.status_code, 200)
            self.assertEqual(status.json()["event_count"], 1)
            self.assertEqual(status.headers["cache-control"], "no-store")
            item = client.get(
                f"/api/claim-evidence/records/{self.record_id}/claims/{self.claim_id}"
            )
            self.assertEqual(item.status_code, 200)
            self.assertEqual(item.json()["publication_state"], "review-only")
            self.assertEqual(len(item.json()["events"]), 1)
            self.assertEqual(
                client.post("/api/claim-evidence/status", json=self.args).status_code,
                405,
            )
            self.assertEqual(
                client.get(
                    f"/api/claim-evidence/records/{self.record_id}/claims/not-a-claim"
                ).status_code,
                404,
            )
            relation = client.get("/api/graph/relationships")
            self.assertEqual(relation.status_code, 423)
            self.assertEqual(self.ledger.status()["event_count"], 1)

        with TestClient(app, client=("192.0.2.22", 4321)) as remote:
            denied = remote.get("/api/claim-evidence/status")
            self.assertEqual(denied.status_code, 403)
            denied_history = remote.get(
                f"/api/claim-evidence/records/{self.record_id}/claims/{self.claim_id}"
            )
            self.assertEqual(denied_history.status_code, 403)


if __name__ == "__main__":
    unittest.main()
