"""General Evidence Search for Phase J / J-02.

Evidence Search is intentionally separate from Object Search and Object Evidence
Package retrieval. Results are Evidence records with provenance, never accepted
Object Knowledge and never truth/confidence scores.
"""

from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from sgokb.domain import validate_vectors

RRF_K = 60


class EvidenceSearchMode(str, Enum):
    LEXICAL = "lexical"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


@dataclass(frozen=True, slots=True)
class EvidenceSearchResult:
    evidence_id: str
    source_id: str
    snapshot_id: str
    run_id: str
    extraction_mode: str
    language: str | None
    content: str
    rank: int
    fused_score: float
    score_type: str
    channels: tuple[str, ...]
    lexical_rank: int | None
    semantic_score: float | None
    provenance: dict


@dataclass(frozen=True, slots=True)
class EvidenceSearchResponse:
    query: str
    mode: EvidenceSearchMode
    results: tuple[EvidenceSearchResult, ...]
    degraded_channels: tuple[str, ...] = ()
    include_historical: bool = False


class EvidenceSearch:
    """Search Evidence independently from accepted Object Knowledge.

    The effective Snapshot / Normalization Run generation is the default scope.
    Historical generations require explicit opt-in. Semantic search uses only the
    injected local embedder and never silently falls back to another provider.
    """

    def __init__(self, repository, embedder=None) -> None:
        self.repository = repository
        self.db = repository.db
        self.embedder = embedder

    @staticmethod
    def _fts_phrase(value: str) -> str:
        return '"' + value.replace('"', '""') + '"'

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        numerator = sum(a * b for a, b in zip(left, right))
        left_length = math.sqrt(sum(value * value for value in left))
        right_length = math.sqrt(sum(value * value for value in right))
        if left_length == 0 or right_length == 0:
            raise ValueError("Zero Evidence vector is invalid for cosine search")
        return numerator / (left_length * right_length)

    def _source_scope(
        self,
        *,
        source_ids: Iterable[str],
        object_id: str | None,
        association_status: str | None,
    ) -> tuple[str, ...] | None:
        explicit = tuple(dict.fromkeys(source_ids))
        if explicit:
            self.repository.source_store.validate_source_references(explicit)
        if object_id is None:
            return explicit or None

        self.repository.object_store.get_object(object_id)
        associations = self.repository.source_store.associations_for_object(object_id)
        if association_status is None:
            statuses = {"candidate", "confirmed"}
        else:
            if association_status not in {"candidate", "confirmed", "excluded"}:
                raise ValueError("Unknown Source/Object association status")
            statuses = {association_status}
        associated = {row["source_id"] for row in associations if row["status"] in statuses}
        if explicit:
            return tuple(source_id for source_id in explicit if source_id in associated)
        return tuple(sorted(associated))

    def _candidate_rows(
        self,
        *,
        source_scope: tuple[str, ...] | None,
        language: str | None,
        include_historical: bool,
    ) -> list[dict]:
        if include_historical:
            clauses = ["1=1"]
            params: list[object] = []
            if source_scope is not None:
                if not source_scope:
                    return []
                marks = ",".join("?" for _ in source_scope)
                clauses.append(f"source_id IN ({marks})")
                params.extend(source_scope)
            if language is not None:
                clauses.append("language=?")
                params.append(language)
            rows = self.db.execute(
                "SELECT * FROM evidence_records WHERE "
                + " AND ".join(clauses)
                + " ORDER BY source_id,snapshot_id,run_id,ordinal,id",
                params,
            ).fetchall()
            return [dict(row) for row in rows]

        if source_scope is not None and not source_scope:
            return []
        rows = list(self.repository.source_store.effective_evidence_rows(source_scope))
        if language is not None:
            rows = [row for row in rows if row.get("language") == language]
        return rows

    @staticmethod
    def _literal_lexical_ranks(query: str, rows: list[dict]) -> dict[str, int]:
        normalized = " ".join(query.casefold().split())
        terms = normalized.split()
        scored = []
        for row in rows:
            content = " ".join(row["content"].casefold().split())
            if normalized in content:
                tier = 0
            elif terms and all(term in content for term in terms):
                tier = 1
            else:
                continue
            scored.append((tier, len(content), row["id"]))
        scored.sort()
        return {evidence_id: rank for rank, (_, _, evidence_id) in enumerate(scored, 1)}

    def _lexical_ranks(
        self,
        query: str,
        rows: list[dict],
        *,
        source_scope: tuple[str, ...] | None,
        include_historical: bool,
        pool: int,
    ) -> dict[str, int]:
        allowed = {row["id"] for row in rows}
        if not include_historical:
            try:
                hits = self.repository.source_store.lexical_evidence_rows(
                    self._fts_phrase(query),
                    source_ids=source_scope,
                    limit=pool,
                )
                ranked = [row["id"] for row in hits if row["id"] in allowed]
                if ranked:
                    return {evidence_id: rank for rank, evidence_id in enumerate(ranked, 1)}
            except sqlite3.OperationalError:
                pass
        return self._literal_lexical_ranks(query, rows)

    def _semantic_scores(
        self,
        query: str,
        rows: list[dict],
        *,
        batch_size: int,
    ) -> dict[str, float]:
        if self.embedder is None:
            raise RuntimeError("Semantic Evidence Search requires an injected local embedder")
        query_vectors = self.embedder.embed([query], query=True)
        dimension = validate_vectors(query_vectors, 1)
        query_vector = query_vectors[0]
        scores: dict[str, float] = {}
        for start in range(0, len(rows), batch_size):
            batch = rows[start : start + batch_size]
            vectors = self.embedder.embed([row["content"] for row in batch])
            current_dimension = validate_vectors(vectors, len(batch))
            if current_dimension != dimension:
                raise ValueError("Evidence embedding dimension differs from query embedding")
            for row, vector in zip(batch, vectors):
                scores[row["id"]] = self._cosine(query_vector, vector)
        return scores

    def search(
        self,
        query: str,
        *,
        mode: EvidenceSearchMode | str = EvidenceSearchMode.HYBRID,
        limit: int = 10,
        source_ids: Iterable[str] = (),
        object_id: str | None = None,
        association_status: str | None = None,
        language: str | None = None,
        include_historical: bool = False,
        semantic_batch_size: int = 32,
    ) -> EvidenceSearchResponse:
        query = query.strip()
        if not query:
            raise ValueError("Evidence Search query must be non-empty")
        if not 1 <= limit <= 1000:
            raise ValueError("Evidence Search limit must be between 1 and 1000")
        if semantic_batch_size < 1:
            raise ValueError("Semantic batch size must be positive")
        mode = EvidenceSearchMode(mode)
        source_scope = self._source_scope(
            source_ids=source_ids,
            object_id=object_id,
            association_status=association_status,
        )
        rows = self._candidate_rows(
            source_scope=source_scope,
            language=language,
            include_historical=include_historical,
        )
        by_id = {row["id"]: row for row in rows}
        pool = min(5000, max(100, limit * 10))
        lexical: dict[str, int] = {}
        semantic: dict[str, float] = {}
        degraded: list[str] = []

        if mode in {EvidenceSearchMode.LEXICAL, EvidenceSearchMode.HYBRID}:
            lexical = self._lexical_ranks(
                query,
                rows,
                source_scope=source_scope,
                include_historical=include_historical,
                pool=pool,
            )

        if mode in {EvidenceSearchMode.SEMANTIC, EvidenceSearchMode.HYBRID}:
            try:
                semantic = self._semantic_scores(
                    query,
                    rows,
                    batch_size=semantic_batch_size,
                )
            except RuntimeError as exc:
                if mode is EvidenceSearchMode.SEMANTIC:
                    raise
                degraded.append(f"semantic:{type(exc).__name__}")

        semantic_rank = {
            evidence_id: rank
            for rank, (evidence_id, _) in enumerate(
                sorted(semantic.items(), key=lambda item: (-item[1], item[0])),
                1,
            )
        }
        candidate_ids = set(lexical) | set(semantic_rank)
        scored = []
        for evidence_id in candidate_ids:
            channels = []
            fused = 0.0
            if evidence_id in lexical:
                channels.append("lexical")
                fused += 1.0 / (RRF_K + lexical[evidence_id])
            if evidence_id in semantic_rank:
                channels.append("semantic")
                fused += 1.0 / (RRF_K + semantic_rank[evidence_id])
            scored.append((evidence_id, fused, tuple(channels)))
        scored.sort(key=lambda item: (-item[1], item[0]))

        results = []
        for rank, (evidence_id, fused, channels) in enumerate(scored[:limit], 1):
            row = by_id[evidence_id]
            results.append(
                EvidenceSearchResult(
                    evidence_id=evidence_id,
                    source_id=row["source_id"],
                    snapshot_id=row["snapshot_id"],
                    run_id=row["run_id"],
                    extraction_mode=row["extraction_mode"],
                    language=row.get("language"),
                    content=row["content"],
                    rank=rank,
                    fused_score=fused,
                    score_type="rrf" if len(channels) > 1 else f"{channels[0]}_rank",
                    channels=channels,
                    lexical_rank=lexical.get(evidence_id),
                    semantic_score=semantic.get(evidence_id),
                    provenance=self.repository.source_store.evidence_context(evidence_id),
                )
            )
        return EvidenceSearchResponse(
            query=query,
            mode=mode,
            results=tuple(results),
            degraded_channels=tuple(degraded),
            include_historical=include_historical,
        )
