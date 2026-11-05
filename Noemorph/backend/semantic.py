from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import threading
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .catalog import CatalogRepository


SEMANTIC_SCHEMA_VERSION = 1
RUN_STATES = frozenset({"building", "complete", "failed"})
DISPOSITIONS = frozenset(
    {"unreviewed", "shortlisted", "needs-review", "dismissed"}
)
RELATION_TAGS = frozenset(
    {
        "possible-convergence",
        "possible-contrast",
        "shared-mechanism",
        "shared-phenomenology",
        "shared-method",
        "possible-lineage",
        "terminological-overlap",
        "artifact-risk",
    }
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class SemanticError(RuntimeError):
    """Base class for semantic-candidate storage errors."""


class SemanticIntegrityError(SemanticError):
    """Raised when a semantic artifact violates its provenance contract."""


class SemanticUnavailableError(SemanticError):
    """Raised when candidate reads or writes are unsafe for the current artifact."""

    def __init__(self, state: str, detail: str) -> None:
        super().__init__(detail)
        self.state = state


class SemanticCandidateNotFoundError(SemanticError):
    """Raised when a semantic candidate does not exist in the active run."""


def _canonicalize(value: Any) -> Any:
    """Remove derived source identifiers before hashing curated record content."""
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            if key != "source_id"
        }
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    return value


