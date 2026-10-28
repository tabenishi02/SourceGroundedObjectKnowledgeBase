"""P-GUI-05 Object-to-Source association review and mutation surface."""

from __future__ import annotations

import json

from PySide6.QtCore import QModelIndex, Slot
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPushButton,
    QSplitter,
    QTableView,
    QTextEdit,
    QVBoxLayout,
)

from sgokb.gui.models import DictTableModel
from sgokb.gui.views.operation_page import OperationPage
from sgokb.gui.worker import BackendCoordinator
from sgokb.operation_contracts import OperationOutcome


class AssociationPage(OperationPage):
    """Review and explicitly set Source↔Object associations."""

    def __init__(self, backend: BackendCoordinator, parent=None) -> None:
        super().__init__(backend, parent)
        self.model = DictTableModel(
            (
                ("source_label", "Source"),
                ("source_id", "Source ID"),
                ("status", "Status"),
                ("subject_relationship", "Subject Relationship"),
                ("origin_kind", "Origin"),
                ("evidence_count", "Evidence"),
                ("top_retrieval_score", "Top Score"),
                ("note", "Note"),
            ),
            self,
        )
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        title_row = QHBoxLayout()
        title = QLabel("Associations", self)
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addWidget(QLabel("Object:", self))
        self.object_combo = QComboBox(self)
        self.object_combo.setMinimumWidth(300)
        self.object_combo.currentIndexChanged.connect(self._object_changed)
        title_row.addWidget(self.object_combo)
        title_row.addStretch(1)
        reload_objects = QPushButton("Reload Objects", self)
        reload_objects.clicked.connect(self.refresh_objects)
        title_row.addWidget(reload_objects)
        layout.addLayout(title_row)

        actions = QHBoxLayout()
        refresh = QPushButton("List Associations", self)
        refresh.clicked.connect(self.refresh_associations)
        self.semantic_suggest = QCheckBox("Semantic suggest", self)
        suggest = QPushButton("Suggest Sources", self)
        suggest.clicked.connect(self.suggest_associations)
        set_button = QPushButton("Set Selected", self)
        set_button.clicked.connect(self._set_dialog)
        clear_button = QPushButton("Clear Selected", self)
        clear_button.clicked.connect(self._clear_selected)
        actions.addWidget(refresh)
        actions.addWidget(self.semantic_suggest)
        actions.addWidget(suggest)
        actions.addWidget(set_button)
        actions.addWidget(clear_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        splitter = QSplitter(self)
        self.table = QTableView(splitter)
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.selectionModel().currentRowChanged.connect(self._row_changed)
        splitter.addWidget(self.table)

        self.detail_text = QTextEdit(splitter)
        self.detail_text.setReadOnly(True)
        self.detail_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        splitter.addWidget(self.detail_text)
        splitter.setSizes([720, 460])
        layout.addWidget(splitter, 1)
        layout.addWidget(self.operation_status)

    def workspace_changed(self) -> None:
        self.model.set_rows([])
        self.detail_text.clear()
        self.refresh_objects()

    def refresh_objects(self) -> str | None:
        return self.submit(
            "object.list",
            callback=self._apply_objects,
            summary="Loading Objects for association review...",
        )

    def _apply_objects(self, outcome: OperationOutcome) -> None:
        current_id = self.object_combo.currentData()
        self.object_combo.blockSignals(True)
        self.object_combo.clear()
        rows = outcome.data if isinstance(outcome.data, list) else []
        target = -1
        for row in rows:
            if not isinstance(row, dict):
                continue
            object_id = row.get("object_id")
            name = row.get("name")
            if not isinstance(object_id, str):
                continue
            self.object_combo.addItem(f"{name} [{object_id}]", object_id)
            if object_id == current_id:
                target = self.object_combo.count() - 1
        if target >= 0:
            self.object_combo.setCurrentIndex(target)
        self.object_combo.blockSignals(False)
        if self.object_combo.count():
            if self.object_combo.currentIndex() < 0:
                self.object_combo.setCurrentIndex(0)
            self.refresh_associations()

    @Slot(int)
    def _object_changed(self, _index: int) -> None:
        self.model.set_rows([])
        self.detail_text.clear()
        if self.object_combo.currentData():
            self.refresh_associations()

    def _selected_object_id(self) -> str | None:
        value = self.object_combo.currentData()
        if isinstance(value, str):
            return value
        self.operation_status.setText("Select an Object first.")
        return None

    def refresh_associations(self) -> str | None:
        object_id = self._selected_object_id()
        if not object_id:
            return None
        return self.submit(
            "association.list",
            {"object": object_id},
            callback=self._apply_association_list,
            summary="Loading Source associations...",
        )

    def _apply_association_list(self, outcome: OperationOutcome) -> None:
        rows = outcome.data if isinstance(outcome.data, list) else []
        normalized = []
        for item in rows:
            if not isinstance(item, dict):
                continue
            row = dict(item)
            row.setdefault("source_label", "")
            row.setdefault("evidence_count", "")
            row.setdefault("top_retrieval_score", "")
            normalized.append(row)
        self.model.set_rows(normalized)
        if normalized:
            self.table.selectRow(0)
            self._show_row(normalized[0])

    def suggest_associations(self) -> str | None:
        object_id = self._selected_object_id()
        if not object_id:
            return None
        return self.submit(
            "association.suggest",
            {
                "object": object_id,
                "semantic": self.semantic_suggest.isChecked(),
                "max_candidates": 500,
            },
            callback=self._apply_suggestions,
            summary="Building Source association suggestions...",
        )

    def _apply_suggestions(self, outcome: OperationOutcome) -> None:
        data = outcome.data if isinstance(outcome.data, dict) else {}
        suggestions = data.get("suggestions", [])
        rows = []
        for item in suggestions if isinstance(suggestions, list) else []:
            if not isinstance(item, dict):
                continue
            row = dict(item)
            association = row.pop("association", None)
            if isinstance(association, dict):
                for key in ("status", "subject_relationship", "origin_kind", "note"):
                    row[key] = association.get(key)
            else:
                row.setdefault("status", "suggested")
                row.setdefault("subject_relationship", "")
                row.setdefault("origin_kind", "retrieval")
                row.setdefault("note", "")
            rows.append(row)
        self.model.set_rows(rows)
        self.operation_status.setToolTip(
            json.dumps(data, ensure_ascii=False, indent=2, default=str)
        )
        if rows:
            self.table.selectRow(0)
            self._show_row(rows[0])

    @Slot(QModelIndex, QModelIndex)
    def _row_changed(self, current: QModelIndex, _previous: QModelIndex) -> None:
        if not current.isValid():
            return
        row = self.model.row_data(current.row())
        if row:
            self._show_row(row)

    def _show_row(self, row: dict[str, object]) -> None:
        self.detail_text.setPlainText(
            json.dumps(row, ensure_ascii=False, indent=2, default=str)
        )
        source_id = row.get("source_id")
        if isinstance(source_id, str):
            self.submit(
                "source.snapshots",
                callback=lambda outcome: self._append_source_detail(source_id, outcome),
                summary=f"Loading Source {source_id} detail...",
            )

    def _append_source_detail(self, source_id: str, outcome: OperationOutcome) -> None:
        snapshots = outcome.data if isinstance(outcome.data, list) else []
        source_snapshots = [
            item
            for item in snapshots
            if isinstance(item, dict) and item.get("source_id") == source_id
        ]
        current = self.detail_text.toPlainText()
        self.detail_text.setPlainText(
            current
            + "\n\nSource snapshots:\n"
            + json.dumps(source_snapshots, ensure_ascii=False, indent=2, default=str)
        )

    def set_association(
        self,
        object_id: str,
        source_id: str,
        status: str,
        *,
        subject_relationship: str | None = None,
        note: str | None = None,
    ) -> str | None:
        return self.submit(
            "association.set",
            {
                "object": object_id,
                "source": source_id,
                "status": status,
                "subject_relationship": subject_relationship or None,
                "note": note or None,
            },
            callback=lambda _outcome: self.refresh_associations(),
            summary=f"Setting association {source_id} → {object_id}...",
        )

    def clear_association(self, object_id: str, source_id: str) -> str | None:
        return self.submit(
            "association.clear",
            {"object": object_id, "source": source_id},
            callback=lambda _outcome: self.refresh_associations(),
            summary=f"Clearing association {source_id} → {object_id}...",
        )

    def _selected_source_id(self) -> str | None:
        index = self.table.currentIndex()
        if not index.isValid():
            self.operation_status.setText("Select a Source row first.")
            return None
        row = self.model.row_data(index.row())
        source_id = row.get("source_id") if row else None
        if isinstance(source_id, str):
            return source_id
        self.operation_status.setText("Selected row has no Source ID.")
        return None

    def _set_dialog(self) -> None:
        object_id = self._selected_object_id()
        source_id = self._selected_source_id()
        if not object_id or not source_id:
            return
        status, ok = QInputDialog.getItem(
            self,
            "Set Source Association",
            "Status:",
            ["candidate", "confirmed", "excluded"],
            editable=False,
        )
        if not ok:
            return
        relationship, ok = QInputDialog.getText(
            self,
            "Set Source Association",
            "Subject relationship (optional):",
        )
        if not ok:
            return
        note, ok = QInputDialog.getText(
            self,
            "Set Source Association",
            "Note (optional):",
        )
        if not ok:
            return
        self.set_association(
            object_id,
            source_id,
            status,
            subject_relationship=relationship.strip() or None,
            note=note.strip() or None,
        )

    def _clear_selected(self) -> None:
        object_id = self._selected_object_id()
        source_id = self._selected_source_id()
        if object_id and source_id:
            self.clear_association(object_id, source_id)
