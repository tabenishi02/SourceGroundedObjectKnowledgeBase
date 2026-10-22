"""Backend-neutral object search contracts for Phase I / R2 Hybrid Search."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ObjectSearchMode(str, Enum):
    LEXICAL = "lexical"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class ObjectSearchChannel(str, Enum):
    EXACT_NAME = "exact_name"
    EXACT_ALIAS = "exact_alias"
    REGISTRY_LEXICAL = "registry_lexical"
    KNOWLEDGE_LEXICAL = "knowledge_lexical"
    # Keep the Python member name for source compatibility while exposing the
    # R2 active channel value. Normal R2 retrieval never emits the legacy value.
    SEMANTIC_OBJECT = "semantic_object_overview"
    SEMANTIC_OBJECT_OVERALL = "semantic_object_overall"
    SEMANTIC_FACET = "semantic_facet"
    SEMANTIC_STATEMENT = "semantic_statement"


@dataclass(frozen=True, slots=True)
class ObjectSearchFilters:
    """Hard filters. Unknown Class/Facet values are validation errors, never ignored."""

    primary_class: str | None = None
    additional_class: str | None = None
    ancestor_class: str | None = None
    facet: str | None = None
    version_id: str | None = None
    temporal_scope_id: str | None = None
    knowledge_valid_at: str | None = None
    derivation_kind: str | None = None
    include_archived: bool = False


@dataclass(frozen=True, slots=True)
class ObjectSearchMatch:
    channel: ObjectSearchChannel
    version_id: str | None
    representation_id: str | None
    membership_id: str | None
    representation_kind: str | None
    facet: str | None
    statement_id: str | None
    snippet: str
    score: float | None = None
    score_type: str | None = None
    source_rank: int | None = None


@dataclass(frozen=True, slots=True)
class ObjectSearchResult:
    object_id: str
    name: str
    primary_class: str
    version_id: str | None
    rank: int
    fused_score: float
    score_type: str
    exact_identity: str | None
    channels: tuple[ObjectSearchChannel, ...]
    matched_facets: tuple[str, ...]
    matches: tuple[ObjectSearchMatch, ...]


@dataclass(frozen=True, slots=True)
class ObjectSearchResponse:
    query: str
    mode: ObjectSearchMode
    results: tuple[ObjectSearchResult, ...]
    degraded_channels: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SimilarObjectResult:
    object_id: str
    name: str
    primary_class: str
    version_id: str
    rank: int
    score: float
    score_type: str
    matched_facet: str | None
    representation_id: str
    membership_id: str


@dataclass(frozen=True, slots=True)
class ObjectSimilarityResponse:
    source_object_id: str
    source_name: str
    source_primary_class: str
    source_version_id: str
    source_representation_id: str
    facet: str | None
    cross_class: bool
    results: tuple[SimilarObjectResult, ...]
