"""Compatibility adapters connecting v4 validation to existing verifier APIs."""

from __future__ import annotations

import re
from typing import Any

from .verifiers import (
    InterpretationDerivationJudgeAdapter,
    SourceFactJudgeAdapter,
    SourceFactVerifierAdapter,
    normalize_adapter_result,
)


def _unit_text(unit: dict[str, Any]) -> str | None:
    content = unit.get("content")
    if not isinstance(content, dict):
        return None
    for key in ("text", "value", "name"):
        value = content.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _safe_normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).casefold()


class V4SourceFactSupportAdapter:
    """V3 deterministic exact support + V4F specialized/judge composition.

    Concrete verifier/judge runtimes remain externally injected and frozen later.
    """

    def __init__(
        self,
        *,
        verifier: SourceFactVerifierAdapter | None,
        judge: SourceFactJudgeAdapter | None,
    ) -> None:
        self.verifier = verifier
        self.judge = judge

    def validate(
        self,
        *,
        claim_text: str,
        support_units: list[dict[str, Any]],
    ) -> dict[str, Any]:
        normalized_claim = _safe_normalize(claim_text)
        exact = [
            unit.get("ref_id")
            for unit in support_units
            if isinstance(text := _unit_text(unit), str)
            and _safe_normalize(text) == normalized_claim
        ]
        if exact:
            return {
                "verdict": "SUPPORTED",
                "support_mode": "deterministic_exact",
                "matched_refs": exact,
            }

        if self.verifier is None:
            return {"verdict": "UNAVAILABLE", "support_mode": "v4f"}
        specialized = normalize_adapter_result(
            self.verifier.verify(
                claim_text=claim_text,
                support_units=support_units,
            ),
            allowed_verdicts={
                "SUPPORTED_CANDIDATE",
                "UNSUPPORTED",
                "CONTRADICTORY",
                "INDETERMINATE",
                "UNAVAILABLE",
            },
        )
        specialized_verdict = specialized["verdict"]
        if specialized_verdict != "SUPPORTED_CANDIDATE":
            mapped = (
                specialized_verdict
                if specialized_verdict in {
                    "UNSUPPORTED",
                    "CONTRADICTORY",
                    "INDETERMINATE",
                    "UNAVAILABLE",
                }
                else "INDETERMINATE"
            )
            return {
                "verdict": mapped,
                "support_mode": "v4f",
                "specialized": specialized,
            }

        if self.judge is None:
            return {
                "verdict": "UNAVAILABLE",
                "support_mode": "v4f",
                "specialized": specialized,
            }
        judge = normalize_adapter_result(
            self.judge.judge(
                claim_text=claim_text,
                support_units=support_units,
            ),
            allowed_verdicts={
                "ENTAILED",
                "UNSUPPORTED",
                "CONTRADICTORY",
                "INDETERMINATE",
                "UNAVAILABLE",
            },
        )
        if judge["verdict"] == "ENTAILED":
            verdict = "SUPPORTED"
        elif judge["verdict"] in {"UNSUPPORTED", "CONTRADICTORY"}:
            verdict = judge["verdict"]
        else:
            verdict = "INDETERMINATE" if judge["verdict"] != "UNAVAILABLE" else "UNAVAILABLE"
        return {
            "verdict": verdict,
            "support_mode": "v4f",
            "specialized": specialized,
            "independent_judge": judge,
        }


class V4InterpretationDerivationAdapter:
    """Bridge the frozen v3 derivation judge API into the v4 V4I boundary."""

    def __init__(self, *, judge: InterpretationDerivationJudgeAdapter | None) -> None:
        self.judge = judge

    def validate(
        self,
        *,
        conclusion_text: str,
        premise_texts: list[str],
        premise_metadata: list[dict[str, Any]],
        purpose: str,
    ) -> dict[str, Any]:
        if self.judge is None:
            return {"verdict": "UNAVAILABLE"}
        result = normalize_adapter_result(
            self.judge.judge(
                conclusion_text=conclusion_text,
                premise_texts=premise_texts,
                premise_metadata=premise_metadata,
                purpose=purpose,
            ),
            allowed_verdicts={
                "REASONABLE_DERIVATION",
                "UNSUPPORTED_DERIVATION",
                "CONTRADICTORY",
                "INDETERMINATE",
                "UNAVAILABLE",
            },
        )
        if result["verdict"] == "UNSUPPORTED_DERIVATION":
            result["verdict"] = "UNSUPPORTED"
        return result
