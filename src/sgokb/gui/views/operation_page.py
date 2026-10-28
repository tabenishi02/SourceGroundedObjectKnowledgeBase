"""Shared queued-operation behavior for P-GUI domain pages."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QLabel, QWidget

from sgokb.gui.operations import GuiOperationRequest
from sgokb.gui.worker import BackendCoordinator
from sgokb.gui.workspace import WorkspaceState
from sgokb.operation_contracts import OperationFailure, OperationOutcome


class OperationPage(QWidget):
    """Base QWidget that owns only presentation state and queued request correlation."""

    def __init__(self, backend: BackendCoordinator, parent=None) -> None:
        super().__init__(parent)
        self.backend = backend
        self.workspace = WorkspaceState.closed()
        self.operation_status = QLabel("Open a Workspace to use this page.", self)
        self.operation_status.setWordWrap(True)
        self._pending: dict[str, tuple[str, Callable[[OperationOutcome], None] | None]] = {}
        self.backend.operation_finished.connect(self._on_operation_finished)
        self.backend.operation_failed.connect(self._on_operation_failed)
        self.backend.operation_warning.connect(self._on_operation_warning)

    def set_workspace(self, state: WorkspaceState) -> None:
        changed = state.db_path != self.workspace.db_path or state.is_open != self.workspace.is_open
        self.workspace = state
        self.setEnabled(state.is_open)
        if not state.is_open:
            self.operation_status.setText("Open a Workspace to use this page.")
        elif changed:
            self.operation_status.setText(f"Workspace: {state.db_path}")
            self.workspace_changed()

    def workspace_changed(self) -> None:
        """Hook called after a different open Workspace becomes active."""

    def submit(
        self,
        operation_id: str,
        arguments: Mapping[str, object] | None = None,
        *,
        callback: Callable[[OperationOutcome], None] | None = None,
        summary: str | None = None,
    ) -> str | None:
        if not self.workspace.is_open or self.workspace.db_path is None:
            self.operation_status.setText("No active Workspace.")
            return None
        request = GuiOperationRequest.create(
            self.workspace.db_path,
            operation_id,
            dict(arguments or {}),
        )
        self._pending[request.request_id] = (operation_id, callback)
        self.operation_status.setText(summary or f"Running {operation_id}...")
        self.backend.submit_request(request)
        return request.request_id

    @Slot(str, object)
    def _on_operation_finished(self, request_id: str, outcome: object) -> None:
        pending = self._pending.pop(request_id, None)
        if pending is None:
            return
        operation_id, callback = pending
        if not isinstance(outcome, OperationOutcome):
            self.operation_status.setText(f"{operation_id}: invalid backend result")
            return
        self.operation_status.setText(f"{operation_id}: {outcome.state}")
        if callback is not None:
            callback(outcome)

    @Slot(str, object)
    def _on_operation_failed(self, request_id: str, failure: object) -> None:
        pending = self._pending.pop(request_id, None)
        if pending is None:
            return
        operation_id, _callback = pending
        if isinstance(failure, OperationFailure):
            self.operation_status.setText(
                f"{operation_id}: [{failure.category}/{failure.code}] {failure.message}"
            )
        else:
            self.operation_status.setText(f"{operation_id}: {failure}")

    @Slot(str, str)
    def _on_operation_warning(self, request_id: str, message: str) -> None:
        if request_id in self._pending:
            self.operation_status.setText(f"Warning: {message}")
