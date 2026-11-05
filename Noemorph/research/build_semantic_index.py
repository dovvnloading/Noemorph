from __future__ import annotations

"""Build Noemorph's local semantic-candidate review index.

This program deliberately produces *research leads*, not conceptual graph edges.
Every candidate remains machine-generated and publication-ineligible until a
human reviewer checks the endpoint claims and performs a prior-art search.

The index uses independent semantic views so names, authors, citations, and the
existing taxonomy cannot manufacture apparent conceptual agreement.  It also
uses a second local embedding model only as a neighbour-rank sensitivity check;
scores from the two model spaces are never averaged.
"""

import argparse
import difflib
import hashlib
import json
import math
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

import numpy as np


APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from backend.catalog import CatalogRepository  # noqa: E402


RECIPE_VERSION = "semantic-candidates-v1"
PRIMARY_MODEL = "nomic-embed-text:latest"
SENSITIVITY_MODEL = "mxbai-embed-large:latest"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
PRIMARY_DIMENSIONS = 768
SENSITIVITY_DIMENSIONS = 1024
CLUSTER_PREFIX = "clustering: "
QUERY_PREFIX = "search_query: "
DOCUMENT_PREFIX = "search_document: "

POSITIVE_VIEWS = ("core_claim", "target", "evidence")
CONCEPTUAL_VIEWS = (*POSITIVE_VIEWS, "limits")
ALL_CLUSTER_VIEWS = (*CONCEPTUAL_VIEWS, "identity")

WORD_RE = re.compile(r"[\w'-]+", re.UNICODE)
STOPWORDS = {
    "a", "about", "an", "and", "are", "as", "at", "be", "been", "but",
    "by", "can", "could", "does", "for", "from", "has", "have", "how",
    "in", "into", "is", "it", "its", "may", "model", "of", "on", "or",
    "that", "the", "their", "theory", "this", "to", "under", "which",
    "with", "within",
}


@dataclass(frozen=True)
class TextUnit:
    record_id: str
    view: str
    text: str
    fields: tuple[tuple[str, str], ...]
    input_hash: str


@dataclass(frozen=True)
class ModelInfo:
    name: str
    digest: str
    dimensions: int
    context_length: int | None


@dataclass
class EmbeddedView:
    name: str
    prefix: str
    units: list[TextUnit]
    vectors: np.ndarray
    record_indices: np.ndarray


@dataclass
class ViewAnalysis:
    cosine: np.ndarray
    csls: np.ndarray
    ranks: np.ndarray
    local_mean: np.ndarray
    global_sorted: np.ndarray
    strata_sorted: dict[tuple[str, str, str], np.ndarray]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def normalize_space(value: Any) -> str:
    return " ".join(str(value or "").split())


def walk_strings(value: Any, path: str) -> Iterator[tuple[str, str]]:
    if isinstance(value, str):
        text = normalize_space(value)
        if text:
            yield path, text
        return
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            yield from walk_strings(child, child_path)
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from walk_strings(child, f"{path}[{index}]")


def field_label(path: str) -> str:
    return re.sub(r"[_\-.]+", " ", path.split(".")[-1]).strip()


def join_fields(fields: Sequence[tuple[str, str]]) -> str:
    return "\n".join(f"{field_label(path)}: {text}" for path, text in fields)


def hash_text_unit(view: str, text: str) -> str:
    return sha256_text(f"{RECIPE_VERSION}\0{view}\0{text}")


def select_claim_fields(record: dict[str, Any]) -> list[tuple[str, str]]:
    fields = list(walk_strings(record.get("summary"), "summary"))
    claim_scope = list(walk_strings(record.get("claim_scope"), "claim_scope"))
    fields.extend(
        (path, text)
        for path, text in claim_scope
        if "does_not_establish" not in path.casefold()
        and "limitation" not in path.casefold()
    )
    fields.extend(walk_strings(record.get("mechanism"), "mechanism"))
    return fields


def select_target_fields(record: dict[str, Any]) -> list[tuple[str, str]]:
    fields = list(walk_strings(record.get("scope"), "scope"))
    claim_fields = list(walk_strings(record.get("claim_scope"), "claim_scope"))
    target_tokens = (
        "target", "applies", "level", "type", "explan", "domain", "phenomen",
        "what_it_explains", "claim_scope",
    )
    selected = [
        (path, text)
        for path, text in claim_fields
        if any(token in path.casefold() for token in target_tokens)
        and "does_not_establish" not in path.casefold()
    ]
    if selected:
        fields.extend(selected)
    elif isinstance(record.get("claim_scope"), str):
        fields.extend(claim_fields)
    return fields


def select_evidence_fields(record: dict[str, Any]) -> list[tuple[str, str]]:
    evidence_fields = list(walk_strings(record.get("evidence_profile"), "evidence_profile"))
    return [
        (path, text)
        for path, text in evidence_fields
        if not any(
            token in path.casefold()
            for token in ("limitation", "caveat", "weakness", "challenge")
        )
    ]


def select_limit_fields(record: dict[str, Any]) -> list[tuple[str, str]]:
    fields: list[tuple[str, str]] = []
    fields.extend(walk_strings(record.get("boundary_note"), "boundary_note"))
    fields.extend(walk_strings(record.get("status_note"), "status_note"))
    fields.extend(
        (path, text)
        for path, text in walk_strings(record.get("claim_scope"), "claim_scope")
        if "does_not_establish" in path.casefold()
        or "limitation" in path.casefold()
    )
    fields.extend(
        (path, text)
        for path, text in walk_strings(record.get("evidence_profile"), "evidence_profile")
        if any(token in path.casefold() for token in ("limitation", "caveat", "weakness", "challenge"))
    )
    return fields


def select_question_fields(record: dict[str, Any]) -> list[tuple[str, str]]:
    return list(walk_strings(record.get("open_questions"), "open_questions"))


def select_identity_fields(record: dict[str, Any]) -> list[tuple[str, str]]:
    fields: list[tuple[str, str]] = []
    fields.extend(walk_strings(record.get("name"), "name"))
    fields.extend(walk_strings(record.get("aliases"), "aliases"))
    fields.extend(walk_strings(record.get("proponents"), "proponents"))
    for index, citation in enumerate(record.get("citations", [])):
        fields.extend(walk_strings(citation.get("title"), f"citations[{index}].title"))
        fields.extend(walk_strings(citation.get("authors"), f"citations[{index}].authors"))
    return fields


def compact_words(text: str, maximum_words: int) -> str:
    words = text.split()
    if len(words) <= maximum_words:
        return text
    return " ".join(words[:maximum_words]) + " …"


