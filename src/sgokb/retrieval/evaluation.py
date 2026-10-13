"""Reusable retrieval evaluation primitives for Phase I / I-07."""

from __future__ import annotations

import math
import statistics
import time
from dataclasses import dataclass
from typing import Mapping, Sequence

from sgokb.domain import (
    EmbeddingSpaceSpec,
    VectorIndexMetadata,
    VectorIndexPoint,
    VectorMatch,
    VectorSearchFilter,
    VectorSearchHit,
)


def ranked_retrieval_metrics(
    ranked_ids: Sequence[str],
    relevance: Mapping[str, int | float],
    *,
    k_values: Sequence[int] = (1, 5, 10),
) -> dict[str, float]:
    """Compute graded ranking metrics without treating score as truth/confidence."""

    relevant = {item_id for item_id, grade in relevance.items() if grade > 0}
    ranks = [rank for rank, item_id in enumerate(ranked_ids, start=1) if item_id in relevant]
    first = min(ranks) if ranks else None
    result: dict[str, float] = {
        "mrr": 0.0 if first is None else 1.0 / first,
    }
    for k in k_values:
        retrieved = set(ranked_ids[:k])
        result[f"recall@{k}"] = 0.0 if not relevant else len(retrieved & relevant) / len(relevant)
    k = max(k_values)
    dcg = 0.0
    for rank, item_id in enumerate(ranked_ids[:k], start=1):
        grade = float(relevance.get(item_id, 0))
        dcg += (2.0**grade - 1.0) / math.log2(rank + 1)
    ideal_grades = sorted((float(value) for value in relevance.values()), reverse=True)[:k]
    ideal = sum(
        (2.0**grade - 1.0) / math.log2(rank + 1) for rank, grade in enumerate(ideal_grades, 1)
    )
    result[f"ndcg@{k}"] = 0.0 if ideal == 0 else dcg / ideal
    return result


def aggregate_metric_rows(rows: Sequence[Mapping[str, float]]) -> dict[str, float]:
    if not rows:
        return {}
    keys = tuple(rows[0].keys())
    return {key: statistics.fmean(float(row[key]) for row in rows) for key in keys}


def ann_recall_at_k(found: Sequence[str], expected: Sequence[str], k: int = 10) -> float:
    expected_top = set(expected[:k])
    if not expected_top:
        return 0.0
    return len(set(found[:k]) & expected_top) / len(expected_top)


def latency_summary(samples_seconds: Sequence[float]) -> dict[str, float]:
    if not samples_seconds:
        return {"count": 0, "p50_ms": 0.0, "p95_ms": 0.0, "mean_ms": 0.0}
    ordered = sorted(float(value) for value in samples_seconds)
    p95_index = min(len(ordered) - 1, math.ceil(len(ordered) * 0.95) - 1)
    return {
        "count": len(ordered),
        "p50_ms": statistics.median(ordered) * 1000.0,
        "p95_ms": ordered[p95_index] * 1000.0,
        "mean_ms": statistics.fmean(ordered) * 1000.0,
    }


