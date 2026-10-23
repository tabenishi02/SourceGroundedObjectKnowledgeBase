"""R2 hierarchical multi-vector Object Similarity.

The Phase-I implementation remains the pre-cutover compatibility path. Once an
active Knowledge Search generation exists, every Vector and SQLite membership read
is scoped to the generation resolved once at operation start.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sgokb.domain import (
    ObjectSimilarityEvidence,
    ObjectSimilarityResponse,
    SearchRepresentationKind,
    SimilarObjectResult,
    VectorMatch,
    VectorSearchFilter,
)

from .similarity import ObjectSimilaritySearch as _PhaseIObjectSimilaritySearch

_PHASE_I_CONTRACT_KEY = "phase-i-search-v1"
_R2_CONTRACT_KEY = "n05d04r2-hierarchical-v2"
_SUPPORTED_GENERATIONS = {
    (_PHASE_I_CONTRACT_KEY, 1),
    (_R2_CONTRACT_KEY, 2),
}

R2_SOURCE_FACET_QUERY_CAP = 8
R2_SOURCE_STATEMENT_QUERY_CAP = 12
R2_OVERVIEW_QUERY_LIMIT = 128
R2_FACET_QUERY_LIMIT = 24
R2_STATEMENT_QUERY_LIMIT = 12
R2_CANDIDATE_OBJECT_CAP = 128
R2_COMPONENT_WEIGHTS = {
    "overview": 0.50,
    "facet": 0.30,
    "statement": 0.20,
}
R2_COMPONENT_EVIDENCE_CAPS = {
    "overview": 1,
    "facet": 2,
    "statement": 3,
}


@dataclass(frozen=True, slots=True)
class _ResolvedKnowledgeGeneration:
    generation_id: str | None
    contract_key: str
    contract_version: int

    @property
    def is_r2(self) -> bool:
        return self.contract_key == _R2_CONTRACT_KEY


@dataclass(frozen=True, slots=True)
class _ComponentHit:
    component: str
    source: dict
    candidate: dict
    raw_score: float


class ObjectSimilaritySearch(_PhaseIObjectSimilaritySearch):
    """Generation-scoped Object Similarity with an R2 hierarchical overall path."""

    def _resolve_generation(self) -> _ResolvedKnowledgeGeneration:
        row = self.db.execute(
            """SELECT a.active_generation_id,g.contract_key,g.contract_version,g.state
               FROM knowledge_search_active_generation a
               JOIN knowledge_search_generations g ON g.id=a.active_generation_id
               WHERE a.scope='knowledge'"""
        ).fetchone()
        if row is None:
            return _ResolvedKnowledgeGeneration(
                generation_id=None,
                contract_key=_PHASE_I_CONTRACT_KEY,
                contract_version=1,
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

    def _generation_source_membership(
        self,
        context: dict,
        *,
        kind: SearchRepresentationKind,
        generation: _ResolvedKnowledgeGeneration,
        facet: str | None = None,
    ) -> dict:
        params: list[object] = [
            generation.generation_id,
            context["object_id"],
            context["version_id"],
            kind.value,
        ]
        facet_clause = ""
        if facet is not None:
            facet_row = self.db.execute(
                "SELECT id FROM facet_definitions WHERE key=?", (facet,)
            ).fetchone()
            if not facet_row:
                raise ValueError(f"Unknown Facet: {facet}")
            facet_clause = " AND m.facet_id=?"
            params.append(facet_row["id"])
        row = self.db.execute(
            """SELECT m.id AS membership_id,m.representation_id,m.target_kind,
                      m.facet_id,f.key AS facet,m.statement_id
               FROM knowledge_search_representation_memberships m
               JOIN knowledge_search_generation_memberships gm
                 ON gm.membership_id=m.id
               LEFT JOIN facet_definitions f ON f.id=m.facet_id
               WHERE gm.generation_id=? AND m.object_id=? AND m.version_id=?
                 AND m.target_kind=?"""
            + facet_clause,
            params,
        ).fetchone()
        if row:
            return dict(row)
        if facet is not None:
            raise ValueError(f"Source Object Version has no content Facet: {facet}")
        raise RuntimeError(
            f"Source Object Version has no {kind.value} membership in active generation"
        )

    def _source_r2_family(
        self,
        context: dict,
        generation: _ResolvedKnowledgeGeneration,
    ) -> tuple[dict, tuple[dict, ...], tuple[dict, ...]]:
        rows = [
            dict(row)
            for row in self.db.execute(
                """SELECT m.id AS membership_id,m.representation_id,m.target_kind,
                          m.facet_id,f.key AS facet,m.statement_id,s.local_key
                   FROM knowledge_search_representation_memberships m
                   JOIN knowledge_search_generation_memberships gm
                     ON gm.membership_id=m.id
                   LEFT JOIN facet_definitions f ON f.id=m.facet_id
                   LEFT JOIN knowledge_statements s ON s.id=m.statement_id
                   WHERE gm.generation_id=? AND m.object_id=? AND m.version_id=?
                     AND m.target_kind IN ('object_overview','facet','statement')
                   ORDER BY m.target_kind,f.key,s.local_key,m.id""",
                (
                    generation.generation_id,
                    context["object_id"],
                    context["version_id"],
                ),
            ).fetchall()
        ]
        overviews = [row for row in rows if row["target_kind"] == "object_overview"]
        if len(overviews) != 1:
            raise RuntimeError(
                "Active R2 source Version must have exactly one object_overview membership"
            )
        facets = tuple(
            sorted(
                (row for row in rows if row["target_kind"] == "facet"),
                key=lambda row: (row["facet"] or "", row["membership_id"]),
            )[:R2_SOURCE_FACET_QUERY_CAP]
        )
        statement_rows = [
            row
            for row in rows
            if row["target_kind"] == "statement" and row["facet_id"] is not None
        ]
        statements = self._round_robin_statements(statement_rows)
        return overviews[0], facets, statements

    @staticmethod
    def _round_robin_statements(rows: list[dict]) -> tuple[dict, ...]:
        groups: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            groups[row["facet"] or ""].append(row)
        for values in groups.values():
            values.sort(
                key=lambda row: (
                    row.get("local_key") or "",
                    row["statement_id"] or "",
                    row["membership_id"],
                )
            )
        selected: list[dict] = []
        offset = 0
        facet_keys = sorted(groups)
        while len(selected) < R2_SOURCE_STATEMENT_QUERY_CAP:
            added = False
            for facet in facet_keys:
                values = groups[facet]
                if offset < len(values):
                    selected.append(values[offset])
                    added = True
                    if len(selected) == R2_SOURCE_STATEMENT_QUERY_CAP:
                        break
            if not added:
                break
            offset += 1
        return tuple(selected)

    def _embedding(self, representation_id: str) -> tuple[float, ...]:
        try:
            return tuple(
                self.repository.embedding_store.representation_embedding(
                    self.space.space_id,
                    representation_id,
                )
            )
        except ValueError as exc:
            raise RuntimeError(
                "Source similarity representation has no embedding in this Embedding Space"
            ) from exc

    def _generation_query_filter(
        self,
        *,
        kind: SearchRepresentationKind,
        facet: str | None,
        source: dict,
        generation: _ResolvedKnowledgeGeneration,
        cross_class: bool,
        include_archived: bool,
    ) -> VectorSearchFilter:
        matches = [
            VectorMatch("kind", (kind.value,)),
            VectorMatch("is_current", (True,)),
        ]
        if generation.is_r2:
            matches.append(VectorMatch("generation_id", (generation.generation_id,)))
        if not include_archived:
            matches.append(VectorMatch("object_status", ("active",)))
        if not cross_class:
            matches.append(VectorMatch("primary_class", (source["primary_class"],)))
        if facet is not None:
            matches.append(VectorMatch("facet", (facet,)))
        return VectorSearchFilter(
            matches=tuple(matches),
            excludes=(VectorMatch("object_id", (source["object_id"],)),),
        )

    def _generation_target_rows(
        self,
        membership_ids: tuple[str, ...],
        generation: _ResolvedKnowledgeGeneration,
    ) -> dict[str, dict]:
        if not membership_ids:
            return {}
        marks = ",".join("?" for _ in membership_ids)
        rows = self.db.execute(
            f"""SELECT m.id AS membership_id,m.representation_id,m.object_id,m.version_id,
                       m.target_kind,m.facet_id,f.key AS facet,m.statement_id,
                       o.name,o.status,o.current_version_id,pc.key AS primary_class
                FROM knowledge_search_representation_memberships m
                JOIN knowledge_search_generation_memberships gm
                  ON gm.membership_id=m.id
                JOIN object_version_lifecycle l
                  ON l.version_id=m.version_id AND l.state='accepted'
                JOIN objects o ON o.id=m.object_id
                JOIN object_version_classification_snapshots cs
                  ON cs.version_id=m.version_id
                JOIN object_classes pc ON pc.id=cs.primary_class_id
                LEFT JOIN facet_definitions f ON f.id=m.facet_id
                WHERE m.id IN ({marks}) AND gm.generation_id=?""",
            [*membership_ids, generation.generation_id],
        ).fetchall()
        return {row["membership_id"]: dict(row) for row in rows}

    @staticmethod
    def _verify_payload_generation(hit, generation: _ResolvedKnowledgeGeneration) -> None:
        payload_generation = hit.metadata.get("generation_id")
        if generation.is_r2 and payload_generation != generation.generation_id:
            raise RuntimeError("Vector Index generation payload mismatch")
        if (
            payload_generation is not None
            and generation.generation_id is not None
            and payload_generation != generation.generation_id
        ):
            raise RuntimeError("Vector Index generation payload mismatch")

    def _component_search(
        self,
        *,
        component: str,
        source_membership: dict,
        source: dict,
        generation: _ResolvedKnowledgeGeneration,
        kind: SearchRepresentationKind,
        facet: str | None,
        query_limit: int,
        cross_class: bool,
        include_archived: bool,
    ) -> tuple[_ComponentHit, ...]:
        hits = self.vector_index.search(
            self.space,
            self._embedding(source_membership["representation_id"]),
            limit=query_limit,
            filters=self._generation_query_filter(
                kind=kind,
                facet=facet,
                source=source,
                generation=generation,
                cross_class=cross_class,
                include_archived=include_archived,
            ),
        )
        for hit in hits:
            self._verify_payload_generation(hit, generation)
        details = self._generation_target_rows(
            tuple(hit.point_id for hit in hits), generation
        )
        best_by_object: dict[str, _ComponentHit] = {}
        for hit in hits:
            candidate = details.get(hit.point_id)
            if candidate is None:
                raise RuntimeError("Vector Index returned membership outside active generation")
            if candidate["object_id"] == source["object_id"]:
                continue
            if candidate["current_version_id"] != candidate["version_id"]:
                continue
            if not include_archived and candidate["status"] != "active":
                continue
            if not cross_class and candidate["primary_class"] != source["primary_class"]:
                continue
            if candidate["target_kind"] != kind.value:
                raise RuntimeError("Vector Index representation kind mismatch")
            if facet is not None and candidate["facet"] != facet:
                raise RuntimeError("Vector Index Facet scope mismatch")
            value = _ComponentHit(
                component=component,
                source=source_membership,
                candidate=candidate,
                raw_score=float(hit.score),
            )
            previous = best_by_object.get(candidate["object_id"])
            if previous is None or self._hit_sort_key(value) < self._hit_sort_key(previous):
                best_by_object[candidate["object_id"]] = value
        return tuple(best_by_object.values())

    @staticmethod
    def _hit_sort_key(hit: _ComponentHit) -> tuple:
        return (
            -hit.raw_score,
            hit.source["membership_id"],
            hit.candidate["membership_id"],
        )

    @staticmethod
    def _bounded_cosine(value: float) -> float:
        return max(0.0, min(1.0, value))

    def _score_candidate(
        self,
        hits: list[_ComponentHit],
        source_counts: dict[str, int],
    ) -> tuple[float, tuple[ObjectSimilarityEvidence, ...]]:
        active_components = [
            component
            for component in ("overview", "facet", "statement")
            if source_counts.get(component, 0) > 0
        ]
        active_weight = sum(
            R2_COMPONENT_WEIGHTS[component] for component in active_components
        )
        evidence: list[ObjectSimilarityEvidence] = []
        final_score = 0.0
        for component in active_components:
            cap = R2_COMPONENT_EVIDENCE_CAPS[component]
            slots = min(cap, source_counts[component])
            component_hits = sorted(
                (hit for hit in hits if hit.component == component),
                key=self._hit_sort_key,
            )[:cap]
            normalized_weight = R2_COMPONENT_WEIGHTS[component] / active_weight
            for hit in component_hits:
                contribution = (
                    normalized_weight * self._bounded_cosine(hit.raw_score) / slots
                )
                final_score += contribution
                evidence.append(
                    ObjectSimilarityEvidence(
                        component=component,
                        source_representation_id=hit.source["representation_id"],
                        source_membership_id=hit.source["membership_id"],
                        candidate_representation_id=hit.candidate["representation_id"],
                        candidate_membership_id=hit.candidate["membership_id"],
                        representation_kind=hit.candidate["target_kind"],
                        facet=hit.candidate.get("facet"),
                        source_statement_id=hit.source.get("statement_id"),
                        candidate_statement_id=hit.candidate.get("statement_id"),
                        score=hit.raw_score,
                        score_type="cosine_similarity",
                        contribution=contribution,
                    )
                )
        component_order = {"overview": 0, "facet": 1, "statement": 2}
        evidence.sort(
            key=lambda item: (
                component_order[item.component],
                -item.contribution,
                item.source_membership_id,
                item.candidate_membership_id,
            )
        )
        return final_score, tuple(evidence)

    @staticmethod
    def _compatibility_anchor(
        hits: list[_ComponentHit],
        evidence: tuple[ObjectSimilarityEvidence, ...],
    ) -> dict:
        overview = sorted(
            (hit for hit in hits if hit.component == "overview"),
            key=ObjectSimilaritySearch._hit_sort_key,
        )
        if overview:
            return overview[0].candidate
        if not evidence:
            raise RuntimeError("Hierarchical Similarity candidate has no inspectable evidence")
        membership_id = evidence[0].candidate_membership_id
        return next(
            hit.candidate
            for hit in hits
            if hit.candidate["membership_id"] == membership_id
        )

    def _r2_overall_similarity(
        self,
        source: dict,
        generation: _ResolvedKnowledgeGeneration,
        *,
        limit: int,
        cross_class: bool,
        include_archived: bool,
    ) -> ObjectSimilarityResponse:
        overview, facets, statements = self._source_r2_family(source, generation)
        all_hits: list[_ComponentHit] = []
        all_hits.extend(
            self._component_search(
                component="overview",
                source_membership=overview,
                source=source,
                generation=generation,
                kind=SearchRepresentationKind.OBJECT_OVERVIEW,
                facet=None,
                query_limit=R2_OVERVIEW_QUERY_LIMIT,
                cross_class=cross_class,
                include_archived=include_archived,
            )
        )
        for membership in facets:
            all_hits.extend(
                self._component_search(
                    component="facet",
                    source_membership=membership,
                    source=source,
                    generation=generation,
                    kind=SearchRepresentationKind.FACET,
                    facet=membership["facet"],
                    query_limit=R2_FACET_QUERY_LIMIT,
                    cross_class=cross_class,
                    include_archived=include_archived,
                )
            )
        for membership in statements:
            all_hits.extend(
                self._component_search(
                    component="statement",
                    source_membership=membership,
                    source=source,
                    generation=generation,
                    kind=SearchRepresentationKind.STATEMENT,
                    facet=membership["facet"],
                    query_limit=R2_STATEMENT_QUERY_LIMIT,
                    cross_class=cross_class,
                    include_archived=include_archived,
                )
            )

        grouped: dict[str, list[_ComponentHit]] = defaultdict(list)
        for hit in all_hits:
            grouped[hit.candidate["object_id"]].append(hit)
        source_counts = {
            "overview": 1,
            "facet": len(facets),
            "statement": len(statements),
        }
        scored = []
        for object_id, hits in grouped.items():
            score, evidence = self._score_candidate(hits, source_counts)
            anchor = self._compatibility_anchor(hits, evidence)
            scored.append((object_id, score, evidence, anchor))
        scored.sort(key=lambda item: (-item[1], item[0], item[3]["version_id"]))
        scored = scored[:R2_CANDIDATE_OBJECT_CAP]
        results = tuple(
            SimilarObjectResult(
                object_id=anchor["object_id"],
                name=anchor["name"],
                primary_class=anchor["primary_class"],
                version_id=anchor["version_id"],
                rank=rank,
                score=score,
                score_type="hierarchical_similarity",
                matched_facet=None,
                representation_id=anchor["representation_id"],
                membership_id=anchor["membership_id"],
                evidence=evidence,
            )
            for rank, (_, score, evidence, anchor) in enumerate(
                scored[:limit], start=1
            )
        )
        return ObjectSimilarityResponse(
            source_object_id=source["object_id"],
            source_name=source["name"],
            source_primary_class=source["primary_class"],
            source_version_id=source["version_id"],
            source_representation_id=overview["representation_id"],
            facet=None,
            cross_class=cross_class,
            results=results,
            source_membership_id=overview["membership_id"],
            generation_id=generation.generation_id,
        )

    def _generation_single_vector_similarity(
        self,
        source: dict,
        generation: _ResolvedKnowledgeGeneration,
        *,
        facet: str | None,
        limit: int,
        cross_class: bool,
        include_archived: bool,
    ) -> ObjectSimilarityResponse:
        kind = (
            SearchRepresentationKind.FACET
            if facet is not None
            else SearchRepresentationKind.OBJECT_OVERALL
        )
        membership = self._generation_source_membership(
            source,
            kind=kind,
            generation=generation,
            facet=facet,
        )
        hits = self.vector_index.search(
            self.space,
            self._embedding(membership["representation_id"]),
            limit=min(1000, max(limit, limit * 2)),
            filters=self._generation_query_filter(
                kind=kind,
                facet=facet,
                source=source,
                generation=generation,
                cross_class=cross_class,
                include_archived=include_archived,
            ),
        )
        for hit in hits:
            self._verify_payload_generation(hit, generation)
        details = self._generation_target_rows(
            tuple(hit.point_id for hit in hits), generation
        )
        best_by_object: dict[str, tuple[float, int, dict]] = {}
        for hit in hits:
            row = details.get(hit.point_id)
            if row is None:
                raise RuntimeError("Vector Index returned membership outside active generation")
            if row["object_id"] == source["object_id"]:
                continue
            if row["current_version_id"] != row["version_id"]:
                continue
            if not include_archived and row["status"] != "active":
                continue
            if row["target_kind"] != kind.value:
                continue
            if facet is not None and row["facet"] != facet:
                continue
            if not cross_class and row["primary_class"] != source["primary_class"]:
                continue
            candidate = (float(hit.score), hit.rank, row)
            previous = best_by_object.get(row["object_id"])
            if (
                previous is None
                or candidate[0] > previous[0]
                or (candidate[0] == previous[0] and candidate[1] < previous[1])
            ):
                best_by_object[row["object_id"]] = candidate
        ordered = sorted(
            best_by_object.values(),
            key=lambda item: (-item[0], item[2]["object_id"], item[2]["version_id"]),
        )[:limit]
        results = tuple(
            SimilarObjectResult(
                object_id=row["object_id"],
                name=row["name"],
                primary_class=row["primary_class"],
                version_id=row["version_id"],
                rank=rank,
                score=score,
                score_type="cosine_similarity",
                matched_facet=facet,
                representation_id=row["representation_id"],
                membership_id=row["membership_id"],
            )
            for rank, (score, _, row) in enumerate(ordered, start=1)
        )
        return ObjectSimilarityResponse(
            source_object_id=source["object_id"],
            source_name=source["name"],
            source_primary_class=source["primary_class"],
            source_version_id=source["version_id"],
            source_representation_id=membership["representation_id"],
            facet=facet,
            cross_class=cross_class,
            results=results,
            source_membership_id=membership["membership_id"],
            generation_id=generation.generation_id,
        )

    def find_similar_objects(
        self,
        object_id: str,
        *,
        facet: str | None = None,
        limit: int = 10,
        cross_class: bool = False,
        source_version_id: str | None = None,
        include_archived: bool = False,
    ) -> ObjectSimilarityResponse:
        if not 1 <= limit <= 1000:
            raise ValueError("Similarity limit must be between 1 and 1000")
        facet = facet.strip() if facet is not None else None
        if facet == "":
            raise ValueError("Facet key must be non-empty")

        generation = self._resolve_generation()
        if generation.generation_id is None:
            return super().find_similar_objects(
                object_id,
                facet=facet,
                limit=limit,
                cross_class=cross_class,
                source_version_id=source_version_id,
                include_archived=include_archived,
            )

        source = super()._source_context(object_id, source_version_id)
        if facet is not None:
            return self._generation_single_vector_similarity(
                source,
                generation,
                facet=facet,
                limit=limit,
                cross_class=cross_class,
                include_archived=include_archived,
            )
        if not generation.is_r2:
            return self._generation_single_vector_similarity(
                source,
                generation,
                facet=None,
                limit=limit,
                cross_class=cross_class,
                include_archived=include_archived,
            )
        return self._r2_overall_similarity(
            source,
            generation,
            limit=limit,
            cross_class=cross_class,
            include_archived=include_archived,
        )
