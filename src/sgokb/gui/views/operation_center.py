"""Session-local operation history, warning, degradation, and error center."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sgokb.gui.operation_ux import equivalent_cli_command, operation_policy
from sgokb.gui.operations import GuiOperationRequest
from sgokb.gui.worker import BackendCoordinator
from sgokb.operation_contracts import OperationFailure, OperationOutcome


class OperationCenter(QDockWidget):
    """Noncanonical session audit surface for GUI operator activity."""

    def __init__(self, backend: BackendCoordinator, parent=None) -> None:
        super().__init__("Operation Center", parent)
        self.backend = backend
        self._request_items: dict[str, QTreeWidgetItem] = {}
        self._requests: dict[str, GuiOperationRequest] = {}
        self._detail_by_request: dict[str, str] = {}
        self._build_ui()
        self._connect_backend()

    @property
    def operation_count(self) -> int:
        return self.operations.topLevelItemCount()

    @property
    def event_count(self) -> int:
        return self.events.topLevelItemCount()

    def _build_ui(self) -> None:
        root = QWidget(self)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        toolbar = QHBoxLayout()
        clear = QPushButton("Clear completed", root)
        clear.clicked.connect(self.clear_completed)
        toolbar.addWidget(clear)
        toolbar.addStretch(1)
        layout.addLayout(toolbar)

        tabs = QTabWidget(root)

        operation_page = QWidget(tabs)
        operation_layout = QVBoxLayout(operation_page)
        operation_layout.setContentsMargins(0, 0, 0, 0)
        operation_split = QSplitter(Qt.Orientation.Vertical, operation_page)
        self.operations = QTreeWidget(operation_split)
        self.operations.setHeaderLabels(
            ("Time", "Operation", "Safety", "State", "Cancellation")
        )
        self.operations.setRootIsDecorated(False)
        self.operations.setAlternatingRowColors(True)
        self.operations.currentItemChanged.connect(self._operation_selected)
        operation_split.addWidget(self.operations)
        self.operation_detail = QTextEdit(operation_split)
        self.operation_detail.setReadOnly(True)
        self.operation_detail.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        operation_split.addWidget(self.operation_detail)
        operation_split.setSizes([170, 110])
        operation_layout.addWidget(operation_split)
        tabs.addTab(operation_page, "Operations")

        event_page = QWidget(tabs)
        event_layout = QVBoxLayout(event_page)
        event_layout.setContentsMargins(0, 0, 0, 0)
        self.events = QTreeWidget(event_page)
        self.events.setHeaderLabels(("Time", "Operation", "Kind", "Message"))
        self.events.setRootIsDecorated(False)
        self.events.setAlternatingRowColors(True)
        event_layout.addWidget(self.events)
        tabs.addTab(event_page, "Warnings / Errors")

        layout.addWidget(tabs)
        self.setWidget(root)

    def _connect_backend(self) -> None:
        self.backend.operation_submitted.connect(self._on_submitted)
        self.backend.operation_started.connect(self._on_started)
        self.backend.operation_warning.connect(self._on_warning)
        self.backend.operation_finished.connect(self._on_finished)
        self.backend.operation_failed.connect(self._on_failed)

    @staticmethod
    def _time_text() -> str:
        return datetime.now().astimezone().strftime("%H:%M:%S")

    @staticmethod
    def _request_id(item: QTreeWidgetItem | None) -> str | None:
        if item is None:
            return None
        value = item.data(0, Qt.ItemDataRole.UserRole)
        return value if isinstance(value, str) else None

    @Slot(str, object)
    def _on_submitted(self, request_id: str, request: object) -> None:
        if not isinstance(request, GuiOperationRequest):
            return
        policy = operation_policy(request.operation.operation_id)
        item = QTreeWidgetItem(
            [
                self._time_text(),
                request.operation.operation_id,
                policy.effect,
                "queued",
                "Available" if policy.cancellable else "Unavailable",
            ]
        )
        item.setData(0, Qt.ItemDataRole.UserRole, request_id)
        self.operations.addTopLevelItem(item)
        self._request_items[request_id] = item
        self._requests[request_id] = request
        cli = equivalent_cli_command(
            request.workspace_path,
            request.operation.operation_id,
            request.operation.arguments,
        )
        self._detail_by_request[request_id] = (
            f"Request ID: {request_id}\n"
            f"Workspace: {request.workspace_path}\n"
            f"Safety class: {policy.effect}\n"
            f"Cancellation: {'available' if policy.cancellable else 'unavailable'}\n"
            f"Safety note: {policy.note}\n\n"
            "Equivalent CLI command:\n"
            f"{cli}\n\n"
            "This history is session-local presentation state, not a canonical audit log."
        )
        self.operations.setCurrentItem(item)

    @Slot(str, object)
    def _on_started(self, request_id: str, _request: object) -> None:
        item = self._request_items.get(request_id)
        if item is not None:
            item.setText(3, "running")

    @Slot(str, str)
    def _on_warning(self, request_id: str, message: str) -> None:
        request = self._requests.get(request_id)
        operation_id = request.operation.operation_id if request is not None else request_id
        self._add_event(operation_id, "warning/degradation", message)
        self.setVisible(True)

    @Slot(str, object)
    def _on_finished(self, request_id: str, outcome: object) -> None:
        item = self._request_items.get(request_id)
        if not isinstance(outcome, OperationOutcome):
            if item is not None:
                item.setText(3, "invalid-result")
            self._add_event(request_id, "error", "Backend returned an invalid outcome shape.")
            self.setVisible(True)
            return
        if item is not None:
            item.setText(3, outcome.state)
        if outcome.state in {"partial", "blocked"}:
            self._add_event(
                outcome.operation_id,
                outcome.state,
                f"Operation completed with state={outcome.state}.",
            )
            self.setVisible(True)

    @Slot(str, object)
    def _on_failed(self, request_id: str, failure: object) -> None:
        item = self._request_items.get(request_id)
        if isinstance(failure, OperationFailure):
            state = f"failed:{failure.category}/{failure.code}"
            operation_id = failure.operation_id
            message = failure.message
        else:
            state = "failed"
            request = self._requests.get(request_id)
            operation_id = request.operation.operation_id if request is not None else request_id
            message = str(failure)
        if item is not None:
            item.setText(3, state)
        self._add_event(operation_id, "error", message)
        self.setVisible(True)

    def _add_event(self, operation_id: str, kind: str, message: str) -> None:
        item = QTreeWidgetItem([self._time_text(), operation_id, kind, message])
        self.events.addTopLevelItem(item)
        self.events.scrollToItem(item)

    @Slot(object, object)
    def _operation_selected(self, current: object, _previous: object) -> None:
        item = current if isinstance(current, QTreeWidgetItem) else None
        request_id = self._request_id(item)
        self.operation_detail.setPlainText(self._detail_by_request.get(request_id or "", ""))

    def clear_completed(self) -> None:
        """Remove completed rows while keeping running/queued requests visible."""

        removable: list[QTreeWidgetItem] = []
        for index in range(self.operations.topLevelItemCount()):
            item = self.operations.topLevelItem(index)
            if item.text(3) not in {"queued", "running"}:
                removable.append(item)
        for item in removable:
            request_id = self._request_id(item)
            index = self.operations.indexOfTopLevelItem(item)
            self.operations.takeTopLevelItem(index)
            if request_id is not None:
                self._request_items.pop(request_id, None)
                self._requests.pop(request_id, None)
                self._detail_by_request.pop(request_id, None)
