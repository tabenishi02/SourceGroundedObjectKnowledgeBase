"""Structured generation output contract for N-04 grounded generation v3."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

GROUNDED_GENERATION_OUTPUT_CONTRACT_VERSION = "sgokb.grounded-generation-output.v2"
SEMANTIC_ROLES = (
    "source_fact",
    "interpretation",
    "creative_addition",
    "context_limit",
)
PRESENTATION_ROLES = ("main", "interpretation", "creative", "context_limit")
PURPOSES = ("roleplay", "comparison", "creative")
CONTEXT_LIMIT_CODE = "material_requirements_not_satisfied"

_ID_PATTERNS = {
    "block_id": "^B[1-9][0-9]*$",
    "unit_id": "^U[1-9][0-9]*$",
    "support_ref": "^K[1-9][0-9]*$",
}

GENERATION_OUTPUT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$defs": {
        "source_fact_unit": {
            "type": "object",
            "additionalProperties": False,
            "required": ["unit_id", "semantic_role", "text", "support_refs"],
            "properties": {
                "unit_id": {"type": "string", "pattern": _ID_PATTERNS["unit_id"]},
                "semantic_role": {"const": "source_fact"},
                "text": {"type": "string", "minLength": 1},
                "support_refs": {
                    "type": "array",
                    "minItems": 1,
                    "uniqueItems": True,
                    "items": {"type": "string", "pattern": _ID_PATTERNS["support_ref"]},
                },
            },
        },
        "interpretation_unit": {
            "type": "object",
            "additionalProperties": False,
            "required": ["unit_id", "semantic_role", "text", "premise_unit_ids"],
            "properties": {
                "unit_id": {"type": "string", "pattern": _ID_PATTERNS["unit_id"]},
                "semantic_role": {"const": "interpretation"},
                "text": {"type": "string", "minLength": 1},
                "premise_unit_ids": {
                    "type": "array",
                    "minItems": 1,
                    "uniqueItems": True,
                    "items": {"type": "string", "pattern": _ID_PATTERNS["unit_id"]},
                },
            },
        },
        "creative_unit": {
            "type": "object",
            "additionalProperties": False,
            "required": ["unit_id", "semantic_role", "text"],
            "properties": {
                "unit_id": {"type": "string", "pattern": _ID_PATTERNS["unit_id"]},
                "semantic_role": {"const": "creative_addition"},
                "text": {"type": "string", "minLength": 1},
            },
        },
        "context_limit_unit": {
            "type": "object",
            "additionalProperties": False,
            "required": ["unit_id", "semantic_role", "limit_code"],
            "properties": {
                "unit_id": {"type": "string", "pattern": _ID_PATTERNS["unit_id"]},
                "semantic_role": {"const": "context_limit"},
                "limit_code": {"const": CONTEXT_LIMIT_CODE},
            },
        },
        "main_block": {
            "type": "object",
            "additionalProperties": False,
            "required": ["block_id", "presentation_role", "units"],
            "properties": {
                "block_id": {"type": "string", "pattern": _ID_PATTERNS["block_id"]},
                "presentation_role": {"const": "main"},
                "units": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"$ref": "#/$defs/source_fact_unit"},
                },
            },
        },
        "interpretation_block": {
            "type": "object",
            "additionalProperties": False,
            "required": ["block_id", "presentation_role", "units"],
            "properties": {
                "block_id": {"type": "string", "pattern": _ID_PATTERNS["block_id"]},
                "presentation_role": {"const": "interpretation"},
                "units": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"$ref": "#/$defs/interpretation_unit"},
                },
            },
        },
        "creative_block": {
            "type": "object",
            "additionalProperties": False,
            "required": ["block_id", "presentation_role", "units"],
            "properties": {
                "block_id": {"type": "string", "pattern": _ID_PATTERNS["block_id"]},
                "presentation_role": {"const": "creative"},
                "units": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"$ref": "#/$defs/creative_unit"},
                },
            },
        },
        "context_limit_block": {
            "type": "object",
            "additionalProperties": False,
            "required": ["block_id", "presentation_role", "units"],
            "properties": {
                "block_id": {"type": "string", "pattern": _ID_PATTERNS["block_id"]},
                "presentation_role": {"const": "context_limit"},
                "units": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 1,
                    "items": {"$ref": "#/$defs/context_limit_unit"},
                },
            },
        },
    },
    "type": "object",
    "additionalProperties": False,
    "required": ["contract_version", "context_fingerprint", "purpose", "blocks"],
    "properties": {
        "contract_version": {"const": GROUNDED_GENERATION_OUTPUT_CONTRACT_VERSION},
        "context_fingerprint": {"type": "string", "minLength": 1},
        "purpose": {"enum": list(PURPOSES)},
        "blocks": {
            "oneOf": [
                {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 3,
                    "items": {
                        "oneOf": [
                            {"$ref": "#/$defs/main_block"},
                            {"$ref": "#/$defs/interpretation_block"},
                            {"$ref": "#/$defs/creative_block"},
                        ]
                    },
                },
                {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 1,
                    "items": {"$ref": "#/$defs/context_limit_block"},
                },
            ]
        },
    },
}


class GenerationOutputContractError(ValueError):
    """Generated output does not satisfy sgokb.grounded-generation-output.v2."""

    code = "generation_output_contract_error"

    def __init__(
        self,
        message: str,
        *,
        failure_code: str = "schema_violation",
        json_path: str = "$",
        block_id: str | None = None,
        unit_id: str | None = None,
        failure_detail: str | None = None,
        expected_rule: str | None = None,
    ) -> None:
        super().__init__(message)
        self.failure_code = failure_code
        self.json_path = json_path
        self.block_id = block_id
        self.unit_id = unit_id
        self.failure_detail = failure_detail or message
        self.expected_rule = expected_rule


def canonical_output_json(output: dict[str, Any]) -> str:
    """Return the canonical JSON representation used for output identity binding."""

    return json.dumps(
        output,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def output_digest(output: dict[str, Any]) -> str:
    """Return SHA-256 of the parsed output envelope's canonical UTF-8 JSON bytes."""

    return hashlib.sha256(canonical_output_json(output).encode("utf-8")).hexdigest()