def build_text_units(records: Sequence[dict[str, Any]]) -> dict[str, list[TextUnit]]:
    selectors = {
        "core_claim": select_claim_fields,
        "target": select_target_fields,
        "evidence": select_evidence_fields,
        "limits": select_limit_fields,
        "identity": select_identity_fields,
        "question": select_question_fields,
    }
    views: dict[str, list[TextUnit]] = {name: [] for name in selectors}
    views["document"] = []
    views["sensitivity"] = []

    for record in records:
        record_id = str(record["id"])
        selected: dict[str, list[tuple[str, str]]] = {}
        for view, selector in selectors.items():
            fields = selector(record)
            selected[view] = fields
            text = join_fields(fields)
            if not text:
                continue
            views[view].append(
                TextUnit(
                    record_id=record_id,
                    view=view,
                    text=text,
                    fields=tuple(fields),
                    input_hash=hash_text_unit(view, text),
                )
            )

        document_fields = [
            *selected.get("core_claim", []),
            *selected.get("evidence", []),
        ]
        document_text = join_fields(document_fields)
        if document_text:
            views["document"].append(
                TextUnit(
                    record_id=record_id,
                    view="document",
                    text=document_text,
                    fields=tuple(document_fields),
                    input_hash=hash_text_unit("document", document_text),
                )
            )

        sensitivity_fields = [
            *selected.get("core_claim", []),
            *selected.get("target", []),
        ]
        sensitivity_text = compact_words(join_fields(sensitivity_fields), 220)
        if sensitivity_text:
            views["sensitivity"].append(
                TextUnit(
                    record_id=record_id,
                    view="sensitivity",
                    text=sensitivity_text,
                    fields=tuple(sensitivity_fields),
                    input_hash=hash_text_unit("sensitivity", sensitivity_text),
                )
            )

    return views


class OllamaEmbeddingClient:
    def __init__(self, base_url: str, *, timeout: float = 180.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _json(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="GET" if data is None else "POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama returned HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Ollama is unavailable at {self.base_url}. Start Ollama before indexing."
            ) from exc

    def model_info(self, name: str) -> ModelInfo:
        tags = self._json("/api/tags")
        for model in tags.get("models", []):
            names = {str(model.get("name", "")), str(model.get("model", ""))}
            if name not in names:
                continue
            details = model.get("details", {})
            dimensions = (
                PRIMARY_DIMENSIONS if "nomic-embed-text" in name else SENSITIVITY_DIMENSIONS
            )
            context = 2048 if "nomic-embed-text" in name else 512
            return ModelInfo(
                name=name,
                digest=str(model.get("digest", "")),
                dimensions=dimensions,
                context_length=context,
            )
        raise RuntimeError(f"Required Ollama model is not installed: {name}")

    def embed(
        self,
        *,
        model: ModelInfo,
        texts: Sequence[str],
        prefix: str,
        batch_size: int,
        progress_label: str,
    ) -> np.ndarray:
        vectors: list[list[float]] = []
        started = time.perf_counter()
        for offset in range(0, len(texts), batch_size):
            batch = [f"{prefix}{text}" for text in texts[offset : offset + batch_size]]
            response = self._json(
                "/api/embed",
                {
                    "model": model.name,
                    "input": batch,
                    "truncate": False,
                    "keep_alive": "10m",
                },
            )
            embedded = response.get("embeddings")
            if not isinstance(embedded, list) or len(embedded) != len(batch):
                raise RuntimeError(
                    f"Ollama returned an invalid embedding batch for {progress_label}"
                )
            vectors.extend(embedded)
            done = min(offset + batch_size, len(texts))
            print(
                f"[{progress_label}] {done}/{len(texts)} units",
                file=sys.stderr,
                flush=True,
            )
        matrix = np.asarray(vectors, dtype=np.float32)
        if matrix.shape != (len(texts), model.dimensions):
            raise RuntimeError(
                f"Unexpected {model.name} shape {matrix.shape}; expected "
                f"({len(texts)}, {model.dimensions})"
            )
        if not np.isfinite(matrix).all():
            raise RuntimeError(f"Non-finite values returned by {model.name}")
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        if np.any(norms <= 0):
            raise RuntimeError(f"Zero-length vector returned by {model.name}")
        matrix /= norms
        elapsed = max(time.perf_counter() - started, 1e-9)
        print(
            f"[{progress_label}] complete in {elapsed:.2f}s ({len(texts) / elapsed:.1f} units/s)",
            file=sys.stderr,
            flush=True,
        )
        return matrix

    def unload(self, model_name: str) -> None:
        try:
            self._json(
                "/api/embed",
                {"model": model_name, "input": ["release"], "keep_alive": 0},
            )
        except RuntimeError:
            pass


def cache_path(cache_dir: Path, model: ModelInfo, view: str, prefix: str) -> Path:
    key = sha256_text(f"{model.digest}\0{view}\0{prefix}\0{RECIPE_VERSION}")[:16]
    safe_model = re.sub(r"[^a-z0-9]+", "-", model.name.casefold()).strip("-")
    return cache_dir / f"{safe_model}-{view}-{key}.npz"


def load_or_embed(
    *,
    client: OllamaEmbeddingClient,
    model: ModelInfo,
    units: list[TextUnit],
    view: str,
    prefix: str,
    cache_dir: Path,
    batch_size: int,
) -> np.ndarray:
    path = cache_path(cache_dir, model, view, prefix)
    ids = np.asarray([unit.record_id for unit in units])
    hashes = np.asarray([sha256_text(prefix + unit.text) for unit in units])
    if path.exists():
        try:
            cached = np.load(path, allow_pickle=False)
            cached_ids = cached["record_ids"]
            cached_hashes = cached["input_hashes"]
            vectors = cached["vectors"].astype(np.float32, copy=False)
            if (
                np.array_equal(cached_ids, ids)
                and np.array_equal(cached_hashes, hashes)
                and vectors.shape == (len(units), model.dimensions)
                and np.isfinite(vectors).all()
            ):
                print(f"[{model.name}/{view}] cache hit ({len(units)} units)", file=sys.stderr)
                return vectors
        except (KeyError, OSError, ValueError):
            pass
    vectors = client.embed(
        model=model,
        texts=[unit.text for unit in units],
        prefix=prefix,
        batch_size=batch_size,
        progress_label=f"{model.name}/{view}",
    )
    cache_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        record_ids=ids,
        input_hashes=hashes,
        vectors=vectors,
        model_digest=np.asarray(model.digest),
        recipe=np.asarray(RECIPE_VERSION),
        prefix=np.asarray(prefix),
    )
    return vectors


def expand_view_matrix(
    embedded: EmbeddedView,
    record_count: int,
) -> np.ndarray:
    matrix = np.full((record_count, embedded.vectors.shape[1]), np.nan, dtype=np.float32)
    matrix[embedded.record_indices] = embedded.vectors
    return matrix


