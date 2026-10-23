"""Application-facing helpers for incremental and full Vector Index maintenance."""

from __future__ import annotations

from sgokb.domain import EmbeddingSpaceSpec, VectorIndexPoint

from .hybrid_search_r2 import KnowledgeVectorIndexBuilder as _R2KnowledgeVectorIndexBuilder


class KnowledgeVectorMaintenanceBuilder(_R2KnowledgeVectorIndexBuilder):
    """Build generation-scoped Vector points without lifecycle side effects.

    If a generation is supplied explicitly, that exact membership set is used.
    Otherwise an active Knowledge Search generation is resolved for normal
    maintenance. Before R2-07 bootstrap there is no pointer, so the historical
    Phase-I all-membership compatibility behavior remains available.
    """

    def __init__(
        self,
        repository,
        vector_index,
        *,
        generation_id: str | None = None,
    ) -> None:
        if generation_id is None:
            row = repository.db.execute(
                """SELECT active_generation_id
                   FROM knowledge_search_active_generation
                   WHERE scope='knowledge'"""
            ).fetchone()
            if row is not None:
                generation_id = row["active_generation_id"]
        super().__init__(
            repository,
            vector_index,
            generation_id=generation_id,
        )

    def points_for_object(
        self,
        space: EmbeddingSpaceSpec,
        object_id: str,
    ) -> tuple[VectorIndexPoint, ...]:
        rows = [row for row in self._membership_rows() if row["object_id"] == object_id]
        if not rows:
            raise ValueError(
                "Vector Index sync found no accepted Search Representation memberships"
            )

        representation_ids = tuple(dict.fromkeys(row["representation_id"] for row in rows))
        embeddings = {
            row["representation_id"]: row["vector"]
            for row in self.repository.embedding_store.embedding_rows(
                space.space_id,
                representation_ids,
            )
        }
        missing = sorted(
            representation_id
            for representation_id in representation_ids
            if representation_id not in embeddings
        )
        if missing:
            raise ValueError(
                "Vector Index sync requires embeddings for every accepted Object membership; "
                f"missing={len(missing)}"
            )

        additional = self._additional_classes_by_version()
        return tuple(
            VectorIndexPoint(
                point_id=row["id"],
                vector=tuple(embeddings[row["representation_id"]]),
                metadata=self._metadata_from_row(row, additional.get(row["version_id"], ())),
            )
            for row in rows
        )

    def upsert_object(self, space: EmbeddingSpaceSpec, object_id: str) -> tuple[int, int]:
        """Upsert every accepted membership for one Object in the selected generation.

        Re-upserting historical memberships is intentional: after current Version
        promotion their ``is_current`` metadata must be rewritten from true to false.
        """

        points = self.points_for_object(space, object_id)
        written = self.vector_index.upsert(space, points)
        return len(points), int(written)

    def _audit_rebuild(self, space: EmbeddingSpaceSpec, points) -> None:
        auditor = getattr(self.vector_index, "audit_memberships", None)
        if auditor is None or self.generation_id is None:
            return
        row = self.db.execute(
            "SELECT contract_key FROM knowledge_search_generations WHERE id=?",
            (self.generation_id,),
        ).fetchone()
        if row is None:
            raise ValueError("Vector Index rebuild generation disappeared during audit")
        auditor(
            space,
            tuple(point.point_id for point in points),
            generation_id=self.generation_id,
            require_generation_payload=(
                row["contract_key"] == "n05d04r2-hierarchical-v2"
            ),
        )

    def rebuild_backend(self, space: EmbeddingSpaceSpec):
        """Rebuild and audit the selected generation from persisted derived state."""

        points = self.points(space)
        metadata = self.vector_index.rebuild(space, points)
        self._audit_rebuild(space, points)
        return metadata, len(points)

    def rebuild(self, space: EmbeddingSpaceSpec):
        """Compatibility entrypoint retaining Vector-only rebuild semantics.

        Unlike the original Phase I implementation, this method does not mutate
        ``object_derived_states``. Lifecycle promotion is revision-guarded by
        ``DerivedSearchMaintenanceApplication.rebuild_vector_index()``.
        """

        metadata, _ = self.rebuild_backend(space)
        return metadata
