"""Versioned staging/preflight/export for Raw-bearing Package v2."""

from __future__ import annotations

import json
import os
import shutil
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .instructions_v2 import INSTRUCTIONS_VERSION_V2
from .object_result_v2 import load_object_result_schema_v2
from .package_manifest_v2 import (
    PACKAGE_SCHEMA_VERSION_V2,
    validate_package_manifest_v2,
    with_manifest_sha256_v2,
)
from .package_transfer import (
    PackageExportResult,
    PackageStageResult,
    _actual_relative_files,
    _credential_findings,
    _declared_paths,
    _json_bytes,
    _load_manifest,
    _safe_file,
    _sha256,
)


@dataclass(frozen=True, slots=True)
class RawPackagePreflight:
    package_id: str | None
    manifest_sha256: str | None
    grounding_set_sha256: str | None
    target_object_id: str | None
    target_name: str | None
    base_version_id: str | None
    schema_version: str | None
    evidence_count: int
    source_count: int
    raw_artifact_count: int
    total_raw_bytes: int
    file_count: int
    total_bytes: int
    destination: str | None
    manifest_disposition: str
    disposition: str
    reasons: tuple[str, ...]
    warnings: tuple[dict[str, Any], ...]
    credential_findings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _contract_findings(root: Path, manifest: Mapping[str, Any]) -> tuple[str, ...]:
    findings: list[str] = []
    try:
        path = str((manifest.get("artifacts") or {})["result_schema_path"])
        package_schema = json.loads(_safe_file(root, path).read_text(encoding="utf-8"))
        if package_schema != load_object_result_schema_v2():
            findings.append("result_schema_snapshot_does_not_match_canonical_schema")
    except (OSError, KeyError, ValueError, json.JSONDecodeError, UnicodeDecodeError):
        findings.append("result_schema_snapshot_is_unreadable")
    try:
        instructions = _safe_file(root, "instructions.md").read_text(encoding="utf-8")
        expected = f"Instructions version: `{INSTRUCTIONS_VERSION_V2}`"
        if expected not in instructions:
            findings.append("instructions_version_marker_mismatch")
    except (OSError, ValueError, UnicodeDecodeError):
        findings.append("instructions_are_unreadable")
    return tuple(findings)