def similarity_for_view(
    embedded: EmbeddedView,
    *,
    records: Sequence[dict[str, Any]],
    local_k: int = 10,
) -> ViewAnalysis:
    count = len(records)
    expanded = expand_view_matrix(embedded, count)
    present = np.isfinite(expanded).all(axis=1)
    cosine = np.full((count, count), np.nan, dtype=np.float32)
    present_indices = np.flatnonzero(present)
    if len(present_indices):
        values = expanded[present_indices] @ expanded[present_indices].T
        cosine[np.ix_(present_indices, present_indices)] = values
    np.fill_diagonal(cosine, np.nan)

    ranks = np.zeros((count, count), dtype=np.uint16)
    local_mean = np.full(count, np.nan, dtype=np.float32)
    for row in present_indices:
        valid = np.flatnonzero(np.isfinite(cosine[row]))
        if not len(valid):
            continue
        ordered = valid[np.argsort(cosine[row, valid])[::-1]]
        rank_values = np.arange(1, len(ordered) + 1, dtype=np.uint16)
        ranks[row, ordered] = rank_values
        local_mean[row] = float(np.mean(cosine[row, ordered[: min(local_k, len(ordered))]]))

    csls = 2 * cosine - local_mean[:, None] - local_mean[None, :]
    upper = cosine[np.triu_indices(count, 1)]
    global_sorted = np.sort(upper[np.isfinite(upper)])

    strata_values: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for left in range(count):
        for right in range(left + 1, count):
            score = cosine[left, right]
            if not math.isfinite(float(score)):
                continue
            kinds = sorted((str(records[left]["kind"]), str(records[right]["kind"])))
            completeness = (
                "deep"
                if records[left].get("claim_scope") and records[right].get("claim_scope")
                else "mixed"
            )
            strata_values[(kinds[0], kinds[1], completeness)].append(float(score))
    strata_sorted = {
        key: np.sort(np.asarray(values, dtype=np.float32))
        for key, values in strata_values.items()
        if len(values) >= 80
    }
    return ViewAnalysis(
        cosine=cosine,
        csls=csls,
        ranks=ranks,
        local_mean=local_mean,
        global_sorted=global_sorted,
        strata_sorted=strata_sorted,
    )


