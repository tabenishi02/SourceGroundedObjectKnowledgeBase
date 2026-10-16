"""Application-facing helpers for incremental and full Vector Index maintenance."""

from __future__ import annotations

from sgokb.domain import EmbeddingSpaceSpec, VectorIndexPoint

from .hybrid_search import KnowledgeVectorIndexBuilder


class KnowledgeVectorMaintenanceBuilder(KnowledgeVectorIndexBuilder):
    """Build membership-scoped Vector points without mutating derived lifecycle state.

    The Phase I builder already owns the canonical metadata projection used by
    Semantic/Hybrid/Similarity retrieval.  This subclass reuses that projection
    while adding an Object-scoped point set for incremental maintenance.  Lifecycle
    state remains the responsibility of the Application layer.
    """

    def points_for_object(
        self,
        space: EmbeddingSpaceSpec,
        object_id: str,
    ) -> tuple[VectorIndexPoint, ...]:
        rows = [row for row in self._membership_rows() if row["object_id"] == object_id]
        if not rows:
            raise ValueError("Vector Index sync found no accepted Search Representation memberships")

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
        """Upsert every accepted membership for one Object.

        Re-upserting historical memberships is intentional: after current Version
        promotion their `is_current` metadata must be rewritten from true to false.
        """

        points = self.points_for_object(space, object_id)
        written = self.vector_index.upsert(space, points)
        return len(points), int(written)

    def rebuild_backend(self, space: EmbeddingSpaceSpec):
        """Rebuild the backend from canonical memberships + persisted Embeddings only."""

        points = self.points(space)
        metadata = self.vector_index.rebuild(space, points)
        return metadata, len(points)
