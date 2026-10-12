"""Budgeted Evidence selection over F-03 retrieval candidates (Phase F / F-04)."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from typing import Iterable

from .evidence import EvidenceCandidate


@dataclass(frozen=True, slots=True)
class EvidenceBudget:
    """Hard bounds for the evidence-selection payload, not the final G-01 file format."""

    max_estimated_tokens: int = 12_000
    max_bytes: int = 65_536
    max_items: int = 64

    def validate(self) -> None:
        if self.max_estimated_tokens < 1:
            raise ValueError("Evidence token budget must be positive")
        if self.max_bytes < 1:
            raise ValueError("Evidence byte budget must be positive")
        if self.max_items < 1:
            raise ValueError("Evidence item budget must be positive")


@dataclass(frozen=True, slots=True)
class SelectedEvidence:
    candidate: EvidenceCandidate
    selected_by: str
    estimated_tokens: int
    byte_size: int
    structure_group: str
    related_selected_evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OmittedEvidence:
    evidence_id: str
    source_id: str
    reason: str
    detail: str
    estimated_tokens: int
    byte_size: int


def estimate_tokens(text: str) -> int:
    """Deterministic tokenizer-independent estimate suitable for a hard selection budget.

    ASCII text is estimated at roughly four characters per token. Non-ASCII code
    points are counted one-per-token. The estimate is deliberately conservative for
    Japanese and remains independent from any particular model tokenizer.
    """

    ascii_count = sum(ord(char) < 128 for char in text)
    non_ascii_count = len(text) - ascii_count
    return max(1, math.ceil(ascii_count / 4) + non_ascii_count)


def _candidate_payload(candidate: EvidenceCandidate) -> str:
    return json.dumps(asdict(candidate), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _cost(candidate: EvidenceCandidate) -> tuple[int, int]:
    payload = _candidate_payload(candidate)
    return estimate_tokens(payload), len(payload.encode("utf-8"))


def _normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _structure_signature(candidate: EvidenceCandidate) -> str:
    metadata = candidate.context.get("metadata") or {}
    payload = {
        "source_id": candidate.source_id,
        "run_id": candidate.run_id,
        "artifact": metadata.get("artifact"),
        "positions": metadata.get("positions") or [],
        "section": metadata.get("section") or [],
        "kinds": metadata.get("kinds") or [],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


def _range(candidate: EvidenceCandidate) -> tuple[int, int] | None:
    metadata = candidate.context.get("metadata") or {}
    start = metadata.get("start")
    if not isinstance(start, int) or start < 0:
        return None
    return start, start + len(candidate.content)


def _overlap_ratio(left: EvidenceCandidate, right: EvidenceCandidate) -> float:
    if _structure_signature(left) != _structure_signature(right):
        return 0.0
    left_range, right_range = _range(left), _range(right)
    if left_range is None or right_range is None:
        return 0.0
    overlap = min(left_range[1], right_range[1]) - max(left_range[0], right_range[0])
    if overlap <= 0:
        return 0.0
    shortest = min(left_range[1] - left_range[0], right_range[1] - right_range[0])
    return overlap / shortest if shortest else 0.0


class EvidencePackageSelector:
    """Select a bounded, diverse subset while preserving F-03 reasons and provenance."""

    def __init__(self, budget: EvidenceBudget | None = None):
        self.budget = budget or EvidenceBudget()
        self.budget.validate()

    def select(
        self,
        retrieval_result: dict,
        *,
        protected_evidence_ids: Iterable[str] = (),
    ) -> dict:
        candidates = tuple(retrieval_result.get("candidates", ()))
        protected = tuple(dict.fromkeys(protected_evidence_ids))
        by_id = {candidate.evidence_id: candidate for candidate in candidates}
        missing = [evidence_id for evidence_id in protected if evidence_id not in by_id]
        if missing:
            raise ValueError(f"Protected Evidence is outside retrieval candidates: {missing[0]}")

        selected: list[SelectedEvidence] = []
        omitted: list[OmittedEvidence] = []
        decided: set[str] = set()
        usage_tokens = usage_bytes = 0
        selected_candidates: list[EvidenceCandidate] = []

        def duplicate_reason(candidate: EvidenceCandidate) -> tuple[str, str] | None:
            normalized = _normalized_text(candidate.content)
            for existing in selected_candidates:
                other = _normalized_text(existing.content)
                if normalized == other:
                    return "duplicate", f"same normalized content as {existing.evidence_id}"
                if candidate.source_id == existing.source_id:
                    ratio = SequenceMatcher(None, normalized, other, autojunk=False).ratio()
                    if ratio >= 0.92:
                        return "near_duplicate", f"similarity={ratio:.3f} to {existing.evidence_id}"
                    overlap = _overlap_ratio(candidate, existing)
                    if overlap >= 0.85:
                        return "overlapping_chunk", (
                            f"structural overlap={overlap:.3f} with {existing.evidence_id}"
                        )
            return None

        def related_ids(candidate: EvidenceCandidate) -> tuple[str, ...]:
            group = _structure_signature(candidate)
            return tuple(
                existing.evidence_id
                for existing in selected_candidates
                if _structure_signature(existing) == group
            )

        def omit(candidate: EvidenceCandidate, reason: str, detail: str) -> None:
            token_cost, byte_cost = _cost(candidate)
            omitted.append(
                OmittedEvidence(
                    candidate.evidence_id,
                    candidate.source_id,
                    reason,
                    detail,
                    token_cost,
                    byte_cost,
                )
            )
            decided.add(candidate.evidence_id)

        def try_select(
            candidate: EvidenceCandidate, selected_by: str, *, protected_item=False
        ) -> bool:
            nonlocal usage_tokens, usage_bytes
            if candidate.evidence_id in decided:
                return False
            token_cost, byte_cost = _cost(candidate)
            if not protected_item:
                duplicate = duplicate_reason(candidate)
                if duplicate is not None:
                    omit(candidate, *duplicate)
                    return False
            limit_reason = self._limit_reason(
                len(selected), usage_tokens, usage_bytes, token_cost, byte_cost
            )
            if limit_reason is not None:
                reason, detail = limit_reason
                if protected_item:
                    raise ValueError(
                        f"Protected Evidence exceeds Package budget ({reason}): "
                        f"{candidate.evidence_id}"
                    )
                omit(candidate, reason, detail)
                return False
            related = related_ids(candidate)
            selected.append(
                SelectedEvidence(
                    candidate=candidate,
                    selected_by=selected_by,
                    estimated_tokens=token_cost,
                    byte_size=byte_cost,
                    structure_group=_structure_signature(candidate),
                    related_selected_evidence_ids=related,
                )
            )
            selected_candidates.append(candidate)
            usage_tokens += token_cost
            usage_bytes += byte_cost
            decided.add(candidate.evidence_id)
            return True

        for evidence_id in protected:
            try_select(by_id[evidence_id], "protected", protected_item=True)

        first_per_source: dict[str, EvidenceCandidate] = {}
        for candidate in candidates:
            if candidate.evidence_id not in decided:
                first_per_source.setdefault(candidate.source_id, candidate)
        for candidate in first_per_source.values():
            try_select(candidate, "source_diversity")

        for candidate in candidates:
            try_select(candidate, "relevance_fill")

        return {
            "object_id": retrieval_result.get("object_id"),
            "scope": retrieval_result.get("scope"),
            "semantic": retrieval_result.get("semantic"),
            "excluded_source_ids": list(retrieval_result.get("excluded_source_ids", ())),
            "budget": asdict(self.budget),
            "usage": {
                "estimated_tokens": usage_tokens,
                "bytes": usage_bytes,
                "items": len(selected),
                "sources": len({item.candidate.source_id for item in selected}),
            },
            "token_estimator": "ascii_div4_plus_non_ascii_v1",
            "candidate_count": len(candidates),
            "selected_count": len(selected),
            "omitted_count": len(omitted),
            "selected": selected,
            "omitted": omitted,
        }

    def _limit_reason(
        self,
        selected_count: int,
        used_tokens: int,
        used_bytes: int,
        token_cost: int,
        byte_cost: int,
    ) -> tuple[str, str] | None:
        if selected_count + 1 > self.budget.max_items:
            return "max_items", f"limit={self.budget.max_items}"
        if used_tokens + token_cost > self.budget.max_estimated_tokens:
            return (
                "token_budget",
                f"used={used_tokens},item={token_cost},limit={self.budget.max_estimated_tokens}",
            )
        if used_bytes + byte_cost > self.budget.max_bytes:
            return (
                "byte_budget",
                f"used={used_bytes},item={byte_cost},limit={self.budget.max_bytes}",
            )
        return None
