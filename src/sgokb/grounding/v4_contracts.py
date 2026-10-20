"""Frozen v4 grounded-generation contracts and structural parsing.

The historical v2/v3 output/request contracts remain in their original modules.
This module implements only the G-23F frozen v4 contracts.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from jsonschema import Draft202012Validator

from .context import GROUNDED_CONTEXT_CONTRACT_VERSION, GroundedContextProjector

STAGE1_REQUEST_VERSION = "sgokb.stage1-grounded-content-request.v1"
STAGE1_PROVIDER_OUTPUT_VERSION = "sgokb.stage1-provider-output.v1"
STRUCTURED_PROPOSITION_VERSION = "sgokb.structured-proposition.v1-candidate"
VALIDATION_RECORD_VERSION = "sgokb.v4-validation-record.v1"
CERTIFIED_CONTENT_VERSION = "sgokb.certified-content.v1"
STAGE2_REQUEST_VERSION = "sgokb.stage2-presentation-request.v1"
STAGE2_PROVIDER_OUTPUT_VERSION = "sgokb.stage2-provider-output.v1"
RETRY_FEEDBACK_VERSION = "sgokb.stage-local-retry-feedback.v1"
VALIDATED_PLAN_VERSION = "sgokb.validated-presentation-plan.v1"
SYSTEM_CONTEXT_LIMIT_VERSION = "sgokb.system-context-limit.v1"
V4_RUN_VERSION = "sgokb.grounded-generation-v4-run.v1"

PATH_STAGE1_FACT = "stage1_fact_candidate"
PATH_CERTIFIED_FACT = "certified_fact_materialization"
PATH_STAGE2_INTERPRETATION = "stage2_interpretation_candidate"
PATH_STAGE2_CREATIVE = "stage2_creative_candidate"
PATH_SYSTEM_CONTEXT_LIMIT = "system_context_limit"

ROLE_SOURCE_FACT = "source_fact"
ROLE_INTERPRETATION = "interpretation"
ROLE_CREATIVE = "creative_addition"
ROLE_CONTEXT_LIMIT = "context_limit"

PROVIDER_COMPLETE = "PROVIDER_COMPLETE"
PROVIDER_INCOMPLETE = "PROVIDER_INCOMPLETE"
PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"

PATH_ROLE_MAP = {
    PATH_STAGE1_FACT: ROLE_SOURCE_FACT,
    PATH_CERTIFIED_FACT: ROLE_SOURCE_FACT,
    PATH_STAGE2_INTERPRETATION: ROLE_INTERPRETATION,
    PATH_STAGE2_CREATIVE: ROLE_CREATIVE,
    PATH_SYSTEM_CONTEXT_LIMIT: ROLE_CONTEXT_LIMIT,
}

PURPOSE_ALLOWED_OUTPUT_KINDS = {
    "roleplay": ("certified_fact", "interpretation"),
    "comparison": ("certified_fact", "interpretation"),
    "creative": ("certified_fact", "interpretation", "creative"),
}


class V4ContractError(ValueError):
    """Raised when a v4 application-owned contract is violated."""

    def __init__(self, code: str, message: str, *, json_path: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.json_path = json_path


class V4ProviderRuntimeError(RuntimeError):
    """Fail-closed provider/runtime failure that must not become semantic repair."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def require_complete_provider_response(response: dict[str, Any]) -> Any:
    status = response.get("status")
    if status == PROVIDER_COMPLETE:
        if "raw_output" not in response:
            raise V4ProviderRuntimeError(
                "PROVIDER_MISSING_PAYLOAD",
                "complete provider response has no raw_output",
            )
        return response["raw_output"]
    if status == PROVIDER_INCOMPLETE:
        raise V4ProviderRuntimeError(
            "PROVIDER_INCOMPLETE",
            "provider output is incomplete and cannot be parsed",
        )
    if status == PROVIDER_UNAVAILABLE:
        raise V4ProviderRuntimeError(
            "PROVIDER_UNAVAILABLE",
            "provider/runtime is unavailable",
        )
    raise V4ProviderRuntimeError(
        "PROVIDER_STATUS_INVALID",
        f"unknown provider status: {status!r}",
    )


