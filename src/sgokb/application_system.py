"""Transport-neutral System / Recovery operator applications."""

from __future__ import annotations

from pathlib import Path

from .application_derived import DerivedSearchOperatorApplication
from .application_maintenance import DerivedMaintenanceRuntimeUnavailableError
from .composite_recovery import (
    composite_restore_apply,
    composite_restore_plan,
    create_composite_backup,
    verify_composite_backup,
)
from .retrieval import KnowledgeVectorIndexBuilder
from .runtime_health import RuntimeHealthApplication
from .system_ops import (
    backup_status,
    create_backup,
    index_status,
    integrity,
    restore_apply,
    restore_plan,
    system_status,
)


class SystemOperatorApplication:
    def __init__(self, repository, db_path: str | Path, *, runtime_factory) -> None:
        self.repository = repository
        self.db_path = Path(db_path)
        self.runtime_factory = runtime_factory

    def status(self):
        return system_status(self.repository, self.db_path)

    def runtime_status(self):
        return RuntimeHealthApplication(
            self.repository,
            self.db_path,
            self.runtime_factory,
        ).status()

    def integrity(self):
        return integrity(self.repository)

    def _derived(self, *, semantic_runtime: bool):
        runtime = {}
        if semantic_runtime:
            try:
                provider, vector = self.runtime_factory.routed_semantic_runtime(self.repository)
            except DerivedMaintenanceRuntimeUnavailableError:
                raise
            except Exception as exc:
                raise DerivedMaintenanceRuntimeUnavailableError(str(exc)) from exc
            runtime = {"embedding_provider": provider, "vector_index": vector}
        return DerivedSearchOperatorApplication(self.repository, **runtime)

    def derived_status(self, object_id: str | None = None, *, semantic_runtime: bool = False):
        return self._derived(semantic_runtime=semantic_runtime).status(object_id)

    def derived_sync(self, object_id: str | None = None, *, semantic_runtime: bool = False):
        return self._derived(semantic_runtime=semantic_runtime).sync(
            object_id, semantic=semantic_runtime
        )

    def index_status(self):
        return index_status(self.repository)

    def index_rebuild(self):
        provider, vector = self.runtime_factory.routed_semantic_runtime(self.repository)
        return KnowledgeVectorIndexBuilder(self.repository, vector).rebuild(provider.space)

    def backup_status(self, *, root: str | Path = "backups"):
        return backup_status(Path(root))

    def backup_create(
        self, *, output: str | Path | None = None, root: str | Path = "backups"
    ):
        return create_backup(
            self.repository,
            None if output is None else Path(output),
            Path(root),
        )

    def composite_backup_create(
        self,
        *,
        incoming_root: str | Path,
        output: str | Path | None = None,
        root: str | Path = "backups",
    ):
        return create_composite_backup(
            self.repository,
            incoming_root=Path(incoming_root),
            output=None if output is None else Path(output),
            root=Path(root),
        )


class RecoveryOperatorApplication:
    """Path-only maintenance actions that do not require opening target Repository."""

    def composite_backup_verify(self, backup: str | Path):
        return verify_composite_backup(Path(backup))

    def restore_plan(self, backup: str | Path, *, db_target: str | Path):
        return restore_plan(Path(backup), Path(db_target))

    def restore_apply(
        self,
        backup: str | Path,
        *,
        db_target: str | Path,
        acknowledge_overwrite: bool = False,
    ):
        return restore_apply(
            Path(backup),
            Path(db_target),
            acknowledge_overwrite=acknowledge_overwrite,
        )

    def composite_restore_plan(
        self,
        backup: str | Path,
        *,
        db_target: str | Path,
        raw_root: str | Path,
        incoming_root: str | Path,
    ):
        return composite_restore_plan(
            Path(backup),
            db_target=Path(db_target),
            raw_root=Path(raw_root),
            incoming_root=Path(incoming_root),
        )

    def composite_restore_apply(
        self,
        backup: str | Path,
        *,
        db_target: str | Path,
        raw_root: str | Path,
        incoming_root: str | Path,
        acknowledge_overwrite: bool = False,
    ):
        return composite_restore_apply(
            Path(backup),
            db_target=Path(db_target),
            raw_root=Path(raw_root),
            incoming_root=Path(incoming_root),
            acknowledge_overwrite=acknowledge_overwrite,
        )
