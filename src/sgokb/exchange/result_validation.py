"""Phase H / H-01 deterministic validation of immutable Object Result receipts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator, FormatChecker

from sgokb.storage import PackageBuildReadRepository, PackageExchangeAuditRepository

from .object_result import (
    ObjectResultContract,
    ObjectResultValidationError,
    collect_evidence_ids,
    load_object_result_schema,
    validate_object_result,
)
from .package_manifest import calculate_manifest_sha256, validate_package_manifest
from .result_receipt import DEFAULT_INCOMING_ROOT, RESULT_FILENAME

ARTIFACT_SYNTAX = "artifact_syntax"
STATIC_SCHEMA = "static_schema"
BINDING_PRECONDITION = "binding_precondition"
REFERENTIAL = "referential"
GROUNDING_PROVENANCE = "grounding_provenance"
DOMAIN_CONTRACT = "domain_contract"


@dataclass(frozen=True, slots=True)
class ResultValidationFinding:
    stage: str
    path: str
    code: str
    message: str
    severity: str = "error"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ResultValidationReport:
    receipt_id: str
    package_id: str
    result_sha256: str
    validation_state: str
    findings: tuple[ResultValidationFinding, ...]
    validation_completed_at: str

    @property
    def is_valid(self) -> bool:
        return self.validation_state == "valid"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["is_valid"] = self.is_valid
        return value


class _ValidationInfrastructureError(RuntimeError):
    def __init__(self, code: str, message: str, *, path: str = "$"):
        self.code = code
        self.path = path
        super().__init__(message)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json_path(parts: Iterable[object]) -> str:
    value = "$"
    for part in parts:
        if isinstance(part, int):
            value += f"[{part}]"
        else:
            value += f".{part}"
    return value


def _error(stage: str, path: str, code: str, message: str) -> ResultValidationFinding:
    return ResultValidationFinding(stage=stage, path=path, code=code, message=message)


def _review(stage: str, path: str, code: str, message: str) -> ResultValidationFinding:
    return ResultValidationFinding(
        stage=stage,
        path=path,
        code=code,
        message=message,
        severity="review",
    )


def _iter_statements(result: Mapping[str, Any]):
    knowledge = result.get("knowledge", {})
    for index, statement in enumerate(knowledge.get("summary", [])):
        yield f"$.knowledge.summary[{index}]", statement
    for facet_index, facet in enumerate(knowledge.get("facets", [])):
        for statement_index, statement in enumerate(facet.get("statements", [])):
            yield (
                f"$.knowledge.facets[{facet_index}].statements[{statement_index}]",
                statement,
            )


def _iter_knowledge_items(result: Mapping[str, Any]):
    yield from _iter_statements(result)
    knowledge = result.get("knowledge", {})
    for index, item in enumerate(knowledge.get("attributes", [])):
        yield f"$.knowledge.attributes[{index}]", item
    for index, item in enumerate(knowledge.get("relations", [])):
        yield f"$.knowledge.relations[{index}]", item


def _iter_temporal_scopes(result: Mapping[str, Any]):
    for path, item in _iter_knowledge_items(result):
        scope = item.get("temporal_scope")
        if isinstance(scope, Mapping):
            yield f"{path}.temporal_scope", scope


def _iter_evidence_refs(result: Mapping[str, Any]):
    for path, item in _iter_knowledge_items(result):
        for index, ref in enumerate(item.get("evidence", [])):
            yield f"{path}.evidence[{index}]", ref
    for collection in ("conflicts", "gaps", "unresolved_references", "registry_proposals"):
        for item_index, item in enumerate(result.get(collection, [])):
            for ref_index, ref in enumerate(item.get("evidence", [])):
                yield f"$.{collection}[{item_index}].evidence[{ref_index}]", ref


def _parse_temporal(value: str) -> datetime:
    if "T" not in value:
        return datetime.combine(date.fromisoformat(value), time.min, tzinfo=timezone.utc)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class ResultValidationService:
    """Validate a G-05 receipt without importing or mutating canonical Knowledge."""

    def __init__(self, repository, audit: PackageExchangeAuditRepository | None = None):
        self.repository = repository
        self.audit = audit or PackageExchangeAuditRepository(repository.db)
        self.package_store = PackageBuildReadRepository(repository.db)

    def validate_receipt(
        self,
        receipt_id: str,
        *,
        incoming_root: str | Path = DEFAULT_INCOMING_ROOT,
        force: bool = False,
    ) -> ResultValidationReport:
        receipt = self.audit.result_receipt(receipt_id)
        if receipt is None:
            raise ValueError("Unknown Result receipt ID")

        if receipt["validation_state"] in {"valid", "invalid", "error"} and not force:
            return self._stored_report(receipt)
        self.audit.start_result_validation(receipt_id, force=force)

        try:
            result, findings = self._load_result(receipt, incoming_root)
            if result is None:
                report = self._finish(receipt, "invalid", findings)
                return report

            schema_findings = self._static_schema_findings(result)
            findings.extend(schema_findings)
            if schema_findings:
                return self._finish(receipt, "invalid", findings)

            package_record, manifest = self._load_package_authority(receipt)
            findings.extend(self._binding_findings(result, package_record, manifest))
            findings.extend(self._referential_findings(result, manifest))
            findings.extend(self._grounding_findings(result, manifest))
            findings.extend(self._domain_findings(result, manifest))
            findings.extend(self._review_findings(result, receipt))
            findings = self._deduplicate(findings)
            state = "invalid" if any(item.severity == "error" for item in findings) else "valid"
            return self._finish(receipt, state, findings)
        except _ValidationInfrastructureError as error:
            finding = _error(
                ARTIFACT_SYNTAX,
                error.path,
                error.code,
                str(error),
            )
            return self._finish(receipt, "error", [finding])
        except Exception as error:  # preserve a terminal audit state for unexpected local failures
            finding = _error(
                ARTIFACT_SYNTAX,
                "$",
                "validator_internal_error",
                f"{type(error).__name__}: {error}",
            )
            return self._finish(receipt, "error", [finding])

    def _stored_report(self, receipt: Mapping[str, Any]) -> ResultValidationReport:
        findings = tuple(
            ResultValidationFinding(**item) for item in receipt.get("validation_findings", [])
        )
        return ResultValidationReport(
            receipt_id=str(receipt["id"]),
            package_id=str(receipt["package_id"]),
            result_sha256=str(receipt["result_sha256"]),
            validation_state=str(receipt["validation_state"]),
            findings=findings,
            validation_completed_at=str(receipt.get("validation_completed_at") or ""),
        )

    def _finish(
        self,
        receipt: Mapping[str, Any],
        state: str,
        findings: Iterable[ResultValidationFinding],
    ) -> ResultValidationReport:
        completed_at = _now()
        normalized = tuple(self._deduplicate(findings))
        self.audit.complete_result_validation(
            str(receipt["id"]),
            state,
            [item.to_dict() for item in normalized],
            completed_at=completed_at,
        )
        return ResultValidationReport(
            receipt_id=str(receipt["id"]),
            package_id=str(receipt["package_id"]),
            result_sha256=str(receipt["result_sha256"]),
            validation_state=state,
            findings=normalized,
            validation_completed_at=completed_at,
        )

    @staticmethod
    def _deduplicate(findings: Iterable[ResultValidationFinding]) -> list[ResultValidationFinding]:
        result: list[ResultValidationFinding] = []
        seen: set[tuple[str, str, str, str, str]] = set()
        for item in findings:
            key = (item.stage, item.path, item.code, item.message, item.severity)
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result

    def _load_result(
        self,
        receipt: Mapping[str, Any],
        incoming_root: str | Path,
    ) -> tuple[Mapping[str, Any] | None, list[ResultValidationFinding]]:
        root = Path(incoming_root).resolve()
        storage_ref = Path(str(receipt["storage_ref"]))
        if storage_ref.is_absolute() or ".." in storage_ref.parts:
            raise _ValidationInfrastructureError(
                "unsafe_receipt_storage_ref",
                "Receipt storage reference is not a safe incoming-root relative path",
            )
        path = (root / storage_ref).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise _ValidationInfrastructureError(
                "unsafe_receipt_storage_ref",
                "Receipt storage reference escapes the incoming root",
            ) from exc
        if path.name != RESULT_FILENAME or path.is_symlink() or not path.is_file():
            raise _ValidationInfrastructureError(
                "receipt_artifact_missing",
                "Immutable receipt result.json is missing or is not a regular file",
            )
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise _ValidationInfrastructureError(
                "receipt_artifact_unreadable",
                f"Cannot read immutable receipt artifact: {exc}",
            ) from exc
        if len(raw) != int(receipt["byte_count"]):
            raise _ValidationInfrastructureError(
                "receipt_byte_count_mismatch",
                "Immutable receipt byte count no longer matches its audit record",
            )
        if _sha256(raw) != receipt["result_sha256"]:
            raise _ValidationInfrastructureError(
                "receipt_sha256_mismatch",
                "Immutable receipt SHA-256 no longer matches its audit record",
            )

        findings: list[ResultValidationFinding] = []
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            findings.append(
                _error(ARTIFACT_SYNTAX, "$", "invalid_utf8", f"Result is not valid UTF-8: {exc}")
            )
            return None, findings
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            findings.append(
                _error(
                    ARTIFACT_SYNTAX,
                    "$",
                    "invalid_json",
                    f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}",
                )
            )
            return None, findings
        if not isinstance(parsed, Mapping):
            findings.append(
                _error(
                    ARTIFACT_SYNTAX,
                    "$",
                    "top_level_result_must_be_object",
                    "Object Result top level must be a JSON object",
                )
            )
            return None, findings
        return parsed, findings

    @staticmethod
    def _static_schema_findings(result: Mapping[str, Any]) -> list[ResultValidationFinding]:
        validator = Draft202012Validator(
            load_object_result_schema(),
            format_checker=FormatChecker(),
        )
        findings: list[ResultValidationFinding] = []
        for issue in sorted(
            validator.iter_errors(result), key=lambda item: list(item.absolute_path)
        ):
            findings.append(
                _error(
                    STATIC_SCHEMA,
                    _json_path(issue.absolute_path),
                    "schema",
                    issue.message,
                )
            )
        return findings

    def _load_package_authority(
        self,
        receipt: Mapping[str, Any],
    ) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
        package_record = self.audit.package_record(str(receipt["package_id"]))
        if package_record is None:
            raise _ValidationInfrastructureError(
                "package_audit_missing",
                "Receipt Package audit record is missing",
            )
        staged = Path(str(package_record["staged_path"])).resolve()
        manifest_path = staged / "manifest.json"
        if manifest_path.is_symlink() or not manifest_path.is_file():
            raise _ValidationInfrastructureError(
                "staged_manifest_missing",
                "Staged Package manifest is missing or is not a regular file",
            )
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise _ValidationInfrastructureError(
                "staged_manifest_unreadable",
                f"Cannot read staged Package manifest: {exc}",
            ) from exc
        if not isinstance(manifest, Mapping):
            raise _ValidationInfrastructureError(
                "staged_manifest_invalid",
                "Staged Package manifest top level is not an object",
            )
        manifest_issues = validate_package_manifest(manifest)
        if manifest_issues:
            raise _ValidationInfrastructureError(
                "staged_manifest_invalid",
                "Staged Package manifest failed canonical validation: "
                + "; ".join(manifest_issues),
            )
        actual_hash = calculate_manifest_sha256(manifest)
        if actual_hash != package_record["manifest_sha256"]:
            raise _ValidationInfrastructureError(
                "staged_manifest_hash_mismatch",
                "Staged Package manifest hash no longer matches the audit record",
            )
        if manifest.get("package_id") != package_record["package_id"]:
            raise _ValidationInfrastructureError(
                "staged_manifest_package_mismatch",
                "Staged Package manifest identity does not match the audit record",
            )
        manifest_evidence = list(
            (manifest.get("evidence") or {}).get("included_evidence_ids") or []
        )
        if manifest_evidence != list(package_record["included_evidence_ids"]):
            raise _ValidationInfrastructureError(
                "staged_manifest_evidence_mismatch",
                "Staged Package Evidence membership does not match the audit record",
            )
        return package_record, manifest

    def _binding_findings(
        self,
        result: Mapping[str, Any],
        package_record: Mapping[str, Any],
        manifest: Mapping[str, Any],
    ) -> list[ResultValidationFinding]:
        findings: list[ResultValidationFinding] = []
        checks = (
            (
                "$.schema_version",
                result.get("schema_version"),
                (manifest.get("binding") or {}).get("expected_result_schema_version"),
                "result_schema_version_mismatch",
            ),
            (
                "$.target.object_id",
                (result.get("target") or {}).get("object_id"),
                (manifest.get("target") or {}).get("object_id"),
                "target_object_mismatch",
            ),
            (
                "$.target.primary_class_id",
                (result.get("target") or {}).get("primary_class_id"),
                (manifest.get("target") or {}).get("primary_class_id"),
                "primary_class_mismatch",
            ),
            (
                "$.target.additional_class_ids",
                (result.get("target") or {}).get("additional_class_ids"),
                (manifest.get("target") or {}).get("additional_class_ids"),
                "additional_classes_mismatch",
            ),
            (
                "$.binding.package_id",
                (result.get("binding") or {}).get("package_id"),
                manifest.get("package_id"),
                "package_id_mismatch",
            ),
            (
                "$.binding.package_schema_version",
                (result.get("binding") or {}).get("package_schema_version"),
                manifest.get("schema_version"),
                "package_schema_version_mismatch",
            ),
            (
                "$.binding.manifest_sha256",
                (result.get("binding") or {}).get("manifest_sha256"),
                (manifest.get("integrity") or {}).get("manifest_sha256"),
                "manifest_sha256_mismatch",
            ),
            (
                "$.binding.package_created_at",
                (result.get("binding") or {}).get("package_created_at"),
                manifest.get("created_at"),
                "package_created_at_mismatch",
            ),
            (
                "$.binding.base_version_id",
                (result.get("binding") or {}).get("base_version_id"),
                (manifest.get("binding") or {}).get("base_version_id"),
                "base_version_mismatch",
            ),
            (
                "$.generation.instructions_version",
                (result.get("generation") or {}).get("instructions_version"),
                (manifest.get("binding") or {}).get("instructions_version"),
                "instructions_version_mismatch",
            ),
        )
        for path, actual, expected, code in checks:
            if actual != expected:
                findings.append(
                    _error(
                        BINDING_PRECONDITION,
                        path,
                        code,
                        f"Expected {expected!r} from the audited Package, got {actual!r}",
                    )
                )

        target_id = (manifest.get("target") or {}).get("object_id")
        try:
            object_record = self.repository.object_store.get_object(str(target_id))
        except ValueError:
            findings.append(
                _error(
                    BINDING_PRECONDITION,
                    "$.target.object_id",
                    "target_object_missing",
                    f"Target Object does not exist in canonical storage: {target_id}",
                )
            )
            return findings

        if object_record.status.value != "active":
            findings.append(
                _error(
                    BINDING_PRECONDITION,
                    "$.target.object_id",
                    "target_object_inactive",
                    "Target Object is no longer active",
                )
            )

        manifest_target = manifest.get("target") or {}
        if object_record.primary_class_id != manifest_target.get("primary_class_id"):
            findings.append(
                _error(
                    BINDING_PRECONDITION,
                    "$.target.primary_class_id",
                    "stale_primary_class",
                    "Package Primary Class no longer matches the canonical Object",
                )
            )
        if list(object_record.additional_class_ids) != list(
            manifest_target.get("additional_class_ids") or []
        ):
            findings.append(
                _error(
                    BINDING_PRECONDITION,
                    "$.target.additional_class_ids",
                    "stale_additional_classes",
                    "Package Additional Classes no longer match the canonical Object",
                )
            )

        expected_base = (manifest.get("binding") or {}).get("base_version_id")
        try:
            current = self.repository.version_store.current_version_id(object_record.object_id)
        except ValueError:
            current = None
        if current != expected_base:
            findings.append(
                _error(
                    BINDING_PRECONDITION,
                    "$.binding.base_version_id",
                    "stale_base_version",
                    f"Package base {expected_base!r} is stale; canonical current is {current!r}",
                )
            )
        if expected_base is not None:
            try:
                version = self.repository.version_store.version_by_id(str(expected_base))
            except ValueError:
                findings.append(
                    _error(
                        BINDING_PRECONDITION,
                        "$.binding.base_version_id",
                        "base_version_missing",
                        f"Package base Version does not exist: {expected_base}",
                    )
                )
            else:
                if version.object_id != object_record.object_id:
                    findings.append(
                        _error(
                            BINDING_PRECONDITION,
                            "$.binding.base_version_id",
                            "base_version_wrong_object",
                            "Package base Version belongs to another Object",
                        )
                    )
                if version.state.value != "accepted":
                    findings.append(
                        _error(
                            BINDING_PRECONDITION,
                            "$.binding.base_version_id",
                            "base_version_not_accepted",
                            "Package base Version is not an accepted Version",
                        )
                    )

        if package_record["schema_version"] != manifest.get("schema_version"):
            findings.append(
                _error(
                    BINDING_PRECONDITION,
                    "$.binding.package_schema_version",
                    "package_audit_schema_mismatch",
                    "Package audit schema version differs from the staged manifest",
                )
            )
        return findings

    def _referential_findings(
        self,
        result: Mapping[str, Any],
        manifest: Mapping[str, Any],
    ) -> list[ResultValidationFinding]:
        findings: list[ResultValidationFinding] = []
        db = self.repository.db

        def active(table: str, identifier: str) -> bool:
            row = db.execute(f"SELECT status FROM {table} WHERE id=?", (identifier,)).fetchone()
            return bool(row and row["status"] == "active")

        def object_exists(identifier: str) -> bool:
            return (
                db.execute("SELECT 1 FROM objects WHERE id=?", (identifier,)).fetchone() is not None
            )

        def source_exists(identifier: str) -> bool:
            return (
                db.execute("SELECT 1 FROM source_records WHERE id=?", (identifier,)).fetchone()
                is not None
            )

        target = result.get("target") or {}
        class_refs = [
            ("$.target.primary_class_id", target.get("primary_class_id")),
            *[
                (f"$.target.additional_class_ids[{index}]", class_id)
                for index, class_id in enumerate(target.get("additional_class_ids") or [])
            ],
        ]
        for path, class_id in class_refs:
            if not active("object_classes", str(class_id)):
                findings.append(
                    _error(
                        REFERENTIAL,
                        path,
                        "class_missing_or_inactive",
                        f"Class is not active: {class_id}",
                    )
                )

        for index, facet in enumerate((result.get("knowledge") or {}).get("facets", [])):
            facet_id = facet.get("facet_id")
            if not active("facet_definitions", str(facet_id)):
                findings.append(
                    _error(
                        REFERENTIAL,
                        f"$.knowledge.facets[{index}].facet_id",
                        "facet_missing_or_inactive",
                        f"Facet is not active: {facet_id}",
                    )
                )

        for index, attribute in enumerate((result.get("knowledge") or {}).get("attributes", [])):
            attribute_id = attribute.get("attribute_id")
            if not active("attribute_definitions", str(attribute_id)):
                findings.append(
                    _error(
                        REFERENTIAL,
                        f"$.knowledge.attributes[{index}].attribute_id",
                        "attribute_missing_or_inactive",
                        f"Attribute Definition is not active: {attribute_id}",
                    )
                )

        for index, relation in enumerate((result.get("knowledge") or {}).get("relations", [])):
            relation_type_id = relation.get("relation_type_id")
            if not active("relation_types", str(relation_type_id)):
                findings.append(
                    _error(
                        REFERENTIAL,
                        f"$.knowledge.relations[{index}].relation_type_id",
                        "relation_type_missing_or_inactive",
                        f"Relation Type is not active: {relation_type_id}",
                    )
                )
            for endpoint in ("subject_object_id", "object_object_id"):
                object_id = relation.get(endpoint)
                if not object_exists(str(object_id)):
                    findings.append(
                        _error(
                            REFERENTIAL,
                            f"$.knowledge.relations[{index}].{endpoint}",
                            "relation_object_missing",
                            f"Relation endpoint Object does not exist: {object_id}",
                        )
                    )

        for path, statement in _iter_statements(result):
            attribution = statement.get("attribution")
            if not isinstance(attribution, Mapping):
                continue
            if attribution.get("kind") == "object" and not object_exists(
                str(attribution.get("object_id"))
            ):
                findings.append(
                    _error(
                        REFERENTIAL,
                        f"{path}.attribution.object_id",
                        "attribution_object_missing",
                        f"Attribution Object does not exist: {attribution.get('object_id')}",
                    )
                )
            if attribution.get("kind") == "source" and not source_exists(
                str(attribution.get("source_id"))
            ):
                findings.append(
                    _error(
                        REFERENTIAL,
                        f"{path}.attribution.source_id",
                        "attribution_source_missing",
                        f"Attribution Source does not exist: {attribution.get('source_id')}",
                    )
                )

        for path, scope in _iter_temporal_scopes(result):
            object_id = scope.get("context_object_id")
            if object_id is not None and not object_exists(str(object_id)):
                findings.append(
                    _error(
                        REFERENTIAL,
                        f"{path}.context_object_id",
                        "temporal_context_object_missing",
                        f"Temporal context Object does not exist: {object_id}",
                    )
                )

        for index, gap in enumerate(result.get("gaps", [])):
            if gap.get("facet_id") is not None and not active(
                "facet_definitions", str(gap.get("facet_id"))
            ):
                findings.append(
                    _error(
                        REFERENTIAL,
                        f"$.gaps[{index}].facet_id",
                        "gap_facet_missing_or_inactive",
                        f"Gap Facet is not active: {gap.get('facet_id')}",
                    )
                )
            if gap.get("attribute_id") is not None and not active(
                "attribute_definitions", str(gap.get("attribute_id"))
            ):
                findings.append(
                    _error(
                        REFERENTIAL,
                        f"$.gaps[{index}].attribute_id",
                        "gap_attribute_missing_or_inactive",
                        f"Gap Attribute is not active: {gap.get('attribute_id')}",
                    )
                )

        for index, unresolved in enumerate(result.get("unresolved_references", [])):
            class_id = unresolved.get("candidate_class_id")
            if class_id is not None and not active("object_classes", str(class_id)):
                findings.append(
                    _error(
                        REFERENTIAL,
                        f"$.unresolved_references[{index}].candidate_class_id",
                        "candidate_class_missing_or_inactive",
                        f"Candidate Class is not active: {class_id}",
                    )
                )
            context = unresolved.get("relation_context")
            if isinstance(context, Mapping):
                relation_type_id = context.get("relation_type_id")
                if not active("relation_types", str(relation_type_id)):
                    findings.append(
                        _error(
                            REFERENTIAL,
                            f"$.unresolved_references[{index}].relation_context.relation_type_id",
                            "unresolved_relation_type_missing_or_inactive",
                            f"Relation Type is not active: {relation_type_id}",
                        )
                    )

        for index, extension in enumerate(result.get("class_extensions", [])):
            class_id = extension.get("class_id")
            if not active("object_classes", str(class_id)):
                findings.append(
                    _error(
                        REFERENTIAL,
                        f"$.class_extensions[{index}].class_id",
                        "extension_class_missing_or_inactive",
                        f"Class extension Class is not active: {class_id}",
                    )
                )

        for index, proposal in enumerate(result.get("registry_proposals", [])):
            if proposal.get("proposal_kind") not in {"primary_class", "additional_class"}:
                continue
            class_id = (proposal.get("payload") or {}).get("class_id")
            if class_id is not None and not active("object_classes", str(class_id)):
                findings.append(
                    _error(
                        REFERENTIAL,
                        f"$.registry_proposals[{index}].payload.class_id",
                        "proposal_class_missing_or_inactive",
                        f"Proposed existing Class is not active: {class_id}",
                    )
                )
        return findings

    def _grounding_findings(
        self,
        result: Mapping[str, Any],
        manifest: Mapping[str, Any],
    ) -> list[ResultValidationFinding]:
        findings: list[ResultValidationFinding] = []
        evidence = manifest.get("evidence") or {}
        membership = set(evidence.get("included_evidence_ids") or [])
        item_by_id = {
            item.get("evidence_id"): item
            for item in evidence.get("items", [])
            if isinstance(item, Mapping)
        }

        referenced = collect_evidence_ids(result)
        paths_by_id: dict[str, list[str]] = {}
        role_paths: list[tuple[str, str]] = []
        for path, ref in _iter_evidence_refs(result):
            evidence_id = str(ref.get("evidence_id"))
            paths_by_id.setdefault(evidence_id, []).append(f"{path}.evidence_id")
            role_paths.append((f"{path}.role", str(ref.get("role"))))

        for role_path, role in role_paths:
            row = self.repository.db.execute(
                "SELECT status FROM evidence_roles WHERE key=?", (role,)
            ).fetchone()
            if not row or row["status"] != "active":
                findings.append(
                    _error(
                        GROUNDING_PROVENANCE,
                        role_path,
                        "evidence_role_missing_or_inactive",
                        f"Evidence role is not active: {role}",
                    )
                )

        for evidence_id in sorted(referenced):
            path = paths_by_id.get(evidence_id, ["$"])[0]
            if evidence_id not in membership:
                findings.append(
                    _error(
                        GROUNDING_PROVENANCE,
                        path,
                        "evidence_outside_package",
                        f"Evidence is not a member of the audited Package: {evidence_id}",
                    )
                )
            try:
                provenance = self.repository.source_store.evidence_provenance(evidence_id)
            except ValueError as exc:
                findings.append(
                    _error(
                        GROUNDING_PROVENANCE,
                        path,
                        "evidence_provenance_invalid",
                        f"Evidence provenance cannot be resolved for {evidence_id}: {exc}",
                    )
                )
                continue

            package_item = item_by_id.get(evidence_id)
            if package_item is None:
                if evidence_id in membership:
                    findings.append(
                        _error(
                            GROUNDING_PROVENANCE,
                            path,
                            "package_evidence_item_missing",
                            f"Package manifest has no Evidence item metadata for {evidence_id}",
                        )
                    )
                continue
            expected = (
                provenance.evidence.source_id,
                provenance.evidence.snapshot_id,
                provenance.evidence.run_id,
            )
            declared = (
                package_item.get("source_id"),
                package_item.get("snapshot_id"),
                package_item.get("normalization_run_id"),
            )
            if expected != declared:
                findings.append(
                    _error(
                        GROUNDING_PROVENANCE,
                        path,
                        "package_provenance_mismatch",
                        "Canonical Evidence provenance differs from the audited Package metadata",
                    )
                )
        return findings

    def _domain_findings(
        self,
        result: Mapping[str, Any],
        manifest: Mapping[str, Any],
    ) -> list[ResultValidationFinding]:
        findings: list[ResultValidationFinding] = []
        target = manifest.get("target") or {}
        target_id = str(target.get("object_id"))
        try:
            self.repository.object_store.get_object(target_id)
        except ValueError:
            return findings

        class_ids = (
            str(target.get("primary_class_id")),
            *tuple(str(value) for value in target.get("additional_class_ids") or []),
        )
        facets = self.repository.semantic_store.facets_for_classes(class_ids)
        attributes = self.package_store.active_attribute_definitions()
        relations = self.package_store.active_relation_types()
        contract = ObjectResultContract(
            target_object_id=target_id,
            primary_class_id=class_ids[0],
            additional_class_ids=tuple(class_ids[1:]),
            facet_ids=tuple(item.facet_id for item in facets),
            attribute_value_types={item["id"]: item["value_type"] for item in attributes},
            relation_type_ids=frozenset(item["id"] for item in relations),
            package_id=str(manifest.get("package_id")),
            package_schema_version=str(manifest.get("schema_version")),
            manifest_sha256=str((manifest.get("integrity") or {}).get("manifest_sha256")),
            base_version_id=(manifest.get("binding") or {}).get("base_version_id"),
        )
        try:
            validate_object_result(result, contract)
        except ObjectResultValidationError as exc:
            for issue in exc.issues:
                stage = (
                    REFERENTIAL
                    if issue.code in {"unknown_attribute", "unknown_relation_type"}
                    else DOMAIN_CONTRACT
                )
                findings.append(_error(stage, issue.path, issue.code, issue.message))

        for path, scope in _iter_temporal_scopes(result):
            valid_from = scope.get("valid_from")
            valid_to = scope.get("valid_to")
            if valid_from is not None and valid_to is not None:
                try:
                    if _parse_temporal(str(valid_from)) > _parse_temporal(str(valid_to)):
                        findings.append(
                            _error(
                                DOMAIN_CONTRACT,
                                path,
                                "invalid_temporal_interval",
                                "temporal_scope.valid_from must not be later than valid_to",
                            )
                        )
                except ValueError:
                    pass  # static Schema reports malformed date/date-time values first

        for index, proposal in enumerate(result.get("registry_proposals", [])):
            findings.extend(self._proposal_payload_findings(index, proposal))
        return findings

    @staticmethod
    def _proposal_payload_findings(
        index: int,
        proposal: Mapping[str, Any],
    ) -> list[ResultValidationFinding]:
        path = f"$.registry_proposals[{index}].payload"
        payload = proposal.get("payload") or {}
        kind = proposal.get("proposal_kind")
        findings: list[ResultValidationFinding] = []

        def require_text(key: str) -> None:
            value = payload.get(key)
            if not isinstance(value, str) or not value.strip():
                findings.append(
                    _error(
                        DOMAIN_CONTRACT,
                        f"{path}.{key}",
                        "registry_proposal_payload",
                        f"{kind} proposal requires non-empty payload.{key}",
                    )
                )

        if kind in {"object_name", "object_alias"}:
            require_text("value")
        elif kind in {"primary_class", "additional_class"}:
            require_text("class_id")
        elif kind in {"new_class", "new_facet", "new_attribute", "new_relation_type"}:
            require_text("key")
            require_text("name")
            if kind == "new_attribute":
                allowed = {
                    "text",
                    "integer",
                    "real",
                    "boolean",
                    "date",
                    "datetime",
                    "identifier",
                    "enum",
                    "json",
                }
                if payload.get("value_type") not in allowed:
                    findings.append(
                        _error(
                            DOMAIN_CONTRACT,
                            f"{path}.value_type",
                            "registry_proposal_payload",
                            "new_attribute proposal requires a supported payload.value_type",
                        )
                    )
            if kind == "new_class" and "assignment_policy" in payload:
                if payload.get("assignment_policy") not in {
                    "structural",
                    "primary_eligible",
                    "additional_only",
                }:
                    findings.append(
                        _error(
                            DOMAIN_CONTRACT,
                            f"{path}.assignment_policy",
                            "registry_proposal_payload",
                            "new_class assignment_policy is not recognized",
                        )
                    )
        return findings

    def _review_findings(
        self,
        result: Mapping[str, Any],
        receipt: Mapping[str, Any],
    ) -> list[ResultValidationFinding]:
        findings: list[ResultValidationFinding] = []
        status = result.get("result_status")
        if status in {"partial", "insufficient_evidence"}:
            findings.append(
                _review(
                    DOMAIN_CONTRACT,
                    "$.result_status",
                    "result_requires_review",
                    f"Result status {status!r} requires review before authoritative import",
                )
            )
        if result.get("registry_proposals"):
            findings.append(
                _review(
                    DOMAIN_CONTRACT,
                    "$.registry_proposals",
                    "registry_proposal_requires_review",
                    "Registry proposals are separate review items and are never auto-applied",
                )
            )
        if result.get("unresolved_references"):
            findings.append(
                _review(
                    DOMAIN_CONTRACT,
                    "$.unresolved_references",
                    "unresolved_reference_requires_review",
                    "Unresolved Object references require explicit identity resolution",
                )
            )
        for index, gap in enumerate(result.get("gaps", [])):
            if gap.get("kind") == "identity_ambiguity":
                findings.append(
                    _review(
                        DOMAIN_CONTRACT,
                        f"$.gaps[{index}]",
                        "identity_ambiguity_requires_review",
                        "Identity ambiguity requires explicit review",
                    )
                )
        if not self.audit.export_events(str(receipt["package_id"])):
            findings.append(
                _review(
                    BINDING_PRECONDITION,
                    "$.binding.package_id",
                    "package_export_audit_missing",
                    "Package has no explicit export audit event",
                )
            )
        return findings
