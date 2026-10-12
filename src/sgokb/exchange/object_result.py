"""Object Result JSON exchange contract for SGOKB.

The static JSON Schema is the single structural contract shared by prompt/export
surfaces and the future import validator.  Registry-driven constraints are composed
on top of that same schema without making the exchange layer depend on SQLite.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from datetime import date, datetime
from importlib import resources
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker

from sgokb.domain.knowledge import AttributeValueType

OBJECT_RESULT_SCHEMA_VERSION = "sgokb.object-result/1.0"
OBJECT_RESULT_SCHEMA_ID = "urn:sgokb:schema:object-result:1.0"


@dataclass(frozen=True, slots=True)
class ResultValidationIssue:
    """One deterministic validation failure."""

    path: str
    code: str
    message: str


class ObjectResultValidationError(ValueError):
    """Raised when an Object Result violates the E-05 contract."""

    def __init__(self, issues: tuple[ResultValidationIssue, ...]):
        self.issues = issues
        summary = "; ".join(f"{issue.path or '$'}: {issue.message}" for issue in issues[:5])
        if len(issues) > 5:
            summary += f"; ... ({len(issues)} issues total)"
        super().__init__(summary)


@dataclass(frozen=True, slots=True)
class ClassExtensionContract:
    """Optional schema for genuinely class-specific payload outside the common model."""

    class_id: str
    schema_id: str
    schema: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ObjectResultContract:
    """Runtime facts used to specialize the registry-driven Object Result schema.

    The application/H-01 layer will build this from the Package manifest and canonical
    registries.  E-05 keeps this value object storage-independent so `exchange` does not
    acquire a SQLite dependency.
    """

    target_object_id: str
    primary_class_id: str
    additional_class_ids: tuple[str, ...]
    facet_ids: tuple[str, ...]
    attribute_value_types: Mapping[str, AttributeValueType | str] = field(default_factory=dict)
    relation_type_ids: frozenset[str] = frozenset()
    package_id: str | None = None
    package_schema_version: str | None = None
    manifest_sha256: str | None = None
    base_version_id: str | None = None
    class_extensions: Mapping[str, ClassExtensionContract] = field(default_factory=dict)


def _schema_path():
    return resources.files("sgokb.exchange.schemas").joinpath("object-result-v1.schema.json")


def load_object_result_schema() -> dict[str, Any]:
    """Load the canonical static Object Result JSON Schema from package data."""

    with _schema_path().open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    if schema.get("$id") != OBJECT_RESULT_SCHEMA_ID:
        raise RuntimeError("Object Result schema ID does not match code contract")
    Draft202012Validator.check_schema(schema)
    return schema


def _exact_array_contract(values: tuple[str, ...]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "minItems": len(values),
        "maxItems": len(values),
        "uniqueItems": True,
    }
    if values:
        result["items"] = {"type": "string", "enum": list(values)}
        result["allOf"] = [
            {
                "contains": {"const": value},
                "minContains": 1,
                "maxContains": 1,
            }
            for value in values
        ]
    return result


def build_object_result_schema(contract: ObjectResultContract | None = None) -> dict[str, Any]:
    """Return the static schema or a Package/Class-specialized derivative of it.

    Class specialization does not create separate handwritten schemas for all 62
    Classes.  It composes the effective Facet profile and binding preconditions into
    the canonical base schema.  Optional truly class-specific payloads remain handled
    by `ClassExtensionContract`.
    """

    schema = copy.deepcopy(load_object_result_schema())
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


def _path(parts) -> str:
    if not parts:
        return "$"
    value = "$"
    for part in parts:
        if isinstance(part, int):
            value += f"[{part}]"
        else:
            value += f".{part}"
    return value


def _schema_issues(
    result: Mapping[str, Any], schema: Mapping[str, Any]
) -> list[ResultValidationIssue]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    issues = []
    for error in sorted(validator.iter_errors(result), key=lambda item: list(item.absolute_path)):
        issues.append(
            ResultValidationIssue(
                path=_path(error.absolute_path),
                code="schema",
                message=error.message,
            )
        )
    return issues


def _iter_statements(result: Mapping[str, Any]):
    knowledge = result.get("knowledge", {})
    for statement in knowledge.get("summary", []):
        yield statement
    for facet in knowledge.get("facets", []):
        for statement in facet.get("statements", []):
            yield statement


def _duplicate_local_key_issues(result: Mapping[str, Any]) -> list[ResultValidationIssue]:
    groups = {
        "statement": list(_iter_statements(result)),
        "attribute": result.get("knowledge", {}).get("attributes", []),
        "relation": result.get("knowledge", {}).get("relations", []),
        "conflict": result.get("conflicts", []),
        "gap": result.get("gaps", []),
        "unresolved_reference": result.get("unresolved_references", []),
        "registry_proposal": result.get("registry_proposals", []),
    }
    issues: list[ResultValidationIssue] = []
    for kind, items in groups.items():
        seen: set[str] = set()
        for item in items:
            key = item.get("local_key")
            if key in seen:
                issues.append(
                    ResultValidationIssue(
                        path="$",
                        code="duplicate_local_key",
                        message=f"duplicate {kind} local_key: {key}",
                    )
                )
            if key is not None:
                seen.add(key)
    return issues


def _attribute_value_issue(
    attribute_id: str,
    value_type: AttributeValueType,
    value: Any,
) -> str | None:
    if value_type in {
        AttributeValueType.TEXT,
        AttributeValueType.IDENTIFIER,
        AttributeValueType.ENUM,
    }:
        return None if isinstance(value, str) else f"{value_type.value} requires a string"
    if value_type is AttributeValueType.INTEGER:
        return (
            None
            if isinstance(value, int) and not isinstance(value, bool)
            else "integer requires int"
        )
    if value_type is AttributeValueType.REAL:
        return (
            None
            if isinstance(value, (int, float)) and not isinstance(value, bool)
            else "real requires a number"
        )
    if value_type is AttributeValueType.BOOLEAN:
        return None if isinstance(value, bool) else "boolean requires bool"
    if value_type is AttributeValueType.DATE:
        if not isinstance(value, str):
            return "date requires an ISO date string"
        try:
            date.fromisoformat(value)
        except ValueError:
            return "date requires an ISO date string"
        return None
    if value_type is AttributeValueType.DATETIME:
        if not isinstance(value, str):
            return "datetime requires an ISO 8601 datetime string"
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return "datetime requires an ISO 8601 datetime string"
        return None
    if value_type is AttributeValueType.JSON:
        try:
            json.dumps(value, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError):
            return "json attribute value must be JSON serializable"
        return None
    return f"unsupported value type for {attribute_id}"


def _registry_contract_issues(
    result: Mapping[str, Any], contract: ObjectResultContract
) -> list[ResultValidationIssue]:
    issues: list[ResultValidationIssue] = []
    knowledge = result.get("knowledge", {})

    attribute_types = {
        key: AttributeValueType(value_type)
        for key, value_type in contract.attribute_value_types.items()
    }
    for index, attribute in enumerate(knowledge.get("attributes", [])):
        attribute_id = attribute.get("attribute_id")
        if attribute_id not in attribute_types:
            issues.append(
                ResultValidationIssue(
                    path=f"$.knowledge.attributes[{index}].attribute_id",
                    code="unknown_attribute",
                    message=f"attribute is not active/known: {attribute_id}",
                )
            )
            continue
        if attribute.get("status") == "known":
            message = _attribute_value_issue(
                attribute_id,
                attribute_types[attribute_id],
                attribute.get("value"),
            )
            if message:
                issues.append(
                    ResultValidationIssue(
                        path=f"$.knowledge.attributes[{index}].value",
                        code="attribute_type",
                        message=message,
                    )
                )

    target_id = result.get("target", {}).get("object_id")
    for index, relation in enumerate(knowledge.get("relations", [])):
        relation_type_id = relation.get("relation_type_id")
        if relation_type_id not in contract.relation_type_ids:
            issues.append(
                ResultValidationIssue(
                    path=f"$.knowledge.relations[{index}].relation_type_id",
                    code="unknown_relation_type",
                    message=f"relation type is not active/known: {relation_type_id}",
                )
            )
        if target_id not in {
            relation.get("subject_object_id"),
            relation.get("object_object_id"),
        }:
            issues.append(
                ResultValidationIssue(
                    path=f"$.knowledge.relations[{index}]",
                    code="target_not_relation_endpoint",
                    message="standard Object Result relation must include the target Object",
                )
            )

    direct_classes = {contract.primary_class_id, *contract.additional_class_ids}
    seen_extension_classes: set[str] = set()
    for index, extension in enumerate(result.get("class_extensions", [])):
        schema_id = extension.get("schema_id")
        extension_contract = contract.class_extensions.get(schema_id)
        path = f"$.class_extensions[{index}]"
        if extension_contract is None:
            issues.append(
                ResultValidationIssue(
                    path=f"{path}.schema_id",
                    code="unknown_class_extension",
                    message=f"class extension schema is not registered: {schema_id}",
                )
            )
            continue
        if extension.get("class_id") != extension_contract.class_id:
            issues.append(
                ResultValidationIssue(
                    path=f"{path}.class_id",
                    code="class_extension_mismatch",
                    message="extension class_id does not match its registered schema",
                )
            )
        if extension_contract.class_id not in direct_classes:
            issues.append(
                ResultValidationIssue(
                    path=f"{path}.class_id",
                    code="class_extension_not_applicable",
                    message="extension class is not in the Result classification snapshot",
                )
            )
        if extension_contract.class_id in seen_extension_classes:
            issues.append(
                ResultValidationIssue(
                    path=f"{path}.class_id",
                    code="duplicate_class_extension",
                    message="only one extension payload per Class is allowed",
                )
            )
        seen_extension_classes.add(extension_contract.class_id)
        for issue in _schema_issues(extension.get("data", {}), extension_contract.schema):
            issues.append(
                ResultValidationIssue(
                    path=f"{path}.data{issue.path[1:]}",
                    code="class_extension_schema",
                    message=issue.message,
                )
            )

    return issues


def _knowledge_reference_issues(result: Mapping[str, Any]) -> list[ResultValidationIssue]:
    keys = {
        "statement": {item["local_key"] for item in _iter_statements(result)},
        "attribute": {
            item["local_key"] for item in result.get("knowledge", {}).get("attributes", [])
        },
        "relation": {
            item["local_key"] for item in result.get("knowledge", {}).get("relations", [])
        },
    }
    issues: list[ResultValidationIssue] = []
    for conflict_index, conflict in enumerate(result.get("conflicts", [])):
        for ref_index, ref in enumerate(conflict.get("related_knowledge", [])):
            if ref.get("local_key") not in keys.get(ref.get("kind"), set()):
                issues.append(
                    ResultValidationIssue(
                        path=(
                            f"$.conflicts[{conflict_index}].related_knowledge"
                            f"[{ref_index}].local_key"
                        ),
                        code="unknown_local_reference",
                        message="conflict references an unknown local Knowledge key",
                    )
                )
    return issues


def validate_object_result(
    result: Mapping[str, Any],
    contract: ObjectResultContract | None = None,
) -> None:
    """Validate structural and registry-driven E-05 constraints.

    This intentionally does *not* check DB object/evidence existence, Package Evidence
    membership, provenance integrity, stale current state, or semantic quality.  H-01
    will orchestrate those layers around this shared schema contract.
    """

    schema = build_object_result_schema(contract)
    issues = _schema_issues(result, schema)
    if not issues:
        issues.extend(_duplicate_local_key_issues(result))
        issues.extend(_knowledge_reference_issues(result))
        if contract is not None:
            issues.extend(_registry_contract_issues(result, contract))
    if issues:
        raise ObjectResultValidationError(tuple(issues))


def collect_evidence_ids(result: Mapping[str, Any]) -> frozenset[str]:
    """Collect every Evidence ID referenced anywhere in an Object Result."""

    evidence_ids: set[str] = set()

    def add(items) -> None:
        for item in items:
            evidence_id = item.get("evidence_id")
            if evidence_id:
                evidence_ids.add(evidence_id)

    for statement in _iter_statements(result):
        add(statement.get("evidence", []))
    for attribute in result.get("knowledge", {}).get("attributes", []):
        add(attribute.get("evidence", []))
    for relation in result.get("knowledge", {}).get("relations", []):
        add(relation.get("evidence", []))
    for collection in ("conflicts", "gaps", "unresolved_references", "registry_proposals"):
        for item in result.get(collection, []):
            add(item.get("evidence", []))
    return frozenset(evidence_ids)
