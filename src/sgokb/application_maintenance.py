"""Transport-neutral local maintenance application boundary for derived artifacts."""

from __future__ import annotations

from dataclasses import dataclass

from .domain import DerivedState
from .retrieval import SearchRepresentationBuilder
from .retrieval.vector_maintenance import KnowledgeVectorMaintenanceBuilder


class DerivedMaintenanceError(RuntimeError):
    """A derived maintenance operation failed without changing canonical Knowledge."""


class DerivedMaintenanceRuntimeUnavailableError(DerivedMaintenanceError):
    """A requested local derived runtime was not explicitly configured."""


class DerivedMaintenanceSupersededError(DerivedMaintenanceError):
    """A maintenance attempt completed after its derived revision had been superseded."""


@dataclass(frozen=True, slots=True)
class SearchRepresentationSyncResult:
    object_id: str
    version_id: str
    revision: int
    representation_count: int
    unique_representation_count: int
    changed: bool
    state: str


@dataclass(frozen=True, slots=True)
class EmbeddingSyncResult:
    object_id: str
    version_id: str
    revision: int
    space_id: str
    representation_count: int
    reused_embedding_count: int
    created_embedding_count: int
    changed: bool
    state: str


@dataclass(frozen=True, slots=True)
class VectorIndexSyncResult:
    object_id: str
    version_id: str
    revision: int
    space_id: str
    backend_key: str
    point_count: int
    written_point_count: int
    changed: bool
    state: str


@dataclass(frozen=True, slots=True)
class VectorIndexRebuildResult:
    space_id: str
    backend_key: str
    point_count: int
    ready_object_count: int
    state: str


