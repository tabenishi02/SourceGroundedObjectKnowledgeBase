"""Transport-neutral operator request/outcome/error contracts.

These types are shared by CLI and future GUI presentation adapters.  They do
not depend on argparse, Qt, stdout/stderr, or CLI exit-code constants.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import httpx

from .application_admin import ObjectSelectorError
from .application_maintenance import (
    DerivedMaintenanceError,
    DerivedMaintenanceRuntimeUnavailableError,
)
from .application_read import KnowledgeRequestError, RetrievalRuntimeUnavailableError

CATEGORY_INTERNAL = "internal"
CATEGORY_INPUT = "input"
CATEGORY_NOT_FOUND = "not_found"
CATEGORY_BLOCKED = "blocked"
CATEGORY_RUNTIME = "runtime"
CATEGORY_IO = "io"
CATEGORY_INTEGRITY = "integrity"

OUTCOME_SUCCESS = "success"
OUTCOME_BLOCKED = "blocked"
OUTCOME_PARTIAL = "partial"


@dataclass(frozen=True, slots=True)
class OperationRequest:
    operation_id: str
    arguments: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class OperationOutcome:
    operation_id: str
    data: object
    warnings: tuple[str, ...] = ()
    state: str = OUTCOME_SUCCESS

    def __post_init__(self) -> None:
        if self.state not in {OUTCOME_SUCCESS, OUTCOME_BLOCKED, OUTCOME_PARTIAL}:
            raise ValueError(f"Unsupported operation outcome state: {self.state}")


class OperationFailure(Exception):
    """Transport-neutral normalized operation failure."""

    def __init__(
        self,
        operation_id: str,
        category: str,
        code: str,
        message: str,
        details: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.operation_id = operation_id
        self.category = category
        self.code = code
        self.message = message
        self.details = dict(details or {})


def normalize_operation_error(operation_id: str, exc: Exception) -> OperationFailure:
    """Map implementation exceptions to stable transport-neutral semantics.

    This preserves the semantic content of the former CLI ``_error_exit``
    mapper while leaving presentation-specific exit codes outside the
    Application layer.
    """

    if isinstance(exc, OperationFailure):
        return exc
    if isinstance(exc, DerivedMaintenanceRuntimeUnavailableError):
        return OperationFailure(
            operation_id, CATEGORY_RUNTIME, "derived_runtime_unavailable", str(exc)
        )
    if isinstance(exc, DerivedMaintenanceError):
        message = str(exc).lower()
        if "unknown" in message or "not found" in message:
            return OperationFailure(operation_id, CATEGORY_NOT_FOUND, "not_found", str(exc))
        return OperationFailure(
            operation_id, CATEGORY_BLOCKED, "precondition_failed", str(exc)
        )
    if isinstance(exc, ObjectSelectorError):
        return OperationFailure(
            operation_id,
            CATEGORY_NOT_FOUND,
            getattr(exc, "code", "object_selector_error"),
            str(exc),
        )
    if isinstance(exc, RetrievalRuntimeUnavailableError):
        return OperationFailure(
            operation_id,
            CATEGORY_RUNTIME,
            getattr(exc, "code", "retrieval_runtime_unavailable"),
            str(exc),
        )
    if isinstance(exc, KnowledgeRequestError):
        message = str(exc).lower()
        category = (
            CATEGORY_NOT_FOUND
            if "not found" in message or "unknown" in message
            else CATEGORY_INPUT
        )
        return OperationFailure(
            operation_id,
            category,
            getattr(exc, "code", "invalid_knowledge_request"),
            str(exc),
        )
    if isinstance(exc, PermissionError):
        return OperationFailure(operation_id, CATEGORY_BLOCKED, "operation_blocked", str(exc))
    if isinstance(exc, FileNotFoundError):
        return OperationFailure(operation_id, CATEGORY_IO, "file_not_found", str(exc))
    if isinstance(exc, (OSError, httpx.HTTPError)):
        return OperationFailure(operation_id, CATEGORY_IO, "io_or_provider_error", str(exc))
    if isinstance(exc, sqlite3.IntegrityError):
        return OperationFailure(operation_id, CATEGORY_INTEGRITY, "integrity_error", str(exc))
    if isinstance(exc, (ValueError, KeyError, json.JSONDecodeError)):
        text = str(exc).lower()
        if any(word in text for word in ("not found", "unknown ", "ambiguous")):
            return OperationFailure(operation_id, CATEGORY_NOT_FOUND, "not_found", str(exc))
        if any(
            word in text
            for word in ("requires explicit", "blocked", "review acknowledgement")
        ):
            return OperationFailure(
                operation_id, CATEGORY_BLOCKED, "precondition_failed", str(exc)
            )
        return OperationFailure(operation_id, CATEGORY_INPUT, "invalid_input", str(exc))
    return OperationFailure(operation_id, CATEGORY_INTERNAL, "internal_error", str(exc))


def path_value(value: object) -> Path:
    """Coerce an operation argument to ``Path`` without transport coupling."""

    return value if isinstance(value, Path) else Path(str(value))
