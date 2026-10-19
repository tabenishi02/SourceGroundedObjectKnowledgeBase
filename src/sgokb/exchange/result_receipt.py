"""Receive ChatGPT Object Results without performing authoritative import."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from sgokb.storage.exchange_repository import PackageExchangeAuditRepository

RESULT_FILENAME = "result.json"
DEFAULT_INCOMING_ROOT = "exchange/incoming"
MAX_RESULT_BYTES = 16 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class DetectedResult:
    package_hint: str
    path: str
    byte_count: int
    result_sha256: str
    package_known: bool
    already_received: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ResultReceipt:
    receipt_id: str
    package_id: str
    result_sha256: str
    byte_count: int
    path: str
    intake_state: str
    intake_findings: tuple[str, ...]
    validation_state: str
    already_received: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _nested(value: Mapping[str, Any], *keys: str) -> tuple[bool, Any]:
    current: Any = value
    for key in keys:
        if not isinstance(current, Mapping) or key not in current:
            return False, None
        current = current[key]
    return True, current


def _binding_findings(
    parsed: Mapping[str, Any],
    package_record: Mapping[str, Any],
    manifest: Mapping[str, Any] | None,
    *,
    has_export_event: bool,
) -> list[str]:
    findings: list[str] = []

    expected: list[tuple[tuple[str, ...], Any, str]] = [
        (("target", "object_id"), package_record["object_id"], "target_object_id"),
        (("binding", "package_id"), package_record["package_id"], "package_id"),
        (
            ("binding", "package_schema_version"),
            package_record["schema_version"],
            "package_schema_version",
        ),
        (
            ("binding", "manifest_sha256"),
            package_record["manifest_sha256"],
            "manifest_sha256",
        ),
        (
            ("binding", "package_created_at"),
            package_record["package_created_at"],
            "package_created_at",
        ),
        (
            ("binding", "base_version_id"),
            package_record["base_version_id"],
            "base_version_id",
        ),
    ]

    if manifest is not None:
        expected.extend(
            [
                (
                    ("schema_version",),
                    manifest.get("binding", {}).get("expected_result_schema_version"),
                    "result_schema_version",
                ),
                (
                    ("target", "primary_class_id"),
                    manifest.get("target", {}).get("primary_class_id"),
                    "primary_class_id",
                ),
                (
                    ("target", "additional_class_ids"),
                    manifest.get("target", {}).get("additional_class_ids"),
                    "additional_class_ids",
                ),
                (
                    ("generation", "instructions_version"),
                    manifest.get("binding", {}).get("instructions_version"),
                    "instructions_version",
                ),
            ]
        )

    for path, expected_value, label in expected:
        present, actual = _nested(parsed, *path)
        if not present:
            findings.append(f"missing_routing_field:{'.'.join(path)}")
        elif actual != expected_value:
            findings.append(f"routing_mismatch:{label}")

    if not has_export_event:
        findings.append("package_has_no_export_audit")
    return findings


def _load_staged_manifest(
    package_record: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        staged = Path(str(package_record["staged_path"]))
        manifest = json.loads((staged / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None, "staged_package_manifest_unavailable"
    if manifest.get("package_id") != package_record["package_id"]:
        return None, "staged_package_manifest_package_id_mismatch"
    if (manifest.get("integrity") or {}).get("manifest_sha256") != package_record[
        "manifest_sha256"
    ]:
        return None, "staged_package_manifest_hash_mismatch"
    return manifest, None


class ResultReceiptService:
    """Detect and receive Result artifacts while keeping validation/import separate."""

    def __init__(self, audit: PackageExchangeAuditRepository):
        self.audit = audit

    def detect(
        self, incoming_root: str | Path = DEFAULT_INCOMING_ROOT
    ) -> tuple[DetectedResult, ...]:
        """List exact `drop/<package_id>/result.json` candidates without modifying them."""

        drop = Path(incoming_root).resolve() / "drop"
        if not drop.exists():
            return ()
        detected: list[DetectedResult] = []
        for path in sorted(drop.glob(f"*/{RESULT_FILENAME}")):
            if path.is_symlink() or not path.is_file():
                continue
            try:
                raw = path.read_bytes()
            except OSError:
                continue
            package_hint = path.parent.name
            digest = _sha256(raw)
            record = self.audit.package_record(package_hint)
            already = bool(record and self.audit.result_receipt_by_hash(package_hint, digest))
            detected.append(
                DetectedResult(
                    package_hint=package_hint,
                    path=str(path),
                    byte_count=len(raw),
                    result_sha256=digest,
                    package_known=record is not None,
                    already_received=already,
                )
            )
        return tuple(detected)

    def receive(
        self,
        result_path: str | Path,
        package_id: str,
        incoming_root: str | Path = DEFAULT_INCOMING_ROOT,
    ) -> ResultReceipt:
        """Copy one Result verbatim to an immutable local receipt and request validation.

        This performs only routing/intake checks. H-01 owns authoritative Result
        validation and H-02 owns Knowledge import.
        """

        package_record = self.audit.package_record(package_id)
        if package_record is None:
            raise ValueError("Unknown Package ID; Result must refer to a staged/audited Package")

        source_input = Path(result_path)
        if source_input.name != RESULT_FILENAME:
            raise ValueError("Standard Result artifact must be named result.json")
        if source_input.is_symlink() or not source_input.is_file():
            raise ValueError("Result artifact must be a regular non-symlink file")
        source = source_input.resolve()
        raw = source.read_bytes()
        if len(raw) > MAX_RESULT_BYTES:
            raise ValueError(f"Result artifact exceeds {MAX_RESULT_BYTES} bytes")
        digest = _sha256(raw)

        existing = self.audit.result_receipt_by_hash(package_id, digest)
        if existing is not None:
            return ResultReceipt(
                receipt_id=str(existing["id"]),
                package_id=package_id,
                result_sha256=digest,
                byte_count=int(existing["byte_count"]),
                path=self._stored_path(incoming_root, str(existing["storage_ref"])),
                intake_state=str(existing["intake_state"]),
                intake_findings=tuple(existing["intake_findings"]),
                validation_state=str(existing["validation_state"]),
                already_received=True,
            )

        findings: list[str] = []
        parsed: dict[str, Any] | None = None
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            findings.append("invalid_utf8")
        else:
            try:
                value = json.loads(text)
            except json.JSONDecodeError:
                findings.append("invalid_json")
            else:
                if not isinstance(value, dict):
                    findings.append("top_level_result_must_be_object")
                else:
                    parsed = value

        manifest, manifest_finding = _load_staged_manifest(package_record)
        if manifest_finding is not None:
            findings.append(manifest_finding)
        if parsed is not None:
            findings.extend(
                _binding_findings(
                    parsed,
                    package_record,
                    manifest,
                    has_export_event=bool(self.audit.export_events(package_id)),
                )
            )
        elif not self.audit.export_events(package_id):
            findings.append("package_has_no_export_audit")

        findings = list(dict.fromkeys(findings))
        intake_state = "ready_for_validation" if not findings else "needs_review"
        receipt_id = str(uuid.uuid4())
        root = Path(incoming_root).resolve()
        package_root = root / "received" / package_id
        final = package_root / receipt_id
        temporary = package_root / f".{receipt_id}.receiving-{uuid.uuid4().hex}"
        storage_ref = (Path("received") / package_id / receipt_id / RESULT_FILENAME).as_posix()

        try:
            package_root.mkdir(parents=True, exist_ok=True)
            temporary.mkdir()
            (temporary / RESULT_FILENAME).write_bytes(raw)
            if _sha256((temporary / RESULT_FILENAME).read_bytes()) != digest:
                raise ValueError("Result copy integrity verification failed")
            os.replace(temporary, final)
            persisted_receipt_id = self.audit.record_result_receipt(
                package_id,
                digest,
                len(raw),
                storage_ref,
                intake_state,
                findings,
                receipt_id=receipt_id,
                parsed_schema_version=self._text_value(parsed, "schema_version"),
                parsed_result_status=self._text_value(parsed, "result_status"),
                parsed_target_object_id=self._nested_text(parsed, "target", "object_id"),
                parsed_binding_package_id=self._nested_text(parsed, "binding", "package_id"),
                parsed_manifest_sha256=self._nested_text(parsed, "binding", "manifest_sha256"),
                parsed_base_version_id=self._nested_nullable_text(
                    parsed, "binding", "base_version_id"
                ),
            )
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            shutil.rmtree(final, ignore_errors=True)
            raise

        return ResultReceipt(
            receipt_id=persisted_receipt_id,
            package_id=package_id,
            result_sha256=digest,
            byte_count=len(raw),
            path=str(final / RESULT_FILENAME),
            intake_state=intake_state,
            intake_findings=tuple(findings),
            validation_state="pending",
            already_received=False,
        )

    @staticmethod
    def _stored_path(incoming_root: str | Path, storage_ref: str) -> str:
        return str(Path(incoming_root).resolve() / Path(*storage_ref.split("/")))

    @staticmethod
    def _text_value(parsed: Mapping[str, Any] | None, key: str) -> str | None:
        if parsed is None:
            return None
        value = parsed.get(key)
        return value if isinstance(value, str) else None

    @staticmethod
    def _nested_text(parsed: Mapping[str, Any] | None, *keys: str) -> str | None:
        if parsed is None:
            return None
        present, value = _nested(parsed, *keys)
        return value if present and isinstance(value, str) else None

    @staticmethod
    def _nested_nullable_text(parsed: Mapping[str, Any] | None, *keys: str) -> str | None:
        if parsed is None:
            return None
        present, value = _nested(parsed, *keys)
        if not present or value is None:
            return None
        return value if isinstance(value, str) else None
