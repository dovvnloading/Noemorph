"""Integrity and epistemic-state tests for claim-level source review leads."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from backend.catalog import CatalogIntegrityError, CatalogRepository
from backend.claim_evidence import (
    ClaimReviewIntegrityError,
    apply_claim_review_supplement,
    stable_source_uid,
)


DATA = Path(__file__).resolve().parents[1] / "data"


class PublishedClaimReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snapshot = CatalogRepository(DATA / "catalog.json")._load_if_changed()

    def test_ten_priority_records_have_two_unreviewed_claim_leads_each(self) -> None:
        with_claims = [
            record for record in self.snapshot.records if record.get("claim_reviews")
        ]
        self.assertEqual(len(with_claims), 10)
        self.assertEqual(
            sum(len(record["claim_reviews"]) for record in with_claims), 20
        )
        self.assertEqual(
            len(self.snapshot.metadata["claim_review_collections"]), 1
        )
        manifest = self.snapshot.metadata["claim_review_collections"][0]
        self.assertEqual(manifest["review_state"], "unreviewed-source-leads")
        self.assertEqual(manifest["record_count"], 10)
        self.assertEqual(manifest["claim_count"], 20)
        self.assertEqual(manifest["source_lead_count"], 20)
        for record in with_claims:
            urls = {citation["url"]: citation for citation in record["citations"]}
            self.assertEqual(
                {claim["kind"] for claim in record["claim_reviews"]},
                {"scope", "boundary"},
            )
            for claim in record["claim_reviews"]:
                with self.subTest(record=record["id"], claim=claim["id"]):
                    self.assertTrue(claim["text"])
                    if claim["kind"] == "scope":
                        self.assertEqual(claim["field"], "summary")
                        self.assertEqual(claim["text"], record["summary"])
                    self.assertEqual(claim["review_state"], "unreviewed")
                    self.assertTrue(claim["id"].startswith(record["id"] + ":"))
                    self.assertEqual(len(claim["citations"]), 1)
                    for lead in claim["citations"]:
                        citation = urls[lead["citation_url"]]
                        self.assertEqual(lead["locator_kind"], "source-url-only")
                        self.assertEqual(lead["review_state"], "unreviewed")
                        self.assertEqual(
                            lead["source_uid"], citation["source_uid"]
                        )
                        self.assertNotIn("evidence_stance", lead)
                        self.assertNotIn("passage", lead)

    def test_stable_source_uid_does_not_depend_on_legacy_source_order(self) -> None:
        a = {"doi": "10.1000/SomeWork", "url": "https://doi.org/10.1000/SomeWork"}
        b = {"doi": "10.1000/somework", "url": "https://example.org/alternate"}
        self.assertEqual(stable_source_uid(a), stable_source_uid(b))
        self.assertTrue(stable_source_uid(a).startswith("work-"))
        self.assertEqual(len(stable_source_uid(a)), 29)


class ClaimReviewRejectsOverclaimsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.record = {
            "id": "example-record",
            "summary": "A provisional research claim.",
            "claim_scope": {"target": "The research target."},
            "boundary_note": "The claim does not establish a mechanism.",
            "citations": [
                {"url": "https://example.org/work-one", "authority": "primary-original"},
                {"url": "https://example.org/work-two", "authority": "scholarly-secondary"},
            ],
        }
        self.payload = {
            "collection": {"review_state": "unreviewed-source-leads"},
            "records": [
                {"id": "example-record", "claims": [
                    {
                        "id": "example-record:scope",
                        "kind": "scope",
                        "field": "claim_scope.target",
                        "citations": [{
                            "citation_url": "https://example.org/work-one",
                            "locator_kind": "source-url-only",
                            "review_state": "unreviewed",
                        }],
                    }
                ]}
            ],
        }

    def apply(self, payload: dict) -> None:
        apply_claim_review_supplement(
            {"example-record": copy.deepcopy(self.record)}, payload
        )

    def test_rejects_unknown_citation_and_pretend_verification(self) -> None:
        for field, value in (
            ("citation_url", "https://example.org/unlisted-source"),
            ("locator_kind", "verified-passage"),
            ("review_state", "human-verified"),
        ):
            with self.subTest(field=field):
                bad = copy.deepcopy(self.payload)
                bad["records"][0]["claims"][0]["citations"][0][field] = value
                with self.assertRaises(ClaimReviewIntegrityError):
                    self.apply(bad)

    def test_rejects_unknown_record_duplicate_claim_and_field_substitution(self) -> None:
        bad = copy.deepcopy(self.payload)
        bad["records"][0]["id"] = "missing"
        with self.assertRaises(ClaimReviewIntegrityError):
            self.apply(bad)

        bad = copy.deepcopy(self.payload)
        bad["records"][0]["claims"].append(copy.deepcopy(bad["records"][0]["claims"][0]))
        with self.assertRaises(ClaimReviewIntegrityError):
            self.apply(bad)

        bad = copy.deepcopy(self.payload)
        bad["records"][0]["claims"][0]["field"] = "review_state"
        with self.assertRaises(ClaimReviewIntegrityError):
            self.apply(bad)

    def test_text_is_sourced_from_catalog_not_supplied_by_overlay(self) -> None:
        bad = copy.deepcopy(self.payload)
        bad["records"][0]["claims"][0]["text"] = "Unsupported claim inserted"
        with self.assertRaises(ClaimReviewIntegrityError):
            self.apply(bad)

        records = {"example-record": copy.deepcopy(self.record)}
        apply_claim_review_supplement(records, copy.deepcopy(self.payload))
        claim = records["example-record"]["claim_reviews"][0]
        self.assertEqual(claim["text"], self.record["claim_scope"]["target"])

    def test_only_explicit_unreviewed_collection_is_accepted(self) -> None:
        bad = copy.deepcopy(self.payload)
        bad["collection"]["review_state"] = "human-verified"
        with self.assertRaises(ClaimReviewIntegrityError):
            self.apply(bad)

    def test_rejects_extra_metadata_claims(self) -> None:
        bad = copy.deepcopy(self.payload)
        bad["collection"]["verified_claim_count"] = 1
        with self.assertRaises(ClaimReviewIntegrityError):
            self.apply(bad)

    def test_catalog_disallows_unvalidated_inline_claim_reviews(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_text(json.dumps({
                "metadata": {"version": "test"},
                "records": [{
                    **self.record,
                    "kind": "Scientific theory",
                    "domain": "Example",
                    "tradition": "Example",
                    "status": "provisional",
                    "name": "Example record",
                    "proponents": [],
                    "claim_reviews": [{"review_state": "human-verified"}],
                }],
            }), encoding="utf-8")
            with self.assertRaises(CatalogIntegrityError):
                CatalogRepository(path).list_records()


if __name__ == "__main__":
    unittest.main()
