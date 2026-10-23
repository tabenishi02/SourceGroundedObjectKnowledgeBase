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
    # Canonical active Object-level channel after R2. Keep SEMANTIC_OBJECT as the
    # source-compatible Python member while also exposing the explicit R2 name.
    SEMANTIC_OBJECT = "semantic_object_overview"
    SEMANTIC_OBJECT_OVERVIEW = "semantic_object_overview"
    # Explicit legacy value for pre-cutover/v1 diagnostics and rollback compatibility.
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
class ObjectSimilarityEvidence:
    """One bounded raw-cosine component contributing to hierarchical similarity."""

    component: str
    source_representation_id: str
    source_membership_id: str
    candidate_representation_id: str
    candidate_membership_id: str
    representation_kind: str
    facet: str | None
    source_statement_id: str | None
    candidate_statement_id: str | None
    score: float
    score_type: str
    contribution: float


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
    evidence: tuple[ObjectSimilarityEvidence, ...] = ()


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
    source_membership_id: str | None = None
    generation_id: str | None = None
