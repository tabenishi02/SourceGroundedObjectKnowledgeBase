"""Grounded-generation contracts and helpers for N-04 remediation."""

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
    TERMINAL_ACCEPTED,
    TERMINAL_INSUFFICIENT_CONTEXT,
    TERMINAL_REJECTED,
    TERMINAL_SYSTEM_FAILURE,
    GroundingFailureController,
)
from .output import (
    GENERATION_OUTPUT_SCHEMA,
    GROUNDED_GENERATION_OUTPUT_CONTRACT_VERSION,
    GenerationOutputContractError,
    parse_generation_output,
)
from .render import DeterministicRenderer
from .validation import (
    GROUNDING_VALIDATION_CONTRACT_VERSION,
    GroundingValidator,
    SemanticValidatorAdapter,
)

__all__ = [
    "ACTION_RETRY",
    "GENERATION_OUTPUT_SCHEMA",
    "GROUNDED_CONTEXT_CONTRACT_VERSION",
    "GROUNDED_GENERATION_OUTPUT_CONTRACT_VERSION",
    "GROUNDING_FAILURE_POLICY_VERSION",
    "GROUNDING_VALIDATION_CONTRACT_VERSION",
    "MAX_GENERATION_ATTEMPTS",
    "MAX_RETRIES",
    "TERMINAL_ACCEPTED",
    "TERMINAL_INSUFFICIENT_CONTEXT",
    "TERMINAL_REJECTED",
    "TERMINAL_SYSTEM_FAILURE",
    "DeterministicRenderer",
    "GenerationOutputContractError",
    "GroundedContextProjector",
    "GroundingEvidenceLogger",
    "GroundingFailureController",
    "GroundingValidator",
    "SemanticValidatorAdapter",
    "parse_generation_output",
]