class DerivedSearchMaintenanceApplication:
    """Application boundary for rebuildable Object Knowledge search artifacts.

    Search Representation synchronization is deterministic and runtime-free.
    Embedding synchronization requires an explicitly injected local provider.
    Vector synchronization requires an explicitly injected Vector backend plus an
    Embedding Space. No method constructs a cloud provider or silently changes
    runtime backends.
    """

    SEARCH_REPRESENTATION_KIND = "search_representation"
    EMBEDDING_KIND = "embedding"
    VECTOR_INDEX_KIND = "vector_index"

    def __init__(
        self,
        repository,
        *,
        search_representation_builder=None,
        embedding_provider=None,
        vector_index=None,
        embedding_space=None,
    ) -> None:
        self._repository = repository
        self._builder = search_representation_builder or SearchRepresentationBuilder(repository)
        self._embedding_provider = embedding_provider
        self._vector_index = vector_index
        self._embedding_space = embedding_space

    def _derived_state(self, object_id: str, kind: str):
        try:
            states = self._repository.version_store.derived_states(object_id)
        except ValueError as exc:
            raise DerivedMaintenanceError(str(exc)) from exc
        state = next((item for item in states if item.kind == kind), None)
        if state is None:
            raise DerivedMaintenanceError(
                f"Object has no {kind} derived state; an accepted Version is required"
            )
        return state

    def _search_representation_state(self, object_id: str):
        return self._derived_state(object_id, self.SEARCH_REPRESENTATION_KIND)

    def _membership_counts(self, object_id: str, version_id: str) -> tuple[int, int]:
        memberships = self._repository.semantic_store.knowledge_search_memberships(
            object_id=object_id,
            version_id=version_id,
        )
        return len(memberships), len({row["representation_id"] for row in memberships})

    def _current_version_id(self, object_id: str) -> str:
        try:
            current_version_id = self._repository.version_store.current_version_id(object_id)
        except ValueError as exc:
            raise DerivedMaintenanceError(str(exc)) from exc
        if current_version_id is None:
            raise DerivedMaintenanceError("Object has no accepted current Version")
        return current_version_id

    def _vector_runtime(self):
        if self._vector_index is None:
            raise DerivedMaintenanceRuntimeUnavailableError(
                "Vector Index maintenance requires an explicitly injected Vector backend"
            )
        space = self._embedding_space
        if space is None and self._embedding_provider is not None:
            space = self._embedding_provider.space
        if space is None:
            raise DerivedMaintenanceRuntimeUnavailableError(
                "Vector Index maintenance requires an explicitly selected Embedding Space"
            )
        return space, self._vector_index

    def _vector_catalog_snapshot(self):
        rows = self._repository.rows(
            """SELECT id,current_version_id FROM objects
               WHERE current_version_id IS NOT NULL ORDER BY id"""
        )
        return tuple(
            (
                row["id"],
                row["current_version_id"],
                self._repository.version_store.derived_states(row["id"]),
            )
            for row in rows
        )

    def sync_search_representation(self, object_id: str) -> SearchRepresentationSyncResult:
        """Synchronize Search Representations for one current accepted Object Version.

        The operation is local and deterministic. It never initializes an embedding
        provider or Vector backend. Completion is revision-guarded so an older attempt
        cannot mark a newly promoted Version as ready.
        """

        state = self._search_representation_state(object_id)
        current_version_id = self._current_version_id(object_id)
        if state.target_version_id != current_version_id:
            raise DerivedMaintenanceError(
                "search_representation target Version does not match the Object current Version"
            )

        version_id = state.target_version_id
        revision = state.revision
        if state.status is DerivedState.READY:
            count, unique_count = self._membership_counts(object_id, version_id)
            return SearchRepresentationSyncResult(
                object_id=object_id,
                version_id=version_id,
                revision=revision,
                representation_count=count,
                unique_representation_count=unique_count,
                changed=False,
                state=DerivedState.READY.value,
            )

        try:
            self._builder.materialize_version(version_id)
        except Exception as exc:
            marked = self._repository.version_store.mark_derived_state(
                object_id,
                self.SEARCH_REPRESENTATION_KIND,
                revision,
                DerivedState.FAILED,
                error=f"{type(exc).__name__}: {exc}",
            )
            if not marked:
                raise DerivedMaintenanceSupersededError(
                    "Search Representation sync failed after its derived revision was superseded"
                ) from exc
            raise DerivedMaintenanceError(
                f"Search Representation sync failed: {type(exc).__name__}: {exc}"
            ) from exc

        marked = self._repository.version_store.mark_derived_state(
            object_id,
            self.SEARCH_REPRESENTATION_KIND,
            revision,
            DerivedState.READY,
        )
        if not marked:
            raise DerivedMaintenanceSupersededError(
                "Search Representation sync completed after its derived revision was superseded"
            )

        count, unique_count = self._membership_counts(object_id, version_id)
        return SearchRepresentationSyncResult(
            object_id=object_id,
            version_id=version_id,
            revision=revision,
            representation_count=count,
            unique_representation_count=unique_count,
            changed=True,
            state=DerivedState.READY.value,
        )

    def sync_embedding(self, object_id: str) -> EmbeddingSyncResult:
        """Incrementally synchronize current Search Representations into one Embedding Space.

        The injected provider defines the active/frozen Embedding Space for this
        maintenance attempt. Existing embeddings in that space are reused by
        representation identity; only missing representations are sent to the local
        provider. A missing provider is an unattempted runtime condition and therefore
        leaves the derived state unchanged rather than marking it failed.
        """

        if self._embedding_provider is None:
            raise DerivedMaintenanceRuntimeUnavailableError(
                "Embedding sync requires an explicitly injected local embedding provider"
            )

        current_version_id = self._current_version_id(object_id)
        search_state = self._search_representation_state(object_id)
        embedding_state = self._derived_state(object_id, self.EMBEDDING_KIND)

        if search_state.target_version_id != current_version_id:
            raise DerivedMaintenanceError(
                "search_representation target Version does not match the Object current Version"
            )
        if search_state.status is not DerivedState.READY:
            raise DerivedMaintenanceError(
                "Embedding sync requires search_representation to be ready for the current Version"
            )
        if embedding_state.target_version_id != current_version_id:
            raise DerivedMaintenanceError(
                "embedding target Version does not match the Object current Version"
            )

        version_id = embedding_state.target_version_id
        revision = embedding_state.revision
        search_revision = search_state.revision

        memberships = self._repository.semantic_store.knowledge_search_memberships(
            object_id=object_id,
            version_id=version_id,
        )
        representation_ids = tuple(dict.fromkeys(row["representation_id"] for row in memberships))
        if not representation_ids:
            raise DerivedMaintenanceError(
                "Embedding sync found no Search Representation memberships for the current Version"
            )

        try:
            space = self._embedding_provider.space
            self._repository.embedding_store.ensure_space(space)
            existing = {
                row["representation_id"]
                for row in self._repository.embedding_store.embedding_rows(
                    space.space_id,
                    representation_ids,
                )
            }
            missing_ids = tuple(
                representation_id
                for representation_id in representation_ids
                if representation_id not in existing
            )

            if missing_ids:
                records = [
                    self._repository.semantic_store.search_representation(representation_id)
                    for representation_id in missing_ids
                ]
                vectors = self._embedding_provider.embed_documents(
                    [record.content for record in records]
                )
                if len(vectors) != len(records):
                    raise ValueError(
                        "Embedding provider returned a different number of vectors than documents"
                    )
                for record, vector in zip(records, vectors):
                    self._repository.embedding_store.save_representation_embedding(
                        space,
                        record.representation_id,
                        vector,
                    )

            current_search_state = self._search_representation_state(object_id)
            if (
                current_search_state.target_version_id != version_id
                or current_search_state.revision != search_revision
                or current_search_state.status is not DerivedState.READY
            ):
                raise DerivedMaintenanceSupersededError(
                    "Embedding sync dependency changed while the maintenance attempt was running"
                )

            completed = {
                row["representation_id"]
                for row in self._repository.embedding_store.embedding_rows(
                    space.space_id,
                    representation_ids,
                )
            }
            incomplete = [
                representation_id
                for representation_id in representation_ids
                if representation_id not in completed
            ]
            if incomplete:
                raise ValueError(
                    "Embedding sync did not persist every current Search Representation; "
                    f"missing={len(incomplete)}"
                )
        except DerivedMaintenanceSupersededError:
            raise
        except Exception as exc:
            marked = self._repository.version_store.mark_derived_state(
                object_id,
                self.EMBEDDING_KIND,
                revision,
                DerivedState.FAILED,
                error=f"{type(exc).__name__}: {exc}",
            )
            if not marked:
                raise DerivedMaintenanceSupersededError(
                    "Embedding sync failed after its derived revision was superseded"
                ) from exc
            raise DerivedMaintenanceError(
                f"Embedding sync failed: {type(exc).__name__}: {exc}"
            ) from exc

        marked = self._repository.version_store.mark_derived_state(
            object_id,
            self.EMBEDDING_KIND,
            revision,
            DerivedState.READY,
        )
        if not marked:
            raise DerivedMaintenanceSupersededError(
                "Embedding sync completed after its derived revision was superseded"
            )

        created_count = len(missing_ids)
        reused_count = len(representation_ids) - created_count
        changed = embedding_state.status is not DerivedState.READY or created_count > 0
        return EmbeddingSyncResult(
            object_id=object_id,
            version_id=version_id,
            revision=revision,
            space_id=space.space_id,
            representation_count=len(representation_ids),
            reused_embedding_count=reused_count,
            created_embedding_count=created_count,
            changed=changed,
            state=DerivedState.READY.value,
        )

    def sync_vector_index(self, object_id: str) -> VectorIndexSyncResult:
        """Incrementally upsert membership-scoped Vector points for one Object.

        Every accepted membership for the Object is re-upserted so historical points
        remain queryable and their `is_current` metadata is refreshed after Version
        promotion. Missing Embeddings are explicit failures; this method never creates
        Embeddings or invokes an embedding provider.
        """

        space, vector_index = self._vector_runtime()
        current_version_id = self._current_version_id(object_id)
        search_state = self._search_representation_state(object_id)
        embedding_state = self._derived_state(object_id, self.EMBEDDING_KIND)
        vector_state = self._derived_state(object_id, self.VECTOR_INDEX_KIND)

        for name, state in (
            (self.SEARCH_REPRESENTATION_KIND, search_state),
            (self.EMBEDDING_KIND, embedding_state),
            (self.VECTOR_INDEX_KIND, vector_state),
        ):
            if state.target_version_id != current_version_id:
                raise DerivedMaintenanceError(
                    f"{name} target Version does not match the Object current Version"
                )
        if search_state.status is not DerivedState.READY:
            raise DerivedMaintenanceError(
                "Vector Index sync requires search_representation to be ready"
            )
        if embedding_state.status is not DerivedState.READY:
            raise DerivedMaintenanceError("Vector Index sync requires embedding to be ready")

        version_id = vector_state.target_version_id
        revision = vector_state.revision
        search_revision = search_state.revision
        embedding_revision = embedding_state.revision
        builder = KnowledgeVectorMaintenanceBuilder(self._repository, vector_index)

        try:
            point_count, written_count = builder.upsert_object(space, object_id)

            current_search_state = self._search_representation_state(object_id)
            current_embedding_state = self._derived_state(object_id, self.EMBEDDING_KIND)
            if (
                self._current_version_id(object_id) != version_id
                or current_search_state.target_version_id != version_id
                or current_search_state.revision != search_revision
                or current_search_state.status is not DerivedState.READY
                or current_embedding_state.target_version_id != version_id
                or current_embedding_state.revision != embedding_revision
                or current_embedding_state.status is not DerivedState.READY
            ):
                raise DerivedMaintenanceSupersededError(
                    "Vector Index sync dependency changed while the maintenance attempt was running"
                )
        except DerivedMaintenanceSupersededError:
            raise
        except Exception as exc:
            marked = self._repository.version_store.mark_derived_state(
                object_id,
                self.VECTOR_INDEX_KIND,
                revision,
                DerivedState.FAILED,
                error=f"{type(exc).__name__}: {exc}",
            )
            if not marked:
                raise DerivedMaintenanceSupersededError(
                    "Vector Index sync failed after its derived revision was superseded"
                ) from exc
            raise DerivedMaintenanceError(
                f"Vector Index sync failed: {type(exc).__name__}: {exc}"
            ) from exc

        marked = self._repository.version_store.mark_derived_state(
            object_id,
            self.VECTOR_INDEX_KIND,
            revision,
            DerivedState.READY,
        )
        if not marked:
            raise DerivedMaintenanceSupersededError(
                "Vector Index sync completed after its derived revision was superseded"
            )

        return VectorIndexSyncResult(
            object_id=object_id,
            version_id=version_id,
            revision=revision,
            space_id=space.space_id,
            backend_key=vector_index.backend_key,
            point_count=point_count,
            written_point_count=written_count,
            changed=vector_state.status is not DerivedState.READY,
            state=DerivedState.READY.value,
        )

    def rebuild_vector_index(self) -> VectorIndexRebuildResult:
        """Rebuild the complete Vector backend from SQLite memberships + Embeddings.

        This is a recovery/full-maintenance operation. It does not generate missing
        Embeddings. A catalog change during rebuild invalidates the attempt so no stale
        revision is promoted to ready.
        """

        space, vector_index = self._vector_runtime()
        before = self._vector_catalog_snapshot()
        builder = KnowledgeVectorMaintenanceBuilder(self._repository, vector_index)

        try:
            metadata, point_count = builder.rebuild_backend(space)
            if metadata.space_id != space.space_id:
                raise ValueError("Vector backend metadata returned a different Embedding Space")
            if metadata.points_count != point_count:
                raise ValueError(
                    "Vector backend metadata point count does not match rebuilt membership count"
                )
        except Exception as exc:
            raise DerivedMaintenanceError(
                f"Vector Index rebuild failed: {type(exc).__name__}: {exc}"
            ) from exc

        after = self._vector_catalog_snapshot()
        if after != before:
            raise DerivedMaintenanceSupersededError(
                "Vector Index rebuild completed after the accepted Object catalog changed"
            )

        eligible = []
        for object_id, current_version_id, states in before:
            by_kind = {state.kind: state for state in states}
            search_state = by_kind.get(self.SEARCH_REPRESENTATION_KIND)
            embedding_state = by_kind.get(self.EMBEDDING_KIND)
            vector_state = by_kind.get(self.VECTOR_INDEX_KIND)
            if search_state is None or embedding_state is None or vector_state is None:
                continue
            if not all(
                state.target_version_id == current_version_id
                for state in (search_state, embedding_state, vector_state)
            ):
                continue
            if search_state.status is not DerivedState.READY:
                continue
            if embedding_state.status is not DerivedState.READY:
                continue
            eligible.append((object_id, vector_state.revision))

        for object_id, revision in eligible:
            marked = self._repository.version_store.mark_derived_state(
                object_id,
                self.VECTOR_INDEX_KIND,
                revision,
                DerivedState.READY,
            )
            if not marked:
                raise DerivedMaintenanceSupersededError(
                    "Vector Index rebuild state promotion was superseded by a newer revision"
                )

        return VectorIndexRebuildResult(
            space_id=space.space_id,
            backend_key=vector_index.backend_key,
            point_count=point_count,
            ready_object_count=len(eligible),
            state=DerivedState.READY.value,
        )