def canonical_json_bytes(value: Any) -> bytes:
    """Return canonical UTF-8 JSON bytes for deterministic identity hashing."""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def digest_object(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def new_application_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _schema_error(instance: Any, schema: dict[str, Any]) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda item: list(item.path))
    error = next(iter(errors), None)
    if error is None:
        return
    path = "$"
    for part in error.absolute_path:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}"
    raise V4ContractError("PROVIDER_SCHEMA_CONTRACT_VIOLATION", error.message, json_path=path)


def _ensure_non_duplicate_strings(
    values: list[str],
    *,
    code: str,
    json_path: str,
) -> None:
    if len(values) != len(set(values)):
        raise V4ContractError(code, f"duplicate identifier in {json_path}", json_path=json_path)


def stage1_provider_schema(
    *,
    allowed_support_refs: list[str],
    max_candidates: int,
) -> dict[str, Any]:
    if max_candidates < 0:
        raise ValueError("max_candidates must be >= 0")
    refs = list(dict.fromkeys(allowed_support_refs))
    support_ref_item: dict[str, Any] = {"type": "string"}
    if refs:
        support_ref_item["enum"] = refs
    candidate_schema: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "required": ["claim_text", "support_refs"],
        "properties": {
            "claim_text": {"type": "string", "minLength": 1},
            "support_refs": {
                "type": "array",
                "minItems": 1,
                "items": support_ref_item,
            },
        },
    }
    effective_max = max_candidates if refs else 0
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["candidates"],
        "properties": {
            "candidates": {
                "type": "array",
                "minItems": 0,
                "maxItems": effective_max,
                "items": candidate_schema,
            }
        },
    }


def stage2_provider_schema(
    *,
    purpose: str,
    allowed_output_kinds: list[str],
    certified_fact_ids: list[str],
) -> dict[str, Any]:
    allowed = set(allowed_output_kinds)
    ids = list(dict.fromkeys(certified_fact_ids))
    alternatives: list[dict[str, Any]] = []

    if ids and "certified_fact" in allowed:
        alternatives.append(
            {
                "type": "object",
                "additionalProperties": False,
                "required": ["block_kind", "certified_fact_ids"],
                "properties": {
                    "block_kind": {"const": "main"},
                    "certified_fact_ids": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string", "enum": ids},
                    },
                },
            }
        )
    if ids and "interpretation" in allowed:
        alternatives.append(
            {
                "type": "object",
                "additionalProperties": False,
                "required": ["block_kind", "candidates"],
                "properties": {
                    "block_kind": {"const": "interpretation"},
                    "candidates": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["claim_text", "premise_fact_ids"],
                            "properties": {
                                "claim_text": {"type": "string", "minLength": 1},
                                "premise_fact_ids": {
                                    "type": "array",
                                    "minItems": 1,
                                    "items": {"type": "string", "enum": ids},
                                },
                            },
                        },
                    },
                },
            }
        )
    if purpose == "creative" and "creative" in allowed:
        alternatives.append(
            {
                "type": "object",
                "additionalProperties": False,
                "required": ["block_kind", "candidates"],
                "properties": {
                    "block_kind": {"const": "creative"},
                    "candidates": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["claim_text"],
                            "properties": {
                                "claim_text": {"type": "string", "minLength": 1}
                            },
                        },
                    },
                },
            }
        )

    blocks: dict[str, Any] = {
        "type": "array",
        "minItems": 0,
        "maxItems": 3,
    }
    if alternatives:
        blocks["items"] = {"oneOf": alternatives}
    else:
        blocks["maxItems"] = 0

    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["blocks"],
        "properties": {"blocks": blocks},
    }


