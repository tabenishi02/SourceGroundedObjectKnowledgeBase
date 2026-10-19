"""Atomic local staging and explicit filesystem export for Object Evidence Packages."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .instructions import INSTRUCTIONS_VERSION
from .object_result import load_object_result_schema
from .package_manifest import validate_package_manifest, with_manifest_sha256

_PRIVATE_KEY_PATTERN = re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")
_TOKEN_PATTERNS = (
    ("openai_api_key", re.compile(rb"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("github_token", re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("aws_access_key", re.compile(rb"\bAKIA[0-9A-Z]{16}\b")),
    ("google_api_key", re.compile(rb"\bAIza[0-9A-Za-z_-]{35}\b")),
)
_SENSITIVE_NAMES = {
    ".env",
    "credentials.json",
    "credentials.txt",
    "client_secret.json",
    "secrets.json",
    "id_rsa",
    "id_ed25519",
}


@dataclass(frozen=True, slots=True)
class PackagePreflight:
    package_id: str | None
    manifest_sha256: str | None
    target_object_id: str | None
    target_name: str | None
    base_version_id: str | None
    schema_version: str | None
    evidence_count: int
    source_count: int
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


@dataclass(frozen=True, slots=True)
class PackageStageResult:
    package_id: str
    manifest_sha256: str
    path: str
    already_staged: bool
    preflight: PackagePreflight

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["preflight"] = self.preflight.to_dict()
        return result


@dataclass(frozen=True, slots=True)
class PackageExportResult:
    package_id: str
    manifest_sha256: str
    destination_root: str
    path: str
    already_present: bool
    acknowledged_review: bool
    preflight: PackagePreflight

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["preflight"] = self.preflight.to_dict()
        return result


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _relative_path(value: str) -> Path:
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError(f"Unsafe Package-relative path: {value!r}")
    return Path(*pure.parts)


def _safe_file(root: Path, relative: str) -> Path:
    path = root.joinpath(_relative_path(relative))
    root_resolved = root.resolve()
    resolved = path.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise ValueError(f"Package path escapes root: {relative!r}")
    return path


def _load_manifest(package_dir: Path) -> dict[str, Any]:
    path = package_dir / "manifest.json"
    if path.is_symlink():
        raise ValueError("manifest.json must not be a symlink")
    return json.loads(path.read_text(encoding="utf-8"))


def _declared_paths(manifest: Mapping[str, Any]) -> set[str]:
    return {str(item["path"]) for item in manifest.get("files", [])}


def _actual_relative_files(root: Path) -> set[str]:
    files: set[str] = set()
    for item in root.rglob("*"):
        if item.is_symlink():
            raise ValueError(f"Package must not contain symlinks: {item.relative_to(root)}")
        if item.is_file():
            files.add(item.relative_to(root).as_posix())
    return files


def _credential_findings(root: Path, manifest: Mapping[str, Any]) -> tuple[str, ...]:
    findings: list[str] = []
    for item in manifest.get("files", []):
        relative = str(item["path"])
        path = _safe_file(root, relative)
        lower_name = path.name.lower()
        if lower_name in _SENSITIVE_NAMES or lower_name.endswith((".pem", ".p12", ".pfx", ".key")):
            findings.append(f"sensitive_filename:{relative}")
        raw = path.read_bytes()
        if _PRIVATE_KEY_PATTERN.search(raw):
            findings.append(f"private_key_material:{relative}")
        for label, pattern in _TOKEN_PATTERNS:
            if pattern.search(raw):
                findings.append(f"{label}:{relative}")
    return tuple(dict.fromkeys(findings))


def _package_contract_findings(root: Path, manifest: Mapping[str, Any]) -> tuple[str, ...]:
    findings: list[str] = []
    try:
        schema_path = _safe_file(root, "schema/object-result-v1.schema.json")
        package_schema = json.loads(schema_path.read_text(encoding="utf-8"))
        if package_schema != load_object_result_schema():
            findings.append("result_schema_snapshot_does_not_match_canonical_schema")
    except (OSError, ValueError, json.JSONDecodeError):
        findings.append("result_schema_snapshot_is_unreadable")

    try:
        instructions = _safe_file(root, "instructions.md").read_text(encoding="utf-8")
        expected = f"Instructions version: `{manifest['binding']['instructions_version']}`"
        if expected not in instructions:
            findings.append("instructions_version_marker_mismatch")
        if manifest["binding"]["instructions_version"] != INSTRUCTIONS_VERSION:
            findings.append("unsupported_instructions_version")
    except (OSError, KeyError, ValueError, UnicodeDecodeError):
        findings.append("instructions_are_unreadable")
    return tuple(findings)


def inspect_package(
    package_dir: str | Path, destination: str | Path | None = None
) -> PackagePreflight:
    """Verify a finalized Package and produce an export-oriented preflight summary."""

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
        schema_issues = validate_package_manifest(manifest)
        reasons.extend(f"manifest_invalid:{issue}" for issue in schema_issues)
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
                # Missing/unsafe files are already reflected above; keep this deterministic.
                continue

        if not reasons:
            reasons.extend(_package_contract_findings(root, manifest))
            credentials = _credential_findings(root, manifest)
            reasons.extend(f"credential_material_detected:{item}" for item in credentials)

        for warning in warnings:
            severity = warning.get("severity")
            if severity == "blocking":
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

    if reasons:
        disposition = "blocked"
    elif manifest_disposition == "blocked":
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

    return PackagePreflight(
        package_id=str(manifest.get("package_id")) if manifest.get("package_id") else None,
        manifest_sha256=(manifest.get("integrity") or {}).get("manifest_sha256")
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
        file_count=len(_declared_paths(manifest)) + (1 if manifest else 0),
        total_bytes=total_bytes,
        destination=destination_text,
        manifest_disposition=manifest_disposition,
        disposition=disposition,
        reasons=tuple(dict.fromkeys(reasons)),
        warnings=warnings,
        credential_findings=credentials,
    )


class PackageTransferService:
    """Finalize Packages locally, then explicitly export them to a filesystem destination.

    A Google Drive desktop sync directory is treated exactly like any other external
    destination. This module has no Google API or network dependency.
    """

    def stage_from_directory(
        self, source_dir: str | Path, staging_root: str | Path = "exchange/staging"
    ) -> PackageStageResult:
        source = Path(source_dir).resolve()
        if not source.is_dir():
            raise ValueError("Package build directory does not exist")
        manifest = with_manifest_sha256(_load_manifest(source))
        issues = validate_package_manifest(manifest)
        if issues:
            raise ValueError("Invalid Package manifest: " + "; ".join(issues))

        expected = _declared_paths(manifest) | {"manifest.json"}
        actual = _actual_relative_files(source)
        if actual != expected:
            missing = sorted(expected - actual)
            unexpected = sorted(actual - expected)
            raise ValueError(
                f"Package build directory scope mismatch: missing={missing}, unexpected={unexpected}"
            )

        for item in manifest["files"]:
            relative = str(item["path"])
            raw = _safe_file(source, relative).read_bytes()
            if len(raw) != item["size_bytes"]:
                raise ValueError(f"Package file size mismatch: {relative}")
            if _sha256(raw) != item["sha256"]:
                raise ValueError(f"Package file SHA-256 mismatch: {relative}")

        contract_findings = _package_contract_findings(source, manifest)
        if contract_findings:
            raise ValueError("Package contract mismatch: " + "; ".join(contract_findings))
        credentials = _credential_findings(source, manifest)
        if credentials:
            raise ValueError("Credential/secret material is not allowed in a standard Package")

        root = Path(staging_root).resolve()
        root.mkdir(parents=True, exist_ok=True)
        final = root / str(manifest["package_id"])
        if final.exists():
            preflight = inspect_package(final)
            if (
                preflight.manifest_sha256 == manifest["integrity"]["manifest_sha256"]
                and preflight.disposition != "blocked"
            ):
                return PackageStageResult(
                    package_id=str(manifest["package_id"]),
                    manifest_sha256=str(manifest["integrity"]["manifest_sha256"]),
                    path=str(final),
                    already_staged=True,
                    preflight=preflight,
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
            preflight = inspect_package(temporary)
            if preflight.disposition == "blocked" and preflight.reasons:
                # A manifest-declared blocked policy may still be locally staged, but
                # integrity/security problems must never become a finalized Package.
                policy_reasons = set((manifest.get("export_preflight") or {}).get("reasons", []))
                non_policy = [
                    reason for reason in preflight.reasons if reason not in policy_reasons
                ]
                if non_policy:
                    raise ValueError(
                        "Staged Package failed integrity/security checks: " + "; ".join(non_policy)
                    )
            os.replace(temporary, final)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise

        final_preflight = inspect_package(final)
        return PackageStageResult(
            package_id=str(manifest["package_id"]),
            manifest_sha256=str(manifest["integrity"]["manifest_sha256"]),
            path=str(final),
            already_staged=False,
            preflight=final_preflight,
        )

    def preflight(
        self, package_dir: str | Path, destination: str | Path | None = None
    ) -> PackagePreflight:
        return inspect_package(package_dir, destination)

    def export(
        self,
        package_dir: str | Path,
        destination_root: str | Path,
        *,
        acknowledge_review: bool = False,
    ) -> PackageExportResult:
        source = Path(package_dir).resolve()
        destination = Path(destination_root).resolve()
        preflight = inspect_package(source, destination)
        if preflight.disposition == "blocked":
            raise ValueError("Package export is blocked: " + "; ".join(preflight.reasons))
        if preflight.disposition == "review_required" and not acknowledge_review:
            raise ValueError("Package export requires explicit review acknowledgement")
        if preflight.package_id is None or preflight.manifest_sha256 is None:
            raise ValueError("Package identity is unavailable")

        destination.mkdir(parents=True, exist_ok=True)
        final = destination / preflight.package_id
        if final.exists():
            existing = inspect_package(final)
            if (
                existing.manifest_sha256 == preflight.manifest_sha256
                and existing.disposition != "blocked"
            ):
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
            copied = inspect_package(temporary)
            if copied.disposition == "blocked":
                raise ValueError("Copied Package failed integrity verification")
            if copied.manifest_sha256 != preflight.manifest_sha256:
                raise ValueError("Copied Package manifest hash changed during export")
            os.replace(temporary, final)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise

        final_check = inspect_package(final)
        if (
            final_check.disposition == "blocked"
            or final_check.manifest_sha256 != preflight.manifest_sha256
        ):
            raise ValueError("Final exported Package failed verification")
        return PackageExportResult(
            package_id=preflight.package_id,
            manifest_sha256=preflight.manifest_sha256,
            destination_root=str(destination),
            path=str(final),
            already_present=False,
            acknowledged_review=acknowledge_review,
            preflight=preflight,
        )
