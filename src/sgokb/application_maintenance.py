"""Transport-neutral local maintenance application boundary for derived artifacts."""

from __future__ import annotations

from dataclasses import dataclass

from .domain import DerivedState
from .retrieval import SearchRepresentationBuilder


class DerivedMaintenanceError(RuntimeError):
    """A derived maintenance operation failed without changing canonical Knowledge."""


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


class DerivedSearchMaintenanceApplication:
    """Application boundary for rebuildable Object Knowledge search artifacts.

    N-04P-02 intentionally implements only Search Representation synchronization.
    Embedding and Vector Index synchronization are added by subsequent prerequisite
    tasks and must not be silently invoked here.
    """

    SEARCH_REPRESENTATION_KIND = "search_representation"

    def __init__(self, repository, *, search_representation_builder=None) -> None:
        self._repository = repository
        self._builder = search_representation_builder or SearchRepresentationBuilder(repository)

    def _search_representation_state(self, object_id: str):
        try:
            states = self._repository.version_store.derived_states(object_id)
        except ValueError as exc:
            raise DerivedMaintenanceError(str(exc)) from exc
        state = next(
            (item for item in states if item.kind == self.SEARCH_REPRESENTATION_KIND),
            None,
        )
        if state is None:
            raise DerivedMaintenanceError(
                "Object has no search_representation derived state; an accepted Version is required"
            )
        return state

    def _membership_counts(self, object_id: str, version_id: str) -> tuple[int, int]:
        memberships = self._repository.semantic_store.knowledge_search_memberships(
            object_id=object_id,
            version_id=version_id,
        )
        return len(memberships), len({row["representation_id"] for row in memberships})

    def sync_search_representation(self, object_id: str) -> SearchRepresentationSyncResult:
        """Synchronize Search Representations for one current accepted Object Version.

        The operation is local and deterministic. It never initializes an embedding
        provider or Vector backend. Completion is revision-guarded so an older attempt
        cannot mark a newly promoted Version as ready.
        """

        state = self._search_representation_state(object_id)
        current_version_id = self._repository.version_store.current_version_id(object_id)
        if current_version_id is None:
            raise DerivedMaintenanceError("Object has no accepted current Version")
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
