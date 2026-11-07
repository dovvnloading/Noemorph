from __future__ import annotations

import copy
import unittest

from backend.editorial_triage import editorial_triage_report


def record(record_id: str, *, pending: bool = True) -> dict:
    url = f"https://example.org/{record_id}"
    return {
        "id": record_id, "name": f"Unreviewed {record_id}",
        "kind": "Scientific theory", "domain": "Synthetic", "status": "Provisional",
        "citations": [{
            "url": url, "title": "Synthetic citation", "year": "2026",
            "authority": "contextual-test",
            "verification": "pending-metadata-review" if pending else "human-verified",
        }],
        "claim_reviews": [{
            "id": f"{record_id}:claim", "field": "summary",
            "citations": [{"source_uid": f"work-{record_id}",
                           "citation_url": url, "review_state": "unreviewed"}],
        }],
    }


class EditorialTriageTests(unittest.TestCase):
    def make(self, rows: list[dict], limit: int = 25) -> dict:
        return editorial_triage_report(rows, catalog_version="fixture-v1",
                                       corpus_date="2026-11-07", profile_limit=limit)

    def test_stable_order_and_no_mutation(self) -> None:
        rows = [record("z"), record("a"), record("m", pending=False)]
        before = copy.deepcopy(rows)
        a = self.make(rows, limit=2)
        self.assertEqual(rows, before)
        self.assertEqual(a, self.make(list(reversed(rows)), limit=2))
        self.assertEqual(a["queue_state"], "unreviewed-human-work")
        self.assertEqual(a["independent_approvals"], 0)
        self.assertTrue(a["relationship_synthesis_locked"])
        self.assertEqual(a["summary"]["proposed_profile_tranche_count"], 2)
        self.assertEqual(a["summary"]["unreviewed_claim_source_leads"], 3)
        self.assertEqual(a["summary"]["pending_citation_occurrences"], 2)

    def test_rejects_bad_limit_and_duplicates(self) -> None:
        for bad in (0, True, -1):
            with self.assertRaises(ValueError):
                self.make([record("a")], limit=bad)
        with self.assertRaises(ValueError):
            self.make([record("a"), record("a")])


if __name__ == "__main__":
    unittest.main()
