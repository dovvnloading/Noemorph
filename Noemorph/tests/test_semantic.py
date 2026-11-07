from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api import create_app
from backend.catalog import CatalogRepository
from backend.semantic import (
    SemanticRepository,
    SemanticUnavailableError,
    catalog_fingerprint,
    initialize_semantic_database,
)


APP_DIR = Path(__file__).resolve().parents[1]


class SemanticRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temporary_directory.name) / "semantic.sqlite3"
        self.catalog = CatalogRepository(APP_DIR / "data" / "catalog.json")
        self.records, self.record_count = self.catalog.list_records(limit=1000)
        self.record_a_id, self.record_b_id = sorted(
            (str(self.records[0]["id"]), str(self.records[1]["id"]))
        )
        self.catalog_hash = catalog_fingerprint(self.records)
        self.catalog_version = str(self.catalog.metadata()["version"])
        self.repository = SemanticRepository(self.db_path, self.catalog)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _create_valid_artifact(self) -> None:
        initialize_semantic_database(self.db_path)
        model = {
            "provider": "ollama",
            "name": "nomic-embed-text:latest",
            "digest": "0a109f422b47e3a30ba2b10eca18548e944e8a23073ee3f3e947efcf3c45e59f",
            "dimensions": 768,
            "runtime_version": "0.33.2",
        }
        recipe = {
            "version": "semantic-candidates-v1",
            "prefix": "clustering: ",
            "text_fields": ["name", "summary", "claim_scope"],
            "metric": "cosine",
        }
        hashes = {
            self.record_a_id: "a" * 64,
            self.record_b_id: "b" * 64,
        }
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                """
                INSERT INTO semantic_runs (
                    id, created_at, model_json, catalog_hash, catalog_version,
                    recipe_json, record_count, candidate_count, state
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'building')
                """,
                (
                    "run-test",
                    "2026-08-30T21:00:00Z",
                    json.dumps(model),
                    self.catalog_hash,
                    self.catalog_version,
                    json.dumps(recipe),
                    self.record_count,
                    1,
                ),
            )
            connection.execute(
                """
                INSERT INTO semantic_candidates (
                    id, run_id, record_a_id, record_b_id, semantic_similarity,
                    similarity_percentile, review_priority, mutual_rank,
                    cross_domain, cross_tradition, source_overlap_count,
                    proponent_overlap_count, flags_json, contributions_json,
                    input_hashes_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "pair-test",
                    "run-test",
                    self.record_a_id,
                    self.record_b_id,
                    0.8125,
                    0.991,
                    0.88,
                    3,
                    1,
                    1,
                    0,
                    0,
                    json.dumps(["reciprocal-neighbor", "lexical-control-passed"]),
                    json.dumps({"semantic": 0.8, "novelty": 0.08}),
                    json.dumps(hashes),
                ),
            )
            connection.execute(
                "UPDATE semantic_runs SET state = 'complete' WHERE id = 'run-test'"
            )
            connection.commit()

    def test_absent_database_is_an_expected_status_not_an_exception(self) -> None:
        status = self.repository.status()
        self.assertFalse(status["ready"])
        self.assertEqual(status["state"], "absent")
        self.assertEqual(status["catalog"]["record_count"], self.record_count)
        self.assertTrue(status["relationship_synthesis_locked"])

    def test_ready_artifact_validates_provenance_and_lists_candidates(self) -> None:
        self._create_valid_artifact()
        status = self.repository.status()
        self.assertTrue(status["ready"])
        self.assertEqual(status["state"], "ready")
        self.assertEqual(status["counts"]["total"], 1)
        self.assertEqual(status["run"]["model"]["dimensions"], 768)

        items, total, run = self.repository.list_candidates(
            record_id=self.record_a_id,
            cross_domain=True,
            min_similarity=0.8,
        )
        self.assertEqual(total, 1)
        self.assertEqual(run["id"], "run-test")
        self.assertEqual(items[0]["id"], "pair-test")
        self.assertEqual(items[0]["record_a"]["id"], self.record_a_id)
        self.assertEqual(items[0]["disposition"], "unreviewed")

        detail = self.repository.get_candidate("pair-test")
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertIn("citations", detail["candidate"]["record_a"])
        self.assertTrue(detail["relationship_synthesis_locked"])
        self.assertIn("not evidence", detail["interpretation_policy"])

    def test_review_patch_is_auditable_and_reset_clears_review_fields(self) -> None:
        self._create_valid_artifact()
        updated = self.repository.update_candidate(
            "pair-test",
            disposition="shortlisted",
            relation_tag="possible-convergence",
            reviewer_note="Compare the primary mechanisms before making any claim.",
        )
        candidate = updated["candidate"]
        self.assertEqual(candidate["disposition"], "shortlisted")
        self.assertEqual(candidate["relation_tag"], "possible-convergence")
        self.assertTrue(candidate["reviewed_at"].endswith("Z"))

        reset = self.repository.update_candidate(
            "pair-test", disposition="unreviewed"
        )["candidate"]
        self.assertIsNone(reset["relation_tag"])
        self.assertIsNone(reset["reviewer_note"])
        self.assertIsNone(reset["reviewed_at"])

    def test_stale_or_unknown_record_artifacts_are_not_served(self) -> None:
        self._create_valid_artifact()
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(
                "UPDATE semantic_runs SET catalog_hash = ? WHERE id = 'run-test'",
                ("0" * 64,),
            )
            connection.commit()
        status = self.repository.status()
        self.assertFalse(status["ready"])
        self.assertEqual(status["state"], "stale")
        with self.assertRaises(SemanticUnavailableError):
            self.repository.list_candidates()

        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(
                "UPDATE semantic_runs SET catalog_hash = ? WHERE id = 'run-test'",
                (self.catalog_hash,),
            )
            connection.execute(
                """
                UPDATE semantic_candidates
                SET record_b_id = ?, input_hashes_json = ?
                WHERE id = 'pair-test'
                """,
                (
                    "zzzz-missing-record",
                    json.dumps(
                        {
                            self.record_a_id: "a" * 64,
                            "zzzz-missing-record": "b" * 64,
                        }
                    ),
                ),
            )
            connection.commit()
        status = self.repository.status()
        self.assertEqual(status["state"], "invalid")
        self.assertIn("unknown catalog record", status["detail"])


class SemanticApiTests(SemanticRepositoryTests):
    def test_api_contract_and_relationship_gate(self) -> None:
        self._create_valid_artifact()
        app = create_app(
            APP_DIR,
            serve_frontend=False,
            semantic_db_path=self.db_path,
        )
        with TestClient(app, base_url="http://127.0.0.1:8765", client=("127.0.0.1", 5555)) as client:
            status = client.get("/api/semantic/status")
            self.assertEqual(status.status_code, 200)
            self.assertEqual(status.json()["state"], "ready")

            listing = client.get(
                "/api/semantic/candidates",
                params={"record_id": self.record_a_id, "limit": 10},
            )
            self.assertEqual(listing.status_code, 200)
            self.assertEqual(listing.json()["total"], 1)
            self.assertTrue(listing.json()["relationship_synthesis_locked"])

            detail = client.get("/api/semantic/candidates/pair-test")
            self.assertEqual(detail.status_code, 200)
            self.assertEqual(detail.json()["candidate"]["id"], "pair-test")

            review = client.patch(
                "/api/semantic/candidates/pair-test",
                json={
                    "disposition": "needs-review",
                    "relation_tag": "artifact-risk",
                    "reviewer_note": "Potential vocabulary leakage; inspect source text.",
                },
            )
            self.assertEqual(review.status_code, 200)
            self.assertEqual(review.json()["candidate"]["disposition"], "needs-review")

            invalid_tag = client.patch(
                "/api/semantic/candidates/pair-test",
                json={"relation_tag": "groundbreaking-discovery"},
            )
            self.assertEqual(invalid_tag.status_code, 422)
            empty_patch = client.patch(
                "/api/semantic/candidates/pair-test", json={}
            )
            self.assertEqual(empty_patch.status_code, 422)

            relationship_graph = client.get("/api/graph/relationships")
            self.assertEqual(relationship_graph.status_code, 423)
            self.assertIn("do not constitute graph edges", relationship_graph.text)


    def test_semantic_review_rejects_remote_clients_and_untrusted_origins(self) -> None:
        self._create_valid_artifact()
        app = create_app(APP_DIR, serve_frontend=False, semantic_db_path=self.db_path)
        review = {
            "disposition": "needs-review",
            "reviewer_note": "A locally reviewed candidate; no scientific conclusion.",
        }
        with TestClient(
            app, base_url="http://127.0.0.1:8765",
            client=("127.0.0.1", 5555),
        ) as local:
            status = local.get("/api/semantic/status")
            self.assertEqual(status.status_code, 200)
            self.assertEqual(status.headers["cache-control"], "no-store")
            self.assertEqual(
                local.get("/api/semantic/candidates").headers["cache-control"],
                "no-store",
            )
            self.assertEqual(
                local.get("/api/semantic/candidates/pair-test").headers["cache-control"],
                "no-store",
            )
            for origin in ("https://attacker.example", "null"):
                denied = local.patch(
                    "/api/semantic/candidates/pair-test",
                    json=review, headers={"Origin": origin},
                )
                self.assertEqual(denied.status_code, 403)
            self.assertEqual(
                local.get(
                    "/api/semantic/candidates/pair-test",
                    headers={"Host": "attacker.example"},
                ).status_code,
                403,
            )
            self.assertEqual(
                local.patch(
                    "/api/semantic/candidates/pair-test", json=review,
                    headers={"Origin": "http://127.0.0.1:5173"},
                ).status_code,
                200,
            )
        with TestClient(
            app, base_url="http://127.0.0.1:8765",
            client=("192.0.2.22", 4321),
        ) as remote:
            for endpoint in (
                "/api/semantic/status",
                "/api/semantic/candidates",
                "/api/semantic/candidates/pair-test",
            ):
                self.assertEqual(remote.get(endpoint).status_code, 403)
            self.assertEqual(
                remote.patch("/api/semantic/candidates/pair-test", json=review).status_code,
                403,
            )
            self.assertEqual(remote.get("/api/catalog", params={"limit": 1}).status_code, 200)


if __name__ == "__main__":
    unittest.main()
