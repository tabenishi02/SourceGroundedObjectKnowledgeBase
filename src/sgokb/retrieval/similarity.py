"""Object-to-object overall and Facet similarity for Phase I / I-05."""

from __future__ import annotations

from sgokb.domain import (
    EmbeddingSpaceSpec,
    ObjectSimilarityResponse,
    SimilarObjectResult,
    VectorIndexAdapter,
    VectorMatch,
    VectorSearchFilter,
)


class ObjectSimilaritySearch:
    """Find current Objects similar to an existing accepted Object Version."""

    def __init__(
        self,
        repository,
        *,
        space: EmbeddingSpaceSpec,
        vector_index: VectorIndexAdapter,
    ) -> None:
        self.repository = repository
        self.db = repository.db
        self.space = space
        self.vector_index = vector_index

    def _source_context(self, object_id: str, source_version_id: str | None) -> dict:
        if source_version_id is None:
            row = self.db.execute(
                """SELECT o.id AS object_id,o.name,o.status,o.current_version_id AS version_id,
                          pc.key AS primary_class
                   FROM objects o
                   JOIN object_version_lifecycle l
                     ON l.version_id=o.current_version_id AND l.state='accepted'
                   JOIN object_version_classification_snapshots cs
                     ON cs.version_id=o.current_version_id
                   JOIN object_classes pc ON pc.id=cs.primary_class_id
                   WHERE o.id=?""",
                (object_id,),
            ).fetchone()
            if not row:
                raise ValueError("Unknown source Object ID")
            if row["version_id"] is None:
                raise ValueError("Source Object has no current Knowledge Version")
            accepted = self.db.execute(
                """SELECT 1 FROM object_version_lifecycle
                   WHERE version_id=? AND state='accepted'""",
                (row["version_id"],),
            ).fetchone()
            if not accepted:
                raise ValueError("Source current Knowledge Version is not accepted")
            return dict(row)

        row = self.db.execute(
            """SELECT o.id AS object_id,o.name,o.status,v.id AS version_id,
                      pc.key AS primary_class
               FROM object_versions v
               JOIN object_version_lifecycle l ON l.version_id=v.id AND l.state='accepted'
               JOIN objects o ON o.id=v.object_id
               JOIN object_version_classification_snapshots cs ON cs.version_id=v.id
               JOIN object_classes pc ON pc.id=cs.primary_class_id
               WHERE o.id=? AND v.id=?""",
            (object_id, source_version_id),
        ).fetchone()
        if not row:
            raise ValueError("Source Version must be an accepted Version of the source Object")
        return dict(row)

    def _source_membership(self, context: dict, facet: str | None) -> dict:
        if facet is None:
            row = self.db.execute(
                """SELECT m.id AS membership_id,m.representation_id
                   FROM knowledge_search_representation_memberships m
                   WHERE m.object_id=? AND m.version_id=?
                     AND m.target_kind='object_overall'""",
                (context["object_id"], context["version_id"]),
            ).fetchone()
            if not row:
                raise RuntimeError(
                    "Source Object Version has no object_overall Search Representation"
                )
            return dict(row)

        facet_row = self.db.execute(
            "SELECT id FROM facet_definitions WHERE key=?", (facet,)
        ).fetchone()
        if not facet_row:
            raise ValueError(f"Unknown Facet: {facet}")
        row = self.db.execute(
            """SELECT m.id AS membership_id,m.representation_id
               FROM knowledge_search_representation_memberships m
               WHERE m.object_id=? AND m.version_id=? AND m.target_kind='facet'
                 AND m.facet_id=?""",
            (context["object_id"], context["version_id"], facet_row["id"]),
        ).fetchone()
        if not row:
            raise ValueError(f"Source Object Version has no content Facet: {facet}")
        return dict(row)

    def _query_filter(
        self,
        *,
        facet: str | None,
        primary_class: str,
        cross_class: bool,
        include_archived: bool,
        source_object_id: str,
    ) -> VectorSearchFilter:
        matches = [
            VectorMatch("kind", ("facet" if facet is not None else "object_overall",)),
            VectorMatch("is_current", (True,)),
        ]
        if not include_archived:
            matches.append(VectorMatch("object_status", ("active",)))
        if not cross_class:
            matches.append(VectorMatch("primary_class", (primary_class,)))
        if facet is not None:
            matches.append(VectorMatch("facet", (facet,)))
        return VectorSearchFilter(
            matches=tuple(matches),
            excludes=(VectorMatch("object_id", (source_object_id,)),),
        )

    def _target_rows(self, membership_ids: tuple[str, ...]) -> dict[str, dict]:
        if not membership_ids:
            return {}
        marks = ",".join("?" for _ in membership_ids)
        rows = self.db.execute(
            f"""SELECT m.id AS membership_id,m.representation_id,m.object_id,m.version_id,
                       m.target_kind,f.key AS facet,o.name,o.status,o.current_version_id,
                       pc.key AS primary_class
                FROM knowledge_search_representation_memberships m
                JOIN object_version_lifecycle l
                  ON l.version_id=m.version_id AND l.state='accepted'
                JOIN objects o ON o.id=m.object_id
                JOIN object_version_classification_snapshots cs ON cs.version_id=m.version_id
                JOIN object_classes pc ON pc.id=cs.primary_class_id
                LEFT JOIN facet_definitions f ON f.id=m.facet_id
                WHERE m.id IN ({marks})""",
            membership_ids,
        ).fetchall()
        return {row["membership_id"]: dict(row) for row in rows}

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
        """Return current Objects most similar to one Object overall or one Facet.

        The source Object is excluded. Candidates default to the same Primary Class.
        Facet mode compares only the same Facet and never falls back to overall similarity.
        """

        if not 1 <= limit <= 1000:
            raise ValueError("Similarity limit must be between 1 and 1000")
        facet = facet.strip() if facet is not None else None
        if facet == "":
            raise ValueError("Facet key must be non-empty")

        source = self._source_context(object_id, source_version_id)
        membership = self._source_membership(source, facet)
        try:
            query_vector = self.repository.embedding_store.representation_embedding(
                self.space.space_id, membership["representation_id"]
            )
        except ValueError as exc:
            raise RuntimeError(
                "Source similarity representation has no embedding in this Embedding Space"
            ) from exc

        candidate_limit = min(1000, max(limit, limit * 2))
        hits = self.vector_index.search(
            self.space,
            query_vector,
            limit=candidate_limit,
            filters=self._query_filter(
                facet=facet,
                primary_class=source["primary_class"],
                cross_class=cross_class,
                include_archived=include_archived,
                source_object_id=object_id,
            ),
        )
        details = self._target_rows(tuple(hit.point_id for hit in hits))
        expected_kind = "facet" if facet is not None else "object_overall"

        best_by_object: dict[str, tuple[float, int, dict]] = {}
        for hit in hits:
            row = details.get(hit.point_id)
            if row is None or row["object_id"] == object_id:
                continue
            if row["current_version_id"] != row["version_id"]:
                continue
            if not include_archived and row["status"] != "active":
                continue
            if row["target_kind"] != expected_kind:
                continue
            if facet is not None and row["facet"] != facet:
                continue
            if not cross_class and row["primary_class"] != source["primary_class"]:
                continue
            previous = best_by_object.get(row["object_id"])
            candidate = (float(hit.score), hit.rank, row)
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
        )
