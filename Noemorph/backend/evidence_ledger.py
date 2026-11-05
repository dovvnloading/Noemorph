"""Local, append-only ledger for independent claim-to-source evidence reviews.

Events are reviewer-attributed *statements*, not authenticated certifications.
No decision automatically changes a catalog claim, citation verification state,
semantic relationship, or publication gate. HTTP access is read-only.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .catalog import CatalogRepository

SCHEMA_VERSION = 1
DECISIONS = frozenset({
    "supports", "challenges", "contextualizes", "inconclusive", "not-relevant",
})
LOCATOR_KINDS = frozenset({
    "page", "section", "paragraph", "figure", "table", "line", "timestamp",
})
_REVIEWER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{2,79}$")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_HASH = re.compile(r"^[0-9a-f]{64}$")
_GENESIS = "0" * 64
_EVENT_FIELDS = (
    "event_id", "record_id", "claim_id", "claim_hash", "source_uid",
    "citation_url", "reviewer_id", "decision", "locator_kind", "locator",
    "excerpt", "note", "created_at",
)


class EvidenceReviewError(ValueError):
    """Invalid local evidence-review input or unknown claim/source."""


class EvidenceIntegrityError(RuntimeError):
    """Review ledger has an invalid schema or a broken event hash chain."""


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def claim_digest(text: str) -> str:
    return _sha256(text)


def _event_digest(previous: str, fields: Mapping[str, Any]) -> str:
    body = json.dumps(
        {field: fields[field] for field in _EVENT_FIELDS},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )
    return _sha256(previous + "\n" + body)


def _require_text(value: Any, label: str, *, min_len: int = 1, max_len: int = 160) -> str:
    if not isinstance(value, str) or not min_len <= len(value.strip()) <= max_len:
        raise EvidenceReviewError(f"{label} must contain {min_len}–{max_len} characters")
    if _CONTROL.search(value):
        raise EvidenceReviewError(f"{label} contains unsupported control characters")
    return value.strip()


def initialize_evidence_database(path: Path) -> None:
    """Explicit local setup. API reads never create files."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path, timeout=10)) as connection:
        current = connection.execute("PRAGMA user_version").fetchone()[0]
        if current not in (0, SCHEMA_VERSION):
            raise EvidenceIntegrityError(f"Unsupported evidence DB schema: {current}")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS evidence_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                record_id TEXT NOT NULL,
                claim_id TEXT NOT NULL,
                claim_hash TEXT NOT NULL,
                source_uid TEXT NOT NULL,
                citation_url TEXT NOT NULL,
                reviewer_id TEXT NOT NULL,
                decision TEXT NOT NULL CHECK (decision IN (
                    'supports','challenges','contextualizes','inconclusive','not-relevant'
                )),
                locator_kind TEXT NOT NULL CHECK (locator_kind IN (
                    'page','section','paragraph','figure','table','line','timestamp'
                )),
                locator TEXT NOT NULL,
                excerpt TEXT,
                note TEXT NOT NULL,
                created_at TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                event_hash TEXT UNIQUE NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_evidence_claim
                ON evidence_events(record_id, claim_id, source_uid, id);
            CREATE TRIGGER IF NOT EXISTS evidence_events_no_update
                BEFORE UPDATE ON evidence_events
                BEGIN SELECT RAISE(ABORT, 'Evidence events are append-only'); END;
            CREATE TRIGGER IF NOT EXISTS evidence_events_no_delete
                BEFORE DELETE ON evidence_events
                BEGIN SELECT RAISE(ABORT, 'Evidence events are append-only'); END;
            """
        )
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        connection.commit()


class ClaimEvidenceLedger:
    """A local-only write interface and an inspectable read-only audit trail."""

    def __init__(self, path: Path, catalog: CatalogRepository) -> None:
        self.path = path
        self.catalog = catalog

    def _connect(self, *, writable: bool = False) -> sqlite3.Connection:
        if not self.path.is_file():
            raise EvidenceIntegrityError("Evidence ledger has not been initialized")
        if writable:
            connection = sqlite3.connect(self.path, timeout=10)
        else:
            connection = sqlite3.connect(
                f"file:{self.path.resolve().as_posix()}?mode=ro", uri=True, timeout=10
            )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 10000")
        if not writable:
            connection.execute("PRAGMA query_only = ON")
        return connection

    @staticmethod
    def _check_schema(connection: sqlite3.Connection) -> None:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version != SCHEMA_VERSION:
            raise EvidenceIntegrityError(f"Invalid evidence schema version: {version}")
        objects = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE name IN "
                "('evidence_events','evidence_events_no_update','evidence_events_no_delete')"
            )
        }
        if objects != {
            "evidence_events", "evidence_events_no_update", "evidence_events_no_delete"
        }:
            raise EvidenceIntegrityError("Evidence ledger immutability controls are missing")

    @classmethod
    def _verified_rows(cls, connection: sqlite3.Connection) -> list[dict[str, Any]]:
        cls._check_schema(connection)
        previous = _GENESIS
        results: list[dict[str, Any]] = []
        try:
            for row in connection.execute("SELECT * FROM evidence_events ORDER BY id"):
                item = dict(row)
                if (
                    item["previous_hash"] != previous
                    or not isinstance(item["event_hash"], str)
                    or not _HASH.fullmatch(item["event_hash"])
                    or item["event_hash"] != _event_digest(previous, item)
                ):
                    raise EvidenceIntegrityError(
                        f"Evidence hash chain failed at event {item['id']}"
                    )
                previous = item["event_hash"]
                results.append(item)
        except (sqlite3.DatabaseError, KeyError, TypeError, ValueError) as exc:
            raise EvidenceIntegrityError("Evidence ledger is invalid") from exc
        return results

    def _claim(self, record_id: str, claim_id: str) -> tuple[dict, dict]:
        record = self.catalog.get(record_id)
        if record is None:
            raise EvidenceReviewError("Unknown catalog record")
        claim = next(
            (item for item in record.get("claim_reviews", []) if item["id"] == claim_id),
            None,
        )
        if claim is None:
            raise EvidenceReviewError("Unknown claim review lead for this record")
        return record, claim

    def record(
        self, *,
        record_id: str, claim_id: str, citation_url: str, reviewer_id: str,
        decision: str, locator_kind: str, locator: str,
        note: str, excerpt: str | None = None,
    ) -> dict[str, Any]:
        """Append a self-attributed evidence assessment from an explicit local caller."""
        record, claim = self._claim(record_id, claim_id)
        match = next(
            (lead for lead in claim["citations"] if lead["citation_url"] == citation_url),
            None,
        )
        if match is None:
            raise EvidenceReviewError("Source is not a nominated citation for this claim")
        reviewer_id = _require_text(reviewer_id, "reviewer_id", min_len=3, max_len=80)
        if not _REVIEWER.fullmatch(reviewer_id):
            raise EvidenceReviewError("reviewer_id must be an identifier, not a display name")
        if decision not in DECISIONS:
            raise EvidenceReviewError("Invalid evidence decision")
        if locator_kind not in LOCATOR_KINDS:
            raise EvidenceReviewError("Use an exact passage locator, not a source URL")
        locator = _require_text(locator, "locator", max_len=160)
        if locator.casefold() in {"unknown", "whole source", "entire article", "see source"}:
            raise EvidenceReviewError("An exact in-source passage locator is required")
        note = _require_text(note, "review note", min_len=20, max_len=2000)
        if excerpt is not None:
            excerpt = _require_text(excerpt, "passage excerpt", min_len=8, max_len=280)
        if decision in {"supports", "challenges"} and not excerpt:
            raise EvidenceReviewError(
                "Supporting/challenging decisions require a short reviewer-supplied excerpt"
            )

        payload = {
            "event_id": uuid.uuid4().hex,
            "record_id": record_id,
            "claim_id": claim_id,
            "claim_hash": claim_digest(claim["text"]),
            "source_uid": match["source_uid"],
            "citation_url": citation_url,
            "reviewer_id": reviewer_id,
            "decision": decision,
            "locator_kind": locator_kind,
            "locator": locator,
            "excerpt": excerpt,
            "note": note,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        with closing(self._connect(writable=True)) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                existing = self._verified_rows(connection)
                previous = existing[-1]["event_hash"] if existing else _GENESIS
                digest = _event_digest(previous, payload)
                fields = (*_EVENT_FIELDS, "previous_hash", "event_hash")
                args = {**payload, "previous_hash": previous, "event_hash": digest}
                connection.execute(
                    f"INSERT INTO evidence_events ({', '.join(fields)}) "
                    f"VALUES ({', '.join('?' for _ in fields)})",
                    tuple(args[key] for key in fields),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return {**args, "publication_state": "review-only"}

    def history(self, record_id: str, claim_id: str) -> dict[str, Any]:
        record, claim = self._claim(record_id, claim_id)
        leads = {lead["source_uid"]: lead for lead in claim["citations"]}
        rows: list[dict[str, Any]] = []
        if self.path.is_file():
            with closing(self._connect()) as connection:
                rows = self._verified_rows(connection)
        entries = [
            {
                **{field: row[field] for field in _EVENT_FIELDS},
                "event_hash": row["event_hash"],
                "previous_hash": row["previous_hash"],
                "current": (
                    row["claim_hash"] == claim_digest(claim["text"])
                    and row["source_uid"] in leads
                    and row["citation_url"] == leads[row["source_uid"]]["citation_url"]
                ),
            }
            for row in rows
            if row["record_id"] == record["id"] and row["claim_id"] == claim_id
        ]
        sources = []
        for uid, lead in leads.items():
            matching = [event for event in entries if event["source_uid"] == uid]
            latest_by_reviewer: dict[str, dict[str, Any]] = {}
            for event in matching:
                if event["current"]:
                    latest_by_reviewer[event["reviewer_id"]] = event
            latest = list(latest_by_reviewer.values())
            votes = {event["decision"] for event in latest}
            if not latest:
                status = "unreviewed"
            elif len(latest) == 1:
                status = "single-review"
            elif votes == {"inconclusive"}:
                status = "inconclusive"
            elif len(votes) == 1:
                status = "recorded-concordance"
            else:
                status = "disagreement"
            sources.append({
                "source_uid": uid,
                "citation_url": lead["citation_url"],
                "status": status,
                "active_reviewer_count": len(latest),
                "distinct_decisions": sorted(votes),
                "recorded_agreement_is_not_verification": True,
            })
        return {
            "record_id": record_id,
            "claim_id": claim_id,
            "claim_text": claim["text"],
            "claim_hash": claim_digest(claim["text"]),
            "events": entries,
            "sources": sources,
            "database_state": "ready" if self.path.is_file() else "absent",
            "publication_state": "review-only",
            "identity_note": (
                "Reviewer IDs are self-declared local labels, not authenticated identities. "
                "Two labels do not independently certify source support."
            ),
            "relationships_locked": True,
        }

    def status(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {
                "state": "absent", "event_count": 0,
                "detail": "No local evidence review ledger has been initialized.",
                "publication_state": "review-only", "relationships_locked": True,
            }
        with closing(self._connect()) as connection:
            entries = self._verified_rows(connection)
        return {
            "state": "ready",
            "event_count": len(entries),
            "reviewer_label_count": len({e["reviewer_id"] for e in entries}),
            "publication_state": "review-only",
            "relationships_locked": True,
            "identity_note": "Local reviewer identifiers are self-declared and unauthenticated.",
        }
