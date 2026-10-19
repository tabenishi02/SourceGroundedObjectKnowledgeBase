"""Grounded-generation contracts and helpers for N-04 post-G12 v3."""

from .context import (
    GROUNDED_CONTEXT_CONTRACT_VERSION,
    GroundedContextProjector,
)
from .evidence import GroundingEvidenceLogger
from .failure import (
    ACTION_RETRY,
    GROUNDING_FAILURE_POLICY_VERSION,
    MAX_GENERATION_ATTEMPTS,
    MAX_RETRIES,
    RENDER_MODE_CONTEXT_LIMIT_ONLY,
    RENDER_MODE_NONE,
    RENDER_MODE_NORMAL,
    TERMINAL_ACCEPTED,
    TERMINAL_INSUFFICIENT_CONTEXT,
    TERMINAL_REJECTED,
    TERMINAL_SYSTEM_FAILURE,
    GroundingFailureController,
)
from .material_gate import (
    MATERIAL_FAIL_CONTEXT_INSUFFICIENT,
    MATERIAL_FAIL_REPAIRABLE,
    MATERIAL_INDETERMINATE,
    MATERIAL_PASS,
    MATERIAL_REQUIREMENT_CONTRACT_VERSION,
    MaterialRequirementGate,
    default_requirement_profile,
)
from .output import (
    CONTEXT_LIMIT_CODE,
    GENERATION_OUTPUT_SCHEMA,
    GROUNDED_GENERATION_OUTPUT_CONTRACT_VERSION,
    GenerationOutputContractError,
    canonical_output_json,
    generation_output_schema_hash,
    is_context_limit_output,
    output_binding,
    output_digest,
    parse_generation_output,
)
from .render import DeterministicRenderer, RenderAuthorizationError
from .request import GroundedGenerationRequestBuilder
from .validation import (
    GROUNDING_VALIDATION_CONTRACT_VERSION,
    GroundingValidator,
)
from .verifiers import (
    AtomicityRoleValidatorAdapter,
    InterpretationDerivationJudgeAdapter,
    SourceFactJudgeAdapter,
    SourceFactVerifierAdapter,
)

__all__ = [
    "ACTION_RETRY",
    "CONTEXT_LIMIT_CODE",
    "GENERATION_OUTPUT_SCHEMA",
    "GROUNDED_CONTEXT_CONTRACT_VERSION",
    "GROUNDED_GENERATION_OUTPUT_CONTRACT_VERSION",
    "GROUNDING_FAILURE_POLICY_VERSION",
    "GROUNDING_VALIDATION_CONTRACT_VERSION",
    "MATERIAL_FAIL_CONTEXT_INSUFFICIENT",
    "MATERIAL_FAIL_REPAIRABLE",
    "MATERIAL_INDETERMINATE",
    "MATERIAL_PASS",
    "MATERIAL_REQUIREMENT_CONTRACT_VERSION",
    "MAX_GENERATION_ATTEMPTS",
    "MAX_RETRIES",
    "RENDER_MODE_CONTEXT_LIMIT_ONLY",
    "RENDER_MODE_NONE",
    "RENDER_MODE_NORMAL",
    "TERMINAL_ACCEPTED",
    "TERMINAL_INSUFFICIENT_CONTEXT",
    "TERMINAL_REJECTED",
    "TERMINAL_SYSTEM_FAILURE",
    "AtomicityRoleValidatorAdapter",
    "DeterministicRenderer",
    "GenerationOutputContractError",
    "GroundedContextProjector",
    "GroundedGenerationRequestBuilder",
    "GroundingEvidenceLogger",
    "GroundingFailureController",
    "GroundingValidator",
    "InterpretationDerivationJudgeAdapter",
    "MaterialRequirementGate",
    "RenderAuthorizationError",
    "SourceFactJudgeAdapter",
    "SourceFactVerifierAdapter",
    "canonical_output_json",
    "default_requirement_profile",
    "generation_output_schema_hash",
    "is_context_limit_output",
    "output_binding",
    "output_digest",
    "parse_generation_output",
]
