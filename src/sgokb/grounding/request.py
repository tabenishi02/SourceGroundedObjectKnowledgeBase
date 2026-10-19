"""Provider-neutral grounded-generation request assembly for N-04 v3."""

from __future__ import annotations

import json
from typing import Any

from .context import GROUNDED_CONTEXT_CONTRACT_VERSION, GroundedContextProjector
from .material_gate import default_requirement_profile
from .output import (
    GENERATION_OUTPUT_SCHEMA,
    GROUNDED_GENERATION_OUTPUT_CONTRACT_VERSION,
    SEMANTIC_ROLES,
    generation_output_schema_hash,
)


class GroundedGenerationRequestBuilder:
    """Build the normative information a consumer supplies to its local generator."""

    def build(
        self,
        *,
        user_task: str,
        grounded_context: dict[str, Any],
        requirement_profile: dict[str, Any] | None = None,
        retry_feedback: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not user_task.strip():
            raise ValueError("Grounded generation requires a non-empty user task")
        if (
            grounded_context.get("grounded_context_contract_version")
            != GROUNDED_CONTEXT_CONTRACT_VERSION
            or not GroundedContextProjector.verify(grounded_context)
        ):
            raise ValueError("Grounded generation requires a valid sgokb.grounded-context.v1")

        purpose = str(grounded_context.get("purpose"))
        profile = (
            dict(requirement_profile)
            if requirement_profile is not None
            else default_requirement_profile(purpose, grounded_context)
        )
        request = {
            "user_task": user_task,
            "purpose": purpose,
            "grounded_context": grounded_context,
            "requirement_profile": profile,
            "output_contract": {
                "contract_version": GROUNDED_GENERATION_OUTPUT_CONTRACT_VERSION,
                "json_schema": GENERATION_OUTPUT_SCHEMA,
                "json_schema_hash": generation_output_schema_hash(),
                "allowed_semantic_roles": list(SEMANTIC_ROLES),
                "rules": [
                    "Use only supplied Grounded Context for source-world factual claims.",
                    "Return only the structured JSON envelope; no separate final prose.",
                    "Keep each material text unit to one atomic semantic proposition.",
                    "main blocks contain source_fact(text, support_refs) units only.",
                    "interpretation blocks contain interpretation(text, premise_unit_ids) units only.",
                    "interpretation premises must reference source_fact units from the same output.",
                    "creative blocks contain creative_addition(text) units only.",
                    "Do not put source-world facts inside creative_addition text.",
                    "Do not emit stylistic_expression or any free-form presentation label.",
                    "Use an exclusive context_limit block with limit_code=material_requirements_not_satisfied when supplied Context cannot meet the requirement profile.",
                    "Do not mix context_limit with main, interpretation, or creative blocks.",
                    "Do not self-declare grounding disposition, confidence, or validator verdicts.",
                ],
            },
        }
        if retry_feedback is not None:
            request["retry_feedback"] = retry_feedback
        return request

    def to_prompt_text(self, request: dict[str, Any]) -> str:
        """Serialize request data without provider-specific chat-message assumptions."""

        return (
            "Follow the SGOKB grounded-generation request below exactly.\n"
            "Do not use external knowledge as factual support.\n\n"
            + json.dumps(request, ensure_ascii=False, sort_keys=True, indent=2)
        )
