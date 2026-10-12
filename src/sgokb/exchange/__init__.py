"""Structured exchange contracts for SGOKB Evidence Packages and Object Results."""

from .object_result import (
    OBJECT_RESULT_SCHEMA_ID,
    OBJECT_RESULT_SCHEMA_VERSION,
    ClassExtensionContract,
    ObjectResultContract,
    ObjectResultValidationError,
    ResultValidationIssue,
    build_object_result_schema,
    collect_evidence_ids,
    load_object_result_schema,
    validate_object_result,
)

__all__ = [
    "OBJECT_RESULT_SCHEMA_ID",
    "OBJECT_RESULT_SCHEMA_VERSION",
    "ClassExtensionContract",
    "ObjectResultContract",
    "ObjectResultValidationError",
    "ResultValidationIssue",
    "build_object_result_schema",
    "collect_evidence_ids",
    "load_object_result_schema",
    "validate_object_result",
]
