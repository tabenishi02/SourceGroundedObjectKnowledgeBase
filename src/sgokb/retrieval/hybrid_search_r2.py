"""R2 generation-scoped Hybrid Object Search.

This module layers the N05D-04R2 active-generation contract over the accepted
Phase-I search implementation without performing the R2-07 production cutover.
Before an active-generation pointer exists, the historical Phase-I serving path
remains available so R2-05 can be deployed before R2-07 bootstraps/cuts over the
runtime. Once the pointer exists, one request resolves exactly one generation and
all Knowledge lexical/semantic channels are scoped to that membership set.
"""

from __future__ import annotations

import sqlite3
from contextvars import ContextVar
from dataclasses import dataclass

from sgokb.domain import (
    ObjectSearchChannel,
    ObjectSearchFilters,
    SearchRepresentationKind,
    VectorIndexAdapter,
    VectorMatch,
    VectorSearchFilter,
)

from .generation import vector_generation_scope
from .hybrid_search import (
    RRF_K,
    _Candidate,
    _normalize,
)
from .hybrid_search import (
    HybridObjectSearch as _PhaseIHybridObjectSearch,
)
from .hybrid_search import (
    KnowledgeVectorIndexBuilder as _PhaseIKnowledgeVectorIndexBuilder,
)

_PHASE_I_CONTRACT_KEY = "phase-i-search-v1"
_R2_CONTRACT_KEY = "n05d04r2-hierarchical-v2"
_SUPPORTED_GENERATIONS = {
    (_PHASE_I_CONTRACT_KEY, 1),
    (_R2_CONTRACT_KEY, 2),
}


@dataclass(frozen=True, slots=True)
class _ResolvedKnowledgeGeneration:
    generation_id: str | None
    contract_key: str
    contract_version: int
    pre_cutover_compatibility: bool = False

    @property
    def object_kind(self) -> SearchRepresentationKind:
        if self.contract_key == _R2_CONTRACT_KEY:
            return SearchRepresentationKind.OBJECT_OVERVIEW
        return SearchRepresentationKind.OBJECT_OVERALL

    @property
    def requires_generation_payload(self) -> bool:
        return self.generation_id is not None and self.contract_key == _R2_CONTRACT_KEY


_GENERATION_CONTEXT: ContextVar[_ResolvedKnowledgeGeneration | None] = ContextVar(
    "sgokb_hybrid_search_generation",
    default=None,
)


