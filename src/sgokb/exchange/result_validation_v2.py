"""Deterministic validation for Raw-grounded Object Result v2 receipts."""

from __future__ import annotations

import json
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker

from sgokb.storage import PackageBuildReadRepository, RawGroundingRepository

from .object_result import ObjectResultContract, ObjectResultValidationError
from .object_result_v2 import (
    iter_raw_grounding_refs,
    load_object_result_schema_v2,
    validate_object_result_v2,
)
from .package_manifest_v2 import (
    PACKAGE_SCHEMA_VERSION_V2,
    calculate_grounding_set_sha256,
    validate_package_manifest_v2,
)
from .package_transfer import _safe_file, _sha256
from .package_transfer_v2 import inspect_package_v2
from .result_validation import (
    ARTIFACT_SYNTAX,
    BINDING_PRECONDITION,
    DOMAIN_CONTRACT,
    GROUNDING_PROVENANCE,
    REFERENTIAL,
    STATIC_SCHEMA,
    ResultValidationFinding,
    ResultValidationReport,
    ResultValidationService,
    _error,
    _iter_temporal_scopes,
    _json_path,
)


class RawResultValidationService:
    """Validate v2 without changing the historical Result v1 validator."""

    def __init__(self, repository, audit):
        self.repository = repository
        self.audit = audit
        self.package_store = PackageBuildReadRepository(repository.db)
        self.raw_store = RawGroundingRepository(repository.db)
        self.legacy = ResultValidationService(repository, audit)

    def validate_receipt(
        self,
        receipt_id: str,
        *,
        incoming_root: str | Path,
        force: bool = False,
    ) -> ResultValidationReport:
        receipt = self.audit.result_receipt(receipt_id)
        if receipt is None:
            raise ValueError("Unknown Result receipt ID")
        if receipt["validation_state"] in {"valid", "invalid", "error"} and not force:
            return self.legacy._stored_report(receipt)
        self.audit.start_result_validation(receipt_id, force=force)
        try:
            result, findings = self.legacy._load_result(receipt, incoming_root)
            if result is None:
                return self.legacy._finish(receipt, "invalid", findings)
            schema_findings = self._static_schema_findings(result)
            findings.extend(schema_findings)
            if schema_findings:
                return self.legacy._finish(receipt, "invalid", findings)
            package_record, manifest = self._load_package_authority(receipt)
            findings.extend(self.legacy._binding_findings(result, package_record, manifest))
            findings.extend(self._v2_binding_findings(result, manifest))
            findings.extend(self.legacy._referential_findings(result, manifest))
            findings.extend(self._grounding_findings(result, package_record, manifest))
            findings.extend(self._domain_findings(result, manifest))
            findings.extend(self.legacy._review_findings(result, receipt))
            findings = self.legacy._deduplicate(findings)
            state = (
                "invalid"
                if any(item.severity == "error" for item in findings)
                else "valid"
            )
            return self.legacy._finish(receipt, state, findings)
        except Exception as error:
            finding = _error(
                ARTIFACT_SYNTAX,
                "$",
                "validator_internal_error",
                f"{type(error).__name__}: {error}",
            )
            return self.legacy._finish(receipt, "error", [finding])

    @staticmethod
    def _static_schema_findings(
        result: Mapping[str, Any],
    ) -> list[ResultValidationFinding]:
        validator = Draft202012Validator(
            load_object_result_schema_v2(),
            format_checker=FormatChecker(),
        )
        return [
            _error(STATIC_SCHEMA, _json_path(issue.absolute_path), "schema", issue.message)
            for issue in sorted(
                validator.iter_errors(result),
                key=lambda item: list(item.absolute_path),
            )
        ]

    def _load_package_authority(self, receipt: Mapping[str, Any]):
        package_record = self.audit.package_record(str(receipt["package_id"]))
        if package_record is None:
            raise ValueError("Receipt Package audit record is missing")
        if package_record["schema_version"] != PACKAGE_SCHEMA_VERSION_V2:
            raise ValueError("Raw Result validator requires a Package v2 audit record")
        staged = Path(str(package_record["staged_path"])).resolve()
        preflight = inspect_package_v2(staged)
        if preflight.disposition == "blocked":
            raise ValueError(
                "Staged Package v2 no longer passes integrity/security preflight"
            )
        manifest = json.loads((staged / "manifest.json").read_text(encoding="utf-8"))
        issues = validate_package_manifest_v2(manifest)
        if issues:
            raise ValueError(
                "Staged Package v2 manifest is invalid: " + "; ".join(issues)
            )
        if manifest["integrity"]["manifest_sha256"] != package_record["manifest_sha256"]:
            raise ValueError("Staged Package manifest hash differs from audit record")
        raw_audit = self.raw_store.package_grounding(str(receipt["package_id"]))
        if raw_audit is None:
            raise ValueError("Package v2 Raw grounding audit is missing")
        raw = manifest["raw_grounding"]
        if tuple(raw["included_raw_artifact_ids"]) != tuple(
            raw_audit["included_raw_artifact_ids"]
        ):
            raise ValueError("Staged Package Raw membership differs from audit record")
        if (
            raw["integrity"]["grounding_set_sha256"]
            != raw_audit["grounding_set_sha256"]
        ):
            raise ValueError("Staged Package grounding-set hash differs from audit record")
        return package_record, manifest

    @staticmethod
    def _v2_binding_findings(result: Mapping[str, Any], manifest: Mapping[str, Any]):
        binding = result.get("binding") or {}
        raw = manifest.get("raw_grounding") or {}
        expected = (
            (
                "$.binding.grounding_contract",
                binding.get("grounding_contract"),
                (manifest.get("binding") or {}).get("grounding_contract"),
                "grounding_contract_mismatch",
            ),
            (
                "$.binding.grounding_set_sha256",
                binding.get("grounding_set_sha256"),
                (raw.get("integrity") or {}).get("grounding_set_sha256"),
                "grounding_set_sha256_mismatch",
            ),
        )
        return [
            _error(
                BINDING_PRECONDITION,
                path,
                code,
                f"Expected {wanted!r} from audited Package, got {actual!r}",
            )
            for path, actual, wanted, code in expected
            if actual != wanted
        ]

    def _grounding_findings(
        self,
        result: Mapping[str, Any],
        package_record: Mapping[str, Any],
        manifest: Mapping[str, Any],
    ) -> list[ResultValidationFinding]:
        findings: list[ResultValidationFinding] = []
        package_id = str(package_record["package_id"])
        raw = manifest["raw_grounding"]
        membership = set(raw["included_raw_artifact_ids"])
        item_by_id = {item["raw_artifact_id"]: item for item in raw["artifacts"]}
        staged = Path(str(package_record["staged_path"])).resolve()
        cache: dict[str, bytes] = {}

        if (
            raw["integrity"]["grounding_set_sha256"]
            != calculate_grounding_set_sha256(raw)
        ):
            findings.append(
                _error(
                    GROUNDING_PROVENANCE,
                    "$.binding.grounding_set_sha256",
                    "grounding_set_integrity_mismatch",
                    "Package grounding-set fingerprint no longer matches its membership",
                )
            )

        for path, ref in iter_raw_grounding_refs(result):
            raw_id = str(ref.get("raw_artifact_id"))
            id_path = f"{path}.raw_artifact_id"
            if raw_id not in membership:
                findings.append(
                    _error(
                        GROUNDING_PROVENANCE,
                        id_path,
                        "raw_artifact_outside_package",
                        f"Raw Artifact is not a member of the audited Package: {raw_id}",
                    )
                )
                continue
            item = item_by_id[raw_id]
            canonical = self.repository.source_store.raw_artifact_by_id(raw_id)
            canonical_snapshot = self.repository.source_store.snapshot_by_id(
                canonical["snapshot_id"]
            )
            if (
                canonical["snapshot_id"] != item["snapshot_id"]
                or canonical_snapshot.source_id != item["source_id"]
                or canonical["sha256"] != item["sha256"]
                or int(canonical["bytes"]) != int(item["byte_size"])
            ):
                findings.append(
                    _error(
                        GROUNDING_PROVENANCE,
                        id_path,
                        "raw_artifact_provenance_mismatch",
                        "Canonical Raw provenance differs from the audited Package metadata",
                    )
                )
                continue
            audited = self.raw_store.package_raw_artifact(package_id, raw_id)
            if audited is None or audited["sha256"] != item["sha256"]:
                findings.append(
                    _error(
                        GROUNDING_PROVENANCE,
                        id_path,
                        "raw_artifact_audit_mismatch",
                        "Raw Artifact is missing or changed in Package audit metadata",
                    )
                )
                continue
            payload = cache.get(raw_id)
            if payload is None:
                payload = _safe_file(staged, item["package_path"]).read_bytes()
                cache[raw_id] = payload
            if len(payload) != item["byte_size"] or _sha256(payload) != item["sha256"]:
                findings.append(
                    _error(
                        GROUNDING_PROVENANCE,
                        id_path,
                        "raw_payload_integrity_mismatch",
                        "Staged Raw payload no longer matches Package size/hash",
                    )
                )
                continue
            locator = ref.get("locator")
            if isinstance(locator, Mapping):
                message = self._locator_issue(locator, item, payload)
                if message:
                    findings.append(
                        _error(
                            GROUNDING_PROVENANCE,
                            f"{path}.locator",
                            "raw_locator_invalid",
                            message,
                        )
                    )
        return findings

    @staticmethod
    def _locator_issue(
        locator: Mapping[str, Any],
        item: Mapping[str, Any],
        payload: bytes,
    ):
        kind = locator.get("kind")
        if kind == "byte_range":
            start, end = int(locator["start"]), int(locator["end"])
            if not 0 <= start < end <= len(payload):
                return "byte_range must satisfy 0 <= start < end <= exact Raw byte_size"
            return None
        if kind == "text_quote":
            charset = item.get("charset")
            if not charset:
                return "text_quote requires a Package Raw artifact with a usable charset"
            try:
                text = payload.decode(str(charset))
            except (LookupError, UnicodeDecodeError):
                return "text_quote Raw payload cannot be decoded with the declared charset"
            exact = str(locator["exact"])
            positions: list[int] = []
            start = 0
            while True:
                index = text.find(exact, start)
                if index < 0:
                    break
                positions.append(index)
                start = index + 1
            if not positions:
                return "text_quote exact text does not occur in the Raw payload"
            prefix = locator.get("prefix")
            suffix = locator.get("suffix")
            matches = []
            for index in positions:
                before = text[:index]
                after = text[index + len(exact) :]
                if prefix is not None and not before.endswith(str(prefix)):
                    continue
                if suffix is not None and not after.startswith(str(suffix)):
                    continue
                matches.append(index)
            if len(matches) != 1:
                return "text_quote locator must resolve to exactly one Raw text occurrence"
            return None
        return "unsupported Raw locator kind"

    def _domain_findings(
        self,
        result: Mapping[str, Any],
        manifest: Mapping[str, Any],
    ) -> list[ResultValidationFinding]:
        target = manifest.get("target") or {}
        class_ids = (
            str(target.get("primary_class_id")),
            *tuple(str(value) for value in target.get("additional_class_ids") or []),
        )
        facets = self.repository.semantic_store.facets_for_classes(class_ids)
        attributes = self.package_store.active_attribute_definitions()
        relations = self.package_store.active_relation_types()
        contract = ObjectResultContract(
            target_object_id=str(target.get("object_id")),
            primary_class_id=class_ids[0],
            additional_class_ids=tuple(class_ids[1:]),
            facet_ids=tuple(item.facet_id for item in facets),
            attribute_value_types={item["id"]: item["value_type"] for item in attributes},
            relation_type_ids=frozenset(item["id"] for item in relations),
            package_id=str(manifest.get("package_id")),
            package_schema_version=str(manifest.get("schema_version")),
            manifest_sha256=str(
                (manifest.get("integrity") or {}).get("manifest_sha256")
            ),
            base_version_id=(manifest.get("binding") or {}).get("base_version_id"),
        )
        findings: list[ResultValidationFinding] = []
        try:
            validate_object_result_v2(result, contract)
        except ObjectResultValidationError as exc:
            for issue in exc.issues:
                stage = (
                    REFERENTIAL
                    if issue.code in {"unknown_attribute", "unknown_relation_type"}
                    else DOMAIN_CONTRACT
                )
                findings.append(_error(stage, issue.path, issue.code, issue.message))
        for path, scope in _iter_temporal_scopes(result):
            left, right = scope.get("valid_from"), scope.get("valid_to")
            if left is not None and right is not None:
                try:
                    if _parse_temporal(str(left)) > _parse_temporal(str(right)):
                        findings.append(
                            _error(
                                DOMAIN_CONTRACT,
                                path,
                                "invalid_temporal_interval",
                                "temporal_scope.valid_from must not be later than valid_to",
                            )
                        )
                except ValueError:
                    pass
        for index, proposal in enumerate(result.get("registry_proposals", [])):
            findings.extend(self.legacy._proposal_payload_findings(index, proposal))
        return findings


def _parse_temporal(value: str) -> datetime:
    if "T" not in value:
        return datetime.combine(date.fromisoformat(value), time.min, tzinfo=timezone.utc)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
