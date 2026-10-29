"""Raw-bearing Object Evidence Package v2 manifest contract."""

from __future__ import annotations

import copy
import hashlib
import json
from importlib import resources
from pathlib import PurePosixPath
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker

from .package_manifest import (
    MANIFEST_CANONICALIZATION,
    calculate_manifest_sha256,
    canonical_manifest_bytes,
)

PACKAGE_SCHEMA_VERSION_V2 = "sgokb.object-evidence-package/2.0"
PACKAGE_SCHEMA_ID_V2 = "urn:sgokb:schema:object-evidence-package:2.0"
GROUNDING_CONTRACT = "sgokb.raw-grounding/1.0"
RESOLUTION_CONTRACT = "sgokb.evidence-to-raw/1.0"


def _schema_path():
    return resources.files("sgokb.exchange.schemas").joinpath(
        "object-evidence-package-v2.schema.json"
    )


def load_package_manifest_schema_v2() -> dict[str, Any]:
    with _schema_path().open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    if schema.get("$id") != PACKAGE_SCHEMA_ID_V2:
        raise RuntimeError("Package v2 manifest schema ID does not match code contract")
    Draft202012Validator.check_schema(schema)
    return schema


def grounding_set_projection(raw_grounding: Mapping[str, Any]) -> dict[str, Any]:
    artifacts = [
        {
            key: item.get(key)
            for key in (
                "raw_artifact_id",
                "source_id",
                "snapshot_id",
                "package_path",
                "logical_path",
                "media_type",
                "charset",
                "byte_size",
                "sha256",
            )
        }
        for item in raw_grounding.get("artifacts", [])
    ]
    bindings = [
        {
            key: item.get(key)
            for key in (
                "evidence_id",
                "source_id",
                "snapshot_id",
                "normalization_run_id",
                "raw_artifact_ids",
            )
        }
        for item in raw_grounding.get("evidence_bindings", [])
    ]
    return {
        "resolution_contract": raw_grounding.get("resolution_contract"),
        "artifacts": artifacts,
        "evidence_bindings": bindings,
    }


