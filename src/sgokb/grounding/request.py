"""Provider-neutral grounded-generation request assembly."""

from __future__ import annotations

import json
from typing import Any

from .context import GROUNDED_CONTEXT_CONTRACT_VERSION, GroundedContextProjector
from .output import (
    GENERATION_OUTPUT_SCHEMA,
    GROUNDED_GENERATION_OUTPUT_CONTRACT_VERSION,
    SEMANTIC_ROLES,
)


class GroundedGenerationRequestBuilder:
    """Build the normative information a consumer must supply to its local LLM."""

    def build(
        self,
        *,
        user_task: str,
        grounded_context: dict[str, Any],
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

        request = {
            "user_task": user_task,
            "purpose": grounded_context.get("purpose"),
            "grounded_context": grounded_context,
            "output_contract": {
                "contract_version": GROUNDED_GENERATION_OUTPUT_CONTRACT_VERSION,
                "json_schema": GENERATION_OUTPUT_SCHEMA,
                "allowed_semantic_roles": list(SEMANTIC_ROLES),
                "rules": [
                    "Use only supplied Grounded Context for source-world factual claims.",
                    "source_fact and interpretation require material K refs in support_refs.",
                    "creative_addition, context_limit and stylistic_expression use no K refs.",
                    "Do not self-declare grounding disposition or confidence.",
                    "Put interpretation in an interpretation presentation block.",
                    "Put creative additions in a creative presentation block.",
                    "Use context_limit rather than model memory when context is insufficient.",
                    "Return only the structured JSON envelope; no separate final prose.",
                    "Keep each material semantic proposition atomic enough to validate.",
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
