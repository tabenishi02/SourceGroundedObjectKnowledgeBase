"""Structured generation output contract for N-04 grounded generation."""

from __future__ import annotations

import json
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

GROUNDED_GENERATION_OUTPUT_CONTRACT_VERSION = "sgokb.grounded-generation-output.v1"
SEMANTIC_ROLES = (
    "source_fact",
    "interpretation",
    "creative_addition",
    "context_limit",
    "stylistic_expression",
)
PRESENTATION_ROLES = ("main", "interpretation", "creative", "context_limit")
PURPOSES = ("roleplay", "comparison", "creative")

GENERATION_OUTPUT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["contract_version", "context_fingerprint", "purpose", "blocks"],
    "properties": {
        "contract_version": {"const": GROUNDED_GENERATION_OUTPUT_CONTRACT_VERSION},
        "context_fingerprint": {"type": "string", "minLength": 1},
        "purpose": {"enum": list(PURPOSES)},
        "blocks": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["block_id", "presentation_role", "label", "units"],
                "properties": {
                    "block_id": {"type": "string", "pattern": "^B[1-9][0-9]*$"},
                    "presentation_role": {"enum": list(PRESENTATION_ROLES)},
                    "label": {"type": ["string", "null"]},
                    "units": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "unit_id",
                                "semantic_role",
                                "text",
                                "support_refs",
                            ],
                            "properties": {
                                "unit_id": {
                                    "type": "string",
                                    "pattern": "^U[1-9][0-9]*$",
                                },
                                "semantic_role": {"enum": list(SEMANTIC_ROLES)},
                                "text": {"type": "string", "minLength": 1},
                                "support_refs": {
                                    "type": "array",
                                    "uniqueItems": True,
                                    "items": {
                                        "type": "string",
                                        "pattern": "^K[1-9][0-9]*$",
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    },
}


class GenerationOutputContractError(ValueError):
    """Generated output does not satisfy sgokb.grounded-generation-output.v1."""

    code = "generation_output_contract_error"

    def __init__(self, message: str, *, failure_code: str = "schema_violation") -> None:
        super().__init__(message)
        self.failure_code = failure_code


def parse_generation_output(raw: str | dict[str, Any]) -> dict[str, Any]:
    """Parse and validate the normative structured LLM output.

    Free prose outside the JSON envelope is rejected rather than heuristically
    repaired, preserving the G-04/G-05 fail-closed contract.
    """

    if isinstance(raw, str):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise GenerationOutputContractError(
                f"Generated output is not a single valid JSON value: {exc.msg}",
                failure_code="malformed_json",
            ) from exc
    elif isinstance(raw, dict):
        payload = raw
    else:
        raise GenerationOutputContractError(
            "Generated output must be a JSON object or JSON object string",
            failure_code="invalid_output_type",
        )

    try:
        Draft202012Validator(GENERATION_OUTPUT_SCHEMA).validate(payload)
    except ValidationError as exc:
        path = ".".join(str(item) for item in exc.absolute_path)
        detail = f"{path}: {exc.message}" if path else exc.message
        raise GenerationOutputContractError(detail) from exc

    block_ids: set[str] = set()
    unit_ids: set[str] = set()
    for block in payload["blocks"]:
        block_id = block["block_id"]
        if block_id in block_ids:
            raise GenerationOutputContractError(
                f"Duplicate block_id: {block_id}",
                failure_code="duplicate_block_id",
            )
        block_ids.add(block_id)

        if block["presentation_role"] in {"interpretation", "creative"}:
            label = block["label"]
            if not isinstance(label, str) or not label.strip():
                raise GenerationOutputContractError(
                    f"{block_id} requires a visible label for separated presentation",
                    failure_code="missing_presentation_label",
                )

        for unit in block["units"]:
            unit_id = unit["unit_id"]
            if unit_id in unit_ids:
                raise GenerationOutputContractError(
                    f"Duplicate unit_id: {unit_id}",
                    failure_code="duplicate_unit_id",
                )
            unit_ids.add(unit_id)

    return payload
