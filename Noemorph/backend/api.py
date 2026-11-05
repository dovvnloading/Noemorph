from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import FastAPI, HTTPException, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from .catalog import CatalogIntegrityError, CatalogRepository
from .evidence_ledger import (
    ClaimEvidenceLedger,
    EvidenceIntegrityError,
    EvidenceReviewError,
)
from .semantic import (
    SemanticCandidateNotFoundError,
    SemanticIntegrityError,
    SemanticRepository,
    SemanticUnavailableError,
    validate_reviewer_note,
)


SemanticDisposition = Literal[
    "unreviewed", "shortlisted", "needs-review", "dismissed"
]
SemanticRelationTag = Literal[
    "possible-convergence",
    "possible-contrast",
    "shared-mechanism",
    "shared-phenomenology",
    "shared-method",
    "possible-lineage",
    "terminological-overlap",
    "artifact-risk",
]


class SemanticReviewPatch(BaseModel):
    """Human review only; this cannot publish a conceptual graph edge."""

    model_config = ConfigDict(extra="forbid")

    disposition: SemanticDisposition | None = None
    relation_tag: SemanticRelationTag | None = None
    reviewer_note: str | None = None

    @field_validator("reviewer_note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        return validate_reviewer_note(value)

    @model_validator(mode="after")
    def validate_patch(self) -> "SemanticReviewPatch":
        if not self.model_fields_set:
            raise ValueError("PATCH must change at least one review field")
        if "disposition" in self.model_fields_set and self.disposition is None:
            raise ValueError("disposition cannot be null")
        if self.disposition == "unreviewed" and (
            self.relation_tag is not None or self.reviewer_note is not None
        ):
            raise ValueError("unreviewed candidates cannot retain a tag or note")
        return self


def create_app(
    project_root: Path,
    *,
    serve_frontend: bool = True,
    semantic_db_path: Path | None = None,
    claim_evidence_db_path: Path | None = None,
) -> FastAPI:
    repository = CatalogRepository(project_root / "data" / "catalog.json")
    semantic_repository = SemanticRepository(
        semantic_db_path or project_root / "data" / "semantic" / "semantic.sqlite3",
        repository,
    )
    claim_evidence_ledger = ClaimEvidenceLedger(
        claim_evidence_db_path
        or project_root / "data" / "reviews" / "claim-evidence.sqlite3",
        repository,
    )
    app = FastAPI(
        title="Noemorph Research API",
        version="0.2.0",
        description="Citation-first catalog API for theories and positions concerning mind and consciousness.",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    app.state.repository = repository
    app.state.semantic_repository = semantic_repository
    app.state.claim_evidence_ledger = claim_evidence_ledger
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=False,
        allow_methods=["GET", "PATCH"],
        allow_headers=["*"],
    )

    @app.exception_handler(CatalogIntegrityError)
    async def catalog_error_handler(_, exc: CatalogIntegrityError) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": str(exc)})

    @app.exception_handler(EvidenceIntegrityError)
    async def evidence_integrity_handler(_, exc: EvidenceIntegrityError) -> JSONResponse:
        return JSONResponse(
            status_code=503, content={"detail": str(exc), "state": "invalid"}
        )

    @app.exception_handler(SemanticUnavailableError)
    async def semantic_unavailable_handler(
        _, exc: SemanticUnavailableError
    ) -> JSONResponse:
        status_code = 409 if exc.state in {"empty", "stale"} else 503
        return JSONResponse(
            status_code=status_code,
            content={"detail": str(exc), "state": exc.state},
        )

    @app.exception_handler(SemanticIntegrityError)
    async def semantic_integrity_handler(_, exc: SemanticIntegrityError) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"detail": str(exc), "state": "invalid"},
        )

    @app.exception_handler(SemanticCandidateNotFoundError)
    async def semantic_not_found_handler(
        _, exc: SemanticCandidateNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.get("/api/health")
    def health() -> dict[str, object]:
        metadata = repository.metadata()
        return {
            "status": "ok",
            "service": "noemorph",
            "catalog_version": metadata.get("version", "unknown"),
        }

    @app.get("/api/meta")
    def meta() -> dict[str, object]:
        return repository.metadata()

    @app.get("/api/catalog")
    def catalog(
        q: str | None = None,
        kind: Annotated[list[str] | None, Query()] = None,
        domain: Annotated[list[str] | None, Query()] = None,
        status: Annotated[list[str] | None, Query()] = None,
        tradition: Annotated[list[str] | None, Query()] = None,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=500, ge=1, le=1000),
    ) -> dict[str, object]:
        items, total = repository.list_records(
            query=q,
            kinds=kind or (),
            domains=domain or (),
            statuses=status or (),
            traditions=tradition or (),
            offset=offset,
            limit=limit,
        )
        return {"items": items, "total": total, "offset": offset, "limit": limit}

    @app.get("/api/catalog/{record_id}")
    def record(record_id: str) -> dict[str, object]:
        item = repository.get(record_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Catalog record not found")
        return item

    @app.get("/api/sources")
    def sources(q: str | None = None, authority: str | None = None) -> dict[str, object]:
        items = repository.list_sources(query=q, authority=authority)
        return {"items": items, "total": len(items)}

    @app.get("/api/discovery/closer-to-truth")
    def closer_to_truth_discovery(
        q: str | None = None,
        category: Annotated[list[str] | None, Query()] = None,
        match_status: Annotated[list[str] | None, Query()] = None,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=500, ge=1, le=1000),
    ) -> dict[str, object]:
        collection = repository.discovery_metadata()
        if collection.get("availability") == "unavailable":
            raise HTTPException(status_code=503, detail=collection["notice"])
        items, total = repository.list_discovery_entries(
            query=q,
            categories=category or (),
            match_statuses=match_status or (),
            offset=offset,
            limit=limit,
        )
        return {
            "items": items,
            "total": total,
            "offset": offset,
            "limit": limit,
            "collection": collection,
        }

    @app.get("/api/coverage")
    def coverage() -> dict[str, object]:
        return repository.coverage()

    @app.get("/api/graph/taxonomy")
    def taxonomy_graph() -> dict[str, object]:
        return repository.taxonomy_graph()

    @app.get("/api/claim-evidence/status")
    def claim_evidence_status() -> dict[str, Any]:
        """Read-only. Never create a database or accept review writes over HTTP."""
        return claim_evidence_ledger.status()

    @app.get("/api/claim-evidence/records/{record_id}/claims/{claim_id}")
    def claim_evidence_history(record_id: str, claim_id: str) -> dict[str, Any]:
        try:
            return claim_evidence_ledger.history(record_id, claim_id)
        except EvidenceReviewError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/semantic/status")
    def semantic_status() -> dict[str, Any]:
        return semantic_repository.status()

    @app.get("/api/semantic/candidates")
    def semantic_candidates(
        q: str | None = None,
        disposition: Annotated[list[str] | None, Query()] = None,
        relation_tag: Annotated[list[str] | None, Query()] = None,
        record_id: str | None = None,
        cross_domain: bool | None = None,
        cross_tradition: bool | None = None,
        min_similarity: float | None = Query(default=None, ge=-1, le=1),
        min_priority: float | None = Query(default=None, ge=0, le=1),
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=500),
    ) -> dict[str, Any]:
        try:
            items, total, run = semantic_repository.list_candidates(
                query=q,
                dispositions=disposition or (),
                relation_tags=relation_tag or (),
                record_id=record_id,
                cross_domain=cross_domain,
                cross_tradition=cross_tradition,
                min_similarity=min_similarity,
                min_priority=min_priority,
                offset=offset,
                limit=limit,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            "items": items,
            "total": total,
            "offset": offset,
            "limit": limit,
            "run_id": run["id"],
            "relationship_synthesis_locked": True,
        }

    @app.get("/api/semantic/candidates/{candidate_id}")
    def semantic_candidate(candidate_id: str) -> dict[str, Any]:
        item = semantic_repository.get_candidate(candidate_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Semantic candidate not found")
        return item

    @app.patch("/api/semantic/candidates/{candidate_id}")
    def review_semantic_candidate(
        candidate_id: str, patch: SemanticReviewPatch
    ) -> dict[str, Any]:
        changes: dict[str, Any] = {}
        if "disposition" in patch.model_fields_set:
            changes["disposition"] = patch.disposition
        if "relation_tag" in patch.model_fields_set:
            changes["relation_tag"] = patch.relation_tag
        if "reviewer_note" in patch.model_fields_set:
            changes["reviewer_note"] = patch.reviewer_note
        try:
            return semantic_repository.update_candidate(candidate_id, **changes)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/api/graph/relationships")
    def relationship_graph() -> JSONResponse:
        coverage = repository.coverage()
        semantic = semantic_repository.status()
        return JSONResponse(
            status_code=423,
            content={
                "detail": (
                    "Conceptual relationship mapping remains locked. Semantic proximity "
                    "candidates require human evidence review and do not constitute graph edges."
                ),
                "gate_state": coverage["gate_state"],
                "readiness_percent": coverage["readiness_percent"],
                "semantic_state": semantic["state"],
            },
        )

    @app.websocket("/{path:path}")
    async def reject_websocket(websocket: WebSocket, path: str) -> None:
        del path
        await websocket.close(code=1008, reason="Noemorph exposes an HTTP-only local API.")

    if serve_frontend:
        dist_dir = project_root / "frontend" / "dist"
        if not dist_dir.exists():
            raise RuntimeError(
                f"Frontend build is missing at {dist_dir}. Run the bootstrap build first."
            )
        app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")

    return app