def verify_certified_content(certified_content: dict[str, Any]) -> bool:
    expected = certified_content.get("certified_content_digest")
    if not isinstance(expected, str):
        return False
    payload = {
        key: value
        for key, value in certified_content.items()
        if key != "certified_content_digest"
    }
    return expected == digest_object(payload)


def _allowed_support_refs(grounded_context: dict[str, Any]) -> list[str]:
    return [
        str(unit["ref_id"])
        for unit in grounded_context.get("grounding_units", [])
        if isinstance(unit, dict) and isinstance(unit.get("ref_id"), str)
    ]


class Stage1RequestBuilder:
    contract_version = STAGE1_REQUEST_VERSION
    provider_contract_version = STAGE1_PROVIDER_OUTPUT_VERSION

    def build(
        self,
        *,
        user_task: str,
        grounded_context: dict[str, Any],
        request_id: str | None = None,
        max_candidates: int = 8,
        attempt: int = 1,
        attempt_id: str | None = None,
        retry_feedback: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not user_task.strip():
            raise ValueError("Stage 1 requires a non-empty user task")
        if (
            grounded_context.get("grounded_context_contract_version")
            != GROUNDED_CONTEXT_CONTRACT_VERSION
        ):
            raise ValueError("Stage 1 requires sgokb.grounded-context.v1")
        if not GroundedContextProjector.verify(grounded_context):
            raise ValueError("Grounded Context fingerprint is invalid")
        if attempt not in {1, 2}:
            raise ValueError("Stage 1 attempt must be 1 or 2")

        allowed_refs = _allowed_support_refs(grounded_context)
        request = {
            "request_contract_version": self.contract_version,
            "request_id": request_id or new_application_id("R"),
            "context_fingerprint": grounded_context["context_fingerprint"],
            "purpose": grounded_context["purpose"],
            "stage": "stage1",
            "path_provenance": PATH_STAGE1_FACT,
            "attempt": attempt,
            "attempt_id": attempt_id or new_application_id("S1A"),
            "user_task": user_task,
            "candidate_budget": {"max_candidates": max_candidates},
            "grounded_context": grounded_context,
            "allowed_support_refs": allowed_refs,
            "provider_output_contract_version": self.provider_contract_version,
        }
        schema = stage1_provider_schema(
            allowed_support_refs=allowed_refs,
            max_candidates=max_candidates,
        )
        request["provider_schema"] = schema
        request["provider_schema_hash"] = digest_object(schema)
        if retry_feedback is not None:
            if retry_feedback.get("retry_contract_version") != RETRY_FEEDBACK_VERSION:
                raise ValueError("invalid v4 retry feedback contract")
            request["retry_feedback"] = retry_feedback
        return request

    def build_retry(
        self,
        previous_request: dict[str, Any],
        *,
        retry_feedback: dict[str, Any],
        attempt_id: str | None = None,
    ) -> dict[str, Any]:
        if previous_request.get("request_contract_version") != self.contract_version:
            raise ValueError("invalid previous Stage 1 request contract")
        if previous_request.get("attempt") != 1:
            raise ValueError("Stage 1 retry may only follow attempt 1")
        if retry_feedback.get("retry_contract_version") != RETRY_FEEDBACK_VERSION:
            raise ValueError("invalid v4 retry feedback contract")
        if retry_feedback.get("stage") != "stage1":
            raise ValueError("retry feedback stage mismatch")
        if retry_feedback.get("previous_attempt_id") != previous_request.get("attempt_id"):
            raise ValueError("retry feedback attempt binding mismatch")
        allowed_refs = set(previous_request["allowed_support_refs"])
        for failure in retry_feedback.get("failures", []):
            if failure.get("premise_fact_ids"):
                raise ValueError("Stage 1 retry feedback cannot contain premise fact IDs")
            if not set(failure.get("support_refs", [])).issubset(allowed_refs):
                raise ValueError("retry feedback introduced a new Stage 1 support ref")
        retry_request = self.build(
            user_task=previous_request["user_task"],
            grounded_context=previous_request["grounded_context"],
            request_id=previous_request["request_id"],
            max_candidates=previous_request["candidate_budget"]["max_candidates"],
            attempt=2,
            attempt_id=attempt_id,
            retry_feedback=retry_feedback,
        )
        if retry_request["provider_schema_hash"] != previous_request["provider_schema_hash"]:
            raise ValueError("Stage 1 retry schema changed")
        return retry_request


def parse_stage1_output(
    raw_output: str | bytes | dict[str, Any],
    *,
    request: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if request.get("request_contract_version") != STAGE1_REQUEST_VERSION:
        raise V4ContractError("REQUEST_CONTRACT_MISMATCH", "invalid Stage 1 request contract")
    if request.get("provider_schema_hash") != digest_object(request.get("provider_schema")):
        raise V4ContractError("SCHEMA_BINDING_MISMATCH", "Stage 1 schema hash mismatch")

    if isinstance(raw_output, dict):
        parsed = json.loads(json.dumps(raw_output, ensure_ascii=False))
    else:
        try:
            text = raw_output.decode("utf-8") if isinstance(raw_output, bytes) else raw_output
            parsed = json.loads(text)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise V4ContractError("MALFORMED_JSON", "Stage 1 output is not valid JSON") from exc

    _schema_error(parsed, request["provider_schema"])
    candidates: list[dict[str, Any]] = []
    request_id = str(request["request_id"])
    short_request = hashlib.sha256(request_id.encode("utf-8")).hexdigest()[:10]
    for index, payload in enumerate(parsed["candidates"]):
        support_refs = list(payload["support_refs"])
        _ensure_non_duplicate_strings(
            support_refs,
            code="DUPLICATE_REFERENCE_ID",
            json_path=f"$.candidates[{index}].support_refs",
        )
        proposition_id = f"P-S1-{short_request}-A{request['attempt']}-C{index + 1}"
        envelope = {
            "candidate_contract_version": STRUCTURED_PROPOSITION_VERSION,
            "request_id": request_id,
            "context_fingerprint": request["context_fingerprint"],
            "purpose": request["purpose"],
            "stage": "stage1",
            "path_provenance": PATH_STAGE1_FACT,
            "attempt": request["attempt"],
            "attempt_id": request["attempt_id"],
            "proposition_id": proposition_id,
            "candidate_index": index,
            "retry_parent_id": None,
            "retry_from_attempt_id": (
                request.get("retry_feedback", {}).get("previous_attempt_id")
            ),
            "payload": {
                "claim_text": payload["claim_text"],
                "support_refs": support_refs,
            },
        }
        envelope["candidate_digest"] = digest_object(envelope)
        candidates.append(envelope)
    return parsed, candidates


class Stage2RequestBuilder:
    contract_version = STAGE2_REQUEST_VERSION
    provider_contract_version = STAGE2_PROVIDER_OUTPUT_VERSION

    def build(
        self,
        *,
        certified_content: dict[str, Any],
        presentation_instruction: str,
        stage2_request_id: str | None = None,
        attempt: int = 1,
        attempt_id: str | None = None,
        allowed_output_kinds: list[str] | None = None,
        retry_feedback: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if certified_content.get("certified_content_contract_version") != CERTIFIED_CONTENT_VERSION:
            raise ValueError("Stage 2 requires sgokb.certified-content.v1")
        if not verify_certified_content(certified_content):
            raise ValueError("Certified Content digest binding is invalid")
        if attempt not in {1, 2}:
            raise ValueError("Stage 2 attempt must be 1 or 2")
        purpose = str(certified_content["purpose"])
        allowed = list(
            allowed_output_kinds
            if allowed_output_kinds is not None
            else PURPOSE_ALLOWED_OUTPUT_KINDS.get(purpose, ())
        )
        valid_allowed = set(PURPOSE_ALLOWED_OUTPUT_KINDS.get(purpose, ()))
        if not set(allowed).issubset(valid_allowed):
            raise ValueError("allowed_output_kinds are incompatible with purpose")

        facts = [
            {
                "certified_fact_id": fact["certified_fact_id"],
                "claim_text": fact["claim_text"],
            }
            for fact in certified_content.get("facts", [])
        ]
        fact_ids = [fact["certified_fact_id"] for fact in facts]
        schema = stage2_provider_schema(
            purpose=purpose,
            allowed_output_kinds=allowed,
            certified_fact_ids=fact_ids,
        )
        request = {
            "request_contract_version": self.contract_version,
            "stage2_request_id": stage2_request_id or new_application_id("S2R"),
            "source_request_id": certified_content["request_id"],
            "certified_content_id": certified_content["certified_content_id"],
            "certified_content_digest": certified_content["certified_content_digest"],
            "context_fingerprint": certified_content["context_fingerprint"],
            "purpose": purpose,
            "stage": "stage2",
            "attempt": attempt,
            "attempt_id": attempt_id or new_application_id("S2A"),
            "allowed_output_kinds": allowed,
            "presentation_instruction": presentation_instruction,
            "certified_facts": facts,
            "provider_output_contract_version": self.provider_contract_version,
            "provider_schema": schema,
            "provider_schema_hash": digest_object(schema),
        }
        if retry_feedback is not None:
            if retry_feedback.get("retry_contract_version") != RETRY_FEEDBACK_VERSION:
                raise ValueError("invalid v4 retry feedback contract")
            request["retry_feedback"] = retry_feedback
        return request

    def build_retry(
        self,
        previous_request: dict[str, Any],
        *,
        certified_content: dict[str, Any],
        retry_feedback: dict[str, Any],
        attempt_id: str | None = None,
    ) -> dict[str, Any]:
        if previous_request.get("request_contract_version") != self.contract_version:
            raise ValueError("invalid previous Stage 2 request contract")
        if previous_request.get("attempt") != 1:
            raise ValueError("Stage 2 retry may only follow attempt 1")
        if retry_feedback.get("retry_contract_version") != RETRY_FEEDBACK_VERSION:
            raise ValueError("invalid v4 retry feedback contract")
        if retry_feedback.get("stage") != "stage2":
            raise ValueError("retry feedback stage mismatch")
        if retry_feedback.get("previous_attempt_id") != previous_request.get("attempt_id"):
            raise ValueError("retry feedback attempt binding mismatch")
        allowed_fact_ids = {
            fact["certified_fact_id"] for fact in certified_content.get("facts", [])
        }
        for failure in retry_feedback.get("failures", []):
            if failure.get("support_refs"):
                raise ValueError("Stage 2 retry feedback cannot contain support refs")
            if not set(failure.get("premise_fact_ids", [])).issubset(allowed_fact_ids):
                raise ValueError("retry feedback introduced a new Certified Fact ID")
        if certified_content.get("certified_content_digest") != previous_request.get(
            "certified_content_digest"
        ):
            raise ValueError("Stage 2 retry Certified Content changed")
        retry_request = self.build(
            certified_content=certified_content,
            presentation_instruction=previous_request["presentation_instruction"],
            stage2_request_id=previous_request["stage2_request_id"],
            attempt=2,
            attempt_id=attempt_id,
            allowed_output_kinds=list(previous_request["allowed_output_kinds"]),
            retry_feedback=retry_feedback,
        )
        if retry_request["provider_schema_hash"] != previous_request["provider_schema_hash"]:
            raise ValueError("Stage 2 retry schema changed")
        return retry_request


def parse_stage2_output(
    raw_output: str | bytes | dict[str, Any],
    *,
    request: dict[str, Any],
) -> dict[str, Any]:
    if request.get("request_contract_version") != STAGE2_REQUEST_VERSION:
        raise V4ContractError("REQUEST_CONTRACT_MISMATCH", "invalid Stage 2 request contract")
    if request.get("provider_schema_hash") != digest_object(request.get("provider_schema")):
        raise V4ContractError("SCHEMA_BINDING_MISMATCH", "Stage 2 schema hash mismatch")
    if isinstance(raw_output, dict):
        parsed = json.loads(json.dumps(raw_output, ensure_ascii=False))
    else:
        try:
            text = raw_output.decode("utf-8") if isinstance(raw_output, bytes) else raw_output
            parsed = json.loads(text)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise V4ContractError("MALFORMED_JSON", "Stage 2 output is not valid JSON") from exc
    _schema_error(parsed, request["provider_schema"])

    seen_kinds: set[str] = set()
    for block_index, block in enumerate(parsed["blocks"]):
        kind = block["block_kind"]
        if kind in seen_kinds:
            raise V4ContractError(
                "PRESENTATION_DUPLICATE_BLOCK_KIND",
                f"duplicate Stage 2 block kind: {kind}",
                json_path=f"$.blocks[{block_index}]",
            )
        seen_kinds.add(kind)
        if kind == "main":
            _ensure_non_duplicate_strings(
                list(block["certified_fact_ids"]),
                code="DUPLICATE_REFERENCE_ID",
                json_path=f"$.blocks[{block_index}].certified_fact_ids",
            )
        elif kind == "interpretation":
            for candidate_index, candidate in enumerate(block["candidates"]):
                _ensure_non_duplicate_strings(
                    list(candidate["premise_fact_ids"]),
                    code="DUPLICATE_REFERENCE_ID",
                    json_path=(
                        f"$.blocks[{block_index}].candidates[{candidate_index}].premise_fact_ids"
                    ),
                )
    return parsed


def build_stage2_candidate_envelopes(
    parsed: dict[str, Any],
    *,
    request: dict[str, Any],
) -> list[dict[str, Any]]:
    envelopes: list[dict[str, Any]] = []
    request_id = str(request["stage2_request_id"])
    short_request = hashlib.sha256(request_id.encode("utf-8")).hexdigest()[:10]
    proposition_counter = 0
    for block_index, block in enumerate(parsed["blocks"]):
        kind = block["block_kind"]
        if kind == "main":
            continue
        for candidate_index, payload in enumerate(block["candidates"]):
            proposition_counter += 1
            path = (
                PATH_STAGE2_INTERPRETATION
                if kind == "interpretation"
                else PATH_STAGE2_CREATIVE
            )
            proposition_id = (
                f"P-S2-{short_request}-A{request['attempt']}-C{proposition_counter}"
            )
            candidate_payload: dict[str, Any] = {"claim_text": payload["claim_text"]}
            if kind == "interpretation":
                candidate_payload["premise_fact_ids"] = list(payload["premise_fact_ids"])
            envelope = {
                "candidate_contract_version": STRUCTURED_PROPOSITION_VERSION,
                "stage2_request_id": request_id,
                "certified_content_id": request["certified_content_id"],
                "certified_content_digest": request["certified_content_digest"],
                "context_fingerprint": request["context_fingerprint"],
                "purpose": request["purpose"],
                "stage": "stage2",
                "path_provenance": path,
                "attempt": request["attempt"],
                "attempt_id": request["attempt_id"],
                "proposition_id": proposition_id,
                "block_index": block_index,
                "candidate_index": candidate_index,
                "retry_parent_id": None,
                "retry_from_attempt_id": (
                    request.get("retry_feedback", {}).get("previous_attempt_id")
                ),
                "payload": candidate_payload,
            }
            envelope["candidate_digest"] = digest_object(envelope)
            envelopes.append(envelope)
    return envelopes