class KnowledgeVectorIndexBuilder(_PhaseIKnowledgeVectorIndexBuilder):
    """Build membership-scoped Vector points for one optional Knowledge generation.

    R2-07 owns namespace creation/cutover. R2-05 only makes the point projection
    generation-aware so a candidate namespace can be built without mixing v1/v2
    memberships and R2 payloads carry their generation identity.
    """

    def __init__(
        self,
        repository,
        vector_index: VectorIndexAdapter,
        *,
        generation_id: str | None = None,
    ):
        super().__init__(repository, vector_index)
        self.generation_id = generation_id
        if generation_id is not None:
            row = self.db.execute(
                """SELECT contract_key,contract_version,state
                   FROM knowledge_search_generations WHERE id=?""",
                (generation_id,),
            ).fetchone()
            if row is None:
                raise ValueError(f"Unknown Knowledge Search generation: {generation_id}")

    def _membership_rows(self) -> list[dict]:
        if self.generation_id is None:
            return super()._membership_rows()
        rows = self.db.execute(
            """SELECT m.*,o.status AS object_status,o.current_version_id,
                      cs.primary_class_id,pc.key AS primary_class,
                      f.key AS facet,s.derivation_kind,s.temporal_scope_id,
                      ts.as_of,ts.valid_from,ts.valid_to
               FROM knowledge_search_representation_memberships m
               JOIN knowledge_search_generation_memberships gm ON gm.membership_id=m.id
               JOIN object_version_lifecycle l ON l.version_id=m.version_id
               JOIN objects o ON o.id=m.object_id
               JOIN object_version_classification_snapshots cs ON cs.version_id=m.version_id
               JOIN object_classes pc ON pc.id=cs.primary_class_id
               LEFT JOIN facet_definitions f ON f.id=m.facet_id
               LEFT JOIN knowledge_statements s ON s.id=m.statement_id
               LEFT JOIN temporal_scopes ts ON ts.id=s.temporal_scope_id
               WHERE l.state='accepted' AND gm.generation_id=?
               ORDER BY m.object_id,m.version_id,m.target_kind,m.facet_id,m.statement_id,m.id""",
            (self.generation_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def _metadata_from_row(self, row: dict, additional_rows: tuple[dict, ...]) -> dict:
        metadata = super()._metadata_from_row(row, additional_rows)
        if self.generation_id is not None:
            metadata["generation_id"] = self.generation_id
        return metadata


class HybridObjectSearch(_PhaseIHybridObjectSearch):
    """Canonical R2-capable Hybrid Object Search.

    Public callers still use ``search_objects``/``HybridObjectSearch.search`` and do
    not supply a representation kind or generation. The active generation is
    resolved exactly once at request start.
    """

    def _resolve_generation(self) -> _ResolvedKnowledgeGeneration:
        row = self.db.execute(
            """SELECT a.active_generation_id,g.contract_key,g.contract_version,g.state
               FROM knowledge_search_active_generation a
               JOIN knowledge_search_generations g ON g.id=a.active_generation_id
               WHERE a.scope='knowledge'"""
        ).fetchone()
        if row is None:
            # R2-07 deliberately owns bootstrap/cutover. Until it creates the
            # singleton pointer, preserve the pre-R2 serving path rather than
            # fabricating readiness for the migration-seeded v1 generation.
            return _ResolvedKnowledgeGeneration(
                generation_id=None,
                contract_key=_PHASE_I_CONTRACT_KEY,
                contract_version=1,
                pre_cutover_compatibility=True,
            )
        if row["state"] != "ready":
            raise RuntimeError("Active Knowledge Search generation is not ready")
        key = (row["contract_key"], int(row["contract_version"]))
        if key not in _SUPPORTED_GENERATIONS:
            raise RuntimeError(
                "Unsupported active Knowledge Search generation contract: "
                f"{row['contract_key']} v{row['contract_version']}"
            )
        return _ResolvedKnowledgeGeneration(
            generation_id=row["active_generation_id"],
            contract_key=row["contract_key"],
            contract_version=int(row["contract_version"]),
        )

    @staticmethod
    def _current_generation() -> _ResolvedKnowledgeGeneration:
        generation = _GENERATION_CONTEXT.get()
        if generation is None:
            raise RuntimeError("Hybrid Search generation context was not resolved")
        return generation

    def search(self, *args, **kwargs):
        generation = self._resolve_generation()
        token = _GENERATION_CONTEXT.set(generation)
        try:
            with vector_generation_scope(self.vector_index, generation.generation_id):
                return super().search(*args, **kwargs)
        finally:
            _GENERATION_CONTEXT.reset(token)

    def _fusion_scores(self, candidates: dict[tuple[str, str | None], _Candidate]) -> dict:
        if self._current_generation().contract_key != _R2_CONTRACT_KEY:
            return super()._fusion_scores(candidates)
        weights = {
            ObjectSearchChannel.SEMANTIC_OBJECT_OVERVIEW: 0.5,
            ObjectSearchChannel.SEMANTIC_FACET: 1.0,
            ObjectSearchChannel.SEMANTIC_STATEMENT: 1.0,
        }
        inner_scores = {
            key: sum(
                weights[channel] / (RRF_K + rank)
                for channel, rank in candidate.channel_ranks.items()
                if channel in weights
            )
            for key, candidate in candidates.items()
        }
        ordered = sorted(
            (key for key, score in inner_scores.items() if score > 0),
            key=lambda key: (-inner_scores[key], key[0], key[1] or ""),
        )
        semantic_ranks = {key: rank for rank, key in enumerate(ordered, start=1)}
        # One Semantic Object ranking votes alongside Registry/Knowledge lexical.
        # Keep actual public match channels and their bounded local ranks intact.
        return {
            key: sum(
                1.0 / (RRF_K + rank)
                for channel, rank in candidate.channel_ranks.items()
                if channel not in weights
            )
            + (1.0 / (RRF_K + semantic_ranks[key]) if key in semantic_ranks else 0.0)
            for key, candidate in candidates.items()
        }

    def _representation_kinds(self, filters: ObjectSearchFilters) -> tuple[str, ...]:
        if filters.knowledge_valid_at is not None or filters.temporal_scope_id is not None:
            return (SearchRepresentationKind.STATEMENT.value,)
        if filters.derivation_kind is not None:
            return (SearchRepresentationKind.STATEMENT.value,)
        if filters.facet is not None:
            return (
                SearchRepresentationKind.FACET.value,
                SearchRepresentationKind.STATEMENT.value,
            )
        return (
            self._current_generation().object_kind.value,
            SearchRepresentationKind.FACET.value,
            SearchRepresentationKind.STATEMENT.value,
        )

    def _registry_rows(self, filters: ObjectSearchFilters) -> list[dict]:
        rows = super()._registry_rows(filters)
        generation = self._current_generation()
        if generation.generation_id is None:
            return rows
        if not any(
            value is not None
            for value in (
                filters.facet,
                filters.temporal_scope_id,
                filters.knowledge_valid_at,
                filters.derivation_kind,
            )
        ):
            return rows

        kinds = self._representation_kinds(filters)
        clauses, params = super()._scope_conditions(filters, kinds=kinds)
        clauses.append("gm.generation_id=?")
        params.append(generation.generation_id)
        sql = """SELECT DISTINCT m.object_id,m.version_id
                 FROM knowledge_search_representation_memberships m
                 JOIN knowledge_search_generation_memberships gm ON gm.membership_id=m.id
                 JOIN object_version_lifecycle l ON l.version_id=m.version_id
                 JOIN objects o ON o.id=m.object_id
                 JOIN object_version_classification_snapshots cs ON cs.version_id=m.version_id
                 JOIN object_classes pc ON pc.id=cs.primary_class_id
                 LEFT JOIN facet_definitions f ON f.id=m.facet_id
                 LEFT JOIN knowledge_statements s ON s.id=m.statement_id
                 WHERE """ + " AND ".join(clauses)
        allowed = {(row["object_id"], row["version_id"]) for row in self.db.execute(sql, params)}
        return [row for row in rows if (row["object_id"], row["version_id"]) in allowed]

    def _knowledge_lexical_hits(
        self,
        query: str,
        filters: ObjectSearchFilters,
        limit: int,
    ) -> list[dict]:
        generation = self._current_generation()
        if generation.generation_id is None:
            return super()._knowledge_lexical_hits(query, filters, limit)

        kinds = self._representation_kinds(filters)
        clauses, params = super()._scope_conditions(filters, kinds=kinds)
        clauses.append("gm.generation_id=?")
        params.append(generation.generation_id)
        base = """SELECT m.id AS membership_id,m.representation_id,m.object_id,m.version_id,
                         m.target_kind,m.facet_id,m.statement_id,r.content,
                         f.key AS facet,s.text AS statement_text,pc.key AS primary_class,
                         o.name AS object_name
                  FROM search_representations r
                  JOIN knowledge_search_representation_memberships m ON m.representation_id=r.id
                  JOIN knowledge_search_generation_memberships gm ON gm.membership_id=m.id
                  JOIN object_version_lifecycle l ON l.version_id=m.version_id
                  JOIN objects o ON o.id=m.object_id
                  JOIN object_version_classification_snapshots cs ON cs.version_id=m.version_id
                  JOIN object_classes pc ON pc.id=cs.primary_class_id
                  LEFT JOIN facet_definitions f ON f.id=m.facet_id
                  LEFT JOIN knowledge_statements s ON s.id=m.statement_id"""
        terms = [term for term in _normalize(query).split() if term]
        if not terms:
            return []
        if all(len(term) >= 3 for term in terms):
            expression = " AND ".join('"' + term.replace('"', '""') + '"' for term in terms)
            sql = """SELECT m.id AS membership_id,m.representation_id,m.object_id,m.version_id,
                            m.target_kind,m.facet_id,m.statement_id,r.content,
                            f.key AS facet,s.text AS statement_text,pc.key AS primary_class,
                            o.name AS object_name,bm25(search_representation_fts) AS lexical_score
                     FROM search_representation_fts
                     JOIN search_representations r
                       ON r.id=search_representation_fts.representation_id
                     JOIN knowledge_search_representation_memberships m ON m.representation_id=r.id
                     JOIN knowledge_search_generation_memberships gm ON gm.membership_id=m.id
                     JOIN object_version_lifecycle l ON l.version_id=m.version_id
                     JOIN objects o ON o.id=m.object_id
                     JOIN object_version_classification_snapshots cs ON cs.version_id=m.version_id
                     JOIN object_classes pc ON pc.id=cs.primary_class_id
                     LEFT JOIN facet_definitions f ON f.id=m.facet_id
                     LEFT JOIN knowledge_statements s ON s.id=m.statement_id
                     WHERE search_representation_fts MATCH ? AND """ + " AND ".join(clauses)
            try:
                rows = self.db.execute(
                    sql + " ORDER BY lexical_score,m.id LIMIT ?",
                    [expression, *params, limit],
                ).fetchall()
                return [dict(row) for row in rows]
            except sqlite3.OperationalError:
                pass
        literal_clauses = ["instr(lower(r.content),lower(?))>0" for _ in terms]
        rows = self.db.execute(
            base
            + " WHERE "
            + " AND ".join([*clauses, *literal_clauses])
            + " ORDER BY m.id LIMIT ?",
            [*params, *terms, limit],
        ).fetchall()
        output = []
        for row in rows:
            item = dict(row)
            item["lexical_score"] = None
            output.append(item)
        return output

    def _vector_filters_for_generation(
        self,
        filters: ObjectSearchFilters,
        kind: SearchRepresentationKind,
    ) -> VectorSearchFilter:
        base = super()._vector_filters(filters, kind)
        generation = self._current_generation()
        if not generation.requires_generation_payload:
            return base
        return VectorSearchFilter(
            matches=(
                *base.matches,
                VectorMatch("generation_id", (generation.generation_id,)),
            ),
            excludes=base.excludes,
            ranges=base.ranges,
        )

    def _semantic_hits(
        self,
        query: str,
        filters: ObjectSearchFilters,
        limit: int,
    ) -> tuple[list[dict], tuple[str, ...]]:
        generation = self._current_generation()
        if generation.generation_id is None:
            rows, degraded = super()._semantic_hits(query, filters, limit)
            for row in rows:
                if row.get("channel") is ObjectSearchChannel.SEMANTIC_OBJECT:
                    row["channel"] = ObjectSearchChannel.SEMANTIC_OBJECT_OVERALL
            return rows, degraded
        if self.embedding_provider is None or self.vector_index is None:
            raise RuntimeError(
                "Semantic search requires an EmbeddingProvider and VectorIndexAdapter"
            )

        space = self.embedding_provider.space
        query_vector = self.embedding_provider.embed_queries([query])[0]
        object_channel = (
            ObjectSearchChannel.SEMANTIC_OBJECT_OVERVIEW
            if generation.contract_key == _R2_CONTRACT_KEY
            else ObjectSearchChannel.SEMANTIC_OBJECT_OVERALL
        )
        kind_channels = {
            generation.object_kind: object_channel,
            SearchRepresentationKind.FACET: ObjectSearchChannel.SEMANTIC_FACET,
            SearchRepresentationKind.STATEMENT: ObjectSearchChannel.SEMANTIC_STATEMENT,
        }
        allowed_kinds = set(self._representation_kinds(filters))
        raw_hits = []
        for kind, channel in kind_channels.items():
            if kind.value not in allowed_kinds:
                continue
            for hit in self.vector_index.search(
                space,
                query_vector,
                limit=limit,
                filters=self._vector_filters_for_generation(filters, kind),
            ):
                raw_hits.append((channel, hit))
        if not raw_hits:
            return [], ()

        membership_ids = tuple(dict.fromkeys(hit.point_id for _, hit in raw_hits))
        marks = ",".join("?" for _ in membership_ids)
        rows = self.db.execute(
            f"""SELECT m.id AS membership_id,m.representation_id,m.object_id,m.version_id,
                       m.target_kind,m.facet_id,m.statement_id,r.content,
                       f.key AS facet,s.text AS statement_text,pc.key AS primary_class,
                       o.name AS object_name
                FROM knowledge_search_representation_memberships m
                JOIN knowledge_search_generation_memberships gm ON gm.membership_id=m.id
                JOIN search_representations r ON r.id=m.representation_id
                JOIN object_version_lifecycle l ON l.version_id=m.version_id AND l.state='accepted'
                JOIN objects o ON o.id=m.object_id
                JOIN object_version_classification_snapshots cs ON cs.version_id=m.version_id
                JOIN object_classes pc ON pc.id=cs.primary_class_id
                LEFT JOIN facet_definitions f ON f.id=m.facet_id
                LEFT JOIN knowledge_statements s ON s.id=m.statement_id
                WHERE m.id IN ({marks}) AND gm.generation_id=?""",
            [*membership_ids, generation.generation_id],
        ).fetchall()
        details = {row["membership_id"]: dict(row) for row in rows}
        output = []
        for channel, hit in raw_hits:
            payload_generation = hit.metadata.get("generation_id")
            if (
                generation.requires_generation_payload
                and payload_generation != generation.generation_id
            ):
                raise RuntimeError("Vector Index generation payload mismatch")
            if payload_generation is not None and payload_generation != generation.generation_id:
                raise RuntimeError("Vector Index generation payload mismatch")
            detail = details.get(hit.point_id)
            if detail is None:
                raise RuntimeError("Vector Index returned membership outside active generation")

            # Defense in depth against an obsolete derived index after a current-pointer change.
            if filters.version_id is None:
                current = self.db.execute(
                    "SELECT status,current_version_id FROM objects WHERE id=?",
                    (detail["object_id"],),
                ).fetchone()
                if not current or current["current_version_id"] != detail["version_id"]:
                    continue
                if not filters.include_archived and current["status"] != "active":
                    continue
            detail["channel"] = channel
            detail["semantic_score"] = hit.score
            detail["source_rank"] = hit.rank
            output.append(detail)
        return output, ()
