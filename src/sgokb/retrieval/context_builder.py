"""Deterministic Knowledge context selection for Phase J / J-04.

The Context Builder is intentionally inference-free. It receives already-resolved
Object Knowledge read models and selects a stable subset according to a named
purpose profile, optional explicit Facet override, and a character budget.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable

CONTEXT_BUILDER_CONTRACT_VERSION = "sgokb.context-builder.v1"
CONTEXT_DEFAULT_MAX_CHARACTERS = 12_000
CONTEXT_MAX_CHARACTERS = 200_000
CONTEXT_MAX_OBJECTS = 20


@dataclass(frozen=True, slots=True)
class ContextPurposeProfile:
    key: str
    facet_priority: tuple[str, ...]
    include_attributes: bool
    include_relations: bool
    include_evidence_refs: bool


_GENERAL_FACETS = (
    "overall",
    "definition",
    "background",
    "properties",
    "purpose",
    "history",
    "relationships",
    "role",
    "themes",
    "function",
    "usage",
    "significance",
)

_ROLEPLAY_FACETS = (
    "overall",
    "background",
    "appearance",
    "personality",
    "values",
    "motivation",
    "behavior",
    "relationships",
    "role",
    "abilities",
    "worldview",
    "setting",
    "culture",
)

_COMPARISON_FACETS = (
    "overall",
    "definition",
    "properties",
    "values",
    "themes",
    "behavior",
    "relationships",
    "purpose",
    "history",
    "structure",
    "culture",
    "scope",
    "chronology",
    "significance",
    "function",
    "usage",
    "mechanism",
    "causes",
    "conditions",
    "effects",
    "requirements",
    "constraints",
    "rules",
    "distribution",
    "manifestations",
)

_ANALYSIS_FACETS = (
    "overall",
    "definition",
    "background",
    "history",
    "structure",
    "properties",
    "purpose",
    "function",
    "mechanism",
    "causes",
    "conditions",
    "effects",
    "requirements",
    "constraints",
    "rules",
    "scope",
    "chronology",
    "changes",
    "relationships",
    "values",
    "themes",
    "worldview",
    "narrative",
    "interpretations",
    "implications",
    "significance",
    "production",
    "reception",
    "usage",
    "examples",
)

_CREATIVE_FACETS = (
    "overall",
    "background",
    "appearance",
    "personality",
    "values",
    "motivation",
    "behavior",
    "relationships",
    "role",
    "abilities",
    "themes",
    "worldview",
    "narrative",
    "tone",
    "characters",
    "setting",
    "culture",
    "symbols",
    "significance",
)

CONTEXT_PURPOSE_PROFILES: dict[str, ContextPurposeProfile] = {
    "general": ContextPurposeProfile(
        key="general",
        facet_priority=_GENERAL_FACETS,
        include_attributes=True,
        include_relations=True,
        include_evidence_refs=True,
    ),
    "roleplay": ContextPurposeProfile(
        key="roleplay",
        facet_priority=_ROLEPLAY_FACETS,
        include_attributes=True,
        include_relations=True,
        include_evidence_refs=False,
    ),
    "comparison": ContextPurposeProfile(
        key="comparison",
        facet_priority=_COMPARISON_FACETS,
        include_attributes=True,
        include_relations=False,
        include_evidence_refs=True,
    ),
    "analysis": ContextPurposeProfile(
        key="analysis",
        facet_priority=_ANALYSIS_FACETS,
        include_attributes=True,
        include_relations=True,
        include_evidence_refs=True,
    ),
    "creative": ContextPurposeProfile(
        key="creative",
        facet_priority=_CREATIVE_FACETS,
        include_attributes=True,
        include_relations=True,
        include_evidence_refs=False,
    ),
}


def context_purpose_profile(purpose: str) -> ContextPurposeProfile:
    try:
        return CONTEXT_PURPOSE_PROFILES[purpose]
    except KeyError as exc:
        allowed = ", ".join(CONTEXT_PURPOSE_PROFILES)
        raise ValueError(f"Unknown Context purpose: {purpose}. Expected one of: {allowed}") from exc


def context_facets_for_purpose(
    purpose: str,
    explicit_facets: Iterable[str] | None = None,
) -> tuple[str, ...]:
    profile = context_purpose_profile(purpose)
    if explicit_facets is None:
        return profile.facet_priority
    values = tuple(dict.fromkeys(value.strip() for value in explicit_facets if value.strip()))
    return values


def _item_cost(value: Any) -> int:
    return len(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def _without_evidence(value: dict[str, Any]) -> dict[str, Any]:
    result = dict(value)
    if "evidence" in result:
        result["evidence"] = []
    return result


class _Budget:
    __slots__ = ("limit", "used", "omitted")

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.used = 0
        self.omitted = 0

    def take(self, value: dict[str, Any]) -> dict[str, Any] | None:
        cost = _item_cost(value)
        if self.used + cost > self.limit:
            self.omitted += 1
            return None
        self.used += cost
        return value


class ContextBuilder:
    """Select deterministic Object Knowledge context without model inference."""

    contract_version = CONTEXT_BUILDER_CONTRACT_VERSION

    def build(
        self,
        objects: Iterable[dict[str, Any]],
        *,
        purpose: str = "general",
        facets: Iterable[str] | None = None,
        max_characters: int = CONTEXT_DEFAULT_MAX_CHARACTERS,
        include_attributes: bool | None = None,
        include_relations: bool | None = None,
        include_evidence_refs: bool | None = None,
    ) -> dict[str, Any]:
        values = tuple(objects)
        if not values:
            raise ValueError("Context Builder requires at least one Object")
        if len(values) > CONTEXT_MAX_OBJECTS:
            raise ValueError(f"Context Builder supports at most {CONTEXT_MAX_OBJECTS} Objects")
        if not 512 <= max_characters <= CONTEXT_MAX_CHARACTERS:
            raise ValueError(f"Context max_characters must be 512..{CONTEXT_MAX_CHARACTERS}")

        profile = context_purpose_profile(purpose)
        selected_facets = context_facets_for_purpose(purpose, facets)
        resolved_attributes = (
            profile.include_attributes if include_attributes is None else include_attributes
        )
        resolved_relations = (
            profile.include_relations if include_relations is None else include_relations
        )
        resolved_evidence = (
            profile.include_evidence_refs
            if include_evidence_refs is None
            else include_evidence_refs
        )

        base = max_characters // len(values)
        remainder = max_characters % len(values)
        output_objects: list[dict[str, Any]] = []
        total_used = 0
        total_omitted = 0
        for index, object_payload in enumerate(values):
            object_limit = base + (1 if index < remainder else 0)
            built = self._build_object(
                object_payload,
                selected_facets=selected_facets,
                include_attributes=resolved_attributes,
                include_relations=resolved_relations,
                include_evidence_refs=resolved_evidence,
                budget_limit=object_limit,
            )
            output_objects.append(built)
            total_used += built["budget"]["used_characters"]
            total_omitted += built["budget"]["omitted_items"]

        return {
            "context_contract_version": self.contract_version,
            "purpose": purpose,
            "selection_policy": {
                "facet_source": "explicit" if facets is not None else "purpose_profile",
                "facet_priority": list(selected_facets),
                "include_summary": True,
                "include_attributes": resolved_attributes,
                "include_relations": resolved_relations,
                "include_evidence_refs": resolved_evidence,
                "budget_metric": "serialized_json_characters",
                "budget_strategy": "equal_share_per_object",
                "partial_statement_truncation": False,
            },
            "objects": output_objects,
            "budget": {
                "metric": "serialized_json_characters",
                "limit_characters": max_characters,
                "used_characters": total_used,
                "omitted_items": total_omitted,
                "truncated": total_omitted > 0,
            },
            "warnings": [],
        }

    def _build_object(
        self,
        payload: dict[str, Any],
        *,
        selected_facets: tuple[str, ...],
        include_attributes: bool,
        include_relations: bool,
        include_evidence_refs: bool,
        budget_limit: int,
    ) -> dict[str, Any]:
        budget = _Budget(budget_limit)
        knowledge = payload.get("knowledge", {})

        summary: list[dict[str, Any]] = []
        omitted_summary = 0
        for item in knowledge.get("summary", []):
            candidate = dict(item) if include_evidence_refs else _without_evidence(item)
            accepted = budget.take(candidate)
            if accepted is None:
                omitted_summary += 1
            else:
                summary.append(accepted)

        available_facets = {item["key"]: item for item in knowledge.get("facets", [])}
        facets_out: list[dict[str, Any]] = []
        for key in selected_facets:
            source = available_facets.get(key)
            if source is None:
                continue
            statements: list[dict[str, Any]] = []
            omitted = 0
            for item in source.get("statements", []):
                candidate = dict(item) if include_evidence_refs else _without_evidence(item)
                accepted = budget.take(candidate)
                if accepted is None:
                    omitted += 1
                else:
                    statements.append(accepted)
            facets_out.append(
                {
                    "facet_id": source.get("facet_id"),
                    "key": source["key"],
                    "name": source.get("name"),
                    "status": source.get("status"),
                    "statements": statements,
                    "omitted_statement_count": omitted,
                }
            )

        attributes: list[dict[str, Any]] = []
        omitted_attributes = 0
        if include_attributes:
            for item in knowledge.get("attributes", []):
                candidate = dict(item) if include_evidence_refs else _without_evidence(item)
                accepted = budget.take(candidate)
                if accepted is None:
                    omitted_attributes += 1
                else:
                    attributes.append(accepted)

        relations: list[dict[str, Any]] = []
        omitted_relations = 0
        if include_relations:
            for item in knowledge.get("relations", []):
                candidate = dict(item) if include_evidence_refs else _without_evidence(item)
                accepted = budget.take(candidate)
                if accepted is None:
                    omitted_relations += 1
                else:
                    relations.append(accepted)

        included_facet_keys = [item["key"] for item in facets_out]
        return {
            "object_id": payload["object_id"],
            "name": payload.get("name"),
            "aliases": payload.get("aliases", []),
            "object_status": payload.get("object_status"),
            "requested_version_id": payload.get("requested_version_id"),
            "resolved_version_id": payload["resolved_version_id"],
            "is_current": payload["is_current"],
            "primary_class": payload.get("primary_class"),
            "additional_classes": payload.get("additional_classes", []),
            "context_scope": {
                "requested_facets": list(selected_facets),
                "included_facets": included_facet_keys,
                "include_attributes": include_attributes,
                "include_relations": include_relations,
                "include_evidence_refs": include_evidence_refs,
            },
            "knowledge": {
                "default_language": knowledge.get("default_language"),
                "result_status": knowledge.get("result_status"),
                "summary": summary,
                "facets": facets_out,
                "attributes": attributes,
                "relations": relations,
            },
            "omitted": {
                "summary_items": omitted_summary,
                "attribute_items": omitted_attributes,
                "relation_items": omitted_relations,
                "unselected_available_facets": [
                    item["key"]
                    for item in knowledge.get("facets", [])
                    if item["key"] not in selected_facets
                ],
            },
            "budget": {
                "limit_characters": budget.limit,
                "used_characters": budget.used,
                "omitted_items": budget.omitted,
                "truncated": budget.omitted > 0,
            },
            "warnings": list(payload.get("warnings", [])),
        }
