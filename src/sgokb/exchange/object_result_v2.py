"""Object Result v2 structural and registry-driven contract."""

from __future__ import annotations

import copy
import json
from importlib import resources
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from .object_result import (
    ObjectResultContract,
    ObjectResultValidationError,
    _duplicate_local_key_issues,
    _exact_array_contract,
    _knowledge_reference_issues,
    _registry_contract_issues,
    _schema_issues,
)

OBJECT_RESULT_SCHEMA_VERSION_V2 = "sgokb.object-result/2.0"
OBJECT_RESULT_SCHEMA_ID_V2 = "urn:sgokb:schema:object-result:2.0"


def _schema_path():
    return resources.files("sgokb.exchange.schemas").joinpath("object-result-v2.schema.json")


def load_object_result_schema_v2() -> dict[str, Any]:
    with _schema_path().open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    if schema.get("$id") != OBJECT_RESULT_SCHEMA_ID_V2:
        raise RuntimeError("Object Result v2 schema ID does not match code contract")
    Draft202012Validator.check_schema(schema)
    return schema


def build_object_result_schema_v2(
    contract: ObjectResultContract | None = None,
) -> dict[str, Any]:
    schema = copy.deepcopy(load_object_result_schema_v2())
    if contract is None:
        return schema

    target = schema["properties"]["target"]["properties"]
    target["object_id"] = {"type": "string", "const": contract.target_object_id}
    target["primary_class_id"] = {"type": "string", "const": contract.primary_class_id}
    target["additional_class_ids"].update(
        _exact_array_contract(tuple(dict.fromkeys(contract.additional_class_ids)))
    )

    binding = schema["properties"]["binding"]["properties"]
    for key, value in (
        ("package_id", contract.package_id),
        ("package_schema_version", contract.package_schema_version),
        ("manifest_sha256", contract.manifest_sha256),
    ):
        if value is not None:
            binding[key] = {"type": "string", "const": value}
    if contract.base_version_id is not None:
        binding["base_version_id"] = {"type": "string", "const": contract.base_version_id}
    else:
        binding["base_version_id"] = {"type": "null"}

    facet_ids = tuple(dict.fromkeys(contract.facet_ids))
    facets = schema["properties"]["knowledge"]["properties"]["facets"]
    facets["minItems"] = len(facet_ids)
    facets["maxItems"] = len(facet_ids)
    if facet_ids:
        facets["items"] = {
            "allOf": [
                {"$ref": "#/$defs/facet"},
                {"properties": {"facet_id": {"enum": list(facet_ids)}}},
            ]
        }
        facets["allOf"] = [
            {
                "contains": {
                    "type": "object",
                    "properties": {"facet_id": {"const": facet_id}},
                    "required": ["facet_id"],
                },
                "minContains": 1,
                "maxContains": 1,
            }
            for facet_id in facet_ids
        ]
    else:
        facets["items"] = False
    return schema


def validate_object_result_v2(
    result: Mapping[str, Any], contract: ObjectResultContract | None = None
) -> None:
    schema = build_object_result_schema_v2(contract)
    issues = _schema_issues(result, schema)
    if not issues:
        issues.extend(_duplicate_local_key_issues(result))
        issues.extend(_knowledge_reference_issues(result))
        if contract is not None:
            issues.extend(_registry_contract_issues(result, contract))
    if issues:
        raise ObjectResultValidationError(tuple(issues))


def collect_raw_grounding_ids(result: Mapping[str, Any]) -> frozenset[str]:
    identifiers: set[str] = set()
    for _, ref in iter_raw_grounding_refs(result):
        value = ref.get("raw_artifact_id")
        if value:
            identifiers.add(str(value))
    return frozenset(identifiers)


def iter_raw_grounding_refs(result: Mapping[str, Any]):
    knowledge = result.get("knowledge", {})
    for index, statement in enumerate(knowledge.get("summary", [])):
        yield from _item_grounding(f"$.knowledge.summary[{index}]", statement)
    for facet_index, facet in enumerate(knowledge.get("facets", [])):
        for statement_index, statement in enumerate(facet.get("statements", [])):
            yield from _item_grounding(
                f"$.knowledge.facets[{facet_index}].statements[{statement_index}]", statement
            )
    for collection in ("attributes", "relations"):
        for index, item in enumerate(knowledge.get(collection, [])):
            yield from _item_grounding(f"$.knowledge.{collection}[{index}]", item)
    for collection in ("conflicts", "gaps", "unresolved_references", "registry_proposals"):
        for index, item in enumerate(result.get(collection, [])):
            yield from _item_grounding(f"$.{collection}[{index}]", item)


def _item_grounding(path: str, item: Mapping[str, Any]):
    for index, ref in enumerate(item.get("grounding", [])):
        yield f"{path}.grounding[{index}]", ref