@dataclass
class ExactVectorIndexAdapter:
    """Float32-style exact cosine reference implementing VectorIndexAdapter.

    This is a benchmark/reference adapter rather than the production ANN backend. It keeps
    vectors in process memory and applies all hard filters before ranking.
    """

    backend_key: str = "exact-cosine"

    def __post_init__(self) -> None:
        self._points_by_space: dict[str, dict[str, VectorIndexPoint]] = {}
        self._dimensions: dict[str, int] = {}

    @staticmethod
    def _matches_value(value, condition: VectorMatch) -> bool:
        if isinstance(value, tuple):
            return any(expected in value for expected in condition.values)
        return value in condition.values

    @classmethod
    def _matches_filter(cls, point: VectorIndexPoint, filters: VectorSearchFilter | None) -> bool:
        if filters is None:
            return True
        for condition in filters.matches:
            if not cls._matches_value(point.metadata.get(condition.field), condition):
                return False
        for condition in filters.excludes:
            if cls._matches_value(point.metadata.get(condition.field), condition):
                return False
        for condition in filters.ranges:
            value = point.metadata.get(condition.field)
            if value is None or isinstance(value, tuple) or isinstance(value, str):
                return False
            numeric = float(value)
            if condition.gt is not None and not numeric > condition.gt:
                return False
            if condition.gte is not None and not numeric >= condition.gte:
                return False
            if condition.lt is not None and not numeric < condition.lt:
                return False
            if condition.lte is not None and not numeric <= condition.lte:
                return False
        return True

    @staticmethod
    def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
        if len(left) != len(right):
            raise ValueError("Vector dimension mismatch")
        numerator = sum(float(a) * float(b) for a, b in zip(left, right))
        left_norm = math.sqrt(sum(float(value) ** 2 for value in left))
        right_norm = math.sqrt(sum(float(value) ** 2 for value in right))
        if left_norm == 0 or right_norm == 0:
            raise ValueError("Zero vector is invalid for cosine search")
        return numerator / (left_norm * right_norm)

    def upsert(self, space: EmbeddingSpaceSpec, points: Sequence[VectorIndexPoint]) -> int:
        bucket = self._points_by_space.setdefault(space.space_id, {})
        self._dimensions[space.space_id] = space.dimension
        for point in points:
            if len(point.vector) != space.dimension:
                raise ValueError("Vector dimension does not match Embedding Space")
            bucket[point.point_id] = point
        return len(points)

    def search(
        self,
        space: EmbeddingSpaceSpec,
        query_vector: Sequence[float],
        *,
        limit: int,
        filters: VectorSearchFilter | None = None,
    ) -> tuple[VectorSearchHit, ...]:
        if not 1 <= limit <= 1000:
            raise ValueError("Vector search limit must be between 1 and 1000")
        if len(query_vector) != space.dimension:
            raise ValueError("Query vector dimension does not match Embedding Space")
        bucket = self._points_by_space.get(space.space_id)
        if bucket is None:
            raise RuntimeError("Vector Index for this Embedding Space is unavailable")
        scored = []
        for point in bucket.values():
            if not self._matches_filter(point, filters):
                continue
            scored.append(
                (point.point_id, self._cosine(query_vector, point.vector), point.metadata)
            )
        scored.sort(key=lambda item: (-item[1], item[0]))
        return tuple(
            VectorSearchHit(point_id=point_id, score=score, rank=rank, metadata=metadata)
            for rank, (point_id, score, metadata) in enumerate(scored[:limit], start=1)
        )

    def delete(self, space: EmbeddingSpaceSpec, point_ids: Sequence[str]) -> int:
        bucket = self._points_by_space.get(space.space_id, {})
        removed = 0
        for point_id in point_ids:
            removed += int(bucket.pop(point_id, None) is not None)
        return removed

    def rebuild(
        self, space: EmbeddingSpaceSpec, points: Sequence[VectorIndexPoint]
    ) -> VectorIndexMetadata:
        started = time.perf_counter()
        self._points_by_space[space.space_id] = {}
        self.upsert(space, points)
        elapsed = time.perf_counter() - started
        return VectorIndexMetadata(
            backend_key=self.backend_key,
            backend_version="1",
            space_id=space.space_id,
            dimension=space.dimension,
            distance="cosine",
            points_count=len(points),
            indexed_points_count=len(points),
            approximate=False,
            status="ready",
            configuration={"build_seconds": elapsed, "storage": "memory"},
        )

    def metadata(self, space: EmbeddingSpaceSpec) -> VectorIndexMetadata:
        bucket = self._points_by_space.get(space.space_id)
        if bucket is None:
            raise RuntimeError("Vector Index for this Embedding Space is unavailable")
        return VectorIndexMetadata(
            backend_key=self.backend_key,
            backend_version="1",
            space_id=space.space_id,
            dimension=space.dimension,
            distance="cosine",
            points_count=len(bucket),
            indexed_points_count=len(bucket),
            approximate=False,
            status="ready",
            configuration={"storage": "memory"},
        )

    def drop(self, space: EmbeddingSpaceSpec) -> None:
        self._points_by_space.pop(space.space_id, None)
        self._dimensions.pop(space.space_id, None)
