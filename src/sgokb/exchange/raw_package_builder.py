"""Build Raw-bearing Object Evidence Package v2 workspaces."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sgokb.retrieval import EvidenceBudget, EvidencePackageSelector, ObjectEvidenceRetriever
from sgokb.storage import PackageBuildReadRepository

from .instructions import (
    AnalysisAttributeProfile,
    AnalysisClassProfile,
    AnalysisFacetProfile,
    AnalysisRelationProfile,
    ObjectAnalysisInstructionContext,
)
from .instructions_v2 import (
    INSTRUCTIONS_VERSION_V2,
    RawAnalysisInstructionContext,
    render_object_analysis_instructions_v2,
)
from .object_result_v2 import OBJECT_RESULT_SCHEMA_VERSION_V2, load_object_result_schema_v2
from .package_builder import DEFAULT_BUILD_ROOT, ObjectEvidencePackageBuilder
from .package_manifest import MANIFEST_CANONICALIZATION, new_package_id
from .package_manifest_v2 import (
    GROUNDING_CONTRACT,
    PACKAGE_SCHEMA_VERSION_V2,
    RESOLUTION_CONTRACT,
    validate_package_manifest_v2,
    with_grounding_set_sha256,
    with_manifest_sha256_v2,
)
from .raw_grounding import EvidenceRawResolver

RAW_POLICY_PROFILE = "sgokb.raw-standard/1.0"
DEFAULT_MAX_TOTAL_RAW_BYTES = 16 * 1024 * 1024
DEFAULT_MAX_SINGLE_RAW_BYTES = 8 * 1024 * 1024
DEFAULT_MAX_RAW_ARTIFACTS = 64


@dataclass(frozen=True, slots=True)
class RawPackageBuildResult:
    package_id: str
    manifest_sha256: str
    grounding_set_sha256: str
    path: str
    object_id: str
    base_version_id: str | None
    evidence_count: int
    raw_artifact_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _file_entry(path: str, role: str, media_type: str, raw: bytes) -> dict[str, Any]:
    return {
        "path": path,
        "role": role,
        "media_type": media_type,
        "size_bytes": len(raw),
        "sha256": _sha256(raw),
    }


def _class_profile(record) -> AnalysisClassProfile:
    return AnalysisClassProfile(
        class_id=record.class_id,
        key=record.key,
        name=record.name,
        description=record.description,
    )


class ObjectRawPackageBuilder:
    """Create Package v2 while retaining Evidence only as selection lineage."""

    def __init__(self, repository, embedder=None):
        self.repository = repository
        self.embedder = embedder
        self.package_store = PackageBuildReadRepository(repository.db)
        self.raw_resolver = EvidenceRawResolver(repository)

    def build(
        self,
        object_id: str,
        *,
        build_root: str | Path = DEFAULT_BUILD_ROOT,
        max_estimated_tokens: int = 12_000,
        max_bytes: int = 65_536,
        max_items: int = 64,
        max_candidates: int = 500,
        semantic: bool | None = None,
        semantic_batch_size: int = 32,
        manual_include=(),
        manual_exclude=(),
        knowledge_language: str = "ja",
        max_total_raw_bytes: int = DEFAULT_MAX_TOTAL_RAW_BYTES,
        max_single_raw_bytes: int = DEFAULT_MAX_SINGLE_RAW_BYTES,
        max_raw_artifacts: int = DEFAULT_MAX_RAW_ARTIFACTS,
    ) -> RawPackageBuildResult:
        extracted_at = _now()
        object_record = self.repository.object_store.get_object(object_id)
        if object_record.status.value != "active":
            raise ValueError("Package build requires an active Object")

        base_version_id = object_record.current_version_id
        current_snapshot = self.package_store.current_object_snapshot(object_id)
        if base_version_id is None and current_snapshot is not None:
            raise ValueError("Initial Package cannot contain current Knowledge")
        if base_version_id is not None and current_snapshot is None:
            raise ValueError("Update Package requires current Knowledge snapshot")

        carry_forward = self.package_store.current_grounding_selection_evidence_ids(base_version_id)
        manual_include = tuple(dict.fromkeys(manual_include))
        manual_exclude = tuple(dict.fromkeys(manual_exclude))
        protected = tuple(dict.fromkeys((*carry_forward, *manual_include)))
        overlap = set(protected).intersection(manual_exclude)
        if overlap:
            raise ValueError(f"Protected Evidence cannot be excluded: {sorted(overlap)[0]}")

        retrieval = ObjectEvidenceRetriever(self.repository, self.embedder).retrieve(
            object_id,
            max_candidates=max_candidates,
            semantic=semantic,
            semantic_batch_size=semantic_batch_size,
            manual_include=protected,
            manual_exclude=manual_exclude,
        )
        selection = EvidencePackageSelector(
            EvidenceBudget(max_estimated_tokens, max_bytes, max_items)
        ).select(retrieval, protected_evidence_ids=protected)
        selected = tuple(selection["selected"])
        if not selected:
            raise ValueError("Object Evidence Package requires at least one Evidence item")

        evidence_ids = tuple(item.candidate.evidence_id for item in selected)
        resolution = self.raw_resolver.resolve(evidence_ids)
        raw_count = len(resolution.artifacts)
        total_raw_bytes = sum(item.byte_size for item in resolution.artifacts)
        largest_raw_bytes = max(item.byte_size for item in resolution.artifacts)
        if raw_count > max_raw_artifacts:
            raise ValueError("Raw grounding artifact count exceeds materialization budget")
        if total_raw_bytes > max_total_raw_bytes:
            raise ValueError("Raw grounding total bytes exceed materialization budget")
        if largest_raw_bytes > max_single_raw_bytes:
            raise ValueError("Raw grounding item exceeds materialization budget")

        for item in resolution.artifacts:
            if not _media_supported(item.media_type):
                raise ValueError(
                    f"Raw Artifact media type is unsupported by {RAW_POLICY_PROFILE}: "
                    f"{item.raw_artifact_id}:{item.media_type!r}"
                )

        raw_paths = {
            item.raw_artifact_id: f"raw/artifact_{index:04d}/payload"
            for index, item in enumerate(resolution.artifacts, 1)
        }
        raw_grounding = {
            "resolution_contract": RESOLUTION_CONTRACT,
            "included_raw_artifact_ids": list(resolution.included_raw_artifact_ids),
            "artifacts": [
                item.manifest_dict(raw_paths[item.raw_artifact_id])
                for item in resolution.artifacts
            ],
            "evidence_bindings": [binding.to_dict() for binding in resolution.bindings],
            "integrity": {
                "hash_algorithm": "sha256",
                "canonicalization": MANIFEST_CANONICALIZATION,
                "grounding_set_sha256": "0" * 64,
            },
        }
        raw_grounding = with_grounding_set_sha256(raw_grounding)
        grounding_set_sha256 = raw_grounding["integrity"]["grounding_set_sha256"]

        package_id = new_package_id()
        analysis_context = self._analysis_context(
            package_id, object_record, base_version_id, knowledge_language
        )
        instructions = render_object_analysis_instructions_v2(
            RawAnalysisInstructionContext(
                analysis=analysis_context,
                raw_artifact_ids=resolution.included_raw_artifact_ids,
                grounding_set_sha256=grounding_set_sha256,
            )
        ).encode("utf-8")
        schema_raw = _json_bytes(load_object_result_schema_v2())

        artifacts: dict[str, bytes] = {
            "instructions.md": instructions,
            "schema/object-result-v2.schema.json": schema_raw,
        }
        if current_snapshot is not None:
            artifacts["current_object.json"] = _json_bytes(current_snapshot)
        for item in resolution.artifacts:
            artifacts[raw_paths[item.raw_artifact_id]] = self.raw_resolver.byte_reader.read(item)

        files = [_file_entry("instructions.md", "instructions", "text/markdown", instructions)]
        if current_snapshot is not None:
            current_raw = artifacts["current_object.json"]
            files.append(
                _file_entry("current_object.json", "current_object", "application/json", current_raw)
            )
        files.append(
            _file_entry(
                "schema/object-result-v2.schema.json",
                "result_schema",
                "application/json",
                schema_raw,
            )
        )
        for item in resolution.artifacts:
            path = raw_paths[item.raw_artifact_id]
            files.append(
                _file_entry(
                    path,
                    "raw_grounding",
                    item.media_type or "application/octet-stream",
                    artifacts[path],
                )
            )

        carry_set = set(carry_forward)
        manual_set = set(manual_include)
        evidence_items = []
        included_sources: list[str] = []
        for item in selected:
            candidate = item.candidate
            if candidate.source_id not in included_sources:
                included_sources.append(candidate.source_id)
            roles = []
            if candidate.evidence_id in carry_set:
                roles.append("carry_forward")
            if candidate.evidence_id in manual_set:
                roles.append("manual_include")
            if not roles:
                roles.append("retrieved")
            evidence_items.append(
                {
                    "evidence_id": candidate.evidence_id,
                    "source_id": candidate.source_id,
                    "snapshot_id": candidate.snapshot_id,
                    "normalization_run_id": candidate.run_id,
                    "selected_by": item.selected_by,
                    "package_roles": roles,
                    "retrieval_reasons": list(
                        dict.fromkeys(reason.channel for reason in candidate.reasons)
                    ),
                    "related_selected_evidence_ids": list(item.related_selected_evidence_ids),
                }
            )

        manifest = {
            "schema_version": PACKAGE_SCHEMA_VERSION_V2,
            "package_id": package_id,
            "created_at": _now(),
            "extracted_at": extracted_at,
            "target": {
                "object_id": object_record.object_id,
                "primary_class_id": object_record.primary_class_id,
                "additional_class_ids": list(object_record.additional_class_ids),
                "name": object_record.name,
                "aliases": [alias.value for alias in object_record.aliases],
            },
            "binding": {
                "base_version_id": base_version_id,
                "expected_result_schema_version": OBJECT_RESULT_SCHEMA_VERSION_V2,
                "instructions_version": INSTRUCTIONS_VERSION_V2,
                "grounding_contract": GROUNDING_CONTRACT,
            },
            "artifacts": {
                "instructions_path": "instructions.md",
                "result_schema_path": "schema/object-result-v2.schema.json",
                "current_object_path": (
                    "current_object.json" if current_snapshot is not None else None
                ),
            },
            "evidence": {
                "included_source_ids": included_sources,
                "included_evidence_ids": evidence_ids,
                "items": evidence_items,
            },
            "raw_grounding": raw_grounding,
            "selection": {
                "token_estimator": selection["token_estimator"],
                "budget": selection["budget"],
                "usage": selection["usage"],
                "candidate_count": selection["candidate_count"],
                "selected_count": selection["selected_count"],
                "omitted_count": selection["omitted_count"],
            },
            "materialization": {
                "policy_profile": RAW_POLICY_PROFILE,
                "budget": {
                    "max_total_raw_bytes": max_total_raw_bytes,
                    "max_single_raw_bytes": max_single_raw_bytes,
                    "max_raw_artifacts": max_raw_artifacts,
                },
                "usage": {
                    "total_raw_bytes": total_raw_bytes,
                    "largest_raw_bytes": largest_raw_bytes,
                    "raw_artifact_count": raw_count,
                    "selected_evidence_count": len(selected),
                    "source_count": len(included_sources),
                },
            },
            "files": files,
            "warnings": [],
            "export_preflight": {
                "disposition": "allow",
                "reasons": [],
                "credential_material_included": False,
            },
            "integrity": {
                "hash_algorithm": "sha256",
                "canonicalization": MANIFEST_CANONICALIZATION,
                "manifest_sha256": "0" * 64,
            },
        }
        manifest = with_manifest_sha256_v2(manifest)
        issues = validate_package_manifest_v2(manifest)
        if issues:
            raise ValueError("Built Package v2 manifest is invalid: " + "; ".join(issues))
        artifacts["manifest.json"] = _json_bytes(manifest)
        final = ObjectEvidencePackageBuilder._write_workspace(build_root, package_id, artifacts)
        return RawPackageBuildResult(
            package_id=package_id,
            manifest_sha256=manifest["integrity"]["manifest_sha256"],
            grounding_set_sha256=grounding_set_sha256,
            path=str(final),
            object_id=object_id,
            base_version_id=base_version_id,
            evidence_count=len(selected),
            raw_artifact_count=raw_count,
        )

    def _analysis_context(
        self, package_id, object_record, base_version_id, knowledge_language
    ) -> ObjectAnalysisInstructionContext:
        object_store = self.repository.object_store
        semantic_store = self.repository.semantic_store
        primary = object_store.class_by_id(object_record.primary_class_id)
        if primary is None:
            raise ValueError("Object Primary Class is missing from Registry")
        ancestors = tuple(
            _class_profile(record)
            for class_id in object_store.ancestor_class_ids(primary.class_id)
            if (record := object_store.class_by_id(class_id)) is not None
        )
        additional = []
        for class_id in object_record.additional_class_ids:
            record = object_store.class_by_id(class_id)
            if record is None:
                raise ValueError(f"Object Additional Class is missing from Registry: {class_id}")
            additional.append(_class_profile(record))
        facets = semantic_store.facets_for_classes(
            (object_record.primary_class_id, *object_record.additional_class_ids)
        )
        attributes = self.package_store.active_attribute_definitions()
        relations = self.package_store.active_relation_types()
        return ObjectAnalysisInstructionContext(
            package_id=package_id,
            object_id=object_record.object_id,
            object_name=object_record.name,
            primary_class=_class_profile(primary),
            ancestor_classes=ancestors,
            additional_classes=tuple(additional),
            effective_facets=tuple(
                AnalysisFacetProfile(
                    facet_id=item.facet_id,
                    key=item.key,
                    name=item.name,
                    description=item.description,
                )
                for item in facets
            ),
            allowed_attributes=tuple(
                AnalysisAttributeProfile(
                    attribute_id=item["id"],
                    key=item["key"],
                    name=item["name"],
                    value_type=item["value_type"],
                    description=item["description"],
                )
                for item in attributes
            ),
            allowed_relations=tuple(
                AnalysisRelationProfile(
                    relation_type_id=item["id"],
                    key=item["key"],
                    name=item["name"],
                    description=item["description"],
                )
                for item in relations
            ),
            base_version_id=base_version_id,
            knowledge_language=knowledge_language,
        )


def _media_supported(media_type: str | None) -> bool:
    value = (media_type or "").lower()
    return value.startswith("text/") or value in {
        "application/json",
        "application/xml",
    }