def generation_output_schema_hash() -> str:
    """Return the stable identity of the canonical provider/application schema."""

    payload = json.dumps(
        GENERATION_OUTPUT_SCHEMA,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def output_binding(output: dict[str, Any], *, attempt: int) -> dict[str, Any]:
    """Build the frozen candidate identity shared by validation/material/terminal/render."""

    if attempt not in {1, 2}:
        raise ValueError("grounded-generation attempt must be 1 or 2")
    return {
        "context_fingerprint": output.get("context_fingerprint"),
        "output_contract_version": output.get("contract_version"),
        "attempt": attempt,
        "output_digest": output_digest(output),
    }


def is_context_limit_output(output: dict[str, Any]) -> bool:
    blocks = output.get("blocks", [])
    return (
        isinstance(blocks, list)
        and len(blocks) == 1
        and isinstance(blocks[0], dict)
        and blocks[0].get("presentation_role") == "context_limit"
    )


def _json_path(path: Iterable[Any]) -> str:
    result = "$"
    for item in path:
        if isinstance(item, int):
            result += f"[{item}]"
        else:
            result += f".{item}"
    return result


def _payload_ids(payload: Any, path: list[Any]) -> tuple[str | None, str | None]:
    block_id: str | None = None
    unit_id: str | None = None
    if not isinstance(payload, dict):
        return block_id, unit_id
    blocks = payload.get("blocks")
    if not isinstance(blocks, list):
        return block_id, unit_id
    try:
        blocks_index = path.index("blocks")
        block_index = path[blocks_index + 1]
    except (ValueError, IndexError):
        return block_id, unit_id
    if not isinstance(block_index, int) or block_index >= len(blocks):
        return block_id, unit_id
    block = blocks[block_index]
    if not isinstance(block, dict):
        return block_id, unit_id
    value = block.get("block_id")
    if isinstance(value, str):
        block_id = value
    try:
        units_index = path.index("units", blocks_index + 2)
        unit_index = path[units_index + 1]
    except (ValueError, IndexError):
        return block_id, unit_id
    units = block.get("units")
    if (
        isinstance(unit_index, int)
        and isinstance(units, list)
        and unit_index < len(units)
        and isinstance(units[unit_index], dict)
    ):
        value = units[unit_index].get("unit_id")
        if isinstance(value, str):
            unit_id = value
    return block_id, unit_id


def _schema_failure_code(exc: ValidationError) -> str:
    path = list(exc.absolute_path)
    if exc.validator == "required":
        return "missing_required_field"
    if exc.validator == "additionalProperties":
        return "unexpected_field"
    if path == ["contract_version"] and exc.validator == "const":
        return "unknown_contract_version"
    return "schema_violation"


def parse_generation_output(raw: str | dict[str, Any]) -> dict[str, Any]:
    """Parse against the same JSON Schema exposed to the structured-output provider.

    Cross-item identity invariants that JSON Schema cannot express are validated
    explicitly by GroundingValidator V0 rather than hidden inside this parser.
    """

    if isinstance(raw, str):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise GenerationOutputContractError(
                f"Generated output is not a single valid JSON value: {exc.msg}",
                failure_code="malformed_output",
                failure_detail=exc.msg,
                expected_rule="return one JSON object and no surrounding prose",
            ) from exc
    elif isinstance(raw, dict):
        payload = raw
    else:
        raise GenerationOutputContractError(
            "Generated output must be a JSON object or JSON object string",
            failure_code="malformed_output",
            failure_detail=f"unsupported output type: {type(raw).__name__}",
            expected_rule="output type must be object or JSON object string",
        )

    if isinstance(payload, dict) and isinstance(payload.get("blocks"), list):
        roles = [
            block.get("presentation_role")
            for block in payload["blocks"]
            if isinstance(block, dict)
        ]
        if "context_limit" in roles and len(payload["blocks"]) != 1:
            raise GenerationOutputContractError(
                "context_limit output must be exclusive",
                failure_code="context_limit_mixed_output",
                json_path="$.blocks",
                expected_rule="context_limit block may not coexist with normal response blocks",
            )

    try:
        Draft202012Validator(GENERATION_OUTPUT_SCHEMA).validate(payload)
    except ValidationError as exc:
        path = list(exc.absolute_path)
        json_path = _json_path(path)
        block_id, unit_id = _payload_ids(payload, path)
        detail = f"{json_path}: {exc.message}"
        raise GenerationOutputContractError(
            detail,
            failure_code=_schema_failure_code(exc),
            json_path=json_path,
            block_id=block_id,
            unit_id=unit_id,
            failure_detail=exc.message,
            expected_rule=f"jsonschema:{exc.validator}",
        ) from exc

    return payload