def cross_similarity(
    queries: EmbeddedView,
    documents: EmbeddedView,
    *,
    record_count: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    query_matrix = expand_view_matrix(queries, record_count)
    document_matrix = expand_view_matrix(documents, record_count)
    scores = query_matrix @ document_matrix.T
    scores[~np.isfinite(scores)] = np.nan
    np.fill_diagonal(scores, np.nan)
    ranks = np.zeros((record_count, record_count), dtype=np.uint16)
    for row in range(record_count):
        valid = np.flatnonzero(np.isfinite(scores[row]))
        if not len(valid):
            continue
        ordered = valid[np.argsort(scores[row, valid])[::-1]]
        ranks[row, ordered] = np.arange(1, len(ordered) + 1, dtype=np.uint16)
    sorted_scores = np.sort(scores[np.isfinite(scores)])
    return scores.astype(np.float32), ranks, sorted_scores.astype(np.float32)


def empirical_percentile(sorted_values: np.ndarray, value: float) -> float:
    if not len(sorted_values) or not math.isfinite(value):
        return 0.0
    return float(np.searchsorted(sorted_values, value, side="right") / len(sorted_values))


def pair_percentile(
    analysis: ViewAnalysis,
    records: Sequence[dict[str, Any]],
    left: int,
    right: int,
) -> float:
    score = float(analysis.cosine[left, right])
    kinds = sorted((str(records[left]["kind"]), str(records[right]["kind"])))
    completeness = (
        "deep" if records[left].get("claim_scope") and records[right].get("claim_scope") else "mixed"
    )
    values = analysis.strata_sorted.get((kinds[0], kinds[1], completeness), analysis.global_sorted)
    return empirical_percentile(values, score)


def normalize_person(value: str) -> str:
    return " ".join(WORD_RE.findall(value.casefold()))


def identity_label_similarity(
    left: dict[str, Any], right: dict[str, Any]
) -> float:
    left_labels = [str(left.get("name", "")), *map(str, left.get("aliases", []))]
    right_labels = [str(right.get("name", "")), *map(str, right.get("aliases", []))]

    def normalize(label: str) -> str:
        return " ".join(
            token
            for token in WORD_RE.findall(label.casefold())
            if token not in {"theory", "model", "framework", "account", "hypothesis"}
        )

    best = 0.0
    for left_label in left_labels:
        normalized_left = normalize(left_label)
        if not normalized_left:
            continue
        for right_label in right_labels:
            normalized_right = normalize(right_label)
            if not normalized_right:
                continue
            best = max(
                best,
                difflib.SequenceMatcher(
                    None, normalized_left, normalized_right, autojunk=False
                ).ratio(),
            )
    return best


def source_keys(record: dict[str, Any]) -> set[str]:
    return {
        str(citation.get("doi") or citation.get("url") or "").casefold()
        for citation in record.get("citations", [])
        if citation.get("doi") or citation.get("url")
    }


def lexical_terms(record: dict[str, Any]) -> set[str]:
    text = " ".join(
        (
            str(record.get("summary", "")),
            str(record.get("scope", "")),
            stable_json(record.get("claim_scope", "")),
        )
    )
    return {
        token
        for token in WORD_RE.findall(text.casefold())
        if len(token) > 2 and token not in STOPWORDS
    }


def lexical_jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def field_excerpt(unit: TextUnit | None, maximum: int = 280) -> tuple[str, str]:
    if unit is None or not unit.fields:
        return "", ""
    path, text = unit.fields[0]
    if len(text) > maximum:
        text = text[: maximum - 1].rstrip() + "…"
    return path, text


def representative_field_pair(
    left: TextUnit | None,
    right: TextUnit | None,
    maximum: int = 280,
) -> tuple[str, str, str, str]:
    """Choose inspectable input excerpts without pretending to explain the vector.

    The embedding score applies to the complete view text.  This lexical selector
    only chooses the most mutually specific fields to show a reviewer; callers
    label them as representative inputs, never as causal feature attribution.
    """
    if left is None or right is None or not left.fields or not right.fields:
        left_path, left_text = field_excerpt(left, maximum)
        right_path, right_text = field_excerpt(right, maximum)
        return left_path, left_text, right_path, right_text

    def terms(text: str) -> set[str]:
        return {
            token
            for token in WORD_RE.findall(text.casefold())
            if len(token) > 2 and token not in STOPWORDS
        }

    best: tuple[float, str, str, str, str] | None = None
    for left_path, left_text in left.fields:
        left_terms = terms(left_text)
        for right_path, right_text in right.fields:
            right_terms = terms(right_text)
            overlap = lexical_jaccard(left_terms, right_terms)
            specificity = min(len(left_terms), len(right_terms)) / 1000
            candidate = (overlap + specificity, left_path, left_text, right_path, right_text)
            if best is None or candidate[0] > best[0]:
                best = candidate
    assert best is not None
    _, left_path, left_text, right_path, right_text = best
    if len(left_text) > maximum:
        left_text = left_text[: maximum - 1].rstrip() + "…"
    if len(right_text) > maximum:
        right_text = right_text[: maximum - 1].rstrip() + "…"
    return left_path, left_text, right_path, right_text


def unit_map(units: Iterable[TextUnit]) -> dict[str, TextUnit]:
    return {unit.record_id: unit for unit in units}


def top_pairs_from_analysis(
    analysis: ViewAnalysis,
    *,
    per_record: int,
) -> set[tuple[int, int]]:
    pairs: set[tuple[int, int]] = set()
    count = analysis.ranks.shape[0]
    for left in range(count):
        neighbors = np.flatnonzero(
            (analysis.ranks[left] > 0) & (analysis.ranks[left] <= per_record)
        )
        for right in neighbors:
            if left == right:
                continue
            pairs.add((min(left, int(right)), max(left, int(right))))
    return pairs


def top_pairs_from_directional(
    ranks: np.ndarray,
    *,
    per_record: int,
) -> set[tuple[int, int]]:
    pairs: set[tuple[int, int]] = set()
    for source in range(ranks.shape[0]):
        targets = np.flatnonzero((ranks[source] > 0) & (ranks[source] <= per_record))
        for target in targets:
            if source == target:
                continue
            pairs.add((min(source, int(target)), max(source, int(target))))
    return pairs


def relation_type_for(
    *,
    percentiles: dict[str, float],
    question_percentile: float,
    cross_tradition: bool,
    identity_percentile: float,
    identity_name_similarity: float,
) -> str:
    if (
        identity_name_similarity >= 0.74
        and identity_percentile >= 0.995
        and percentiles.get("core_claim", 0) >= 0.97
    ):
        return "possible_duplicate"
    if question_percentile >= 0.995:
        return "question_relevance"
    if (
        percentiles.get("evidence", 0) >= 0.99
        and percentiles.get("target", 0) >= 0.85
    ):
        return "methodological_bridge"
    if cross_tradition and max(
        percentiles.get("core_claim", 0), percentiles.get("target", 0)
    ) >= 0.985:
        return "cross_tradition_analogy"
    if percentiles.get("target", 0) >= 0.99:
        return "shared_explanandum"
    return "conceptual_affinity"


def candidate_flags(
    *,
    cross_domain: bool,
    cross_tradition: bool,
    source_overlap: int,
    proponent_overlap: int,
    lexical_overlap: float,
    cross_model: bool,
    shallow: bool,
    hub_endpoint: bool,
    scope_barrier_signal: bool,
) -> list[str]:
    flags: list[str] = []
    if cross_domain:
        flags.append("cross-domain")
    if cross_tradition:
        flags.append("cross-tradition")
    if source_overlap == 0:
        flags.append("independent-record-sources")
    else:
        flags.append("shared-source")
    if proponent_overlap:
        flags.append("shared-proponent")
    if lexical_overlap >= 0.35:
        flags.append("high-lexical-overlap")
    if cross_model:
        flags.append("cross-model-neighbour")
    if shallow:
        flags.append("shallow-profile")
    if hub_endpoint:
        flags.append("semantic-hub-risk")
    if scope_barrier_signal:
        flags.append("scope-barrier-signal")
    return flags


def compute_candidates(
    *,
    records: Sequence[dict[str, Any]],
    units: dict[str, list[TextUnit]],
    analyses: dict[str, ViewAnalysis],
    directional_scores: np.ndarray,
    directional_ranks: np.ndarray,
    directional_sorted: np.ndarray,
    scope_barrier_scores: np.ndarray,
    scope_barrier_sorted: np.ndarray,
    sensitivity: ViewAnalysis,
    run_id: str,
    maximum_candidates: int,
    prior_art_pairs: set[tuple[str, str]],
) -> list[dict[str, Any]]:
    count = len(records)
    record_index_by_id = {
        str(record["id"]): index for index, record in enumerate(records)
    }
    candidate_pairs: set[tuple[int, int]] = set()
    for view in POSITIVE_VIEWS:
        candidate_pairs |= top_pairs_from_analysis(analyses[view], per_record=12)
    candidate_pairs |= top_pairs_from_directional(directional_ranks, per_record=6)
    candidate_pairs |= top_pairs_from_analysis(sensitivity, per_record=12)
    # A completed literature screen is durable research work. Keep its pair in
    # the scored pool even if a later catalog addition changes nearest-neighbour
    # ranks. This does not raise semantic confidence or publication eligibility.
    for record_a_id, record_b_id in prior_art_pairs:
        candidate_pairs.add(
            tuple(
                sorted(
                    (
                        record_index_by_id[record_a_id],
                        record_index_by_id[record_b_id],
                    )
                )
            )
        )

    unit_maps = {view: unit_map(view_units) for view, view_units in units.items()}
    source_sets = [source_keys(record) for record in records]
    people_sets = [
        {normalize_person(person) for person in record.get("proponents", []) if normalize_person(person)}
        for record in records
    ]
    term_sets = [lexical_terms(record) for record in records]

    # Count top-neighbour in-degree to expose hubness rather than silently rewarding it.
    indegree = np.zeros(count, dtype=np.int32)
    for analysis in (analyses["core_claim"], analyses["target"]):
        for row in range(count):
            for neighbor in np.flatnonzero(
                (analysis.ranks[row] > 0) & (analysis.ranks[row] <= 10)
            ):
                indegree[int(neighbor)] += 1
    hub_threshold = max(1, int(np.quantile(indegree, 0.97)))

    candidates: list[dict[str, Any]] = []
    for left, right in candidate_pairs:
        left_record = records[left]
        right_record = records[right]
        left_id = str(left_record["id"])
        right_id = str(right_record["id"])
        pair_ids = tuple(sorted((left_id, right_id)))
        is_prior_art_pair = pair_ids in prior_art_pairs
        percentiles = {
            view: pair_percentile(analyses[view], records, left, right)
            for view in POSITIVE_VIEWS
        }
        question_lr = float(directional_scores[left, right])
        question_rl = float(directional_scores[right, left])
        question_score = max(
            question_lr if math.isfinite(question_lr) else -1,
            question_rl if math.isfinite(question_rl) else -1,
        )
        question_pct = empirical_percentile(directional_sorted, question_score)
        barrier_lr = float(scope_barrier_scores[left, right])
        barrier_rl = float(scope_barrier_scores[right, left])
        scope_barrier_score = max(
            barrier_lr if math.isfinite(barrier_lr) else -1,
            barrier_rl if math.isfinite(barrier_rl) else -1,
        )
        scope_barrier_pct = empirical_percentile(
            scope_barrier_sorted, scope_barrier_score
        )
        identity_pct = pair_percentile(analyses["identity"], records, left, right)
        name_similarity = identity_label_similarity(left_record, right_record)
        strongest_positive = max((*percentiles.values(), question_pct))
        strong_groups = [view for view, pct in percentiles.items() if pct >= 0.95]
        if question_pct >= 0.99:
            strong_groups.append("question")
        # Keep the review queue sparse and high-signal. Shallow records may enter,
        # but can never be marked as robust candidates.
        if (
            not is_prior_art_pair
            and strongest_positive < 0.985
            and len(strong_groups) < 2
        ):
            continue

        source_overlap_keys = sorted(source_sets[left] & source_sets[right])
        people_overlap = sorted(people_sets[left] & people_sets[right])
        lexical_overlap = lexical_jaccard(term_sets[left], term_sets[right])
        cross_domain = left_record.get("domain") != right_record.get("domain")
        cross_tradition = left_record.get("tradition") != right_record.get("tradition")
        deep = bool(left_record.get("claim_scope") and right_record.get("claim_scope"))
        shallow = not deep

        core_ranks = (
            int(analyses["core_claim"].ranks[left, right]),
            int(analyses["core_claim"].ranks[right, left]),
        )
        sensitivity_ranks = (
            int(sensitivity.ranks[left, right]),
            int(sensitivity.ranks[right, left]),
        )
        reciprocal = all(0 < rank <= 20 for rank in core_ranks)
        cross_model = all(0 < rank <= 25 for rank in sensitivity_ranks)
        hub_endpoint = bool(indegree[left] >= hub_threshold or indegree[right] >= hub_threshold)
        scope_barrier_signal = scope_barrier_pct >= 0.99

        relation_type = relation_type_for(
            percentiles=percentiles,
            question_percentile=question_pct,
            cross_tradition=cross_tradition,
            identity_percentile=identity_pct,
            identity_name_similarity=name_similarity,
        )
        ranked_signals = sorted(
            [
                ("core_claim", percentiles["core_claim"]),
                ("target", percentiles["target"]),
                ("evidence", percentiles["evidence"]),
                ("question", question_pct),
            ],
            key=lambda item: item[1],
            reverse=True,
        )
        top_signal_values = [value for _, value in ranked_signals[:2]]
        reciprocal_strength = (
            max(0.0, 1.0 - (max(core_ranks) - 1) / 20) if reciprocal else 0.0
        )
        sensitivity_strength = (
            max(0.0, 1.0 - (max(sensitivity_ranks) - 1) / 25)
            if cross_model
            else 0.0
        )
        priority = 0.38 * top_signal_values[0] + 0.22 * top_signal_values[1]
        priority += 0.14 * reciprocal_strength
        priority += 0.10 * sensitivity_strength
        priority += 0.055 if cross_domain else 0
        priority += 0.035 if cross_tradition else 0
        priority -= 0.10 if shallow else 0
        priority -= 0.06 if source_overlap_keys else 0
        priority -= 0.04 if people_overlap else 0
        priority -= 0.045 if hub_endpoint else 0
        priority = float(np.clip(priority, 0.0, 1.0))

        independent_signal = (
            percentiles.get("evidence", 0) >= 0.98 or question_pct >= 0.995
        )
        confidence_tier = (
            "T1"
            if (
                deep
                and independent_signal
                and percentiles.get("core_claim", 0) >= 0.98
                and all(0 < rank <= 10 for rank in core_ranks)
                and all(0 < rank <= 15 for rank in sensitivity_ranks)
                and not source_overlap_keys
                and not people_overlap
                and not hub_endpoint
            )
            else "T0"
        )
        direction = "undirected"
        if relation_type == "question_relevance":
            direction = "a-to-b" if question_lr >= question_rl else "b-to-a"

        flags = candidate_flags(
            cross_domain=cross_domain,
            cross_tradition=cross_tradition,
            source_overlap=len(source_overlap_keys),
            proponent_overlap=len(people_overlap),
            lexical_overlap=lexical_overlap,
            cross_model=cross_model,
            shallow=shallow,
            hub_endpoint=hub_endpoint,
            scope_barrier_signal=scope_barrier_signal,
        )

        contributions: list[dict[str, Any]] = []
        for view, percentile in ranked_signals:
            if percentile < 0.90 and not (is_prior_art_pair and not contributions):
                continue
            if view == "question":
                source_index, target_index = (
                    (left, right) if question_lr >= question_rl else (right, left)
                )
                source_id = str(records[source_index]["id"])
                target_id = str(records[target_index]["id"])
                source_unit = unit_maps["question"].get(source_id)
                target_unit = unit_maps["document"].get(target_id)
                source_path, source_excerpt, target_path, target_excerpt = (
                    representative_field_pair(source_unit, target_unit)
                )
                contributions.append(
                    {
                        "signal": "question-to-record",
                        "field_a": source_path,
                        "field_b": target_path,
                        "excerpt_a": source_excerpt,
                        "excerpt_b": target_excerpt,
                        "score": round(question_score, 6),
                        "percentile": round(percentile, 6),
                        "source_rank": int(directional_ranks[source_index, target_index]),
                        "target_rank": None,
                        "input_hashes": {
                            source_id: source_unit.input_hash if source_unit else None,
                            target_id: target_unit.input_hash if target_unit else None,
                        },
                        "attribution_note": (
                            "The score applies to the complete semantic views. These are "
                            "representative input fields, not causal feature attribution."
                        ),
                    }
                )
                continue
            analysis = analyses[view]
            left_unit = unit_maps[view].get(left_id)
            right_unit = unit_maps[view].get(right_id)
            left_path, left_excerpt, right_path, right_excerpt = (
                representative_field_pair(left_unit, right_unit)
            )
            contributions.append(
                {
                    "signal": view.replace("_", "-"),
                    "field_a": left_path,
                    "field_b": right_path,
                    "excerpt_a": left_excerpt,
                    "excerpt_b": right_excerpt,
                    "score": round(float(analysis.cosine[left, right]), 6),
                    "csls": round(float(analysis.csls[left, right]), 6),
                    "percentile": round(percentile, 6),
                    "source_rank": int(analysis.ranks[left, right]) or None,
                    "target_rank": int(analysis.ranks[right, left]) or None,
                    "input_hashes": {
                        left_id: left_unit.input_hash if left_unit else None,
                        right_id: right_unit.input_hash if right_unit else None,
                    },
                    "attribution_note": (
                        "The score applies to the complete semantic views. These are "
                        "representative input fields, not causal feature attribution."
                    ),
                }
            )
            if len(contributions) >= 3:
                break

        primary_similarity = float(analyses["core_claim"].cosine[left, right])
        if not math.isfinite(primary_similarity):
            primary_similarity = question_score
        pair_key = f"{run_id}\0{left_id}\0{right_id}"
        candidate_id = f"sem-{sha256_text(pair_key)[:20]}"
        limits_left = unit_maps["limits"].get(left_id)
        limits_right = unit_maps["limits"].get(right_id)
        candidates.append(
            {
                "id": candidate_id,
                "run_id": run_id,
                "record_a_id": left_id,
                "record_b_id": right_id,
                "relation_type": relation_type,
                "direction": direction,
                "status": "machine-candidate",
                "publication_eligible": False,
                "confidence_tier": confidence_tier,
                "semantic_similarity": round(primary_similarity, 6),
                "similarity_percentile": round(percentiles["core_claim"], 6),
                "review_priority": round(priority, 6),
                "mutual_rank": max(core_ranks) if reciprocal else None,
                "cross_domain": cross_domain,
                "cross_tradition": cross_tradition,
                "source_overlap_count": len(source_overlap_keys),
                "proponent_overlap_count": len(people_overlap),
                "flags": flags,
                "field_contributions": contributions,
                "input_hashes": {
                    left_id: unit_maps["core_claim"][left_id].input_hash,
                    right_id: unit_maps["core_claim"][right_id].input_hash,
                },
                "signal_summary": {
                    "view_percentiles": {key: round(value, 6) for key, value in percentiles.items()},
                    "question_percentile": round(question_pct, 6),
                    "scope_barrier_percentile": round(scope_barrier_pct, 6),
                    "scope_barrier_direction": (
                        "a-limits-to-b-claim" if barrier_lr >= barrier_rl
                        else "b-limits-to-a-claim"
                    ),
                    "identity_percentile": round(identity_pct, 6),
                    "identity_name_similarity": round(name_similarity, 6),
                    "core_ranks": core_ranks,
                    "sensitivity_ranks": sensitivity_ranks,
                    "strong_signal_groups": strong_groups,
                    "lexical_jaccard": round(lexical_overlap, 6),
                    "endpoint_hub_indegree": [int(indegree[left]), int(indegree[right])],
                    "raw_review_priority": round(priority, 6),
                },
                "confounds": {
                    "shared_source_keys": source_overlap_keys,
                    "shared_proponents": people_overlap,
                    "limits_text_hashes": {
                        left_id: limits_left.input_hash if limits_left else None,
                        right_id: limits_right.input_hash if limits_right else None,
                    },
                },
                "novelty": {
                    "taxonomy_separation": "cross-domain" if cross_domain else "same-domain",
                    "tradition_separation": "cross-tradition" if cross_tradition else "same-tradition",
                    "literature_search_status": "not-run",
                    "earliest_direct_comparison": None,
                },
            }
        )

    # Prevent one familiar family from occupying the entire review queue while
    # retaining both a high-priority tranche and a corpus-coverage tranche. A
    # single global cut systematically hides records from sparse or newly added
    # research strata even when they have reviewable candidates.
    candidates.sort(
        key=lambda item: (
            item["confidence_tier"] == "T1",
            item["review_priority"],
            item["similarity_percentile"],
        ),
        reverse=True,
    )
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    relation_counts: Counter[str] = Counter()
    endpoint_counts: Counter[str] = Counter()
    covered_endpoints: set[str] = set()
    priority_quota = max(1, maximum_candidates // 2)
    priority_relation_cap = max(18, priority_quota // 3)
    relation_cap = max(18, maximum_candidates // 3)
    endpoint_cap = 5

    def add_candidate(candidate: dict[str, Any], *, selection_phase: str) -> None:
        relation_type = str(candidate["relation_type"])
        candidate["selection_phase"] = selection_phase
        selected.append(candidate)
        selected_ids.add(str(candidate["id"]))
        relation_counts[relation_type] += 1
        endpoint_counts[candidate["record_a_id"]] += 1
        endpoint_counts[candidate["record_b_id"]] += 1
        covered_endpoints.add(str(candidate["record_a_id"]))
        covered_endpoints.add(str(candidate["record_b_id"]))

    def admissible(candidate: dict[str, Any], *, cap: int) -> bool:
        if str(candidate["id"]) in selected_ids:
            return False
        relation_type = str(candidate["relation_type"])
        if relation_counts[relation_type] >= cap:
            return False
        return not (
            endpoint_counts[candidate["record_a_id"]] >= endpoint_cap
            or endpoint_counts[candidate["record_b_id"]] >= endpoint_cap
        )

    # Completed human prior-art screens are retained before automatic ranking.
    # They keep their computed confidence tier and scores; this phase records
    # provenance and prevents completed review work from disappearing as the
    # corpus evolves.
    screened_candidates = [
        candidate
        for candidate in candidates
        if tuple(sorted((candidate["record_a_id"], candidate["record_b_id"])))
        in prior_art_pairs
    ]
    if len(screened_candidates) > maximum_candidates:
        raise RuntimeError(
            "Prior-art screens exceed the configured semantic review queue size"
        )
    for candidate in screened_candidates:
        add_candidate(candidate, selection_phase="prior-art")

    # Phase 1 preserves the strongest, diversity-capped review candidates.
    for candidate in candidates:
        if len(selected) >= priority_quota:
            break
        if not admissible(candidate, cap=priority_relation_cap):
            continue
        add_candidate(candidate, selection_phase="priority")

    # Phase 2 adds the best available edge that exposes at least one endpoint
    # not represented in the priority tranche. It broadens review coverage; it
    # does not raise confidence or imply that every record has a valid relation.
    for candidate in candidates:
        if len(selected) >= maximum_candidates:
            break
        if not admissible(candidate, cap=relation_cap):
            continue
        if (
            candidate["record_a_id"] in covered_endpoints
            and candidate["record_b_id"] in covered_endpoints
        ):
            continue
        add_candidate(candidate, selection_phase="coverage")

    # Fill unused capacity by priority after coverage has been represented.
    for candidate in candidates:
        if len(selected) >= maximum_candidates:
            break
        if not admissible(candidate, cap=relation_cap):
            continue
        add_candidate(candidate, selection_phase="priority-fill")
    # Review priority is a within-run queue position, explicitly not confidence.
    # Rank normalization avoids a wall of clipped 1.0 values at the top.
    denominator = max(len(selected), 1)
    for rank, candidate in enumerate(selected, 1):
        candidate["review_priority"] = round(
            1.0 - (rank - 0.5) / denominator,
            6,
        )
    return selected


def catalog_file_manifest(catalog_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    paths = [catalog_path]
    for name in (
        *payload.get("supplements", []),
        *payload.get("profile_enrichments", []),
    ):
        paths.append(catalog_path.parent / str(name))
    return [
        {
            "file": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        }
        for path in paths
    ]


def load_prior_art_screen(
    path: Path,
    *,
    catalog_ids: set[str],
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, Any]]:
    if not path.exists():
        return {}, {"file": path.name, "status": "absent", "entry_count": 0}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("entries"), list):
        raise RuntimeError("Prior-art screen must contain an entries array")
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        raise RuntimeError("Prior-art screen must contain metadata")
    if metadata.get("entry_count") != len(payload["entries"]):
        raise RuntimeError("Prior-art screen entry_count does not match its entries")

    by_pair: dict[tuple[str, str], dict[str, Any]] = {}
    for index, entry in enumerate(payload["entries"]):
        if not isinstance(entry, dict):
            raise RuntimeError(f"Prior-art entry {index} is not an object")
        record_ids = entry.get("record_ids")
        if (
            not isinstance(record_ids, list)
            or len(record_ids) != 2
            or not all(isinstance(record_id, str) for record_id in record_ids)
        ):
            raise RuntimeError(f"Prior-art entry {index} needs two record IDs")
        unknown = set(record_ids) - catalog_ids
        if unknown:
            raise RuntimeError(
                f"Prior-art entry {index} references unknown records: {', '.join(sorted(unknown))}"
            )
        pair = tuple(sorted(record_ids))
        if pair in by_pair:
            raise RuntimeError(f"Prior-art screen repeats pair {pair[0]} / {pair[1]}")
        for field in ("status", "direct_comparison", "assessment", "caution"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise RuntimeError(f"Prior-art entry {index} lacks {field}")
        sources = entry.get("sources")
        if not isinstance(sources, list) or not sources:
            raise RuntimeError(f"Prior-art entry {index} needs sources")
        for source in sources:
            if (
                not isinstance(source, dict)
                or not str(source.get("url", "")).startswith("https://")
                or not str(source.get("title", "")).strip()
                or not str(source.get("role", "")).strip()
            ):
                raise RuntimeError(f"Prior-art entry {index} has an invalid source")
        by_pair[pair] = entry
    return by_pair, {
        "file": path.name,
        "status": "focused-screen",
        "entry_count": len(by_pair),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "screened_at": metadata.get("screened_at"),
        "method": metadata.get("method"),
        "epistemic_note": metadata.get("epistemic_note"),
    }


def build_run_provenance(
    *,
    records: Sequence[dict[str, Any]],
    catalog_manifest: list[dict[str, Any]],
    primary: ModelInfo,
    sensitivity: ModelInfo,
    ollama_version: str,
    prior_art_manifest: dict[str, Any],
) -> tuple[str, dict[str, Any], dict[str, Any], str]:
    from backend.semantic import catalog_fingerprint

    catalog_hash = catalog_fingerprint(records)
    model_json = {
        "provider": "Ollama local",
        "name": primary.name,
        "digest": primary.digest,
        "dimensions": primary.dimensions,
        "effective_context_length": primary.context_length,
        "primary": {
            "name": primary.name,
            "digest": primary.digest,
            "dimensions": primary.dimensions,
            "effective_context_length": primary.context_length,
            "task_prefixes": {
                "symmetric": CLUSTER_PREFIX.strip(),
                "query": QUERY_PREFIX.strip(),
                "document": DOCUMENT_PREFIX.strip(),
            },
        },
        "sensitivity": {
            "name": sensitivity.name,
            "digest": sensitivity.digest,
            "dimensions": sensitivity.dimensions,
            "effective_context_length": sensitivity.context_length,
            "use": "neighbour-rank agreement only",
        },
        "ollama_version": ollama_version,
    }
    recipe_json = {
        "version": RECIPE_VERSION,
        "metric": "cosine",
        "prefix": CLUSTER_PREFIX.strip(),
        "text_fields": [
            "summary",
            "scope",
            "claim_scope",
            "evidence_profile",
            "open_questions",
            "boundary_note",
            "status_note",
        ],
        "view_fields": {
            "conceptual": [
                "summary",
                "scope",
                "claim_scope excluding does_not_establish",
                "evidence_profile excluding limitations",
                "open_questions",
            ],
            "negative_controls": [
                "boundary_note",
                "status_note",
                "claim_scope.does_not_establish",
                "evidence_profile.limitations",
            ],
            "excluded_from_conceptual_vectors": [
                "name",
                "aliases",
                "proponents",
                "citations",
                "domain",
                "tradition",
                "status",
            ],
        },
        "comparison": "exact all-pairs",
        "record_count": len(records),
        "pair_count": len(records) * (len(records) - 1) // 2,
        "calibration": (
            "empirical percentile within sufficiently large kind/completeness strata; "
            "CSLS retained as a hubness diagnostic"
        ),
        "review_priority": (
            "within-run queue rank after multi-view, reciprocal-neighbour, cross-model, "
            "source-overlap, hubness, profile-depth, relation-diversity, and corpus-coverage "
            "controls; not confidence"
        ),
        "review_queue_selection": (
            "completed prior-art screens retained first without raising confidence, then "
            "half priority-first, best candidates exposing previously unrepresented "
            "endpoints, and priority fill; coverage selection does not raise confidence"
        ),
        "prior_art_screen": prior_art_manifest,
        "guardrail": "machine candidates are not accepted relationships or novelty claims",
    }
    run_fingerprint = sha256_text(
        stable_json(
            {
                "catalog_hash": catalog_hash,
                "model": model_json,
                "recipe": recipe_json,
            }
        )
    )
    return f"semrun-{run_fingerprint[:20]}", model_json, recipe_json, catalog_hash


def read_existing_reviews(db_path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    if not db_path.exists():
        return {}
    try:
        connection = sqlite3.connect(db_path)
        rows = connection.execute(
            """
            SELECT record_a_id, record_b_id, disposition, relation_tag,
                   reviewer_note, reviewed_at
            FROM semantic_candidates
            WHERE disposition <> 'unreviewed'
            """
        ).fetchall()
    except sqlite3.Error:
        return {}
    finally:
        try:
            connection.close()
        except UnboundLocalError:
            pass
    return {
        (str(row[0]), str(row[1])): {
            "disposition": row[2],
            "relation_tag": row[3],
            "reviewer_note": row[4],
            "reviewed_at": row[5],
        }
        for row in rows
    }


def write_semantic_database(
    *,
    db_path: Path,
    run_id: str,
    created_at: str,
    catalog_hash: str,
    catalog_version: str,
    model_json: dict[str, Any],
    recipe_json: dict[str, Any],
    records: Sequence[dict[str, Any]],
    candidates: Sequence[dict[str, Any]],
    prior_art_by_pair: dict[tuple[str, str], dict[str, Any]],
) -> None:
    from backend.semantic import initialize_semantic_database

    db_path.parent.mkdir(parents=True, exist_ok=True)
    reviews = read_existing_reviews(db_path)
    temporary = db_path.with_suffix(".building.sqlite3")
    if temporary.exists():
        temporary.unlink()
    initialize_semantic_database(temporary)
    connection = sqlite3.connect(temporary)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(
            """
            INSERT INTO semantic_runs (
                id, created_at, model_json, catalog_hash, catalog_version,
                recipe_json, record_count, candidate_count, state
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'building')
            """,
            (
                run_id,
                created_at,
                stable_json(model_json),
                catalog_hash,
                catalog_version,
                stable_json(recipe_json),
                len(records),
                len(candidates),
            ),
        )
        for candidate in candidates:
            review = reviews.get(
                (candidate["record_a_id"], candidate["record_b_id"]),
                {
                    "disposition": "unreviewed",
                    "relation_tag": None,
                    "reviewer_note": None,
                    "reviewed_at": None,
                },
            )
            contribution_payload = {
                "field_contributions": candidate["field_contributions"],
                "relation_type": candidate["relation_type"],
                "direction": candidate["direction"],
                "confidence_tier": candidate["confidence_tier"],
                "publication_eligible": candidate["publication_eligible"],
                "signal_summary": candidate["signal_summary"],
                "confounds": candidate["confounds"],
                "novelty": candidate["novelty"],
                "selection_phase": candidate["selection_phase"],
            }
            prior_art = prior_art_by_pair.get(
                (candidate["record_a_id"], candidate["record_b_id"])
            )
            if prior_art is not None:
                contribution_payload["prior_art"] = prior_art
            connection.execute(
                """
                INSERT INTO semantic_candidates (
                    id, run_id, record_a_id, record_b_id,
                    semantic_similarity, similarity_percentile, review_priority,
                    mutual_rank, cross_domain, cross_tradition,
                    source_overlap_count, proponent_overlap_count,
                    flags_json, contributions_json, input_hashes_json,
                    disposition, relation_tag, reviewer_note, reviewed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate["id"],
                    run_id,
                    candidate["record_a_id"],
                    candidate["record_b_id"],
                    candidate["semantic_similarity"],
                    candidate["similarity_percentile"],
                    candidate["review_priority"],
                    candidate["mutual_rank"],
                    int(candidate["cross_domain"]),
                    int(candidate["cross_tradition"]),
                    candidate["source_overlap_count"],
                    candidate["proponent_overlap_count"],
                    stable_json(candidate["flags"]),
                    stable_json(contribution_payload),
                    stable_json(candidate["input_hashes"]),
                    review["disposition"],
                    review["relation_tag"],
                    review["reviewer_note"],
                    review["reviewed_at"],
                ),
            )
        connection.execute(
            "UPDATE semantic_runs SET state = 'complete', candidate_count = ? WHERE id = ?",
            (len(candidates), run_id),
        )
        connection.commit()
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if not integrity or integrity[0] != "ok":
            raise RuntimeError(f"SQLite integrity check failed: {integrity}")
    finally:
        connection.close()
    os.replace(temporary, db_path)


def build_index(args: argparse.Namespace) -> dict[str, Any]:
    catalog_path = args.catalog.resolve()
    repository = CatalogRepository(catalog_path)
    records, total = repository.list_records(limit=1000)
    if total != len(records):
        raise RuntimeError(f"Expected all catalog records, loaded {len(records)} of {total}")
    records = sorted(records, key=lambda record: str(record["id"]))
    record_index = {str(record["id"]): index for index, record in enumerate(records)}
    units = build_text_units(records)
    print(
        "Semantic views: "
        + ", ".join(f"{name}={len(view_units)}" for name, view_units in units.items()),
        file=sys.stderr,
    )

    client = OllamaEmbeddingClient(args.ollama_url)
    primary = client.model_info(args.primary_model)
    sensitivity_model = client.model_info(args.sensitivity_model)
    version = client._json("/api/version").get("version", "unknown")
    if primary.dimensions != PRIMARY_DIMENSIONS:
        raise RuntimeError(f"Primary model dimensions changed: {primary.dimensions}")
    if sensitivity_model.dimensions != SENSITIVITY_DIMENSIONS:
        raise RuntimeError(f"Sensitivity model dimensions changed: {sensitivity_model.dimensions}")

    cache_dir = args.output.parent / "embedding-cache"
    embedded_views: dict[str, EmbeddedView] = {}
    for view in ALL_CLUSTER_VIEWS:
        view_units = units[view]
        vectors = load_or_embed(
            client=client,
            model=primary,
            units=view_units,
            view=view,
            prefix=CLUSTER_PREFIX,
            cache_dir=cache_dir,
            batch_size=args.batch_size,
        )
        embedded_views[view] = EmbeddedView(
            name=view,
            prefix=CLUSTER_PREFIX,
            units=view_units,
            vectors=vectors,
            record_indices=np.asarray([record_index[unit.record_id] for unit in view_units]),
        )

    question_vectors = load_or_embed(
        client=client,
        model=primary,
        units=units["question"],
        view="question-query",
        prefix=QUERY_PREFIX,
        cache_dir=cache_dir,
        batch_size=args.batch_size,
    )
    document_vectors = load_or_embed(
        client=client,
        model=primary,
        units=units["document"],
        view="record-document",
        prefix=DOCUMENT_PREFIX,
        cache_dir=cache_dir,
        batch_size=args.batch_size,
    )
    question_view = EmbeddedView(
        name="question",
        prefix=QUERY_PREFIX,
        units=units["question"],
        vectors=question_vectors,
        record_indices=np.asarray([record_index[unit.record_id] for unit in units["question"]]),
    )
    document_view = EmbeddedView(
        name="document",
        prefix=DOCUMENT_PREFIX,
        units=units["document"],
        vectors=document_vectors,
        record_indices=np.asarray([record_index[unit.record_id] for unit in units["document"]]),
    )

    sensitivity_vectors = load_or_embed(
        client=client,
        model=sensitivity_model,
        units=units["sensitivity"],
        view="sensitivity",
        prefix="",
        cache_dir=cache_dir,
        batch_size=max(8, args.batch_size // 2),
    )
    sensitivity_view = EmbeddedView(
        name="sensitivity",
        prefix="",
        units=units["sensitivity"],
        vectors=sensitivity_vectors,
        record_indices=np.asarray(
            [record_index[unit.record_id] for unit in units["sensitivity"]]
        ),
    )

    analyses = {
        view: similarity_for_view(embedded_views[view], records=records)
        for view in ALL_CLUSTER_VIEWS
    }
    directional_scores, directional_ranks, directional_sorted = cross_similarity(
        question_view,
        document_view,
        record_count=len(records),
    )
    scope_barrier_scores, _, scope_barrier_sorted = cross_similarity(
        embedded_views["limits"],
        embedded_views["core_claim"],
        record_count=len(records),
    )
    sensitivity_analysis = similarity_for_view(sensitivity_view, records=records)

    catalog_manifest = catalog_file_manifest(catalog_path)
    prior_art_by_pair, prior_art_manifest = load_prior_art_screen(
        args.output.parent / "prior-art-screen.json",
        catalog_ids=set(record_index),
    )
    run_id, model_json, recipe_json, catalog_hash = build_run_provenance(
        records=records,
        catalog_manifest=catalog_manifest,
        primary=primary,
        sensitivity=sensitivity_model,
        ollama_version=str(version),
        prior_art_manifest=prior_art_manifest,
    )
    candidates = compute_candidates(
        records=records,
        units=units,
        analyses=analyses,
        directional_scores=directional_scores,
        directional_ranks=directional_ranks,
        directional_sorted=directional_sorted,
        scope_barrier_scores=scope_barrier_scores,
        scope_barrier_sorted=scope_barrier_sorted,
        sensitivity=sensitivity_analysis,
        run_id=run_id,
        maximum_candidates=args.maximum_candidates,
        prior_art_pairs=set(prior_art_by_pair),
    )
    created_at = utc_now()
    write_semantic_database(
        db_path=args.output.resolve(),
        run_id=run_id,
        created_at=created_at,
        catalog_hash=catalog_hash,
        catalog_version=str(repository.metadata().get("version", "unknown")),
        model_json=model_json,
        recipe_json=recipe_json,
        records=records,
        candidates=candidates,
        prior_art_by_pair=prior_art_by_pair,
    )

    manifest = {
        "run_id": run_id,
        "created_at": created_at,
        "status": "ready",
        "record_count": len(records),
        "pair_count": len(records) * (len(records) - 1) // 2,
        "candidate_count": len(candidates),
        "confidence_tiers": dict(Counter(candidate["confidence_tier"] for candidate in candidates)),
        "relation_types": dict(Counter(candidate["relation_type"] for candidate in candidates)),
        "flags": dict(Counter(flag for candidate in candidates for flag in candidate["flags"])),
        "prior_art_screen": prior_art_manifest,
        "screened_candidate_count": sum(
            (candidate["record_a_id"], candidate["record_b_id"]) in prior_art_by_pair
            for candidate in candidates
        ),
        "catalog_hash": catalog_hash,
        "catalog_files": catalog_manifest,
        "models": model_json,
        "recipe": recipe_json,
        "database": str(args.output.resolve()),
        "epistemic_status": (
            "All rows are machine-generated research candidates. Embedding proximity does not "
            "establish correlation, causation, influence, equivalence, support, refutation, or novelty."
        ),
    }
    manifest_path = args.output.parent / "semantic-run.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    client.unload(primary.name)
    client.unload(sensitivity_model.name)
    return manifest


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a local, review-only semantic candidate index for Noemorph."
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=APP_ROOT / "data" / "catalog.json",
        help="Path to the catalog root JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=APP_ROOT / "data" / "semantic" / "semantic.sqlite3",
        help="SQLite review index destination.",
    )
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--primary-model", default=PRIMARY_MODEL)
    parser.add_argument("--sensitivity-model", default=SENSITIVITY_MODEL)
    parser.add_argument("--batch-size", type=int, default=48)
    parser.add_argument("--maximum-candidates", type=int, default=600)
    args = parser.parse_args(argv)
    if args.batch_size < 1 or args.batch_size > 128:
        parser.error("--batch-size must be between 1 and 128")
    if args.maximum_candidates < 1 or args.maximum_candidates > 5000:
        parser.error("--maximum-candidates must be between 1 and 5000")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manifest = build_index(args)
    except Exception as exc:  # noqa: BLE001 - CLI boundary with a concise failure
        print(f"Semantic indexing failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
