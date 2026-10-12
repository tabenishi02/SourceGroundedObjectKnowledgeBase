"""Persistence-independent contracts for canonical SGOKB Object identity."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


class AssignmentPolicy(str, Enum):
    """How a Class Registry entry may be assigned to Objects."""

    STRUCTURAL = "structural"
    PRIMARY_ELIGIBLE = "primary_eligible"
    ADDITIONAL_ONLY = "additional_only"


class LifecycleStatus(str, Enum):
    """Registry lifecycle shared by Objects and registry vocabulary."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class ClassProposalStatus(str, Enum):
    """Review state for a proposed Class Registry addition."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


def new_persistent_id() -> str:
    """Return an SGOKB-owned persistent runtime ID.

    Canonical Object/runtime records use locally generated UUIDv4 strings. Registry
    seed IDs are fixed textual IDs supplied by migrations instead of being generated.
    """

    return str(uuid4())


@dataclass(frozen=True, slots=True)
class ObjectClassRecord:
    class_id: str
    key: str
    name: str
    description: str
    assignment_policy: AssignmentPolicy
    status: LifecycleStatus
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class ObjectAliasRecord:
    alias_id: str
    value: str
    language: str | None
    kind: str


@dataclass(frozen=True, slots=True)
class ObjectRecord:
    object_id: str
    name: str
    primary_class_id: str
    status: LifecycleStatus
    current_version_id: str | None
    created_at: str
    updated_at: str
    aliases: tuple[ObjectAliasRecord, ...] = ()
    additional_class_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ObjectVersionRef:
    version_id: str
    object_id: str
    version_number: int
    created_at: str


@dataclass(frozen=True, slots=True)
class RelationTypeRecord:
    relation_type_id: str
    key: str
    name: str
    description: str
    status: LifecycleStatus
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class ObjectRelationRecord:
    relation_id: str
    version_id: str
    subject_object_id: str
    relation_type_id: str
    object_object_id: str
    created_at: str
