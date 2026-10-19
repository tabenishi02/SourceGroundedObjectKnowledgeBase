"""Adapter boundaries for N-04 v3 semantic validation components."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AtomicityRoleValidatorAdapter(Protocol):
    """Classify atomicity and content-first semantic-role validity.

    The adapter must not use Web/external retrieval. Runtime/model identity is
    frozen later by the formal harness, not by this interface.
    """

    def validate(
        self,
        *,
        text: str,
        semantic_role: str,
        purpose: str,
        presentation_role: str,
    ) -> dict[str, Any]: ...


@runtime_checkable
class SourceFactVerifierAdapter(Protocol):
    """Specialized document/claim support checker for V3-unresolved source facts."""

    def verify(
        self,
        *,
        claim_text: str,
        support_units: list[dict[str, Any]],
    ) -> dict[str, Any] | str: ...


@runtime_checkable
class SourceFactJudgeAdapter(Protocol):
    """Independent bounded LLM second opinion for specialized-positive claims."""

    def judge(
        self,
        *,
        claim_text: str,
        support_units: list[dict[str, Any]],
    ) -> dict[str, Any] | str: ...


@runtime_checkable
class InterpretationDerivationJudgeAdapter(Protocol):
    """Judge only whether a conclusion follows from validated source-fact premises."""

    def judge(
        self,
        *,
        conclusion_text: str,
        premise_texts: list[str],
        premise_metadata: list[dict[str, Any]],
        purpose: str,
    ) -> dict[str, Any] | str: ...


def normalize_adapter_result(
    result: dict[str, Any] | str,
    *,
    allowed_verdicts: set[str],
) -> dict[str, Any]:
    """Normalize adapter result while retaining audit metadata."""

    if isinstance(result, str):
        verdict = result
        payload: dict[str, Any] = {"verdict": verdict}
    elif isinstance(result, dict):
        payload = dict(result)
        verdict = payload.get("verdict")
    else:
        return {"verdict": "INDETERMINATE", "raw_result_type": type(result).__name__}

    if verdict not in allowed_verdicts:
        payload["raw_verdict"] = verdict
        payload["verdict"] = "INDETERMINATE"
    return payload
