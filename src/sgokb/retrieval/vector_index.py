"""Qdrant implementation of the Phase I / I-03 VectorIndexAdapter contract."""

from __future__ import annotations

import math
import time
import uuid
from importlib import metadata
from typing import Iterable, Mapping, Sequence

from sgokb.domain.embedding import EmbeddingSpaceSpec
from sgokb.domain.vector_index import (
    VectorIndexMetadata,
    VectorIndexPoint,
    VectorMatch,
    VectorPayloadValue,
    VectorRange,
    VectorSearchFilter,
    VectorSearchHit,
)

_RESERVED_POINT_ID = "__sgokb_point_id"
_RESERVED_SPACE_ID = "__sgokb_space_id"
_POINT_NAMESPACE = uuid.UUID("999aa35a-7f34-4d16-a629-1aed8a4b5511")

DEFAULT_VECTOR_INDEX_BACKEND = "qdrant"
DEFAULT_QDRANT_HNSW_M = 16
DEFAULT_QDRANT_EF_CONSTRUCT = 128
DEFAULT_QDRANT_SEARCH_EF = 768
DEFAULT_QDRANT_FULL_SCAN_THRESHOLD = 10
DEFAULT_QDRANT_INDEXING_THRESHOLD = 1000

DEFAULT_QDRANT_FILTER_SCHEMA: Mapping[str, str] = {
    "membership_id": "keyword",
    "representation_id": "keyword",
    "kind": "keyword",
    "object_id": "keyword",
    "version_id": "keyword",
    "facet_id": "keyword",
    "facet": "keyword",
    "statement_id": "keyword",
    "evidence_id": "keyword",
    "source_id": "keyword",
    "snapshot_id": "keyword",
    "primary_class": "keyword",
    "additional_classes": "keyword",
    "ancestor_classes": "keyword",
    "object_status": "keyword",
    "derivation_kind": "keyword",
    "temporal_scope_id": "keyword",
    "valid_from_ordinal": "integer",
    "valid_to_ordinal": "integer",
    "is_current": "bool",
}


def _require_vector(vector: Sequence[float], dimension: int) -> list[float]:
    values = [float(value) for value in vector]
    if len(values) != dimension:
        raise ValueError("Vector dimension does not match Embedding Space")
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Vector contains a non-finite value")
    return values


def _payload_value(value: VectorPayloadValue):
    return list(value) if isinstance(value, tuple) else value


