"""Shared queued-operation behavior for P-GUI domain pages."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QLabel, QMessageBox, QWidget

from sgokb.gui.operation_ux import confirmation_text, operation_policy
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
        self._confirmation_enabled = False
        self.backend.operation_finished.connect(self._on_operation_finished)
        self.backend.operation_failed.connect(self._on_operation_failed)
        self.backend.operation_warning.connect(self._on_operation_warning)

    def set_confirmation_enabled(self, enabled: bool) -> None:
        """Enable interactive safety confirmations for the real desktop shell.

        Direct page tests and embedding callers keep this disabled unless they opt in.
        MainWindow enables it for ordinary interactive use.
        """

        self._confirmation_enabled = enabled

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
        confirmation_already_shown: bool = False,
    ) -> str | None:
        if not self.workspace.is_open or self.workspace.db_path is None:
            self.operation_status.setText("No active Workspace.")
            return None
        resolved_arguments = dict(arguments or {})
        policy = operation_policy(operation_id)
        if (
            self._confirmation_enabled
            and policy.confirmation_required
            and not confirmation_already_shown
            and not self._confirm_submission(operation_id, resolved_arguments)
        ):
            self.operation_status.setText(f"{operation_id}: cancelled before submission")
            return None
        request = GuiOperationRequest.create(
            self.workspace.db_path,
            operation_id,
            resolved_arguments,
        )
        self._pending[request.request_id] = (operation_id, callback)
        self.operation_status.setText(summary or f"Running {operation_id}...")
        self.backend.submit_request(request)
        return request.request_id

    def _confirm_submission(self, operation_id: str, arguments: Mapping[str, object]) -> bool:
        if self.workspace.db_path is None:
            return False
        policy = operation_policy(operation_id)
        answer = QMessageBox.warning(
            self,
            f"Confirm {policy.effect} operation",
            confirmation_text(self.workspace.db_path, operation_id, arguments),
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Ok

    @Slot(str, object)
    def _on_operation_finished(self, request_id: str, outcome: object) -> None:
        pending = self._pending.pop(request_id, None)
        if pending is None:
            return
        operation_id, callback = pending
        if not isinstance(outcome, OperationOutcome):
            self.operation_status.setText(f"{operation_id}: invalid backend result")
            return
        if outcome.state == "partial":
            self.operation_status.setText(
                f"{operation_id}: partial — inspect Operation Center for warnings/failures"
            )
        elif outcome.state == "blocked":
            self.operation_status.setText(
                f"{operation_id}: blocked — inspect Operation Center for details"
            )
        else:
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
        pending = self._pending.get(request_id)
        if pending is not None:
            operation_id, _callback = pending
            self.operation_status.setText(f"{operation_id}: warning/degradation — {message}")
