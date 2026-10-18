"""Grounded Context projection for N-04 grounded generation.

This module projects deterministic Context Builder output into a context-local
K-reference namespace without mutating canonical Knowledge or changing Context
selection/budget semantics.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

GROUNDED_CONTEXT_CONTRACT_VERSION = "sgokb.grounded-context.v1"
SOURCE_CONTEXT_CONTRACT_VERSION = "sgokb.context-builder.v1"


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _evidence_refs(item: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(value) for value in item.get("evidence", [])]


class GroundedContextProjector:
    """Project selected Context Builder Knowledge into deterministic K references."""

    contract_version = GROUNDED_CONTEXT_CONTRACT_VERSION

    def project(self, context: dict[str, Any]) -> dict[str, Any]:
        source_version = context.get("context_contract_version")
        if source_version != SOURCE_CONTEXT_CONTRACT_VERSION:
            raise ValueError(
                "Grounded Context projection requires "
                f"{SOURCE_CONTEXT_CONTRACT_VERSION}; got {source_version!r}"
            )

        units: list[dict[str, Any]] = []
        ref_number = 1
        objects: list[dict[str, Any]] = []

        for object_payload in context.get("objects", []):
            object_id = object_payload["object_id"]
            resolved_version_id = object_payload["resolved_version_id"]
            objects.append(
                {
                    "object_id": object_id,
                    "name": object_payload.get("name"),
                    "requested_version_id": object_payload.get("requested_version_id"),
                    "resolved_version_id": resolved_version_id,
                    "is_current": object_payload.get("is_current"),
                }
            )

            def append_unit(
                source_kind: str,
                canonical_ref: dict[str, Any],
                content: dict[str, Any],
                *,
                facet: str | None = None,
                evidence_refs: list[dict[str, Any]] | None = None,
            ) -> None:
                nonlocal ref_number
                units.append(
                    {
                        "ref_id": f"K{ref_number}",
                        "object_id": object_id,
                        "resolved_version_id": resolved_version_id,
                        "source_kind": source_kind,
                        "canonical_ref": canonical_ref,
                        "facet": facet,
                        "content": content,
                        "evidence_refs": evidence_refs or [],
                    }
                )
                ref_number += 1

            # Object envelope facts are selected outside the J-04 Knowledge budget and are
            # therefore projected after selection without affecting budget behavior.
            if object_payload.get("name") is not None:
                append_unit(
                    "object_field",
                    {
                        "kind": "object_field",
                        "object_id": object_id,
                        "field_path": "name",
                    },
                    {"field_path": "name", "value": object_payload["name"]},
                )

            for index, alias in enumerate(object_payload.get("aliases", [])):
                append_unit(
                    "object_field",
                    {
                        "kind": "object_field",
                        "object_id": object_id,
                        "field_path": f"aliases[{index}]",
                    },
                    {"field_path": f"aliases[{index}]", "value": alias},
                )

            primary_class = object_payload.get("primary_class")
            if primary_class:
                append_unit(
                    "object_field",
                    {
                        "kind": "object_field",
                        "object_id": object_id,
                        "field_path": "primary_class",
                    },
                    {"field_path": "primary_class", "value": primary_class},
                )

            for index, class_payload in enumerate(object_payload.get("additional_classes", [])):
                append_unit(
                    "object_field",
                    {
                        "kind": "object_field",
                        "object_id": object_id,
                        "field_path": f"additional_classes[{index}]",
                    },
                    {
                        "field_path": f"additional_classes[{index}]",
                        "value": class_payload,
                    },
                )

            knowledge = object_payload.get("knowledge", {})
            for statement in knowledge.get("summary", []):
                append_unit(
                    "statement",
                    {"kind": "statement", "id": statement["statement_id"]},
                    {
                        key: statement.get(key)
                        for key in (
                            "local_key",
                            "text",
                            "derivation_kind",
                            "language",
                            "temporal_scope",
                            "attribution",
                        )
                    },
                    facet=statement.get("facet"),
                    evidence_refs=_evidence_refs(statement),
                )

            for facet_payload in knowledge.get("facets", []):
                facet_key = facet_payload.get("key")
                for statement in facet_payload.get("statements", []):
                    append_unit(
                        "statement",
                        {"kind": "statement", "id": statement["statement_id"]},
                        {
                            key: statement.get(key)
                            for key in (
                                "local_key",
                                "text",
                                "derivation_kind",
                                "language",
                                "temporal_scope",
                                "attribution",
                            )
                        },
                        facet=facet_key,
                        evidence_refs=_evidence_refs(statement),
                    )

            for attribute in knowledge.get("attributes", []):
                append_unit(
                    "attribute",
                    {
                        "kind": "attribute",
                        "id": attribute["attribute_value_id"],
                        "attribute_id": attribute.get("attribute_id"),
                    },
                    {
                        key: attribute.get(key)
                        for key in (
                            "key",
                            "name",
                            "value_type",
                            "ordinal",
                            "status",
                            "value",
                            "language",
                            "temporal_scope",
                        )
                    },
                    evidence_refs=_evidence_refs(attribute),
                )

            for relation in knowledge.get("relations", []):
                append_unit(
                    "relation",
                    {
                        "kind": "relation",
                        "id": relation["relation_id"],
                        "relation_type_id": relation.get("relation_type_id"),
                    },
                    {
                        key: relation.get(key)
                        for key in (
                            "relation_key",
                            "relation_name",
                            "subject_object_id",
                            "object_object_id",
                            "object_name",
                            "temporal_scope",
                        )
                    },
                    evidence_refs=_evidence_refs(relation),
                )

        projected = {
            "grounded_context_contract_version": self.contract_version,
            "source_context_contract_version": source_version,
            "purpose": context.get("purpose"),
            "selection_policy": context.get("selection_policy", {}),
            "objects": objects,
            "grounding_units": units,
            "budget": context.get("budget", {}),
            "warnings": list(context.get("warnings", [])),
        }
        projected["context_fingerprint"] = self.fingerprint(projected)
        return projected

    @staticmethod
    def fingerprint(grounded_context: dict[str, Any]) -> str:
        payload = {
            "grounded_context_contract_version": grounded_context.get(
                "grounded_context_contract_version"
            ),
            "source_context_contract_version": grounded_context.get(
                "source_context_contract_version"
            ),
            "purpose": grounded_context.get("purpose"),
            "selection_policy": grounded_context.get("selection_policy", {}),
            "objects": grounded_context.get("objects", []),
            "grounding_units": grounded_context.get("grounding_units", []),
        }
        return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()

    @classmethod
    def verify(cls, grounded_context: dict[str, Any]) -> bool:
        if (
            grounded_context.get("grounded_context_contract_version")
            != GROUNDED_CONTEXT_CONTRACT_VERSION
        ):
            return False
        expected = grounded_context.get("context_fingerprint")
        return isinstance(expected, str) and expected == cls.fingerprint(grounded_context)
