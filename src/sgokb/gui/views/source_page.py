"""P-GUI-05 Source import, processing, selection, and Raw inspection surface."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QModelIndex, Slot
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableView,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
)

from sgokb.gui.models import DictTableModel
from sgokb.gui.views.operation_page import OperationPage
from sgokb.gui.worker import BackendCoordinator
from sgokb.operation_contracts import OperationOutcome


class SourcePage(OperationPage):
    """Operate Source lifecycle without exposing storage access to Qt widgets."""

    def __init__(self, backend: BackendCoordinator, parent=None) -> None:
        super().__init__(backend, parent)
        self.selected_snapshot: dict[str, object] | None = None
        self.snapshot_model = DictTableModel(
            (
                ("title", "Title"),
                ("source_label", "Source Label"),
                ("source_id", "Source ID"),
                ("id", "Snapshot ID"),
                ("captured_at", "Captured"),
                ("completeness", "Completeness"),
                ("effective", "Effective"),
                ("effective_run_id", "Effective Run"),
            ),
            self,
        )
        self.raw_model = DictTableModel(
            (
                ("id", "Artifact ID"),
                ("artifact_kind", "Kind"),
                ("logical_path", "Logical Path"),
                ("media_type", "Media Type"),
                ("byte_count", "Bytes"),
                ("sha256", "SHA-256"),
                ("storage_ref", "Storage Ref"),
            ),
            self,
        )
        self.run_model = DictTableModel(
            (
                ("id", "Run ID"),
                ("extractor_key", "Extractor"),
                ("extractor_version", "Version"),
                ("status", "Status"),
                ("effective", "Effective"),
                ("created_at", "Created"),
            ),
            self,
        )
        self._build_ui()
        self.setAcceptDrops(True)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        title_row = QHBoxLayout()
        title = QLabel("Sources", self)
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch(1)
        import_button = QPushButton("Import Capture...", self)
        import_button.clicked.connect(self._import_dialog)
        import_folder_button = QPushButton("Import Folder...", self)
        import_folder_button.clicked.connect(self._import_folder_dialog)
        refresh_button = QPushButton("Refresh", self)
        refresh_button.clicked.connect(self.refresh_sources)
        title_row.addWidget(import_button)
        title_row.addWidget(import_folder_button)
        title_row.addWidget(refresh_button)
        layout.addLayout(title_row)

        process_row = QHBoxLayout()
        process_row.addWidget(QLabel("Chunk size:", self))
        self.chunk_size = QSpinBox(self)
        self.chunk_size.setRange(100, 100000)
        self.chunk_size.setValue(1000)
        process_row.addWidget(self.chunk_size)
        process_row.addWidget(QLabel("Overlap:", self))
        self.overlap = QSpinBox(self)
        self.overlap.setRange(0, 99999)
        self.overlap.setValue(100)
        process_row.addWidget(self.overlap)
        self.include_auxiliary = QCheckBox("Include auxiliary", self)
        process_row.addWidget(self.include_auxiliary)
        process_selected = QPushButton("Process Selected", self)
        process_selected.clicked.connect(self._process_selected)
        process_all = QPushButton("Process All", self)
        process_all.clicked.connect(self._process_all)
        select_snapshot = QPushButton("Set Effective Snapshot", self)
        select_snapshot.clicked.connect(self._select_snapshot_dialog)
        select_run = QPushButton("Set Effective Run", self)
        select_run.clicked.connect(self._select_run_dialog)
        process_row.addWidget(process_selected)
        process_row.addWidget(process_all)
        process_row.addWidget(select_snapshot)
        process_row.addWidget(select_run)
        process_row.addStretch(1)
        layout.addLayout(process_row)

        self.source_status = QLabel("Source status unavailable", self)
        self.source_status.setWordWrap(True)
        layout.addWidget(self.source_status)

        splitter = QSplitter(self)
        self.snapshot_table = QTableView(splitter)
        self.snapshot_table.setModel(self.snapshot_model)
        self.snapshot_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.snapshot_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.snapshot_table.setAlternatingRowColors(True)
        self.snapshot_table.horizontalHeader().setStretchLastSection(True)
        self.snapshot_table.selectionModel().currentRowChanged.connect(self._snapshot_changed)
        splitter.addWidget(self.snapshot_table)

        tabs = QTabWidget(splitter)
        self.raw_table = QTableView(tabs)
        self.raw_table.setModel(self.raw_model)
        self.raw_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.raw_table.setAlternatingRowColors(True)
        self.raw_table.horizontalHeader().setStretchLastSection(True)
        tabs.addTab(self.raw_table, "Raw Artifacts")

        self.run_table = QTableView(tabs)
        self.run_table.setModel(self.run_model)
        self.run_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.run_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.run_table.setAlternatingRowColors(True)
        self.run_table.horizontalHeader().setStretchLastSection(True)
        tabs.addTab(self.run_table, "Normalization Runs")

        self.source_detail = QTextEdit(tabs)
        self.source_detail.setReadOnly(True)
        self.source_detail.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        tabs.addTab(self.source_detail, "Snapshot Metadata / Provenance")
        splitter.addWidget(tabs)
        splitter.setSizes([560, 620])
        layout.addWidget(splitter, 1)
        layout.addWidget(self.operation_status)

    def workspace_changed(self) -> None:
        self.selected_snapshot = None
        self.snapshot_model.set_rows([])
        self.raw_model.set_rows([])
        self.run_model.set_rows([])
        self.source_detail.clear()
        self.refresh_sources()

    def refresh_sources(self, *, select_snapshot_id: str | None = None) -> None:
        self.submit(
            "source.status",
            callback=self._apply_status,
            summary="Loading Source status...",
        )
        self.submit(
            "source.snapshots",
            callback=lambda outcome: self._apply_snapshots(outcome, select_snapshot_id),
            summary="Loading Source snapshots...",
        )

    def _apply_status(self, outcome: OperationOutcome) -> None:
        if not isinstance(outcome.data, dict):
            self.source_status.setText("Source status unavailable")
            return
        self.source_status.setText(
            " | ".join(f"{key}: {value}" for key, value in outcome.data.items())
        )

    def _apply_snapshots(self, outcome: OperationOutcome, select_snapshot_id: str | None) -> None:
        rows = outcome.data if isinstance(outcome.data, list) else []
        normalized = [dict(row) for row in rows if isinstance(row, dict)]
        self.snapshot_model.set_rows(normalized)
        target = select_snapshot_id
        if target is None and self.selected_snapshot:
            value = self.selected_snapshot.get("id")
            target = value if isinstance(value, str) else None
        if target:
            self._select_snapshot_row(target)
        elif normalized:
            self.snapshot_table.selectRow(0)
            self._show_snapshot(0)
        else:
            self.selected_snapshot = None
            self.raw_model.set_rows([])
            self.run_model.set_rows([])
            self.source_detail.clear()

    def _select_snapshot_row(self, snapshot_id: str) -> None:
        for row in range(self.snapshot_model.rowCount()):
            item = self.snapshot_model.row_data(row)
            if item and item.get("id") == snapshot_id:
                self.snapshot_table.selectRow(row)
                self.snapshot_table.setCurrentIndex(self.snapshot_model.index(row, 0))
                self._show_snapshot(row)
                return

    @Slot(QModelIndex, QModelIndex)
    def _snapshot_changed(self, current: QModelIndex, _previous: QModelIndex) -> None:
        if current.isValid():
            self._show_snapshot(current.row())

    def _show_snapshot(self, row: int) -> None:
        item = self.snapshot_model.row_data(row)
        if item is None:
            return
        self.selected_snapshot = item
        raw = item.get("raw_artifacts", [])
        runs = item.get("normalization_runs", [])
        self.raw_model.set_rows(row for row in raw if isinstance(row, dict))
        self.run_model.set_rows(row for row in runs if isinstance(row, dict))
        detail = {
            "source_id": item.get("source_id"),
            "source_label": item.get("source_label"),
            "snapshot_id": item.get("id"),
            "title": item.get("title"),
            "captured_at": item.get("captured_at"),
            "completeness": item.get("completeness"),
            "effective": item.get("effective"),
            "effective_run_id": item.get("effective_run_id"),
            "locators": item.get("locators", []),
            "metadata": item.get("metadata", {}),
        }
        self.source_detail.setPlainText(
            json.dumps(detail, ensure_ascii=False, indent=2, default=str)
        )

    def import_path(self, path: str | Path) -> str | None:
        return self.submit(
            "source.import",
            {"path": str(path)},
            callback=self._after_source_write,
            summary=f"Importing Source: {path}",
        )

    def process_snapshot(self, snapshot_id: str | None) -> str | None:
        arguments: dict[str, object] = {
            "size": self.chunk_size.value(),
            "overlap": self.overlap.value(),
            "include_auxiliary": self.include_auxiliary.isChecked(),
        }
        if snapshot_id is not None:
            arguments["snapshot"] = snapshot_id
        return self.submit(
            "source.process",
            arguments,
            callback=self._after_source_write,
            summary="Processing Source snapshot(s)...",
        )

    def select_snapshot(self, source_id: str, snapshot_id: str, reason: str) -> str | None:
        return self.submit(
            "source.select-snapshot",
            {"source": source_id, "snapshot": snapshot_id, "reason": reason},
            callback=lambda outcome: self._after_selection(snapshot_id, outcome),
            summary="Changing effective Snapshot...",
        )

    def select_run(self, snapshot_id: str, run_id: str, reason: str) -> str | None:
        return self.submit(
            "source.select-run",
            {"snapshot": snapshot_id, "run": run_id, "reason": reason},
            callback=lambda outcome: self._after_selection(snapshot_id, outcome),
            summary="Changing effective normalization run...",
        )

    def _after_source_write(self, outcome: OperationOutcome) -> None:
        target = None
        data = outcome.data
        if isinstance(data, list) and data:
            last = data[-1]
            if isinstance(last, dict):
                candidate = last.get("snapshot") or last.get("input")
                target = candidate if isinstance(candidate, str) else None
        self.operation_status.setToolTip(
            json.dumps(outcome.data, ensure_ascii=False, indent=2, default=str)
        )
        self.refresh_sources(select_snapshot_id=target)

    def _after_selection(self, snapshot_id: str, outcome: OperationOutcome) -> None:
        self.operation_status.setToolTip(
            json.dumps(outcome.data, ensure_ascii=False, indent=2, default=str)
        )
        self.refresh_sources(select_snapshot_id=snapshot_id)

    def _import_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Web Capture Bundle",
            "",
            "Web Capture Bundle (*.webcapture.zip *.zip);;All files (*)",
        )
        if path:
            self.import_path(path)

    def _import_folder_dialog(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self,
            "Import ZIP Bundles from Folder",
            "",
        )
        if path:
            self.import_path(path)

    def _selected_snapshot_ids(self) -> tuple[str, str] | None:
        if not self.selected_snapshot:
            self.operation_status.setText("Select a Snapshot first.")
            return None
        source_id = self.selected_snapshot.get("source_id")
        snapshot_id = self.selected_snapshot.get("id")
        if not isinstance(source_id, str) or not isinstance(snapshot_id, str):
            self.operation_status.setText("Selected Snapshot has invalid identity.")
            return None
        return source_id, snapshot_id

    def _process_selected(self) -> None:
        identities = self._selected_snapshot_ids()
        if identities:
            self.process_snapshot(identities[1])

    def _process_all(self) -> None:
        self.process_snapshot(None)

    def _select_snapshot_dialog(self) -> None:
        identities = self._selected_snapshot_ids()
        if not identities:
            return
        reason, ok = QInputDialog.getText(
            self,
            "Set Effective Snapshot",
            "Reason (required):",
        )
        if ok and reason.strip():
            self.select_snapshot(identities[0], identities[1], reason.strip())
        elif ok:
            self.operation_status.setText("A reason is required for effective Snapshot selection.")

    def _selected_run_id(self) -> str | None:
        index = self.run_table.currentIndex()
        if not index.isValid():
            self.operation_status.setText("Select a normalization run first.")
            return None
        item = self.run_model.row_data(index.row())
        run_id = item.get("id") if item else None
        if not isinstance(run_id, str):
            self.operation_status.setText("Selected run has invalid identity.")
            return None
        return run_id

    def _select_run_dialog(self) -> None:
        identities = self._selected_snapshot_ids()
        run_id = self._selected_run_id()
        if not identities or not run_id:
            return
        reason, ok = QInputDialog.getText(
            self,
            "Set Effective Run",
            "Reason (required):",
        )
        if ok and reason.strip():
            self.select_run(identities[1], run_id, reason.strip())
        elif ok:
            self.operation_status.setText("A reason is required for effective Run selection.")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802 - Qt API
        if event.mimeData().hasUrls() and any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802 - Qt API
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        if not paths:
            event.ignore()
            return
        for path in paths:
            self.import_path(path)
        event.acceptProposedAction()
