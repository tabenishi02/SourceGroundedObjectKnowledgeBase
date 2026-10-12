"""Persistence-independent contracts for versioned semantic Object knowledge."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FacetStatus(str, Enum):
    CONTENT = "content"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NOT_APPLICABLE = "not_applicable"
    NOT_ANALYZED = "not_analyzed"


class DerivationKind(str, Enum):
    DIRECT_STATEMENT = "direct_statement"
    SYNTHESIS = "synthesis"
    INTERPRETATION = "interpretation"
    REPORTED_VIEW = "reported_view"


class AttributeValueType(str, Enum):
    TEXT = "text"
    INTEGER = "integer"
    REAL = "real"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    IDENTIFIER = "identifier"
    ENUM = "enum"
    JSON = "json"


class AttributeStatus(str, Enum):
    KNOWN = "known"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NOT_APPLICABLE = "not_applicable"
    NOT_ANALYZED = "not_analyzed"


class SearchRepresentationKind(str, Enum):
    OBJECT = "object"
    FACET = "facet"
    STATEMENT = "statement"


@dataclass(frozen=True, slots=True)
class FacetDefinitionRecord:
    facet_id: str
    key: str
    name: str
    description: str
    is_common: bool
    status: str


@dataclass(frozen=True, slots=True)
class TemporalScopeRecord:
    scope_id: str
    version_id: str
    as_of: str | None
    valid_from: str | None
    valid_to: str | None
    context_object_id: str | None
    label: str | None


@dataclass(frozen=True, slots=True)
class KnowledgeStatementRecord:
    statement_id: str
    version_id: str
    facet_id: str | None
    local_key: str
    text: str
    derivation_kind: DerivationKind
    language: str | None
    temporal_scope_id: str | None


@dataclass(frozen=True, slots=True)
class AttributeDefinitionRecord:
    attribute_id: str
    key: str
    name: str
    description: str
    value_type: AttributeValueType
    status: str


@dataclass(frozen=True, slots=True)
class SearchRepresentationRecord:
    representation_id: str
    kind: SearchRepresentationKind
    builder_key: str
    builder_version: str
    content: str
    content_hash: str