def calculate_grounding_set_sha256(raw_grounding: Mapping[str, Any]) -> str:
    raw = json.dumps(
        grounding_set_projection(raw_grounding),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def with_grounding_set_sha256(raw_grounding: Mapping[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(dict(raw_grounding))
    integrity = result.setdefault("integrity", {})
    integrity.update(
        {
            "hash_algorithm": "sha256",
            "canonicalization": MANIFEST_CANONICALIZATION,
            "grounding_set_sha256": calculate_grounding_set_sha256(result),
        }
    )
    return result


def with_manifest_sha256_v2(manifest: Mapping[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(dict(manifest))
    result.setdefault("integrity", {})["manifest_sha256"] = calculate_manifest_sha256(result)
    return result


def _safe_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and all(part not in {"", ".", ".."} for part in path.parts)


def _semantic_issues(manifest: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    binding = manifest.get("binding") or {}
    artifacts = manifest.get("artifacts") or {}
    base = binding.get("base_version_id")
    current = artifacts.get("current_object_path")
    if base is None and current is not None:
        issues.append("initial Package must not include current_object_path")
    if base is not None and current != "current_object.json":
        issues.append("update Package must include current_object.json")

    evidence = manifest.get("evidence") or {}
    evidence_items = evidence.get("items") or []
    evidence_ids = [item.get("evidence_id") for item in evidence_items]
    if evidence_ids != list(evidence.get("included_evidence_ids") or []):
        issues.append("included_evidence_ids must exactly match evidence.items order")
    sources = [item.get("source_id") for item in evidence_items]
    if list(dict.fromkeys(sources)) != list(evidence.get("included_source_ids") or []):
        issues.append("included_source_ids must match first-seen Evidence Source order")

    raw = manifest.get("raw_grounding") or {}
    raw_items = raw.get("artifacts") or []
    raw_ids = [item.get("raw_artifact_id") for item in raw_items]
    if raw_ids != sorted(raw_ids):
        issues.append("raw_grounding.artifacts must be ordered by raw_artifact_id")
    if raw_ids != list(raw.get("included_raw_artifact_ids") or []):
        issues.append("included_raw_artifact_ids must exactly match Raw artifact order")
    if len(raw_ids) != len(set(raw_ids)):
        issues.append("Raw Artifact membership must be unique by raw_artifact_id")

    expected_paths = {
        raw_id: f"raw/artifact_{index:04d}/payload"
        for index, raw_id in enumerate(raw_ids, 1)
    }
    for item in raw_items:
        raw_id = item.get("raw_artifact_id")
        if item.get("package_path") != expected_paths.get(raw_id):
            issues.append(f"non-deterministic Raw package path: {raw_id}")
        if not _safe_path(item.get("package_path")):
            issues.append(f"unsafe Raw package path: {item.get('package_path')!r}")

    raw_id_set = set(raw_ids)
    bindings = raw.get("evidence_bindings") or []
    binding_ids = [item.get("evidence_id") for item in bindings]
    if binding_ids != evidence_ids:
        issues.append("evidence_bindings must exactly match Evidence item order")
    referenced_raw: set[str] = set()
    evidence_by_id = {item.get("evidence_id"): item for item in evidence_items}
    for item in bindings:
        evidence_id = item.get("evidence_id")
        evidence_item = evidence_by_id.get(evidence_id) or {}
        for key in ("source_id", "snapshot_id", "normalization_run_id"):
            if item.get(key) != evidence_item.get(key):
                issues.append(f"Evidence-to-Raw binding lineage mismatch: {evidence_id}:{key}")
        ids = list(item.get("raw_artifact_ids") or [])
        if ids != sorted(ids) or len(ids) != len(set(ids)):
            issues.append(f"Raw covering set must be sorted/unique: {evidence_id}")
        if not ids:
            issues.append(f"Raw covering set is empty: {evidence_id}")
        unknown = set(ids) - raw_id_set
        if unknown:
            issues.append(f"Evidence binding references Raw outside Package: {evidence_id}")
        referenced_raw.update(ids)
    if referenced_raw != raw_id_set:
        issues.append("Raw artifacts must be referenced by at least one Evidence binding")

    expected_grounding_hash = (raw.get("integrity") or {}).get("grounding_set_sha256")
    if expected_grounding_hash != calculate_grounding_set_sha256(raw):
        issues.append("raw_grounding.integrity.grounding_set_sha256 mismatch")

    files = manifest.get("files") or []
    paths = [item.get("path") for item in files]
    if len(paths) != len(set(paths)):
        issues.append("files[].path must be unique")
    for path in paths:
        if not _safe_path(path):
            issues.append(f"unsafe Package-relative path: {path!r}")
    file_by_path = {item.get("path"): item for item in files}
    singleton = {
        "instructions.md": ("instructions", "text/markdown"),
        "schema/object-result-v2.schema.json": ("result_schema", "application/json"),
    }
    if base is not None:
        singleton["current_object.json"] = ("current_object", "application/json")
    for path, expected in singleton.items():
        item = file_by_path.get(path)
        if not item or (item.get("role"), item.get("media_type")) != expected:
            issues.append(f"required Package file role mismatch: {path}")
    if base is None and "current_object.json" in file_by_path:
        issues.append("initial Package must not contain current_object.json")

    for raw_item in raw_items:
        path = raw_item.get("package_path")
        file_item = file_by_path.get(path)
        if not file_item or file_item.get("role") != "raw_grounding":
            issues.append(f"Raw payload missing from files[]: {path}")
            continue
        if file_item.get("media_type") != (raw_item.get("media_type") or "application/octet-stream"):
            issues.append(f"Raw payload media type mismatch: {path}")
        if file_item.get("size_bytes") != raw_item.get("byte_size"):
            issues.append(f"Raw payload size mismatch: {path}")
        if file_item.get("sha256") != raw_item.get("sha256"):
            issues.append(f"Raw payload SHA-256 mismatch: {path}")

    materialization = manifest.get("materialization") or {}
    usage = materialization.get("usage") or {}
    budget = materialization.get("budget") or {}
    total = sum(int(item.get("byte_size") or 0) for item in raw_items)
    largest = max((int(item.get("byte_size") or 0) for item in raw_items), default=0)
    expected_usage = {
        "total_raw_bytes": total,
        "largest_raw_bytes": largest,
        "raw_artifact_count": len(raw_items),
        "selected_evidence_count": len(evidence_items),
        "source_count": len(set(sources)),
    }
    for key, expected in expected_usage.items():
        if usage.get(key) != expected:
            issues.append(f"materialization usage mismatch: {key}")
    if total > int(budget.get("max_total_raw_bytes") or 0):
        issues.append("Raw total exceeds materialization budget")
    if largest > int(budget.get("max_single_raw_bytes") or 0):
        issues.append("Raw item exceeds materialization budget")
    if len(raw_items) > int(budget.get("max_raw_artifacts") or 0):
        issues.append("Raw artifact count exceeds materialization budget")

    preflight = manifest.get("export_preflight") or {}
    if preflight.get("disposition") in {"review_required", "blocked"} and not (
        preflight.get("reasons") or []
    ):
        issues.append("review_required/blocked export_preflight requires reasons")

    expected_manifest_hash = (manifest.get("integrity") or {}).get("manifest_sha256")
    if isinstance(expected_manifest_hash, str) and expected_manifest_hash != calculate_manifest_sha256(
        manifest
    ):
        issues.append("integrity.manifest_sha256 mismatch")
    return issues


def validate_package_manifest_v2(manifest: Mapping[str, Any]) -> tuple[str, ...]:
    validator = Draft202012Validator(
        load_package_manifest_schema_v2(), format_checker=FormatChecker()
    )
    issues = [
        f"schema:{'/'.join(map(str, error.absolute_path)) or '$'}:{error.message}"
        for error in sorted(
            validator.iter_errors(manifest), key=lambda item: list(item.absolute_path)
        )
    ]
    issues.extend(f"contract:{message}" for message in _semantic_issues(manifest))
    return tuple(issues)


def canonical_manifest_bytes_v2(manifest: Mapping[str, Any]) -> bytes:
    return canonical_manifest_bytes(manifest)
