"""Qt worker-thread boundary for transport-neutral SGOKB operations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot

from sgokb.application_operator import OperatorSession
from sgokb.operation_contracts import OperationFailure, normalize_operation_error
from sgokb.runtime import RuntimeFactory

from .operations import GuiOperationRequest


@dataclass(slots=True)
class BackendSession:
    """Long-lived noncanonical runtime cache for one Workspace."""

    workspace_path: Path
    runtime_factory: RuntimeFactory

    @classmethod
    def create(cls, workspace_path: Path) -> "BackendSession":
        return cls(workspace_path=workspace_path, runtime_factory=RuntimeFactory())

    def dispose(self) -> None:
        self.runtime_factory.clear_cache()


class BackendWorker(QObject):
    """Execute one request at a time on the dedicated backend QThread."""

    finished = Signal(str, object)
    failed = Signal(str, object)
    warning = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self._session: BackendSession | None = None

    def _session_for(self, workspace_path: Path) -> BackendSession:
        resolved = workspace_path.expanduser().resolve()
        if self._session is None or self._session.workspace_path != resolved:
            if self._session is not None:
                self._session.dispose()
            self._session = BackendSession.create(resolved)
        return self._session

    @Slot(object)
    def execute(self, request: GuiOperationRequest) -> None:
        try:
            session = self._session_for(request.workspace_path)
            operator = OperatorSession(
                session.workspace_path,
                runtime_factory=session.runtime_factory,
            )
            outcome = operator.execute(request.operation)
            for message in outcome.warnings:
                self.warning.emit(request.request_id, message)
            self.finished.emit(request.request_id, outcome)
        except OperationFailure as exc:
            self.failed.emit(request.request_id, exc)
        except Exception as exc:  # pragma: no cover - defensive Qt boundary
            failure = normalize_operation_error(request.operation.operation_id, exc)
            self.failed.emit(request.request_id, failure)

    @Slot()
    def dispose(self) -> None:
        if self._session is not None:
            self._session.dispose()
            self._session = None


class BackendCoordinator(QObject):
    """Main-thread owner of the serialized backend lane."""

    _submit_requested = Signal(object)
    _dispose_requested = Signal()

    operation_finished = Signal(str, object)
    operation_failed = Signal(str, object)
    operation_warning = Signal(str, str)
    busy_changed = Signal(bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._pending: set[str] = set()
        self._thread = QThread(self)
        self._worker = BackendWorker()
        self._worker.moveToThread(self._thread)
        self._submit_requested.connect(self._worker.execute)
        self._dispose_requested.connect(self._worker.dispose)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.warning.connect(self.operation_warning)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.start()

    @property
    def is_busy(self) -> bool:
        return bool(self._pending)

    def submit_request(self, request: GuiOperationRequest) -> str:
        """Queue a pre-correlated request after its caller records local intent."""

        was_busy = self.is_busy
        self._pending.add(request.request_id)
        if not was_busy:
            self.busy_changed.emit(True)
        self._submit_requested.emit(request)
        return request.request_id

    def submit(
        self,
        workspace_path: str | Path,
        operation_id: str,
        arguments: dict[str, object] | None = None,
    ) -> str:
        request = GuiOperationRequest.create(workspace_path, operation_id, arguments)
        return self.submit_request(request)

    def _complete(self, request_id: str) -> None:
        was_busy = self.is_busy
        self._pending.discard(request_id)
        if was_busy and not self.is_busy:
            self.busy_changed.emit(False)

    @Slot(str, object)
    def _on_finished(self, request_id: str, outcome: object) -> None:
        # Notify consumers before clearing the completed request. A page callback may
        # enqueue follow-up reads; keeping the completed request pending until after
        # that callback prevents a false busy=False/True flicker between chained work.
        self.operation_finished.emit(request_id, outcome)
        self._complete(request_id)

    @Slot(str, object)
    def _on_failed(self, request_id: str, failure: object) -> None:
        self.operation_failed.emit(request_id, failure)
        self._complete(request_id)

    def shutdown(self, timeout_ms: int = 5000) -> bool:
        """Stop the worker event loop without force-terminating an active operation."""

        if self.is_busy:
            return False
        if not self._thread.isRunning():
            return True
        self._dispose_requested.emit()
        self._thread.quit()
        return self._thread.wait(timeout_ms)