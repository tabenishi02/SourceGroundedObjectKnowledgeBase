"""Controller for safe active-Workspace selection."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from sgokb.operation_contracts import OperationFailure, OperationOutcome

from ..worker import BackendCoordinator
from ..workspace import WorkspaceSettings, WorkspaceState


class WorkspaceController(QObject):
    """Promote a candidate database only after backend validation succeeds."""

    state_changed = Signal(object)
    open_failed = Signal(str, object)

    def __init__(
        self,
        backend: BackendCoordinator,
        settings: WorkspaceSettings,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.backend = backend
        self.settings = settings
        self._state = WorkspaceState.closed()
        self._pending: dict[str, Path] = {}
        self.backend.operation_finished.connect(self._on_operation_finished)
        self.backend.operation_failed.connect(self._on_operation_failed)

    @property
    def state(self) -> WorkspaceState:
        return self._state

    def open_workspace(self, path: str | Path) -> str | None:
        candidate = Path(path).expanduser().resolve()
        if self.backend.is_busy:
            failure = OperationFailure(
                "system.status",
                "blocked",
                "workspace_switch_blocked",
                "Workspace cannot be changed while a backend operation is running.",
            )
            self.open_failed.emit(str(candidate), failure)
            return None
        request_id = self.backend.submit(candidate, "system.status")
        self._pending[request_id] = candidate
        return request_id

    def refresh(self) -> str | None:
        if not self._state.is_open or self._state.db_path is None:
            return None
        return self.open_workspace(self._state.db_path)

    @Slot(str, object)
    def _on_operation_finished(self, request_id: str, outcome: object) -> None:
        candidate = self._pending.pop(request_id, None)
        if candidate is None:
            return
        if not isinstance(outcome, OperationOutcome):
            failure = OperationFailure(
                "system.status",
                "internal",
                "invalid_workspace_probe_result",
                "Workspace probe returned an unexpected result object.",
            )
            self.open_failed.emit(str(candidate), failure)
            return
        status = outcome.data if isinstance(outcome.data, dict) else {"result": outcome.data}
        self._state = WorkspaceState.opened(candidate, status)
        self.settings.record_workspace(candidate)
        self.state_changed.emit(self._state)

    @Slot(str, object)
    def _on_operation_failed(self, request_id: str, failure: object) -> None:
        candidate = self._pending.pop(request_id, None)
        if candidate is None:
            return
        self.open_failed.emit(str(candidate), failure)
