"""Backend-independent Vector Index contracts for Phase I / I-03."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol, Sequence, TypeAlias

from .embedding import EmbeddingSpaceSpec

VectorScalar: TypeAlias = str | int | bool
VectorPayloadValue: TypeAlias = VectorScalar | tuple[VectorScalar, ...] | None


@dataclass(frozen=True, slots=True)
class VectorIndexPoint:
    """One derived Search Representation vector plus rebuildable filter metadata."""

    point_id: str
    vector: tuple[float, ...]
    metadata: Mapping[str, VectorPayloadValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.point_id.strip():
            raise ValueError("Vector point ID must be non-empty")
        if not self.vector:
            raise ValueError("Vector point must contain at least one dimension")
        if any(key.startswith("__sgokb_") for key in self.metadata):
            raise ValueError("Vector metadata keys beginning with __sgokb_ are reserved")


@dataclass(frozen=True, slots=True)
class VectorMatch:
    """Hard equality/IN filter applied during candidate generation."""

    field: str
    values: tuple[VectorScalar, ...]

    def __post_init__(self) -> None:
        if not self.field.strip() or not self.values:
            raise ValueError("Vector match filter requires a field and at least one value")


@dataclass(frozen=True, slots=True)
class VectorRange:
    """Numeric hard range filter; all supplied bounds are conjunctive."""

    field: str
    gt: float | int | None = None
    gte: float | int | None = None
    lt: float | int | None = None
    lte: float | int | None = None

    def __post_init__(self) -> None:
        if not self.field.strip():
            raise ValueError("Vector range filter field must be non-empty")
        if all(value is None for value in (self.gt, self.gte, self.lt, self.lte)):
            raise ValueError("Vector range filter requires at least one bound")


@dataclass(frozen=True, slots=True)
class VectorSearchFilter:
    """Backend-neutral hard filter. Backends must not silently post-filter top-k."""

    matches: tuple[VectorMatch, ...] = ()
    excludes: tuple[VectorMatch, ...] = ()
    ranges: tuple[VectorRange, ...] = ()


@dataclass(frozen=True, slots=True)
class VectorSearchHit:
    point_id: str
    score: float
    rank: int
    metadata: Mapping[str, VectorPayloadValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VectorIndexMetadata:
    backend_key: str
    backend_version: str
    space_id: str
    dimension: int
    distance: str
    points_count: int
    indexed_points_count: int | None
    approximate: bool
    status: str
    configuration: Mapping[str, object] = field(default_factory=dict)


class VectorIndexAdapter(Protocol):
    """Replaceable derived Vector Index boundary used by Phase I retrieval."""

    backend_key: str

    def upsert(self, space: EmbeddingSpaceSpec, points: Sequence[VectorIndexPoint]) -> int: ...

    def search(
        self,
        space: EmbeddingSpaceSpec,
        query_vector: Sequence[float],
        *,
        limit: int,
        filters: VectorSearchFilter | None = None,
    ) -> tuple[VectorSearchHit, ...]: ...

    def delete(self, space: EmbeddingSpaceSpec, point_ids: Sequence[str]) -> int: ...

    def rebuild(
        self, space: EmbeddingSpaceSpec, points: Sequence[VectorIndexPoint]
    ) -> VectorIndexMetadata: ...

    def metadata(self, space: EmbeddingSpaceSpec) -> VectorIndexMetadata: ...

    def drop(self, space: EmbeddingSpaceSpec) -> None: ...