def catalog_fingerprint(records: Iterable[Mapping[str, Any]]) -> str:
    """Return the stable SHA-256 used to bind a run to exact catalog content."""
    canonical_records = sorted(
        (_canonicalize(record) for record in records),
        key=lambda record: str(record.get("id", "")),
    )
    encoded = json.dumps(
        canonical_records,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def initialize_semantic_database(db_path: Path) -> None:
    """Create an empty semantic artifact for an offline pipeline.

    The API never calls this function implicitly. Keeping creation in the pipeline
    prevents an absent artifact from being mistaken for a completed analysis run.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, timeout=30)
    try:
        connection.executescript(
            f"""
            PRAGMA foreign_keys = ON;
            PRAGMA journal_mode = DELETE;
            PRAGMA user_version = {SEMANTIC_SCHEMA_VERSION};

            CREATE TABLE IF NOT EXISTS semantic_runs (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                model_json TEXT NOT NULL CHECK (json_valid(model_json)),
                catalog_hash TEXT NOT NULL,
                catalog_version TEXT NOT NULL,
                recipe_json TEXT NOT NULL CHECK (json_valid(recipe_json)),
                record_count INTEGER NOT NULL CHECK (record_count >= 0),
                candidate_count INTEGER NOT NULL CHECK (candidate_count >= 0),
                state TEXT NOT NULL CHECK (state IN ('building', 'complete', 'failed')),
                CHECK (length(trim(id)) BETWEEN 1 AND 160),
                CHECK (length(catalog_hash) = 64),
                CHECK (length(trim(catalog_version)) > 0)
            );

            CREATE TABLE IF NOT EXISTS semantic_candidates (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL REFERENCES semantic_runs(id) ON DELETE CASCADE,
                record_a_id TEXT NOT NULL,
                record_b_id TEXT NOT NULL,
                semantic_similarity REAL NOT NULL
                    CHECK (semantic_similarity BETWEEN -1.0 AND 1.0),
                similarity_percentile REAL NOT NULL
                    CHECK (similarity_percentile BETWEEN 0.0 AND 1.0),
                review_priority REAL NOT NULL
                    CHECK (review_priority BETWEEN 0.0 AND 1.0),
                mutual_rank INTEGER CHECK (mutual_rank IS NULL OR mutual_rank > 0),
                cross_domain INTEGER NOT NULL CHECK (cross_domain IN (0, 1)),
                cross_tradition INTEGER NOT NULL CHECK (cross_tradition IN (0, 1)),
                source_overlap_count INTEGER NOT NULL
                    CHECK (source_overlap_count >= 0),
                proponent_overlap_count INTEGER NOT NULL
                    CHECK (proponent_overlap_count >= 0),
                flags_json TEXT NOT NULL
                    CHECK (json_valid(flags_json) AND json_type(flags_json) = 'array'),
                contributions_json TEXT NOT NULL
                    CHECK (
                        json_valid(contributions_json)
                        AND json_type(contributions_json) IN ('array', 'object')
                    ),
                input_hashes_json TEXT NOT NULL
                    CHECK (
                        json_valid(input_hashes_json)
                        AND json_type(input_hashes_json) = 'object'
                    ),
                disposition TEXT NOT NULL DEFAULT 'unreviewed'
                    CHECK (
                        disposition IN (
                            'unreviewed', 'shortlisted', 'needs-review', 'dismissed'
                        )
                    ),
                relation_tag TEXT CHECK (
                    relation_tag IS NULL OR relation_tag IN (
                        'possible-convergence',
                        'possible-contrast',
                        'shared-mechanism',
                        'shared-phenomenology',
                        'shared-method',
                        'possible-lineage',
                        'terminological-overlap',
                        'artifact-risk'
                    )
                ),
                reviewer_note TEXT CHECK (
                    reviewer_note IS NULL OR length(reviewer_note) <= 2000
                ),
                reviewed_at TEXT,
                UNIQUE (run_id, record_a_id, record_b_id),
                CHECK (length(trim(id)) BETWEEN 1 AND 160),
                CHECK (record_a_id < record_b_id),
                CHECK (
                    (disposition = 'unreviewed' AND reviewed_at IS NULL)
                    OR (disposition != 'unreviewed' AND reviewed_at IS NOT NULL)
                )
            );

            CREATE INDEX IF NOT EXISTS idx_semantic_candidates_run_priority
                ON semantic_candidates(run_id, review_priority DESC, semantic_similarity DESC);
            CREATE INDEX IF NOT EXISTS idx_semantic_candidates_run_disposition
                ON semantic_candidates(run_id, disposition, review_priority DESC);
            CREATE INDEX IF NOT EXISTS idx_semantic_candidates_record_a
                ON semantic_candidates(run_id, record_a_id);
            CREATE INDEX IF NOT EXISTS idx_semantic_candidates_record_b
                ON semantic_candidates(run_id, record_b_id);
            """
        )
        connection.commit()
    finally:
        connection.close()


def _parse_json_object(raw: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise SemanticIntegrityError(f"{label} is not valid JSON") from exc
    if not isinstance(value, dict):
        raise SemanticIntegrityError(f"{label} must be a JSON object")
    return value


def _parse_json_collection(raw: str, label: str) -> list[Any] | dict[str, Any]:
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise SemanticIntegrityError(f"{label} is not valid JSON") from exc
    if not isinstance(value, (list, dict)):
        raise SemanticIntegrityError(f"{label} must be a JSON array or object")
    return value


def _validate_timestamp(value: str, label: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise SemanticIntegrityError(f"{label} is not an ISO-8601 timestamp") from exc


class SemanticRepository:
    """Read and review immutable semantic candidates from a versioned SQLite run."""

    def __init__(self, db_path: Path, catalog: CatalogRepository) -> None:
        self.db_path = db_path
        self.catalog = catalog
        self._write_lock = threading.RLock()

    def _connect(self, *, writable: bool = False) -> sqlite3.Connection:
        if not self.db_path.is_file():
            raise SemanticUnavailableError(
                "absent", "No semantic analysis artifact has been generated yet."
            )
        if writable:
            connection = sqlite3.connect(self.db_path, timeout=5)
        else:
            uri = f"file:{self.db_path.resolve().as_posix()}?mode=ro"
            connection = sqlite3.connect(uri, uri=True, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        if not writable:
            connection.execute("PRAGMA query_only = ON")
        return connection

    def _catalog_records(self) -> tuple[list[dict[str, Any]], int]:
        records: list[dict[str, Any]] = []
        offset = 0
        total = 0
        while True:
            page, total = self.catalog.list_records(offset=offset, limit=1000)
            records.extend(page)
            offset += len(page)
            if not page or offset >= total:
                break
        return records, total

    @staticmethod
    def _check_schema(connection: sqlite3.Connection) -> None:
        version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if version != SEMANTIC_SCHEMA_VERSION:
            raise SemanticIntegrityError(
                f"Semantic schema version {version} is unsupported; expected "
                f"{SEMANTIC_SCHEMA_VERSION}."
            )
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        missing = {"semantic_runs", "semantic_candidates"} - tables
        if missing:
            raise SemanticIntegrityError(
                f"Semantic artifact is missing tables: {', '.join(sorted(missing))}."
            )

    @staticmethod
    def _latest_run_row(connection: sqlite3.Connection) -> sqlite3.Row | None:
        return connection.execute(
            """
            SELECT id, created_at, model_json, catalog_hash, catalog_version,
                   recipe_json, record_count, candidate_count, state
            FROM semantic_runs
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """
        ).fetchone()

    @staticmethod
    def _validate_run(row: sqlite3.Row) -> dict[str, Any]:
        run_id = str(row["id"]).strip()
        if not run_id:
            raise SemanticIntegrityError("Semantic run has an empty identifier")
        _validate_timestamp(str(row["created_at"]), f"Run {run_id} created_at")

        model = _parse_json_object(row["model_json"], f"Run {run_id} model provenance")
        for key in ("provider", "name", "digest", "dimensions"):
            if key not in model:
                raise SemanticIntegrityError(
                    f"Run {run_id} model provenance lacks {key}"
                )
        if not isinstance(model["provider"], str) or not model["provider"].strip():
            raise SemanticIntegrityError(f"Run {run_id} has an invalid model provider")
        if not isinstance(model["name"], str) or not model["name"].strip():
            raise SemanticIntegrityError(f"Run {run_id} has an invalid model name")
        digest = str(model["digest"]).casefold()
        if not _SHA256_RE.fullmatch(digest):
            raise SemanticIntegrityError(f"Run {run_id} has an invalid model digest")
        if not isinstance(model["dimensions"], int) or model["dimensions"] <= 0:
            raise SemanticIntegrityError(f"Run {run_id} has invalid embedding dimensions")

        recipe = _parse_json_object(row["recipe_json"], f"Run {run_id} recipe")
        for key in ("version", "prefix", "text_fields", "metric"):
            if key not in recipe:
                raise SemanticIntegrityError(f"Run {run_id} recipe lacks {key}")
        if not isinstance(recipe["version"], (str, int)) or str(
            recipe["version"]
        ).strip() == "":
            raise SemanticIntegrityError(f"Run {run_id} recipe version is invalid")
        if not isinstance(recipe["prefix"], str) or not recipe["prefix"].strip():
            raise SemanticIntegrityError(f"Run {run_id} recipe prefix is invalid")
        if not isinstance(recipe["text_fields"], list) or not recipe["text_fields"]:
            raise SemanticIntegrityError(f"Run {run_id} recipe text_fields is invalid")
        if not all(
            isinstance(field, str) and field.strip() for field in recipe["text_fields"]
        ):
            raise SemanticIntegrityError(
                f"Run {run_id} recipe text_fields contains an invalid field"
            )
        if recipe["metric"] != "cosine":
            raise SemanticIntegrityError(
                f"Run {run_id} uses unsupported metric {recipe['metric']!r}"
            )

        catalog_hash = str(row["catalog_hash"]).casefold()
        if not _SHA256_RE.fullmatch(catalog_hash):
            raise SemanticIntegrityError(f"Run {run_id} has an invalid catalog hash")
        state = str(row["state"])
        if state not in RUN_STATES:
            raise SemanticIntegrityError(f"Run {run_id} has invalid state {state!r}")
        record_count = int(row["record_count"])
        candidate_count = int(row["candidate_count"])
        if record_count < 0 or candidate_count < 0:
            raise SemanticIntegrityError(f"Run {run_id} has negative counts")

        return {
            "id": run_id,
            "created_at": str(row["created_at"]),
            "model": model,
            "catalog_hash": catalog_hash,
            "catalog_version": str(row["catalog_version"]),
            "recipe": recipe,
            "record_count": record_count,
            "candidate_count": candidate_count,
            "state": state,
        }

    @staticmethod
    def _validate_candidate_row(
        row: sqlite3.Row, *, run_id: str, catalog_ids: set[str]
    ) -> None:
        candidate_id = str(row["id"])
        if not candidate_id.strip():
            raise SemanticIntegrityError("Semantic candidate has an empty identifier")
        if row["run_id"] != run_id:
            raise SemanticIntegrityError(
                f"Candidate {candidate_id} is attached to the wrong run"
            )
        record_a_id = str(row["record_a_id"])
        record_b_id = str(row["record_b_id"])
        if record_a_id >= record_b_id:
            raise SemanticIntegrityError(
                f"Candidate {candidate_id} does not use canonical record ordering"
            )
        unknown = {record_a_id, record_b_id} - catalog_ids
        if unknown:
            raise SemanticIntegrityError(
                f"Candidate {candidate_id} references unknown catalog record(s): "
                f"{', '.join(sorted(unknown))}"
            )
        for field, lower, upper in (
            ("semantic_similarity", -1.0, 1.0),
            ("similarity_percentile", 0.0, 1.0),
            ("review_priority", 0.0, 1.0),
        ):
            value = float(row[field])
            if not math.isfinite(value) or not lower <= value <= upper:
                raise SemanticIntegrityError(
                    f"Candidate {candidate_id} has invalid {field}"
                )
        mutual_rank = row["mutual_rank"]
        if mutual_rank is not None and int(mutual_rank) <= 0:
            raise SemanticIntegrityError(
                f"Candidate {candidate_id} has invalid mutual_rank"
            )
        for field in ("cross_domain", "cross_tradition"):
            if row[field] not in (0, 1):
                raise SemanticIntegrityError(
                    f"Candidate {candidate_id} has invalid {field}"
                )
        for field in ("source_overlap_count", "proponent_overlap_count"):
            if int(row[field]) < 0:
                raise SemanticIntegrityError(
                    f"Candidate {candidate_id} has invalid {field}"
                )

        try:
            flags = json.loads(row["flags_json"])
        except (TypeError, json.JSONDecodeError) as exc:
            raise SemanticIntegrityError(
                f"Candidate {candidate_id} flags are invalid JSON"
            ) from exc
        if not isinstance(flags, list) or not all(
            isinstance(flag, str) and flag.strip() for flag in flags
        ):
            raise SemanticIntegrityError(
                f"Candidate {candidate_id} flags must be non-empty strings"
            )
        _parse_json_collection(
            row["contributions_json"], f"Candidate {candidate_id} contributions"
        )
        hashes = _parse_json_object(
            row["input_hashes_json"], f"Candidate {candidate_id} input hashes"
        )
        if set(hashes) != {record_a_id, record_b_id} or not all(
            isinstance(value, str) and _SHA256_RE.fullmatch(value.casefold())
            for value in hashes.values()
        ):
            raise SemanticIntegrityError(
                f"Candidate {candidate_id} input hashes must map both records to SHA-256"
            )
        disposition = str(row["disposition"])
        if disposition not in DISPOSITIONS:
            raise SemanticIntegrityError(
                f"Candidate {candidate_id} has invalid disposition"
            )
        relation_tag = row["relation_tag"]
        if relation_tag is not None and relation_tag not in RELATION_TAGS:
            raise SemanticIntegrityError(
                f"Candidate {candidate_id} has invalid relation tag"
            )
        note = row["reviewer_note"]
        if note is not None:
            validate_reviewer_note(str(note))
        reviewed_at = row["reviewed_at"]
        if disposition == "unreviewed" and reviewed_at is not None:
            raise SemanticIntegrityError(
                f"Unreviewed candidate {candidate_id} has a review timestamp"
            )
        if disposition != "unreviewed":
            if reviewed_at is None:
                raise SemanticIntegrityError(
                    f"Reviewed candidate {candidate_id} lacks a review timestamp"
                )
            _validate_timestamp(str(reviewed_at), f"Candidate {candidate_id} reviewed_at")

    def _artifact_context(
        self,
        connection: sqlite3.Connection,
        *,
        validate_candidates: bool,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, Any]]]:
        self._check_schema(connection)
        run_row = self._latest_run_row(connection)
        if run_row is None:
            raise SemanticUnavailableError(
                "empty", "The semantic database contains no analysis runs."
            )
        run = self._validate_run(run_row)
        if run["state"] == "building":
            raise SemanticUnavailableError(
                "building", f"Semantic run {run['id']} is still being generated."
            )
        if run["state"] == "failed":
            raise SemanticUnavailableError(
                "failed", f"Semantic run {run['id']} did not complete."
            )

        records, total = self._catalog_records()
        by_id = {str(record["id"]): record for record in records}
        current_hash = catalog_fingerprint(records)
        current_version = str(self.catalog.metadata().get("version", "unknown"))
        stale_reasons: list[str] = []
        if run["catalog_hash"] != current_hash:
            stale_reasons.append("catalog fingerprint changed")
        if run["record_count"] != total:
            stale_reasons.append(
                f"record count changed ({run['record_count']} to {total})"
            )
        if run["catalog_version"] != current_version:
            stale_reasons.append(
                f"catalog version changed ({run['catalog_version']} to {current_version})"
            )
        if stale_reasons:
            raise SemanticUnavailableError(
                "stale",
                f"Semantic run {run['id']} is stale: {'; '.join(stale_reasons)}.",
            )

        actual_count = int(
            connection.execute(
                "SELECT COUNT(*) FROM semantic_candidates WHERE run_id = ?",
                (run["id"],),
            ).fetchone()[0]
        )
        if actual_count != run["candidate_count"]:
            raise SemanticIntegrityError(
                f"Run {run['id']} declares {run['candidate_count']} candidates but "
                f"contains {actual_count}."
            )

        if validate_candidates:
            rows = connection.execute(
                "SELECT * FROM semantic_candidates WHERE run_id = ?", (run["id"],)
            )
            for row in rows:
                self._validate_candidate_row(
                    row, run_id=run["id"], catalog_ids=set(by_id)
                )
        return run, records, by_id

    def status(self) -> dict[str, Any]:
        records, total = self._catalog_records()
        catalog_info = {
            "version": str(self.catalog.metadata().get("version", "unknown")),
            "record_count": total,
            "fingerprint": catalog_fingerprint(records),
        }
        base: dict[str, Any] = {
            "ready": False,
            "state": "absent",
            "detail": "No semantic analysis artifact has been generated yet.",
            "schema_version": SEMANTIC_SCHEMA_VERSION,
            "catalog": catalog_info,
            "run": None,
            "counts": {"total": 0, "by_disposition": {}, "by_relation_tag": {}},
            "relationship_synthesis_locked": True,
        }
        if not self.db_path.is_file():
            return base

        try:
            with closing(self._connect()) as connection:
                self._check_schema(connection)
                run_row = self._latest_run_row(connection)
                if run_row is None:
                    return {
                        **base,
                        "state": "empty",
                        "detail": "The semantic database contains no analysis runs.",
                    }
                run_for_error = self._validate_run(run_row)
                try:
                    run, _, _ = self._artifact_context(
                        connection, validate_candidates=True
                    )
                except SemanticUnavailableError as exc:
                    return {
                        **base,
                        "state": exc.state,
                        "detail": str(exc),
                        "run": run_for_error,
                    }
                dispositions = {
                    row[0]: int(row[1])
                    for row in connection.execute(
                        """
                        SELECT disposition, COUNT(*)
                        FROM semantic_candidates
                        WHERE run_id = ?
                        GROUP BY disposition
                        """,
                        (run["id"],),
                    )
                }
                relation_tags = {
                    row[0]: int(row[1])
                    for row in connection.execute(
                        """
                        SELECT relation_tag, COUNT(*)
                        FROM semantic_candidates
                        WHERE run_id = ? AND relation_tag IS NOT NULL
                        GROUP BY relation_tag
                        """,
                        (run["id"],),
                    )
                }
                return {
                    **base,
                    "ready": True,
                    "state": "ready",
                    "detail": "Semantic candidates are ready for evidence review.",
                    "run": run,
                    "counts": {
                        "total": run["candidate_count"],
                        "by_disposition": dispositions,
                        "by_relation_tag": relation_tags,
                    },
                }
        except sqlite3.Error as exc:
            return {
                **base,
                "state": "invalid",
                "detail": f"Semantic database could not be read: {exc}.",
            }
        except SemanticIntegrityError as exc:
            return {**base, "state": "invalid", "detail": str(exc)}
        except SemanticUnavailableError as exc:
            return {**base, "state": exc.state, "detail": str(exc)}

    def _require_ready(
        self, connection: sqlite3.Connection
    ) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
        try:
            run, _, by_id = self._artifact_context(
                connection, validate_candidates=True
            )
            return run, by_id
        except SemanticIntegrityError as exc:
            raise SemanticUnavailableError("invalid", str(exc)) from exc

    @staticmethod
    def _candidate_from_row(
        row: sqlite3.Row, by_id: Mapping[str, Mapping[str, Any]]
    ) -> dict[str, Any]:
        record_a = by_id[str(row["record_a_id"])]
        record_b = by_id[str(row["record_b_id"])]

        def record_summary(record: Mapping[str, Any]) -> dict[str, Any]:
            return {
                "id": record["id"],
                "name": record["name"],
                "kind": record["kind"],
                "domain": record["domain"],
                "tradition": record["tradition"],
                "status": record["status"],
            }

        return {
            "id": row["id"],
            "run_id": row["run_id"],
            "record_a_id": row["record_a_id"],
            "record_b_id": row["record_b_id"],
            "record_a": record_summary(record_a),
            "record_b": record_summary(record_b),
            "semantic_similarity": float(row["semantic_similarity"]),
            "similarity_percentile": float(row["similarity_percentile"]),
            "review_priority": float(row["review_priority"]),
            "mutual_rank": row["mutual_rank"],
            "cross_domain": bool(row["cross_domain"]),
            "cross_tradition": bool(row["cross_tradition"]),
            "source_overlap_count": int(row["source_overlap_count"]),
            "proponent_overlap_count": int(row["proponent_overlap_count"]),
            "flags": json.loads(row["flags_json"]),
            "contributions": json.loads(row["contributions_json"]),
            "input_hashes": json.loads(row["input_hashes_json"]),
            "disposition": row["disposition"],
            "relation_tag": row["relation_tag"],
            "reviewer_note": row["reviewer_note"],
            "reviewed_at": row["reviewed_at"],
        }

    def list_candidates(
        self,
        *,
        query: str | None = None,
        dispositions: Sequence[str] = (),
        relation_tags: Sequence[str] = (),
        record_id: str | None = None,
        cross_domain: bool | None = None,
        cross_tradition: bool | None = None,
        min_similarity: float | None = None,
        min_priority: float | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[dict[str, Any]], int, dict[str, Any]]:
        invalid_dispositions = set(dispositions) - DISPOSITIONS
        if invalid_dispositions:
            raise ValueError(
                f"Unsupported dispositions: {', '.join(sorted(invalid_dispositions))}"
            )
        invalid_tags = set(relation_tags) - RELATION_TAGS
        if invalid_tags:
            raise ValueError(f"Unsupported relation tags: {', '.join(sorted(invalid_tags))}")
        if min_similarity is not None and not -1 <= min_similarity <= 1:
            raise ValueError("min_similarity must be between -1 and 1")
        if min_priority is not None and not 0 <= min_priority <= 1:
            raise ValueError("min_priority must be between 0 and 1")

        with closing(self._connect()) as connection:
            run, by_id = self._require_ready(connection)
            if record_id is not None and record_id not in by_id:
                raise ValueError("record_id is not a catalog record")
            rows = connection.execute(
                """
                SELECT * FROM semantic_candidates
                WHERE run_id = ?
                ORDER BY review_priority DESC, semantic_similarity DESC, id ASC
                """,
                (run["id"],),
            ).fetchall()
            items = [self._candidate_from_row(row, by_id) for row in rows]

        query_terms = tuple((query or "").casefold().split())

        def matches(item: Mapping[str, Any]) -> bool:
            if dispositions and item["disposition"] not in dispositions:
                return False
            if relation_tags and item["relation_tag"] not in relation_tags:
                return False
            if record_id and record_id not in {
                item["record_a_id"],
                item["record_b_id"],
            }:
                return False
            if cross_domain is not None and item["cross_domain"] is not cross_domain:
                return False
            if (
                cross_tradition is not None
                and item["cross_tradition"] is not cross_tradition
            ):
                return False
            if (
                min_similarity is not None
                and item["semantic_similarity"] < min_similarity
            ):
                return False
            if min_priority is not None and item["review_priority"] < min_priority:
                return False
            if query_terms:
                haystack = " ".join(
                    [
                        str(item["id"]),
                        str(item["record_a_id"]),
                        str(item["record_b_id"]),
                        str(item["record_a"]["name"]),
                        str(item["record_b"]["name"]),
                        str(item["record_a"]["domain"]),
                        str(item["record_b"]["domain"]),
                        str(item["record_a"]["tradition"]),
                        str(item["record_b"]["tradition"]),
                        " ".join(item["flags"]),
                        str(item["relation_tag"] or ""),
                        str(item["reviewer_note"] or ""),
                    ]
                ).casefold()
                if not all(term in haystack for term in query_terms):
                    return False
            return True

        filtered = [item for item in items if matches(item)]
        total = len(filtered)
        safe_offset = max(0, offset)
        safe_limit = min(max(1, limit), 500)
        return filtered[safe_offset : safe_offset + safe_limit], total, run

    def get_candidate(self, candidate_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            run, by_id = self._require_ready(connection)
            row = connection.execute(
                """
                SELECT * FROM semantic_candidates
                WHERE run_id = ? AND id = ?
                """,
                (run["id"], candidate_id),
            ).fetchone()
            if row is None:
                return None
            item = self._candidate_from_row(row, by_id)
            item["record_a"] = by_id[item["record_a_id"]]
            item["record_b"] = by_id[item["record_b_id"]]
            return {
                "candidate": item,
                "run": run,
                "interpretation_policy": (
                    "Embedding proximity is a review lead, not evidence of a conceptual, "
                    "historical, causal, or novel relationship."
                ),
                "relationship_synthesis_locked": True,
            }

    def update_candidate(
        self,
        candidate_id: str,
        *,
        disposition: str | None = None,
        relation_tag: str | None | object = ...,
        reviewer_note: str | None | object = ...,
    ) -> dict[str, Any]:
        if disposition is not None and disposition not in DISPOSITIONS:
            raise ValueError("Unsupported disposition")
        if relation_tag is not ...:
            validate_relation_tag(relation_tag)
        if reviewer_note is not ...:
            reviewer_note = validate_reviewer_note(reviewer_note)
        if disposition is None and relation_tag is ... and reviewer_note is ...:
            raise ValueError("PATCH must change at least one review field")

        with self._write_lock, closing(self._connect(writable=True)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            run, _ = self._require_ready(connection)
            current = connection.execute(
                """
                SELECT disposition, relation_tag, reviewer_note
                FROM semantic_candidates
                WHERE run_id = ? AND id = ?
                """,
                (run["id"], candidate_id),
            ).fetchone()
            if current is None:
                raise SemanticCandidateNotFoundError(
                    f"Semantic candidate {candidate_id!r} was not found."
                )

            next_disposition = disposition or str(current["disposition"])
            next_tag = (
                current["relation_tag"] if relation_tag is ... else relation_tag
            )
            next_note = (
                current["reviewer_note"] if reviewer_note is ... else reviewer_note
            )
            if (
                next_disposition == "unreviewed"
                and disposition is None
                and (next_tag is not None or next_note is not None)
            ):
                raise ValueError(
                    "Set a reviewed disposition before adding a relation tag or note"
                )
            if next_disposition == "unreviewed":
                next_tag = None
                next_note = None
                reviewed_at = None
            else:
                reviewed_at = datetime.now(timezone.utc).isoformat().replace(
                    "+00:00", "Z"
                )

            connection.execute(
                """
                UPDATE semantic_candidates
                SET disposition = ?, relation_tag = ?, reviewer_note = ?, reviewed_at = ?
                WHERE run_id = ? AND id = ?
                """,
                (
                    next_disposition,
                    next_tag,
                    next_note,
                    reviewed_at,
                    run["id"],
                    candidate_id,
                ),
            )
            connection.commit()
        result = self.get_candidate(candidate_id)
        if result is None:  # Defensive: the row existed inside the write transaction.
            raise SemanticCandidateNotFoundError(
                f"Semantic candidate {candidate_id!r} was not found."
            )
        return result


def validate_relation_tag(value: object) -> None:
    if value is not None and (not isinstance(value, str) or value not in RELATION_TAGS):
        raise ValueError("Unsupported relation_tag")


def validate_reviewer_note(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("reviewer_note must be a string or null")
    note = value.strip()
    if not note:
        return None
    if len(note) > 2000:
        raise ValueError("reviewer_note must be at most 2000 characters")
    if _CONTROL_RE.search(note):
        raise ValueError("reviewer_note contains unsupported control characters")
    return note


def candidate_count_summary(items: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Small public helper for offline reports and tests."""
    rows = list(items)
    return {
        "total": len(rows),
        "by_disposition": dict(Counter(str(row["disposition"]) for row in rows)),
        "by_relation_tag": dict(
            Counter(
                str(row["relation_tag"])
                for row in rows
                if row.get("relation_tag") is not None
            )
        ),
    }
