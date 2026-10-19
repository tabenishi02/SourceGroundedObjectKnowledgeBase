"""Object Evidence Package manifest contract (Phase G / G-02)."""

from __future__ import annotations

import copy
import hashlib
import json
import uuid
from importlib import resources
from pathlib import PurePosixPath
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker

PACKAGE_SCHEMA_VERSION = "sgokb.object-evidence-package/1.0"
PACKAGE_SCHEMA_ID = "urn:sgokb:schema:object-evidence-package:1.0"
MANIFEST_CANONICALIZATION = "sgokb-json-c14n-v1"


def _schema_path():
    return resources.files("sgokb.exchange.schemas").joinpath(
        "object-evidence-package-v1.schema.json"
    )


def load_package_manifest_schema() -> dict[str, Any]:
    """Load and verify the canonical G-02 manifest schema."""

    with _schema_path().open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    if schema.get("$id") != PACKAGE_SCHEMA_ID:
        raise RuntimeError("Package manifest schema ID does not match code contract")
    Draft202012Validator.check_schema(schema)
    return schema


def new_package_id() -> str:
    """Return a Package identity independent from paths and Object identity."""

    return f"pkg_{uuid.uuid4()}"


def _manifest_hash_projection(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Return the exact projection hashed by `manifest_sha256`.

    The hash field itself is removed to avoid recursive self-hashing. All remaining
    manifest content, including per-file hashes, is covered by the digest.
    """

    projected = copy.deepcopy(dict(manifest))
    integrity = projected.get("integrity")
    if isinstance(integrity, dict):
        integrity.pop("manifest_sha256", None)
    return projected


def canonical_manifest_bytes(manifest: Mapping[str, Any]) -> bytes:
    """Serialize the manifest using the SGOKB v1 deterministic JSON profile."""

    projection = _manifest_hash_projection(manifest)
    return json.dumps(
        projection,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def calculate_manifest_sha256(manifest: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_manifest_bytes(manifest)).hexdigest()


def with_manifest_sha256(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy with the canonical manifest digest filled in."""

    result = copy.deepcopy(dict(manifest))
    integrity = result.setdefault("integrity", {})
    integrity["manifest_sha256"] = calculate_manifest_sha256(result)
    return result


def _path_is_safe(path: str) -> bool:
    if not path or "\\" in path:
        return False
    parsed = PurePosixPath(path)
    if parsed.is_absolute():
        return False
    return all(part not in {"", ".", ".."} for part in parsed.parts)


def _semantic_issues(manifest: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []

    binding = manifest.get("binding", {})
    artifacts = manifest.get("artifacts", {})
    base_version_id = binding.get("base_version_id")
    current_path = artifacts.get("current_object_path")
    if base_version_id is None and current_path is not None:
        issues.append("initial Package must not include current_object_path")
    if base_version_id is not None and current_path != "current_object.json":
        issues.append("update Package must include current_object.json")

    files = manifest.get("files", [])
    file_paths = [item.get("path") for item in files if isinstance(item, Mapping)]
    if len(file_paths) != len(set(file_paths)):
        issues.append("files[].path must be unique")
    for path in file_paths:
        if not isinstance(path, str) or not _path_is_safe(path):
            issues.append(f"unsafe Package-relative path: {path!r}")

    by_role: dict[str, list[Mapping[str, Any]]] = {}
    for item in files:
        if isinstance(item, Mapping):
            by_role.setdefault(str(item.get("role")), []).append(item)

    expected_singletons = {
        "instructions": "instructions.md",
        "result_schema": "schema/object-result-v1.schema.json",
    }
    if base_version_id is not None:
        expected_singletons["current_object"] = "current_object.json"
    for role, expected_path in expected_singletons.items():
        matches = by_role.get(role, [])
        if len(matches) != 1 or matches[0].get("path") != expected_path:
            issues.append(f"files must contain exactly one {role} at {expected_path}")
    if base_version_id is None and by_role.get("current_object"):
        issues.append("initial Package files must not contain current_object")

    evidence = manifest.get("evidence", {})
    items = evidence.get("items", []) if isinstance(evidence, Mapping) else []
    item_ids = [item.get("evidence_id") for item in items if isinstance(item, Mapping)]
    included_ids = (
        evidence.get("included_evidence_ids", []) if isinstance(evidence, Mapping) else []
    )
    if item_ids != included_ids:
        issues.append("included_evidence_ids must exactly match evidence.items order")

    item_sources = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        item_sources.append(item.get("source_id"))
        package_roles = set(item.get("package_roles") or ())
        if package_roles.intersection({"carry_forward", "manual_include"}):
            if item.get("selected_by") != "protected":
                issues.append(
                    f"protected Package role requires selected_by=protected: "
                    f"{item.get('evidence_id')}"
                )
    included_sources = (
        evidence.get("included_source_ids", []) if isinstance(evidence, Mapping) else []
    )
    first_seen_sources = list(dict.fromkeys(item_sources))
    if first_seen_sources != included_sources:
        issues.append("included_source_ids must match first-seen evidence.items source order")

    generations = evidence.get("source_generations", []) if isinstance(evidence, Mapping) else []
    generation_membership: dict[str, tuple[str, str, str, str]] = {}
    for generation in generations:
        if not isinstance(generation, Mapping):
            continue
        key = (
            generation.get("source_id"),
            generation.get("snapshot_id"),
            generation.get("normalization_run_id"),
            generation.get("file_path"),
        )
        for evidence_id in generation.get("evidence_ids") or ():
            if evidence_id in generation_membership:
                issues.append(f"Evidence appears in multiple source_generations: {evidence_id}")
            generation_membership[evidence_id] = key

    evidence_file_paths = {
        item.get("path")
        for item in by_role.get("evidence", [])
        if isinstance(item.get("path"), str)
    }
    generation_file_paths = [
        generation.get("file_path") for generation in generations if isinstance(generation, Mapping)
    ]
    if len(generation_file_paths) != len(set(generation_file_paths)):
        issues.append("source_generations must use one distinct file per Source generation")
    if evidence_file_paths != set(generation_file_paths):
        issues.append("Evidence files[] must exactly match source_generations file paths")

    included_id_set = set(item_ids)
    for item in items:
        if not isinstance(item, Mapping):
            continue
        evidence_id = item.get("evidence_id")
        key = (
            item.get("source_id"),
            item.get("snapshot_id"),
            item.get("normalization_run_id"),
            item.get("file_path"),
        )
        if generation_membership.get(evidence_id) != key:
            issues.append(f"source_generation mapping mismatch for Evidence: {evidence_id}")
        if item.get("file_path") not in evidence_file_paths:
            issues.append(f"Evidence file missing from files[]: {item.get('file_path')}")
        related = item.get("related_selected_evidence_ids") or ()
        if evidence_id in related:
            issues.append(f"Evidence cannot relate to itself: {evidence_id}")
        unknown_related = set(related) - included_id_set
        if unknown_related:
            issues.append(f"related Evidence is outside Package membership: {evidence_id}")

    if set(generation_membership) != included_id_set:
        issues.append("source_generations Evidence membership must equal evidence.items")

    expected_media_types = {
        "instructions": "text/markdown",
        "current_object": "application/json",
        "result_schema": "application/json",
        "evidence": "text/markdown",
    }
    for item in files:
        if not isinstance(item, Mapping):
            continue
        role = item.get("role")
        expected_media_type = expected_media_types.get(role)
        if expected_media_type is not None and item.get("media_type") != expected_media_type:
            issues.append(f"invalid media_type for {role}: {item.get('path')}")

    selection = manifest.get("selection", {})
    if isinstance(selection, Mapping):
        selected_count = selection.get("selected_count")
        omitted_count = selection.get("omitted_count")
        candidate_count = selection.get("candidate_count")
        if selected_count != len(items):
            issues.append("selection.selected_count must equal Evidence item count")
        if (
            isinstance(candidate_count, int)
            and isinstance(selected_count, int)
            and isinstance(omitted_count, int)
            and candidate_count != selected_count + omitted_count
        ):
            issues.append("selection candidate_count must equal selected_count + omitted_count")
        usage = selection.get("usage", {})
        budget = selection.get("budget", {})
        if isinstance(usage, Mapping):
            if usage.get("items") != len(items):
                issues.append("selection.usage.items must equal Evidence item count")
            if usage.get("sources") != len(set(item_sources)):
                issues.append("selection.usage.sources must equal included Source count")
        if isinstance(usage, Mapping) and isinstance(budget, Mapping):
            if (
                isinstance(usage.get("estimated_tokens"), int)
                and isinstance(budget.get("max_estimated_tokens"), int)
                and usage["estimated_tokens"] > budget["max_estimated_tokens"]
            ):
                issues.append("selection token usage exceeds budget")
            if (
                isinstance(usage.get("bytes"), int)
                and isinstance(budget.get("max_bytes"), int)
                and usage["bytes"] > budget["max_bytes"]
            ):
                issues.append("selection byte usage exceeds budget")
            if (
                isinstance(usage.get("items"), int)
                and isinstance(budget.get("max_items"), int)
                and usage["items"] > budget["max_items"]
            ):
                issues.append("selection item usage exceeds budget")

    preflight = manifest.get("export_preflight", {})
    if isinstance(preflight, Mapping):
        disposition = preflight.get("disposition")
        reasons = preflight.get("reasons") or []
        if disposition in {"review_required", "blocked"} and not reasons:
            issues.append("review_required/blocked export_preflight requires reasons")

    integrity = manifest.get("integrity", {})
    if isinstance(integrity, Mapping):
        expected = integrity.get("manifest_sha256")
        if isinstance(expected, str) and expected != calculate_manifest_sha256(manifest):
            issues.append("integrity.manifest_sha256 mismatch")

    return issues


def validate_package_manifest(manifest: Mapping[str, Any]) -> tuple[str, ...]:
    """Return deterministic structural + cross-field validation issues."""

    validator = Draft202012Validator(load_package_manifest_schema(), format_checker=FormatChecker())
    issues = [
        f"schema:{'/'.join(map(str, error.absolute_path)) or '$'}:{error.message}"
        for error in sorted(
            validator.iter_errors(manifest), key=lambda item: list(item.absolute_path)
        )
    ]
    issues.extend(f"contract:{message}" for message in _semantic_issues(manifest))
    return tuple(issues)
