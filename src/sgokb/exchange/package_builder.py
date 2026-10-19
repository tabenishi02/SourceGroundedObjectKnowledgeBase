"""Build Object Evidence Package workspaces from canonical SGOKB storage."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sgokb.retrieval import EvidenceBudget, EvidencePackageSelector, ObjectEvidenceRetriever
from sgokb.storage import PackageBuildReadRepository

from .instructions import (
    INSTRUCTIONS_VERSION,
    AnalysisAttributeProfile,
    AnalysisClassProfile,
    AnalysisFacetProfile,
    AnalysisRelationProfile,
    ObjectAnalysisInstructionContext,
    render_object_analysis_instructions,
)
from .object_result import OBJECT_RESULT_SCHEMA_VERSION, load_object_result_schema
from .package_manifest import (
    MANIFEST_CANONICALIZATION,
    PACKAGE_SCHEMA_VERSION,
    new_package_id,
    validate_package_manifest,
    with_manifest_sha256,
)

DEFAULT_BUILD_ROOT = ".local/transient/package-build"


@dataclass(frozen=True, slots=True)
class PackageBuildResult:
    package_id: str
    manifest_sha256: str
    path: str
    object_id: str
    base_version_id: str | None
    evidence_count: int
    source_generation_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now() -> str:
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


def _markdown_value(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _content_fence(content: str) -> str:
    longest = max((len(match.group(0)) for match in re.finditer(r"`+", content)), default=0)
    return "`" * max(3, longest + 1)


class ObjectEvidencePackageBuilder:
    """Create a complete Package workspace without invoking a generative LLM."""

    def __init__(self, repository, embedder=None):
        self.repository = repository
        self.embedder = embedder
        self.package_store = PackageBuildReadRepository(repository.db)

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
    ) -> PackageBuildResult:
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

        carry_forward = self.package_store.current_grounding_evidence_ids(base_version_id)
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
        budget = EvidenceBudget(max_estimated_tokens, max_bytes, max_items)
        selection = EvidencePackageSelector(budget).select(
            retrieval,
            protected_evidence_ids=protected,
        )
        selected = tuple(selection["selected"])
        if not selected:
            raise ValueError("Object Evidence Package requires at least one Evidence item")

        package_id = new_package_id()
        artifacts: dict[str, bytes] = {}

        instructions = self._instructions(
            package_id,
            object_record,
            base_version_id,
            knowledge_language,
        ).encode("utf-8")
        artifacts["instructions.md"] = instructions
        artifacts["schema/object-result-v1.schema.json"] = _json_bytes(load_object_result_schema())
        if current_snapshot is not None:
            artifacts["current_object.json"] = _json_bytes(current_snapshot)

        generation_paths, evidence_files = self._render_evidence_files(selected)
        artifacts.update(evidence_files)

        files = [
            _file_entry("instructions.md", "instructions", "text/markdown", instructions),
        ]
        if current_snapshot is not None:
            raw = artifacts["current_object.json"]
            files.append(
                _file_entry("current_object.json", "current_object", "application/json", raw)
            )
        schema_raw = artifacts["schema/object-result-v1.schema.json"]
        files.append(
            _file_entry(
                "schema/object-result-v1.schema.json",
                "result_schema",
                "application/json",
                schema_raw,
            )
        )
        for path in generation_paths.values():
            files.append(_file_entry(path, "evidence", "text/markdown", artifacts[path]))

        carry_set = set(carry_forward)
        manual_set = set(manual_include)
        evidence_items = []
        included_sources: list[str] = []
        generation_members: dict[tuple[str, str, str], list[str]] = {}
        for item in selected:
            candidate = item.candidate
            generation = (candidate.source_id, candidate.snapshot_id, candidate.run_id)
            generation_members.setdefault(generation, []).append(candidate.evidence_id)
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
                    "file_path": generation_paths[generation],
                    "selected_by": item.selected_by,
                    "package_roles": roles,
                    "retrieval_reasons": list(
                        dict.fromkeys(reason.channel for reason in candidate.reasons)
                    ),
                    "related_selected_evidence_ids": list(item.related_selected_evidence_ids),
                }
            )

        source_generations = [
            {
                "source_id": source_id,
                "snapshot_id": snapshot_id,
                "normalization_run_id": run_id,
                "file_path": generation_paths[(source_id, snapshot_id, run_id)],
                "evidence_ids": generation_members[(source_id, snapshot_id, run_id)],
            }
            for source_id, snapshot_id, run_id in generation_paths
        ]

        manifest = {
            "schema_version": PACKAGE_SCHEMA_VERSION,
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
                "expected_result_schema_version": OBJECT_RESULT_SCHEMA_VERSION,
                "instructions_version": INSTRUCTIONS_VERSION,
            },
            "artifacts": {
                "instructions_path": "instructions.md",
                "result_schema_path": "schema/object-result-v1.schema.json",
                "current_object_path": (
                    "current_object.json" if current_snapshot is not None else None
                ),
            },
            "evidence": {
                "included_source_ids": included_sources,
                "included_evidence_ids": [item.candidate.evidence_id for item in selected],
                "source_generations": source_generations,
                "items": evidence_items,
            },
            "selection": {
                "token_estimator": selection["token_estimator"],
                "budget": selection["budget"],
                "usage": selection["usage"],
                "candidate_count": selection["candidate_count"],
                "selected_count": selection["selected_count"],
                "omitted_count": selection["omitted_count"],
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
        manifest = with_manifest_sha256(manifest)
        issues = validate_package_manifest(manifest)
        if issues:
            raise ValueError("Built Package manifest is invalid: " + "; ".join(issues))
        artifacts["manifest.json"] = _json_bytes(manifest)

        final = self._write_workspace(build_root, package_id, artifacts)
        return PackageBuildResult(
            package_id=package_id,
            manifest_sha256=manifest["integrity"]["manifest_sha256"],
            path=str(final),
            object_id=object_id,
            base_version_id=base_version_id,
            evidence_count=len(selected),
            source_generation_count=len(source_generations),
        )

    def _instructions(
        self,
        package_id: str,
        object_record,
        base_version_id: str | None,
        knowledge_language: str,
    ) -> str:
        object_store = self.repository.object_store
        semantic_store = self.repository.semantic_store
        primary = object_store.class_by_id(object_record.primary_class_id)
        if primary is None:
            raise ValueError("Object Primary Class is missing from Registry")
        ancestors = []
        for class_id in object_store.ancestor_class_ids(primary.class_id):
            record = object_store.class_by_id(class_id)
            if record is not None:
                ancestors.append(_class_profile(record))
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
        context = ObjectAnalysisInstructionContext(
            package_id=package_id,
            object_id=object_record.object_id,
            object_name=object_record.name,
            primary_class=_class_profile(primary),
            ancestor_classes=tuple(ancestors),
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
        return render_object_analysis_instructions(context)

    def _render_evidence_files(self, selected):
        generations: dict[tuple[str, str, str], list] = {}
        for item in selected:
            candidate = item.candidate
            key = (candidate.source_id, candidate.snapshot_id, candidate.run_id)
            generations.setdefault(key, []).append(item)
        paths = {key: f"evidence/source_{index:03d}.md" for index, key in enumerate(generations, 1)}
        artifacts = {
            paths[key]: self._render_generation(key, items).encode("utf-8")
            for key, items in generations.items()
        }
        return paths, artifacts

    def _render_generation(self, generation, items) -> str:
        source_id, snapshot_id, run_id = generation
        store = self.repository.source_store
        source = store.source_by_id(source_id)
        snapshot = store.snapshot_by_id(snapshot_id)
        association = store.association_for_object_source(
            items[0].candidate.context.get("object_id", ""), source_id
        )
        # Retrieval context does not carry object_id. Resolve the association from the
        # selected candidates only when one exists; no association is required.
        if association is None:
            association = None
        locators = items[0].candidate.context.get("locators") or []
        lines = [
            "# Source Generation",
            "",
            f"- source_id: `{source_id}`",
            f"- snapshot_id: `{snapshot_id}`",
            f"- normalization_run_id: `{run_id}`",
            f"- source_label: {_markdown_value(source.label)}",
            f"- snapshot_title: {_markdown_value(snapshot.title)}",
            f"- snapshot_captured_at: `{snapshot.captured_at}`",
            f"- locators: {_markdown_value(locators)}",
        ]
        if association and association.get("subject_relationship"):
            lines.append(
                "- subject_relationship: "
                + _markdown_value(association.get("subject_relationship"))
            )
        lines.append("")

        for item in items:
            candidate = item.candidate
            context = candidate.context
            fence = _content_fence(candidate.content)
            lines.extend(
                [
                    f"## Evidence `{candidate.evidence_id}`",
                    "",
                    f"- extraction_mode: `{context.get('extraction_mode')}`",
                    f"- language: {_markdown_value(context.get('language'))}",
                    f"- content_sha256: `{context.get('content_hash')}`",
                    f"- locations: {_markdown_value(context.get('locations') or [])}",
                    "",
                    fence,
                    candidate.content,
                    fence,
                    "",
                ]
            )
        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def _write_workspace(
        build_root: str | Path, package_id: str, artifacts: dict[str, bytes]
    ) -> Path:
        root = Path(build_root).resolve()
        root.mkdir(parents=True, exist_ok=True)
        final = root / package_id
        if final.exists():
            raise ValueError("Package build destination already exists")
        temporary = root / f".{package_id}.building-{uuid.uuid4().hex}"
        try:
            temporary.mkdir()
            for relative, raw in artifacts.items():
                target = temporary / Path(*relative.split("/"))
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            os.replace(temporary, final)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise
        return final
