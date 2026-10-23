"""Operator-facing application facade for the rebuildable Derived Search pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from .application_generation import (
    LEGACY_GENERATION_ID,
    KnowledgeSearchGenerationApplication,
)
from .application_maintenance import (
    DerivedMaintenanceError,
    DerivedMaintenanceRuntimeUnavailableError,
    DerivedMaintenanceSupersededError,
    DerivedSearchMaintenanceApplication,
)
from .retrieval.generation import (
    GenerationAwareSearchRepresentationBuilder,
    route_generation_vector_index,
    vector_generation_scope,
)


@dataclass(frozen=True, slots=True)
class DerivedSyncStageResult:
    kind: str
    status: str
    result: object | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class DerivedObjectSyncResult:
    object_id: str
    current_version_id: str
    semantic_requested: bool
    complete: bool
    stages: tuple[DerivedSyncStageResult, ...]


@dataclass(frozen=True, slots=True)
class DerivedBatchSyncResult:
    semantic_requested: bool
    object_count: int
    completed_object_count: int
    partial: bool
    objects: tuple[DerivedObjectSyncResult, ...]


class DerivedSearchOperatorApplication:
    """Public Application boundary used by ``system derived`` operator commands.

    Normal incremental maintenance follows the active generation after R2-07
    bootstrap. Generation lifecycle methods are explicit operator actions and never
    run as a side effect of read traffic.
    """

    _PIPELINE_KINDS = ("search_representation", "embedding", "vector_index", "rendering")

    def __init__(self, repository, *, embedding_provider=None, vector_index=None) -> None:
        self._repository = repository
        self._embedding_provider = embedding_provider
        self._vector_index = route_generation_vector_index(repository, vector_index)
        self._generation = KnowledgeSearchGenerationApplication(
            repository,
            embedding_provider=embedding_provider,
            vector_index=self._vector_index,
        )
        self._maintenance = DerivedSearchMaintenanceApplication(
            repository,
            search_representation_builder=GenerationAwareSearchRepresentationBuilder(repository),
            embedding_provider=embedding_provider,
            vector_index=self._vector_index,
            embedding_space=(embedding_provider.space if embedding_provider is not None else None),
        )

    def _target_rows(self, object_id: str | None) -> tuple[dict, ...]:
        if object_id is not None:
            row = self._repository.one(
                "SELECT id,name,current_version_id FROM objects WHERE id=?",
                (object_id,),
            )
            if row is None:
                raise DerivedMaintenanceError(f"Unknown Object ID: {object_id}")
            if row["current_version_id"] is None:
                raise DerivedMaintenanceError("Object has no accepted current Version")
            return (dict(row),)
        return tuple(
            dict(row)
            for row in self._repository.rows(
                """SELECT id,name,current_version_id FROM objects
                   WHERE current_version_id IS NOT NULL ORDER BY id"""
            )
        )

    @staticmethod
    def _state_payload(state) -> dict:
        return {
            "kind": state.kind,
            "target_version_id": state.target_version_id,
            "status": state.status.value,
            "revision": state.revision,
            "last_error": state.last_error,
            "updated_at": state.updated_at,
        }

    def _runtime_payload(self) -> dict:
        provider = self._embedding_provider
        vector = self._vector_index
        if provider is None or vector is None:
            return {
                "semantic_configured": False,
                "embedding_space": None,
                "vector_backend": None,
            }

        space = provider.space
        backend = {
            "backend_key": vector.backend_key,
            "available": False,
            "metadata": None,
            "error": None,
        }
        try:
            metadata = vector.metadata(space)
            backend["available"] = True
            backend["metadata"] = metadata
        except Exception as exc:
            backend["error"] = f"{type(exc).__name__}: {exc}"
        return {
            "semantic_configured": True,
            "embedding_space": {
                "space_id": space.space_id,
                "provider_key": space.provider_key,
                "model": space.model,
                "model_revision": space.model_revision,
                "dimension": space.dimension,
            },
            "vector_backend": backend,
        }

    def status(self, object_id: str | None = None) -> dict:
        """Return operator-visible derived state without changing data."""

        runtime = self._runtime_payload()
        space = self._embedding_provider.space if self._embedding_provider is not None else None
        objects = []
        for row in self._target_rows(object_id):
            current_version_id = row["current_version_id"]
            states = self._repository.version_store.derived_states(row["id"])
            by_kind = {state.kind: state for state in states}
            memberships = self._maintenance._current_memberships(row["id"], current_version_id)
            representation_ids = tuple(
                dict.fromkeys(item["representation_id"] for item in memberships)
            )
            embedding = None
            if space is not None:
                space_exists = self._repository.one(
                    "SELECT 1 FROM search_embedding_spaces WHERE id=?",
                    (space.space_id,),
                )
                embedded_ids: set[str] = set()
                if space_exists is not None and representation_ids:
                    embedded_ids = {
                        item["representation_id"]
                        for item in self._repository.embedding_store.embedding_rows(
                            space.space_id,
                            representation_ids,
                        )
                    }
                embedding = {
                    "space_id": space.space_id,
                    "representation_count": len(representation_ids),
                    "embedding_count": len(embedded_ids),
                    "missing_embedding_count": len(representation_ids) - len(embedded_ids),
                }
            objects.append(
                {
                    "object_id": row["id"],
                    "name": row["name"],
                    "current_version_id": current_version_id,
                    "derived_states": [
                        self._state_payload(by_kind[kind])
                        for kind in self._PIPELINE_KINDS
                        if kind in by_kind
                    ],
                    "search_representations": {
                        "membership_count": len(memberships),
                        "unique_representation_count": len(representation_ids),
                    },
                    "embedding": embedding,
                }
            )
        return {
            "object_count": len(objects),
            "objects": objects,
            "runtime": runtime,
            "generation": self._generation.status(),
        }

    def generation_status(self) -> dict:
        return self._generation.status()

    def bootstrap_legacy_generation(self, *, reason: str = "R2-07 legacy bootstrap"):
        return self._generation.bootstrap_legacy(reason=reason)

    def build_r2_candidate_generation(self):
        return self._generation.build_r2_candidate()

    def cutover_generation(
        self,
        generation_id: str,
        *,
        reason: str = "R2-07 cutover",
        smoke: bool = True,
    ):
        return self._generation.cutover(
            generation_id,
            reason=reason,
            smoke=smoke,
        )

    def rollback_generation(
        self,
        generation_id: str = LEGACY_GENERATION_ID,
        *,
        reason: str = "R2-07 rollback rehearsal",
        smoke: bool = True,
    ):
        return self._generation.rollback(
            generation_id,
            reason=reason,
            smoke=smoke,
        )

    def recover_interrupted_generations(
        self,
        *,
        reason: str = "R2-07 interrupted build recovery",
    ) -> int:
        return self._generation.recover_interrupted_builds(reason=reason)

    def _sync_one(self, row: dict, *, semantic: bool) -> DerivedObjectSyncResult:
        active = self._repository.one(
            "SELECT active_generation_id FROM knowledge_search_active_generation"
        )
        generation_id = active["active_generation_id"] if active is not None else None
        with vector_generation_scope(self._vector_index, generation_id):
            result = self._sync_one_pinned(row, semantic=semantic)
            current = self._repository.one(
                "SELECT active_generation_id FROM knowledge_search_active_generation"
            )
            current_id = current["active_generation_id"] if current is not None else None
            if current_id != generation_id:
                raise DerivedMaintenanceSupersededError("Generation changed during derived sync")
            return result

    def _sync_one_pinned(self, row: dict, *, semantic: bool) -> DerivedObjectSyncResult:
        stages: list[DerivedSyncStageResult] = []
        pipeline = [("search_representation", self._maintenance.sync_search_representation)]
        if semantic:
            pipeline.extend(
                (
                    ("embedding", self._maintenance.sync_embedding),
                    ("vector_index", self._maintenance.sync_vector_index),
                )
            )

        for kind, operation in pipeline:
            try:
                result = operation(row["id"])
            except DerivedMaintenanceRuntimeUnavailableError as exc:
                stages.append(
                    DerivedSyncStageResult(
                        kind=kind,
                        status="runtime_unavailable",
                        error=str(exc),
                    )
                )
                return DerivedObjectSyncResult(
                    object_id=row["id"],
                    current_version_id=row["current_version_id"],
                    semantic_requested=semantic,
                    complete=False,
                    stages=tuple(stages),
                )
            except DerivedMaintenanceSupersededError as exc:
                stages.append(
                    DerivedSyncStageResult(kind=kind, status="superseded", error=str(exc))
                )
                return DerivedObjectSyncResult(
                    object_id=row["id"],
                    current_version_id=row["current_version_id"],
                    semantic_requested=semantic,
                    complete=False,
                    stages=tuple(stages),
                )
            except DerivedMaintenanceError as exc:
                states = self._repository.version_store.derived_states(row["id"])
                state = next((item for item in states if item.kind == kind), None)
                status = state.status.value if state is not None else "blocked"
                stages.append(DerivedSyncStageResult(kind=kind, status=status, error=str(exc)))
                return DerivedObjectSyncResult(
                    object_id=row["id"],
                    current_version_id=row["current_version_id"],
                    semantic_requested=semantic,
                    complete=False,
                    stages=tuple(stages),
                )
            stages.append(DerivedSyncStageResult(kind=kind, status="ready", result=result))

        return DerivedObjectSyncResult(
            object_id=row["id"],
            current_version_id=row["current_version_id"],
            semantic_requested=semantic,
            complete=True,
            stages=tuple(stages),
        )

    def sync(
        self,
        object_id: str | None = None,
        *,
        semantic: bool = False,
    ) -> DerivedBatchSyncResult:
        """Synchronize one or all current Objects in dependency order."""

        if semantic and (self._embedding_provider is None or self._vector_index is None):
            raise DerivedMaintenanceRuntimeUnavailableError(
                "Semantic derived sync requires an explicitly configured local semantic runtime"
            )
        active = self._repository.one(
            "SELECT active_generation_id FROM knowledge_search_active_generation"
        )
        generation_id = active["active_generation_id"] if active is not None else None
        rows = self._target_rows(object_id)
        results = tuple(self._sync_one(row, semantic=semantic) for row in rows)
        completed = sum(result.complete for result in results)
        if completed == len(results) and semantic and generation_id is not None:
            self._generation.refresh_active_generation(generation_id)
        return DerivedBatchSyncResult(
            semantic_requested=semantic,
            object_count=len(results),
            completed_object_count=completed,
            partial=completed != len(results),
            objects=results,
        )