def inspect_package_v2(
    package_dir: str | Path, destination: str | Path | None = None
) -> RawPackagePreflight:
    root = Path(package_dir).resolve()
    reasons: list[str] = []
    warnings: tuple[dict[str, Any], ...] = ()
    credentials: tuple[str, ...] = ()
    manifest: dict[str, Any] = {}
    manifest_disposition = "blocked"

    if not root.is_dir():
        reasons.append("package_directory_missing")
    else:
        try:
            manifest = _load_manifest(root)
        except (OSError, ValueError, json.JSONDecodeError, UnicodeDecodeError) as error:
            reasons.append(f"manifest_unreadable:{type(error).__name__}")

    if manifest:
        if manifest.get("schema_version") != PACKAGE_SCHEMA_VERSION_V2:
            reasons.append("package_schema_version_is_not_v2")
        else:
            reasons.extend(
                f"manifest_invalid:{issue}" for issue in validate_package_manifest_v2(manifest)
            )
        warnings = tuple(manifest.get("warnings") or ())
        manifest_disposition = str(
            (manifest.get("export_preflight") or {}).get("disposition", "blocked")
        )
        try:
            expected = _declared_paths(manifest) | {"manifest.json"}
            actual = _actual_relative_files(root)
            for missing in sorted(expected - actual):
                reasons.append(f"missing_file:{missing}")
            for unexpected in sorted(actual - expected):
                reasons.append(f"unexpected_file:{unexpected}")
        except ValueError as error:
            reasons.append(f"unsafe_package_layout:{error}")

        for item in manifest.get("files", []):
            try:
                relative = str(item["path"])
                raw = _safe_file(root, relative).read_bytes()
                if len(raw) != item["size_bytes"]:
                    reasons.append(f"size_mismatch:{relative}")
                if _sha256(raw) != item["sha256"]:
                    reasons.append(f"sha256_mismatch:{relative}")
            except (OSError, KeyError, TypeError, ValueError):
                continue

        if not reasons:
            reasons.extend(_contract_findings(root, manifest))
            credentials = _credential_findings(root, manifest)
            reasons.extend(f"credential_material_detected:{item}" for item in credentials)
        for warning in warnings:
            if warning.get("severity") == "blocking":
                reasons.append(f"blocking_warning:{warning.get('code', 'UNKNOWN')}")

    destination_text = None
    if destination is not None:
        destination_root = Path(destination).resolve()
        destination_text = str(destination_root)
        if root == destination_root or root in destination_root.parents:
            reasons.append("destination_must_not_be_inside_package")
        package_id = manifest.get("package_id") if manifest else None
        if package_id and (destination_root / str(package_id)).exists():
            existing = destination_root / str(package_id)
            try:
                existing_manifest = _load_manifest(existing)
                same = existing_manifest.get("integrity", {}).get(
                    "manifest_sha256"
                ) == manifest.get("integrity", {}).get("manifest_sha256")
                if not same:
                    reasons.append("destination_package_id_collision")
            except Exception:
                reasons.append("destination_package_is_unreadable")

    if reasons or manifest_disposition == "blocked":
        disposition = "blocked"
    elif manifest_disposition == "review_required" or any(
        warning.get("severity") == "review_required" for warning in warnings
    ):
        disposition = "review_required"
    else:
        disposition = "allow"
    if manifest and manifest_disposition in {"review_required", "blocked"}:
        reasons.extend(
            str(reason) for reason in (manifest.get("export_preflight") or {}).get("reasons", [])
        )

    try:
        total_bytes = sum(path.stat().st_size for path in root.rglob("*") if path.is_file())
    except OSError:
        total_bytes = 0
    raw = manifest.get("raw_grounding") or {}
    materialization = manifest.get("materialization") or {}
    usage = materialization.get("usage") or {}
    return RawPackagePreflight(
        package_id=str(manifest.get("package_id")) if manifest.get("package_id") else None,
        manifest_sha256=(manifest.get("integrity") or {}).get("manifest_sha256")
        if manifest
        else None,
        grounding_set_sha256=(raw.get("integrity") or {}).get("grounding_set_sha256")
        if manifest
        else None,
        target_object_id=(manifest.get("target") or {}).get("object_id") if manifest else None,
        target_name=(manifest.get("target") or {}).get("name") if manifest else None,
        base_version_id=(manifest.get("binding") or {}).get("base_version_id")
        if manifest
        else None,
        schema_version=manifest.get("schema_version") if manifest else None,
        evidence_count=len((manifest.get("evidence") or {}).get("included_evidence_ids", [])),
        source_count=len((manifest.get("evidence") or {}).get("included_source_ids", [])),
        raw_artifact_count=len(raw.get("included_raw_artifact_ids", [])),
        total_raw_bytes=int(usage.get("total_raw_bytes") or 0),
        file_count=len(_declared_paths(manifest)) + (1 if manifest else 0),
        total_bytes=total_bytes,
        destination=destination_text,
        manifest_disposition=manifest_disposition,
        disposition=disposition,
        reasons=tuple(dict.fromkeys(reasons)),
        warnings=warnings,
        credential_findings=credentials,
    )


