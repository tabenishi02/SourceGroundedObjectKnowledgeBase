"""Persistence-independent contracts for Object Knowledge Version lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class VersionState(str, Enum):
    """Lifecycle of a persisted Object Knowledge Version candidate."""

    CANDIDATE = "candidate"
    ACCEPTED = "accepted"
    ABANDONED = "abandoned"


class DerivedState(str, Enum):
    """Synchronization state of rebuildable artifacts for one Object."""

    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"
    STALE = "stale"


class StaleVersionError(ValueError):
    """Raised when a candidate/result base no longer matches current Knowledge."""


@dataclass(frozen=True, slots=True)
class VersionClassificationSnapshot:
    primary_class_id: str
    additional_class_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ObjectVersionRecord:
    version_id: str
    object_id: str
    version_number: int
    base_version_id: str | None
    state: VersionState
    snapshot_kind: str
    created_at: str
    accepted_at: str | None
    abandoned_at: str | None
    classification: VersionClassificationSnapshot


@dataclass(frozen=True, slots=True)
class DerivedStateRecord:
    object_id: str
    kind: str
    target_version_id: str
    status: DerivedState
    revision: int
    last_error: str | None
    updated_at: str