class QdrantVectorIndexAdapter:
    """Local/server Qdrant HNSW adapter; it never falls back to another backend."""

    backend_key = "qdrant"

    def __init__(
        self,
        *,
        url: str = "http://localhost:6333",
        grpc_port: int = 6334,
        prefer_grpc: bool = True,
        collection_prefix: str = "sgokb_vector",
        hnsw_m: int = DEFAULT_QDRANT_HNSW_M,
        ef_construct: int = DEFAULT_QDRANT_EF_CONSTRUCT,
        search_ef: int = DEFAULT_QDRANT_SEARCH_EF,
        full_scan_threshold: int = DEFAULT_QDRANT_FULL_SCAN_THRESHOLD,
        indexing_threshold: int = DEFAULT_QDRANT_INDEXING_THRESHOLD,
        filter_schema: Mapping[str, str] | None = None,
        client=None,
        wait_for_index: bool = True,
        index_wait_timeout_seconds: float = 120.0,
    ) -> None:
        try:
            from qdrant_client import QdrantClient
        except ImportError as exc:
            raise RuntimeError(
                "Qdrant Vector Index requires the vector-qdrant optional dependency"
            ) from exc

        if hnsw_m <= 0 or ef_construct <= 0 or search_ef <= 0:
            raise ValueError("Qdrant HNSW parameters must be positive")
        self.collection_prefix = collection_prefix
        self.hnsw_m = hnsw_m
        self.ef_construct = ef_construct
        self.search_ef = search_ef
        self.full_scan_threshold = full_scan_threshold
        self.indexing_threshold = indexing_threshold
        self.filter_schema = dict(
            DEFAULT_QDRANT_FILTER_SCHEMA if filter_schema is None else filter_schema
        )
        self.wait_for_index = wait_for_index
        self.index_wait_timeout_seconds = index_wait_timeout_seconds
        self._client = client or QdrantClient(
            url=url,
            grpc_port=grpc_port,
            prefer_grpc=prefer_grpc,
            timeout=max(30, int(index_wait_timeout_seconds)),
        )

    def _collection(self, space: EmbeddingSpaceSpec) -> str:
        return f"{self.collection_prefix}_{space.space_id[:24]}"

    @staticmethod
    def _backend_id(space: EmbeddingSpaceSpec, point_id: str) -> str:
        value = f"sgokb-vector:{space.space_id}:{point_id}"
        return str(uuid.uuid5(_POINT_NAMESPACE, value))

    def _server_version(self) -> str:
        try:
            value = self._client.info()
            return str(getattr(value, "version", None) or metadata.version("qdrant-client"))
        except Exception:
            return f"client-{metadata.version('qdrant-client')}"

    def _models(self):
        try:
            from qdrant_client import models
        except ImportError as exc:  # pragma: no cover - guarded in __init__
            raise RuntimeError("qdrant-client is unavailable") from exc
        return models

    def _ensure_collection(self, space: EmbeddingSpaceSpec, *, bulk_build: bool) -> None:
        name = self._collection(space)
        if self._client.collection_exists(name):
            info = self._client.get_collection(name)
            params = info.config.params.vectors
            size = getattr(params, "size", None)
            if size != space.dimension:
                raise ValueError(
                    "Existing Qdrant collection dimension does not match Embedding Space"
                )
            collection_metadata = dict(getattr(info.config, "metadata", None) or {})
            if collection_metadata.get("sgokb_space_id") != space.space_id:
                raise ValueError("Qdrant collection belongs to a different Embedding Space")
            return
        models = self._models()
        threshold = 0 if bulk_build else self.indexing_threshold
        self._client.create_collection(
            name,
            vectors_config=models.VectorParams(
                size=space.dimension,
                distance=models.Distance.COSINE,
            ),
            hnsw_config=models.HnswConfigDiff(
                m=self.hnsw_m,
                ef_construct=self.ef_construct,
                full_scan_threshold=self.full_scan_threshold,
                on_disk=False,
            ),
            optimizers_config=models.OptimizersConfigDiff(
                indexing_threshold=threshold,
                default_segment_number=2,
            ),
            metadata={"sgokb_space_id": space.space_id},
        )
        schema_types = {
            "keyword": models.PayloadSchemaType.KEYWORD,
            "integer": models.PayloadSchemaType.INTEGER,
            "bool": models.PayloadSchemaType.BOOL,
            "float": models.PayloadSchemaType.FLOAT,
            "datetime": models.PayloadSchemaType.DATETIME,
            "uuid": models.PayloadSchemaType.UUID,
        }
        for field_name, field_type in self.filter_schema.items():
            try:
                schema = schema_types[field_type]
            except KeyError as exc:
                raise ValueError(f"Unsupported Qdrant filter schema type: {field_type}") from exc
            self._client.create_payload_index(
                name,
                field_name=field_name,
                field_schema=schema,
                wait=True,
            )

    def _point_structs(
        self, space: EmbeddingSpaceSpec, points: Iterable[VectorIndexPoint]
    ) -> Iterable[object]:
        models = self._models()
        for point in points:
            payload = {
                _RESERVED_POINT_ID: point.point_id,
                _RESERVED_SPACE_ID: space.space_id,
                **{key: _payload_value(value) for key, value in point.metadata.items()},
            }
            yield models.PointStruct(
                id=self._backend_id(space, point.point_id),
                vector=_require_vector(point.vector, space.dimension),
                payload=payload,
            )

    def _compile_filter(self, filters: VectorSearchFilter | None):
        if filters is None or (not filters.matches and not filters.ranges):
            return None
        models = self._models()
        must = []
        must_not = []
        for condition in filters.matches:
            must.append(self._match_condition(condition, models))
        for condition in filters.excludes:
            must_not.append(self._match_condition(condition, models))
        for condition in filters.ranges:
            must.append(self._range_condition(condition, models))
        return models.Filter(must=must, must_not=must_not)

    @staticmethod
    def _match_condition(condition: VectorMatch, models):
        if len(condition.values) == 1:
            match = models.MatchValue(value=condition.values[0])
        else:
            match = models.MatchAny(any=list(condition.values))
        return models.FieldCondition(key=condition.field, match=match)

    @staticmethod
    def _range_condition(condition: VectorRange, models):
        return models.FieldCondition(
            key=condition.field,
            range=models.Range(
                gt=condition.gt,
                gte=condition.gte,
                lt=condition.lt,
                lte=condition.lte,
            ),
        )

    def _wait_until_indexed(self, space: EmbeddingSpaceSpec, expected: int) -> None:
        if not self.wait_for_index or expected == 0:
            return
        deadline = time.monotonic() + self.index_wait_timeout_seconds
        name = self._collection(space)
        while time.monotonic() < deadline:
            info = self._client.get_collection(name)
            points = int(info.points_count or 0)
            status_ready = "green" in str(info.status).lower()
            optimizer_ready = "ok" in str(info.optimizer_status).lower()
            if points >= expected and status_ready and optimizer_ready:
                return
            time.sleep(0.25)
        raise RuntimeError("Qdrant HNSW index did not become ready before timeout")

    def initialize_empty(self, space: EmbeddingSpaceSpec) -> VectorIndexMetadata:
        """Prepare the normal schema without uploading a dummy point or dropping data."""
        self._ensure_collection(space, bulk_build=False)
        result = self.metadata(space)
        if result.points_count != 0:
            raise RuntimeError("Empty namespace initialization requires zero points")
        return result

    def upsert(self, space: EmbeddingSpaceSpec, points: Sequence[VectorIndexPoint]) -> int:
        if not points:
            return 0
        self._ensure_collection(space, bulk_build=False)
        self._client.upload_points(
            self._collection(space),
            points=self._point_structs(space, points),
            batch_size=256,
            parallel=1,
            wait=True,
        )
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
        name = self._collection(space)
        if not self._client.collection_exists(name):
            raise RuntimeError("Vector Index for this Embedding Space is unavailable")
        models = self._models()
        response = self._client.query_points(
            name,
            query=_require_vector(query_vector, space.dimension),
            query_filter=self._compile_filter(filters),
            search_params=models.SearchParams(hnsw_ef=self.search_ef, exact=False),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        hits = []
        for point in response.points:
            payload = dict(point.payload or {})
            if payload.get(_RESERVED_SPACE_ID) != space.space_id:
                raise RuntimeError("Qdrant point belongs to a different Embedding Space")
            point_id = str(payload.pop(_RESERVED_POINT_ID))
            payload.pop(_RESERVED_SPACE_ID, None)
            hits.append((point_id, float(point.score), payload))
        hits.sort(key=lambda item: (-item[1], item[0]))
        return tuple(
            VectorSearchHit(point_id=point_id, score=score, rank=rank, metadata=payload)
            for rank, (point_id, score, payload) in enumerate(hits[:limit], start=1)
        )

    def delete(self, space: EmbeddingSpaceSpec, point_ids: Sequence[str]) -> int:
        if not point_ids or not self._client.collection_exists(self._collection(space)):
            return 0
        models = self._models()
        self._client.delete(
            self._collection(space),
            points_selector=models.PointIdsList(
                points=[self._backend_id(space, point_id) for point_id in point_ids]
            ),
            wait=True,
        )
        return len(point_ids)

    def rebuild(
        self, space: EmbeddingSpaceSpec, points: Sequence[VectorIndexPoint]
    ) -> VectorIndexMetadata:
        self.drop(space)
        self._ensure_collection(space, bulk_build=True)
        if points:
            self._client.upload_points(
                self._collection(space),
                points=self._point_structs(space, points),
                batch_size=256,
                parallel=1,
                wait=True,
            )
        models = self._models()
        self._client.update_collection(
            self._collection(space),
            optimizers_config=models.OptimizersConfigDiff(
                indexing_threshold=self.indexing_threshold
            ),
        )
        self._wait_until_indexed(space, len(points))
        return self.metadata(space)

    def metadata(self, space: EmbeddingSpaceSpec) -> VectorIndexMetadata:
        name = self._collection(space)
        if not self._client.collection_exists(name):
            raise RuntimeError("Vector Index for this Embedding Space is unavailable")
        info = self._client.get_collection(name)
        return VectorIndexMetadata(
            backend_key=self.backend_key,
            backend_version=self._server_version(),
            space_id=space.space_id,
            dimension=space.dimension,
            distance="cosine",
            points_count=int(info.points_count or 0),
            indexed_points_count=(
                None if info.indexed_vectors_count is None else int(info.indexed_vectors_count)
            ),
            approximate=bool(info.indexed_vectors_count),
            status=str(info.status),
            configuration={
                "m": self.hnsw_m,
                "ef_construct": self.ef_construct,
                "search_ef": self.search_ef,
                "full_scan_threshold": self.full_scan_threshold,
                "indexing_threshold": self.indexing_threshold,
                "filter_schema": dict(self.filter_schema),
            },
        )

    def drop(self, space: EmbeddingSpaceSpec) -> None:
        name = self._collection(space)
        if self._client.collection_exists(name):
            self._client.delete_collection(name)