class RawPackageTransferService:
    def stage_from_directory(
        self, source_dir: str | Path, staging_root: str | Path = "exchange/staging"
    ) -> PackageStageResult:
        source = Path(source_dir).resolve()
        if not source.is_dir():
            raise ValueError("Package build directory does not exist")
        manifest = with_manifest_sha256_v2(_load_manifest(source))
        issues = validate_package_manifest_v2(manifest)
        if issues:
            raise ValueError("Invalid Package v2 manifest: " + "; ".join(issues))
        expected = _declared_paths(manifest) | {"manifest.json"}
        actual = _actual_relative_files(source)
        if actual != expected:
            raise ValueError(
                "Package build directory scope mismatch: "
                f"missing={sorted(expected-actual)}, unexpected={sorted(actual-expected)}"
            )
        preflight = inspect_package_v2(source)
        if preflight.disposition == "blocked":
            raise ValueError("Package v2 failed integrity/security preflight: " + "; ".join(preflight.reasons))

        root = Path(staging_root).resolve()
        root.mkdir(parents=True, exist_ok=True)
        final = root / str(manifest["package_id"])
        if final.exists():
            existing = inspect_package_v2(final)
            if existing.manifest_sha256 == manifest["integrity"]["manifest_sha256"] and existing.disposition != "blocked":
                return PackageStageResult(
                    package_id=str(manifest["package_id"]),
                    manifest_sha256=str(manifest["integrity"]["manifest_sha256"]),
                    path=str(final),
                    already_staged=True,
                    preflight=existing,
                )
            raise ValueError("Staging destination already contains this Package ID")

        temporary = root / f".{manifest['package_id']}.staging-{uuid.uuid4().hex}"
        try:
            temporary.mkdir()
            for item in manifest["files"]:
                relative = str(item["path"])
                source_file = _safe_file(source, relative)
                target_file = _safe_file(temporary, relative)
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_file, target_file)
            (temporary / "manifest.json").write_bytes(_json_bytes(manifest))
            checked = inspect_package_v2(temporary)
            if checked.disposition == "blocked":
                raise ValueError("Staged Package v2 failed integrity/security checks")
            os.replace(temporary, final)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise
        return PackageStageResult(
            package_id=str(manifest["package_id"]),
            manifest_sha256=str(manifest["integrity"]["manifest_sha256"]),
            path=str(final),
            already_staged=False,
            preflight=inspect_package_v2(final),
        )

    def preflight(
        self, package_dir: str | Path, destination: str | Path | None = None
    ) -> RawPackagePreflight:
        return inspect_package_v2(package_dir, destination)

    def export(
        self,
        package_dir: str | Path,
        destination_root: str | Path,
        *,
        acknowledge_review: bool = False,
    ) -> PackageExportResult:
        source = Path(package_dir).resolve()
        destination = Path(destination_root).resolve()
        preflight = inspect_package_v2(source, destination)
        if preflight.disposition == "blocked":
            raise ValueError("Package export is blocked: " + "; ".join(preflight.reasons))
        if preflight.disposition == "review_required" and not acknowledge_review:
            raise ValueError("Package export requires explicit review acknowledgement")
        if preflight.package_id is None or preflight.manifest_sha256 is None:
            raise ValueError("Package identity is unavailable")
        destination.mkdir(parents=True, exist_ok=True)
        final = destination / preflight.package_id
        if final.exists():
            existing = inspect_package_v2(final)
            if existing.manifest_sha256 == preflight.manifest_sha256 and existing.disposition != "blocked":
                return PackageExportResult(
                    package_id=preflight.package_id,
                    manifest_sha256=preflight.manifest_sha256,
                    destination_root=str(destination),
                    path=str(final),
                    already_present=True,
                    acknowledged_review=acknowledge_review,
                    preflight=preflight,
                )
            raise ValueError("External destination already contains a conflicting Package ID")
        temporary = destination / f".{preflight.package_id}.exporting-{uuid.uuid4().hex}"
        try:
            shutil.copytree(source, temporary)
            copied = inspect_package_v2(temporary)
            if copied.disposition == "blocked" or copied.manifest_sha256 != preflight.manifest_sha256:
                raise ValueError("Copied Package v2 failed integrity verification")
            os.replace(temporary, final)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise
        final_check = inspect_package_v2(final)
        if final_check.disposition == "blocked" or final_check.manifest_sha256 != preflight.manifest_sha256:
            raise ValueError("Final exported Package v2 failed verification")
        return PackageExportResult(
            package_id=preflight.package_id,
            manifest_sha256=preflight.manifest_sha256,
            destination_root=str(destination),
            path=str(final),
            already_present=False,
            acknowledged_review=acknowledge_review,
            preflight=preflight,
        )
