"""High-recall Object -> canonical Evidence retrieval for Phase F / F-03."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from sgokb.domain import validate_vectors


@dataclass(frozen=True, slots=True)
class EvidenceSelectionReason:
    channel: str
    detail: str
    score: float | None = None


@dataclass(frozen=True, slots=True)
class EvidenceCandidate:
    evidence_id: str
    source_id: str
    snapshot_id: str
    run_id: str
    content: str
    retrieval_score: float
    reasons: tuple[EvidenceSelectionReason, ...]
    context: dict


class ObjectEvidenceRetriever:
    """Combine independent retrieval signals without turning ranking into truth judgement."""

    def __init__(self, repository, embedder=None):
        self.repository = repository
        self.embedder = embedder

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        numerator = sum(a * b for a, b in zip(left, right))
        left_length = math.sqrt(sum(value * value for value in left))
        right_length = math.sqrt(sum(value * value for value in right))
        return numerator / (left_length * right_length)

    @staticmethod
    def _fts_phrase(value: str) -> str:
        return '"' + value.replace('"', '""') + '"'

    def retrieve(
        self,
        object_id: str,
        *,
        max_candidates: int = 500,
        semantic: bool | None = None,
        semantic_batch_size: int = 32,
        manual_include: Iterable[str] = (),
        manual_exclude: Iterable[str] = (),
    ) -> dict:
        if not 1 <= max_candidates <= 5000:
            raise ValueError("Evidence candidate limit must be 1..5000")
        if semantic_batch_size < 1:
            raise ValueError("Semantic batch size must be positive")
        semantic = self.embedder is not None if semantic is None else semantic
        if semantic and self.embedder is None:
            raise ValueError("Semantic Evidence retrieval requires an embedder")

        object_record = self.repository.object_store.get_object(object_id)
        if object_record.status.value != "active":
            raise ValueError("Evidence retrieval requires an active Object")
        names = tuple(
            dict.fromkeys(
                value.strip()
                for value in [object_record.name, *(alias.value for alias in object_record.aliases)]
                if value.strip()
            )
        )
        aliases = tuple(names[1:])
        store = self.repository.source_store
        associations = store.associations_for_object(object_id)
        excluded_sources = {row["source_id"] for row in associations if row["status"] == "excluded"}
        explicit = {
            row["source_id"]: row
            for row in associations
            if row["status"] in {"candidate", "confirmed"}
        }
        all_rows = [
            row
            for row in store.effective_evidence_rows()
            if row["source_id"] not in excluded_sources
        ]
        rows_by_id = {row["id"]: row for row in all_rows}
        candidates: dict[str, dict] = {}

        def add(row: dict, channel: str, detail: str, weight: float, score=None) -> None:
            item = candidates.setdefault(
                row["id"],
                {"row": row, "score": 0.0, "reasons": {}},
            )
            key = (channel, detail)
            if key in item["reasons"]:
                return
            item["score"] += weight
            item["reasons"][key] = EvidenceSelectionReason(channel, detail, score)

        self._add_explicit_associations(all_rows, explicit, add)
        self._add_name_alias_matches(all_rows, object_record.name, aliases, add)
        self._add_source_metadata_matches(store, all_rows, names, add)
        self._add_lexical_matches(store, names, excluded_sources, max_candidates, add)
        if semantic:
            self._add_semantic_matches(
                all_rows,
                names,
                max_candidates,
                semantic_batch_size,
                add,
            )

        manual_include = tuple(dict.fromkeys(manual_include))
        if manual_include:
            store.validate_evidence_references(manual_include)
            for evidence_id in manual_include:
                row = rows_by_id.get(evidence_id)
                if row is None:
                    record = store.evidence_context(evidence_id)
                    row = record
                add(row, "manual", "explicit include", 100.0)

        manual_exclude = set(manual_exclude)
        if manual_exclude:
            store.validate_evidence_references(manual_exclude)
        for evidence_id in manual_exclude:
            candidates.pop(evidence_id, None)

        ranked = sorted(
            candidates.values(),
            key=lambda item: (-item["score"], item["row"]["id"]),
        )[:max_candidates]
        output = []
        for item in ranked:
            row = item["row"]
            output.append(
                EvidenceCandidate(
                    evidence_id=row["id"],
                    source_id=row["source_id"],
                    snapshot_id=row["snapshot_id"],
                    run_id=row["run_id"],
                    content=row["content"],
                    retrieval_score=item["score"],
                    reasons=tuple(item["reasons"].values()),
                    context=store.evidence_context(row["id"]),
                )
            )

        return {
            "object_id": object_record.object_id,
            "name": object_record.name,
            "aliases": [alias.value for alias in object_record.aliases],
            "scope": "effective_snapshot_and_run",
            "semantic": bool(semantic),
            "excluded_source_ids": sorted(excluded_sources),
            "candidate_count": len(output),
            "candidates": output,
        }

    @staticmethod
    def _add_explicit_associations(rows, explicit, add) -> None:
        for row in rows:
            association = explicit.get(row["source_id"])
            if not association:
                continue
            status = association["status"]
            relation = association.get("subject_relationship") or "unspecified"
            weight = 50.0 if status == "confirmed" else 35.0
            add(row, "explicit_association", f"{status}:{relation}", weight)

    @staticmethod
    def _add_name_alias_matches(rows, canonical_name, aliases, add) -> None:
        canonical = canonical_name.casefold()
        folded_aliases = {alias.casefold(): alias for alias in aliases}
        for row in rows:
            content = row["content"].casefold()
            if canonical in content:
                add(row, "name", canonical_name, 25.0)
            for folded, original in folded_aliases.items():
                if folded in content:
                    add(row, "alias", original, 20.0)

    @staticmethod
    def _add_source_metadata_matches(store, rows, names, add) -> None:
        matched = store.metadata_matching_sources(names)
        if not matched:
            return
        for row in rows:
            details = matched.get(row["source_id"])
            if not details:
                continue
            for detail in details:
                add(row, "source_metadata", detail, 12.0)

    def _add_lexical_matches(self, store, names, excluded_sources, max_candidates, add) -> None:
        for term in names:
            rows = store.lexical_evidence_rows(
                self._fts_phrase(term),
                limit=max_candidates,
            )
            for rank, row in enumerate(rows, 1):
                if row["source_id"] in excluded_sources:
                    continue
                score = 1.0 / rank
                add(row, "lexical", term, 10.0 + score, score)

    def _add_semantic_matches(self, rows, names, max_candidates, batch_size, add) -> None:
        if not rows:
            return
        query_text = names[0]
        if len(names) > 1:
            query_text += "\nAliases: " + ", ".join(names[1:])
        query_vectors = self.embedder.embed([query_text], query=True)
        dimension = validate_vectors(query_vectors, 1)
        query_vector = query_vectors[0]
        scored: list[tuple[float, dict]] = []
        for start in range(0, len(rows), batch_size):
            batch = rows[start : start + batch_size]
            vectors = self.embedder.embed([row["content"] for row in batch])
            current_dimension = validate_vectors(vectors, len(batch))
            if current_dimension != dimension:
                raise ValueError("Evidence embedding dimension differs from query embedding")
            scored.extend(
                (self._cosine(query_vector, vector), row) for row, vector in zip(batch, vectors)
            )
        scored.sort(key=lambda item: (-item[0], item[1]["id"]))
        for score, row in scored[:max_candidates]:
            add(row, "semantic", "object name/aliases embedding", 8.0 + max(score, 0.0), score)
