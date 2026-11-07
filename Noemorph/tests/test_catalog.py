from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.catalog import CatalogRepository


APP_DIR = Path(__file__).resolve().parents[1]
FORBIDDEN_MISDIRECTED_URLS = {
    "https://doi.org/10.1017/S0031819100056084",
    "https://philpapers.org/rec/PUTPS",
    "https://doi.org/10.1093/monist/onw008",
    "https://doi.org/10.1016/S0010-0277%2800%2900130-8",
    "https://doi.org/10.1016/S0896-6273%2800%2980825-5",
    "https://profiles.nlm.nih.gov/spotlight/sc/catalog/nlm:nlmuid-101584582X67-doc",
    "https://doi.org/10.1016/j.neuropharm.2017.09.020",
}


class CatalogIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = CatalogRepository(APP_DIR / "data" / "catalog.json")
        cls.records, cls.total = cls.repository.list_records(limit=1000)

    def test_collection_has_expected_breadth_and_unique_identifiers(self) -> None:
        self.assertGreaterEqual(self.total, 577)
        ids = [record["id"] for record in self.records]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(self.repository.list_sources()), 1000)

    def test_source_roles_and_verification_are_per_citation_use(self) -> None:
        shared_url = "https://example.org/shared-work"

        def citation(url: str, authority: str, verification: str) -> dict:
            return {
                "title": "Test work",
                "authors": "A. Researcher",
                "year": 2025,
                "url": url,
                "authority": authority,
                "verification": verification,
            }

        def record(identifier: str, citations: list[dict]) -> dict:
            return {
                "id": identifier,
                "name": identifier,
                "kind": "Scientific theory",
                "domain": "Test domain",
                "tradition": "Test tradition",
                "status": "provisional",
                "summary": "A test record.",
                "proponents": [],
                "citations": citations,
            }

        payload = {
            "metadata": {"version": "test"},
            "records": [
                record("record-a", [
                    citation(shared_url, "primary-original", "human-verified"),
                    citation("https://example.org/unique-a", "scholarly-secondary", "locator-recorded"),
                ]),
                record("record-b", [
                    citation(shared_url, "scholarly-secondary", "locator-recorded"),
                    citation("https://example.org/unique-b", "primary-original", "doi-resolved"),
                ]),
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            repository = CatalogRepository(path)
            sources = repository.list_sources()
            shared = next(source for source in sources if source["url"] == shared_url)

            self.assertEqual(shared["used_by"], ["record-a", "record-b"])
            self.assertEqual(
                shared["authority_roles"], ["primary-original", "scholarly-secondary"]
            )
            self.assertEqual(
                shared["verification_states"], ["human-verified", "locator-recorded"]
            )
            self.assertEqual(
                shared["uses"],
                [
                    {"record_id": "record-a", "authority": "primary-original",
                     "verification": "human-verified", "url": shared_url},
                    {"record_id": "record-b", "authority": "scholarly-secondary",
                     "verification": "locator-recorded", "url": shared_url},
                ],
            )
            self.assertNotIn("authority", shared)
            self.assertNotIn("verification", shared)
            self.assertIn(
                shared["id"],
                {source["id"] for source in repository.list_sources(authority="primary-original")},
            )
            self.assertIn(
                shared["id"],
                {source["id"] for source in repository.list_sources(authority="scholarly-secondary")},
            )

    def test_record_search_matches_taxonomy_aliases_and_keywords(self) -> None:
        """Search fields must match what the public and desktop readers expose."""
        record = {
            "id": "search-field-fixture",
            "name": "Search Field Fixture",
            "kind": "Scientific theory",
            "domain": "Lattice Research Field",
            "tradition": "Archive Tradition",
            "status": "provisional",
            "summary": "A provisional research record.",
            "aliases": ["Orchid Lantern"],
            "keywords": ["Bluebird Transmission"],
            "proponents": ["Example Researcher"],
            "citations": [
                {
                    "title": "Bibliography Sentinel",
                    "authors": "Example Researcher",
                    "year": 2024,
                    "url": "https://example.org/search-source-one",
                    "authority": "primary-original",
                },
                {
                    "title": "Second Citation",
                    "authors": "Example Researcher",
                    "year": 2025,
                    "url": "https://example.org/search-source-two",
                    "authority": "scholarly-secondary",
                },
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_text(
                json.dumps({"metadata": {"version": "search-fixture"}, "records": [record]}),
                encoding="utf-8",
            )
            repository = CatalogRepository(path)
            for query in (
                "search field",
                "SCIENTIFIC",
                "lattice research",
                "ARCHIVE tradition",
                "ORCHID lantern",
                "bluebird transmission",
                "scientific ORCHID archive",
            ):
                matches, total = repository.list_records(query=query)
                self.assertEqual(total, 1, query)
                self.assertEqual([item["id"] for item in matches], [record["id"]], query)

            # Citations are provenance, not searchable claims or record identity.
            bibliography_matches, total = repository.list_records(
                query="Bibliography Sentinel"
            )
            self.assertEqual((bibliography_matches, total), ([], 0))

    def test_awareness_clinical_and_comparative_strata_are_present(self) -> None:
        names = {record["name"] for record in self.records}
        expected = {
            "Phenomenal consciousness",
            "Access consciousness",
            "Awareness and attention distinction",
            "Pure consciousness and contentless awareness",
            "Disorders of consciousness diagnostic spectrum",
            "Anesthesia-induced unconsciousness",
            "Dignāga–Dharmakīrti reflexive awareness",
            "Akan theories of personhood",
            "Perceptual Reality Monitoring theory (PRM)",
        }
        self.assertTrue(expected.issubset(names))

        kinds = {record["kind"] for record in self.records}
        self.assertTrue(
            {
                "Scientific theory",
                "Philosophical position",
                "Historical tradition",
                "Phenomenological construct",
                "Clinical / state model",
                "Theory of mind / social cognition",
                "Argument / challenge",
            }.issubset(kinds)
        )

    def test_deep_gap_audit_spans_neuroscience_awareness_and_history(self) -> None:
        names = {record["name"] for record in self.records}
        expected = {
            "Beautiful Loop Theory",
            "ALARM theory of consciousness",
            "Criticality hypothesis of consciousness",
            "Perturbational Complexity Index framework",
            "Partial Awareness Hypothesis",
            "Meta-d′ and Metacognitive-Efficiency Framework",
            "Bayesian Theory of Mind and Inverse Planning",
            "Knowledge argument (Mary thought experiment)",
            "Mīmāṃsā rival accounts of self-awareness",
            "Anishinaabe Place-Thought and human/nonhuman agency in Vanessa Watts",
        }
        self.assertTrue(expected.issubset(names))

    def test_current_cross_cultural_clinical_and_emerging_packets_are_present(self) -> None:
        names = {record["name"] for record in self.records}
        expected = {
            "Pudgalavāda person theory",
            "Lu Jiuyuan's heart-mind as principle",
            "Weighted Symbolic Mutual Information",
            "Perceptual Awareness Scale",
            "Joint Determinant Theory",
            "ConCrit Framework",
            "Energy–Mass–Information Model",
            "Five-Level Model of Access Consciousness",
        }
        self.assertTrue(expected.issubset(names))

    def test_dated_supplements_retain_provenance_and_research_boundaries(self) -> None:
        base_payload = json.loads((APP_DIR / "data" / "catalog.json").read_text(encoding="utf-8"))
        supplements = base_payload.get("supplements", [])
        self.assertGreaterEqual(len(supplements), 4)

        for filename in supplements:
            with self.subTest(supplement=filename):
                payload = json.loads((APP_DIR / "data" / filename).read_text(encoding="utf-8"))
                manifest = payload.get("collection")
                records = payload.get("records")
                self.assertIsInstance(manifest, dict)
                self.assertIsInstance(records, list)
                self.assertEqual(manifest.get("record_count"), len(records))
                self.assertGreater(len(records), 0)
                for record in records:
                    self.assertEqual(record.get("review_state"), "provisional")
                    for field in (
                        "claim_scope",
                        "boundary_note",
                        "evidence_profile",
                        "open_questions",
                    ):
                        self.assertTrue(record.get(field), f"{record.get('id')} lacks {field}")
                    self.assertGreaterEqual(len(record["citations"]), 2)
                    for citation in record["citations"]:
                        self.assertTrue(citation["url"].startswith("https://"))
                        self.assertNotEqual(citation.get("verification"), "pending-metadata-review")
                        self.assertNotIn("pending", citation["title"].casefold())
                        self.assertNotIn("pending", citation["authors"].casefold())

        manifests = self.repository.metadata().get("collections", [])
        self.assertEqual(len(manifests), len(supplements))
        self.assertEqual(
            sum(item["record_count"] for item in manifests),
            self.total - len(base_payload["records"]),
        )

    def test_explicit_acronym_aliases_are_retained(self) -> None:
        records_by_name = {record["name"]: record for record in self.records}
        self.assertIn("PRM", records_by_name["Perceptual Reality Monitoring theory (PRM)"]["aliases"])
        self.assertIn("MToC", records_by_name["Memory Theory of Consciousness (MToC)"]["aliases"])

    def test_research_profiles_are_materially_deep_not_just_new_rows(self) -> None:
        profiled = [record for record in self.records if record.get("claim_scope")]
        self.assertGreaterEqual(len(profiled), 405)
        for record in profiled:
            with self.subTest(record=record["id"]):
                self.assertTrue(record.get("boundary_note"))
                self.assertTrue(record.get("evidence_profile"))
                self.assertTrue(record.get("open_questions"))

        base_payload = json.loads(
            (APP_DIR / "data" / "catalog.json").read_text(encoding="utf-8")
        )
        self.assertGreaterEqual(
            sum(bool(record.get("claim_scope")) for record in base_payload["records"]),
            35,
        )

    def test_every_record_has_two_exact_https_locators(self) -> None:
        for record in self.records:
            with self.subTest(record=record["id"]):
                self.assertGreaterEqual(len(record["citations"]), 2)
                for citation in record["citations"]:
                    self.assertTrue(citation["url"].startswith("https://"))
                    self.assertNotIn(citation["url"], FORBIDDEN_MISDIRECTED_URLS)

    def test_verification_language_does_not_overclaim_resolution(self) -> None:
        allowed = {
            "doi-resolved",
            "locator-recorded",
            "human-verified",
            "pending-metadata-review",
        }
        for record in self.records:
            for citation in record["citations"]:
                self.assertIn(citation.get("verification"), allowed)

    def test_profile_enrichment_deepens_records_without_rewriting_identity(self) -> None:
        record = {
            "id": "record-1",
            "name": "Original identity",
            "kind": "Scientific theory",
            "domain": "Test domain",
            "tradition": "Test tradition",
            "status": "provisional",
            "summary": "Original summary.",
            "proponents": ["Researcher"],
            "citations": [
                {
                    "title": "Source one",
                    "authors": "Author one",
                    "year": 2020,
                    "url": "https://example.org/one",
                    "authority": "primary-original",
                    "verification": "locator-recorded",
                },
                {
                    "title": "Source two",
                    "authors": "Author two",
                    "year": 2021,
                    "url": "https://example.org/two",
                    "authority": "scholarly-secondary",
                    "verification": "locator-recorded",
                },
            ],
        }
        profile = {
            "collection": {"name": "Test enrichment", "profile_count": 1},
            "profiles": [
                {
                    "id": "record-1",
                    "boundary_note": "The evidence does not establish identity.",
                    "claim_scope": {"target": "A bounded target."},
                    "evidence_profile": {"basis": ["A tested basis."]},
                    "open_questions": ["What would distinguish the account?"],
                    "citation_additions": [
                        {
                            "title": "Source three",
                            "authors": "Author three",
                            "year": 2022,
                            "url": "https://example.org/three",
                            "authority": "independent-test",
                            "verification": "locator-recorded",
                        }
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "catalog.json").write_text(
                json.dumps(
                    {
                        "metadata": {},
                        "profile_enrichments": ["profiles.json"],
                        "records": [record],
                    }
                ),
                encoding="utf-8",
            )
            (root / "profiles.json").write_text(json.dumps(profile), encoding="utf-8")
            repository = CatalogRepository(root / "catalog.json")
            enriched = repository.get("record-1")
            self.assertIsNotNone(enriched)
            assert enriched is not None
            self.assertEqual(enriched["name"], "Original identity")
            self.assertEqual(enriched["boundary_note"], profile["profiles"][0]["boundary_note"])
            self.assertEqual(len(enriched["citations"]), 3)
            self.assertEqual(repository.metadata()["profile_collections"][0]["profile_count"], 1)

    def test_profile_enrichment_rejects_identity_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = {
                "metadata": {},
                "profile_enrichments": ["profiles.json"],
                "records": [
                    {
                        "id": "record-1",
                        "name": "Original identity",
                        "kind": "Scientific theory",
                        "domain": "Test domain",
                        "tradition": "Test tradition",
                        "status": "provisional",
                        "summary": "Original summary.",
                        "proponents": [],
                        "citations": [
                            {
                                "title": "Source one",
                                "authors": "Author one",
                                "year": 2020,
                                "url": "https://example.org/one",
                                "authority": "primary-original",
                                "verification": "locator-recorded",
                            },
                            {
                                "title": "Source two",
                                "authors": "Author two",
                                "year": 2021,
                                "url": "https://example.org/two",
                                "authority": "scholarly-secondary",
                                "verification": "locator-recorded",
                            },
                        ],
                    }
                ],
            }
            (root / "catalog.json").write_text(json.dumps(base), encoding="utf-8")
            (root / "profiles.json").write_text(
                json.dumps(
                    {
                        "collection": {},
                        "profiles": [{"id": "record-1", "name": "Replacement"}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(Exception, "unsupported fields: name"):
                CatalogRepository(root / "catalog.json").metadata()

    def test_known_corrective_sources_are_retained(self) -> None:
        expected = {
            "seed-001-": "https://doi.org/10.2307/2182164",
            "seed-021-": "https://doi.org/10.1093/acprof:oso/9780199359943.003.0005",
            "seed-047-": "https://authors.library.caltech.edu/records/7fap3-5v118",
            "seed-059-": "https://doi.org/10.1016/j.neuropharm.2018.03.010",
        }
        for prefix, expected_url in expected.items():
            record = next(item for item in self.records if item["id"].startswith(prefix))
            self.assertIn(expected_url, {citation["url"] for citation in record["citations"]})

    def test_collection_graph_exposes_no_theory_relationship_claims(self) -> None:
        graph = self.repository.taxonomy_graph()
        self.assertIn("Taxonomic classification only", graph["edge_policy"])
        self.assertTrue(graph["links"])
        self.assertTrue(
            all(link["kind"] in {"organizational", "classification"} for link in graph["links"])
        )

    def test_discovery_registry_is_large_traceable_and_separate(self) -> None:
        if not (APP_DIR / "data" / "discovery-closer-to-truth.json").exists():
            self.skipTest("Optional third-party discovery registry is not distributed")
        payload = json.loads(
            (APP_DIR / "data" / "discovery-closer-to-truth.json").read_text(
                encoding="utf-8"
            )
        )
        entries = payload["entries"]
        manifest = payload["collection"]
        self.assertGreaterEqual(len(entries), 470)
        self.assertEqual(manifest["entry_count"], len(entries))
        self.assertIn("not identity", manifest["catalog_match_note"])
        self.assertIn("not Noemorph verification", manifest["source_verification_note"])
        self.assertIn("not independent attribution", manifest["people_note"])
        self.assertEqual(len(entries), len({entry["slug"] for entry in entries}))
        self.assertGreaterEqual(len({entry["category"] for entry in entries}), 20)
        self.assertGreaterEqual(
            sum(len(entry.get("references", [])) for entry in entries), 1400
        )
        self.assertTrue(
            all(
                entry["url"].startswith("https://loc.closertotruth.com/theory/")
                for entry in entries
            )
        )
        self.assertGreaterEqual(
            sum(entry["catalog_match"]["status"] == "not-matched" for entry in entries),
            250,
        )
        self.assertTrue(
            all(
                entry["catalog_match"]["status"] == "not-applicable"
                for entry in entries
                if entry["entry_type"] != "theory"
            )
        )
        locators = [
            locator
            for entry in entries
            for reference in entry.get("references", [])
            for locator in reference.get("locators", [])
        ]
        self.assertTrue(all(locator.startswith("https://") for locator in locators))
        self.assertTrue(all(", https://" not in locator for locator in locators))
        self.assertTrue(all("utm_" not in locator.casefold() for locator in locators))
        listed, total = self.repository.list_discovery_entries(query="consciousness")
        self.assertGreater(total, 100)
        self.assertTrue(listed)
        base_payload = json.loads(
            (APP_DIR / "data" / "catalog.json").read_text(encoding="utf-8")
        )
        self.assertNotIn(
            "discovery-closer-to-truth.json", base_payload.get("supplements", [])
        )

    def test_independent_landscape_and_scope_frames_are_machine_readable(self) -> None:
        kuhn = json.loads(
            (APP_DIR / "data" / "discovery-kuhn-landscape.json").read_text(encoding="utf-8")
        )
        self.assertEqual(kuhn["collection"]["entry_count"], len(kuhn["entries"]))
        self.assertEqual(kuhn["collection"]["entry_count"], 219)
        self.assertGreaterEqual(kuhn["collection"]["named_position_count"], 200)
        self.assertTrue(all(entry["source"].startswith("https://doi.org/") for entry in kuhn["entries"]))

        tsc = json.loads(
            (APP_DIR / "data" / "scope-tsc-taxonomy.json").read_text(encoding="utf-8")
        )
        self.assertEqual(tsc["collection"]["item_count"], len(tsc["items"]))
        self.assertEqual(tsc["collection"]["item_count"], 102)
        self.assertEqual(len(tsc["collection"]["group_counts"]), 6)
        self.assertEqual(len(tsc["items"]), len({item["code"] for item in tsc["items"]}))
        self.assertIn("not a theory", tsc["collection"]["role"].casefold())

        report = json.loads(
            (APP_DIR / "data" / "coverage-report.json").read_text(encoding="utf-8")
        )
        self.assertEqual(report["reviewed_catalog"]["record_count"], self.total)
        discovery_path = APP_DIR / "data" / "discovery-closer-to-truth.json"
        if discovery_path.exists():
            self.assertEqual(
                report["discovery_frames"]["closer_to_truth"]["profile_count"],
                len(json.loads(discovery_path.read_text(encoding="utf-8"))["entries"]),
            )
        self.assertEqual(report["coverage_gate"], "locked")

    def test_optional_discovery_registry_reports_unavailable(self) -> None:
        from fastapi import HTTPException
        from backend.api import create_app

        app = create_app(APP_DIR, serve_frontend=False)
        with tempfile.TemporaryDirectory() as directory:
            app.state.repository.discovery_path = Path(directory) / "missing.json"
            discovery_route = next(route for route in app.routes if route.path == "/api/discovery/closer-to-truth")
            with self.assertRaises(HTTPException) as raised:
                discovery_route.endpoint(q=None, category=None, match_status=None, offset=0, limit=500)
            self.assertEqual(raised.exception.status_code, 503)
            self.assertIn("not included", raised.exception.detail)
            coverage = app.state.repository.coverage()
            self.assertEqual(coverage["discovery_registry"]["availability"], "unavailable")

    def test_synthesis_gate_remains_locked_without_completeness_claim(self) -> None:
        coverage = self.repository.coverage()
        self.assertEqual(coverage["gate_state"], "locked")
        self.assertNotIn("readiness_percent", self.repository.metadata())
        self.assertGreaterEqual(coverage["full_research_profile_count"], 420)
        self.assertEqual(
            coverage["full_research_profile_count"]
            + coverage["research_profile_gap_count"],
            coverage["record_count"],
        )
        self.assertGreater(coverage["human_verified_percent"], 0)
        self.assertEqual(coverage["locator_coverage_percent"], 100)


if __name__ == "__main__":
    unittest.main()
