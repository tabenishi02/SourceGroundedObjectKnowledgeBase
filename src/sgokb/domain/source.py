"""Persistence-independent contracts for canonical Source / Evidence provenance."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SourceStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class LocatorStatus(str, Enum):
    ACTIVE = "active"
    RETIRED = "retired"


class MetadataOrigin(str, Enum):
    CAPTURED = "captured"
    DETERMINISTIC = "deterministic"
    INFERRED = "inferred"
    OVERRIDE = "override"


class AssociationStatus(str, Enum):
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"
    EXCLUDED = "excluded"


class SnapshotCompleteness(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


class NormalizationStatus(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


class EvidenceExtractionMode(str, Enum):
    VERBATIM = "verbatim"
    NORMALIZED = "normalized"
    STRUCTURED = "structured"
    TRANSCRIBED = "transcribed"


class EvidenceRole(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CONTEXTUALIZES = "contextualizes"


class EvidenceTargetKind(str, Enum):
    STATEMENT = "statement"
    ATTRIBUTE = "attribute"
    RELATION = "relation"


@dataclass(frozen=True, slots=True)
class SourceRecord:
    source_id: str
    label: str | None
    status: SourceStatus
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class SourceLocatorRecord:
    locator_id: str
    source_id: str
    kind: str
    value: str
    is_preferred: bool
    status: LocatorStatus


@dataclass(frozen=True, slots=True)
class SourceSnapshotRecord:
    snapshot_id: str
    source_id: str
    observed_locator_id: str | None
    captured_at: str
    imported_at: str
    capture_method: str
    completeness: SnapshotCompleteness
    title: str | None


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    evidence_id: str
    run_id: str
    snapshot_id: str
    source_id: str
    ordinal: int
    content: str
    content_hash: str
    extraction_mode: EvidenceExtractionMode
    language: str | None


@dataclass(frozen=True, slots=True)
class EvidenceLinkRecord:
    link_id: str
    version_id: str
    target_kind: EvidenceTargetKind
    target_id: str
    evidence_id: str
    role: EvidenceRole
    origin_kind: str
    origin_ref: str | None


@dataclass(frozen=True, slots=True)
class EvidenceProvenance:
    evidence: EvidenceRecord
    snapshot: SourceSnapshotRecord
    source: SourceRecord
    raw_artifact_ids: tuple[str, ...]
