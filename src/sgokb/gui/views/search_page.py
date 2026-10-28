"""P-GUI-06 Object Search and Similarity surface."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum

from PySide6.QtCore import QModelIndex, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableView,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sgokb.gui.models import DictTableModel
from sgokb.gui.views.operation_page import OperationPage
from sgokb.gui.worker import BackendCoordinator
from sgokb.operation_contracts import OperationOutcome


def _plain(value):
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _json(value) -> str:
    return json.dumps(_plain(value), ensure_ascii=False, indent=2, default=str)


def _optional(text: str) -> str | None:
    value = text.strip()
    return value or None


class SearchPage(OperationPage):
    """Search accepted Knowledge and run explicit Object similarity requests."""

    def __init__(self, backend: BackendCoordinator, parent=None) -> None:
        super().__init__(backend, parent)
        self.search_model = DictTableModel(
            (
                ("rank", "Rank"),
                ("name", "Name"),
                ("primary_class", "Primary Class"),
                ("version_id", "Version"),
                ("fused_score", "Score"),
                ("channels", "Channels"),
                ("matched_facets", "Matched Facets"),
            ),
            self,
        )
        self.similar_model = DictTableModel(
            (
                ("rank", "Rank"),
                ("name", "Name"),
                ("primary_class", "Primary Class"),
                ("version_id", "Version"),
                ("score", "Score"),
                ("matched_facet", "Matched Facet"),
            ),
            self,
        )
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        title = QLabel("Search / Similarity", self)
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(title)

        tabs = QTabWidget(self)
        tabs.addTab(self._build_search_tab(), "Search")
        tabs.addTab(self._build_similarity_tab(), "Similarity")
        layout.addWidget(tabs, 1)
        layout.addWidget(self.operation_status)

    def _build_search_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)

        query_row = QHBoxLayout()
        self.search_query = QLineEdit(page)
        self.search_query.setPlaceholderText("Search accepted Object Knowledge...")
        self.search_query.returnPressed.connect(self.run_search)
        self.search_mode = QComboBox(page)
        self.search_mode.addItems(("lexical", "semantic", "hybrid"))
        self.search_mode.setCurrentText("hybrid")
        self.semantic_runtime = QCheckBox("Semantic runtime", page)
        self.require_full_runtime = QCheckBox("Require full runtime", page)
        self.search_limit = QSpinBox(page)
        self.search_limit.setRange(1, 100)
        self.search_limit.setValue(10)
        self.candidate_limit = QSpinBox(page)
        self.candidate_limit.setRange(0, 5000)
        self.candidate_limit.setValue(0)
        self.candidate_limit.setSpecialValueText("Auto")
        run = QPushButton("Search", page)
        run.clicked.connect(self.run_search)
        query_row.addWidget(self.search_query, 1)
        query_row.addWidget(self.search_mode)
        query_row.addWidget(self.semantic_runtime)
        query_row.addWidget(self.require_full_runtime)
        query_row.addWidget(QLabel("Limit:", page))
        query_row.addWidget(self.search_limit)
        query_row.addWidget(QLabel("Candidates:", page))
        query_row.addWidget(self.candidate_limit)
        query_row.addWidget(run)
        layout.addLayout(query_row)

        body = QSplitter(page)
        filters = QGroupBox("Hard filters", body)
        filters.setMaximumWidth(360)
        form = QFormLayout(filters)
        self.primary_class = QLineEdit(filters)
        self.additional_class = QLineEdit(filters)
        self.ancestor_class = QLineEdit(filters)
        self.facet = QLineEdit(filters)
        self.version = QLineEdit(filters)
        self.temporal_scope = QLineEdit(filters)
        self.valid_at = QLineEdit(filters)
        self.valid_at.setPlaceholderText("YYYY-MM-DD")
        self.derivation_kind = QLineEdit(filters)
        self.include_archived = QCheckBox("Include archived Objects", filters)
        form.addRow("Primary Class:", self.primary_class)
        form.addRow("Additional Class:", self.additional_class)
        form.addRow("Ancestor Class:", self.ancestor_class)
        form.addRow("Facet:", self.facet)
        form.addRow("Version ID:", self.version)
        form.addRow("Temporal Scope ID:", self.temporal_scope)
        form.addRow("Knowledge valid at:", self.valid_at)
        form.addRow("Derivation kind:", self.derivation_kind)
        form.addRow("", self.include_archived)
        body.addWidget(filters)

        results_panel = QWidget(body)
        results_layout = QVBoxLayout(results_panel)
        results_layout.setContentsMargins(0, 0, 0, 0)
        self.search_runtime_state = QLabel("No search has run.", results_panel)
        self.search_runtime_state.setWordWrap(True)
        results_layout.addWidget(self.search_runtime_state)

        result_splitter = QSplitter(results_panel)
        self.search_table = QTableView(result_splitter)
        self.search_table.setModel(self.search_model)
        self.search_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.search_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.search_table.setAlternatingRowColors(True)
        self.search_table.horizontalHeader().setStretchLastSection(True)
        self.search_table.selectionModel().currentRowChanged.connect(self._search_row_changed)
        result_splitter.addWidget(self.search_table)
        self.search_detail = QTextEdit(result_splitter)
        self.search_detail.setReadOnly(True)
        self.search_detail.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        result_splitter.addWidget(self.search_detail)
        result_splitter.setSizes([650, 430])
        results_layout.addWidget(result_splitter, 1)
        body.addWidget(results_panel)
        body.setSizes([300, 900])
        layout.addWidget(body, 1)
        return page

    def _build_similarity_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)

        controls = QHBoxLayout()
        self.similar_object = QComboBox(page)
        self.similar_object.setMinimumWidth(260)
        self.similar_facet = QLineEdit(page)
        self.similar_facet.setPlaceholderText("Optional Facet key")
        self.similar_version = QLineEdit(page)
        self.similar_version.setPlaceholderText("Optional source Version ID")
        self.similar_limit = QSpinBox(page)
        self.similar_limit.setRange(1, 100)
        self.similar_limit.setValue(10)
        self.cross_class = QCheckBox("Cross-class", page)
        self.similar_archived = QCheckBox("Include archived", page)
        run = QPushButton("Find Similar", page)
        run.clicked.connect(self.run_similarity)
        controls.addWidget(QLabel("Object:", page))
        controls.addWidget(self.similar_object)
        controls.addWidget(QLabel("Facet:", page))
        controls.addWidget(self.similar_facet)
        controls.addWidget(QLabel("Version:", page))
        controls.addWidget(self.similar_version)
        controls.addWidget(QLabel("Limit:", page))
        controls.addWidget(self.similar_limit)
        controls.addWidget(self.cross_class)
        controls.addWidget(self.similar_archived)
        controls.addWidget(run)
        layout.addLayout(controls)

        requirement = QLabel(
            "Similarity requires the configured local Embedding Space and Vector Index; "
            "there is no silent lexical or cloud fallback.",
            page,
        )
        requirement.setWordWrap(True)
        layout.addWidget(requirement)
        self.similar_source = QLabel("No similarity request has run.", page)
        self.similar_source.setWordWrap(True)
        layout.addWidget(self.similar_source)

        splitter = QSplitter(page)
        self.similar_table = QTableView(splitter)
        self.similar_table.setModel(self.similar_model)
        self.similar_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.similar_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.similar_table.setAlternatingRowColors(True)
        self.similar_table.horizontalHeader().setStretchLastSection(True)
        self.similar_table.selectionModel().currentRowChanged.connect(self._similar_row_changed)
        splitter.addWidget(self.similar_table)
        self.similar_detail = QTextEdit(splitter)
        self.similar_detail.setReadOnly(True)
        self.similar_detail.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        splitter.addWidget(self.similar_detail)
        splitter.setSizes([700, 480])
        layout.addWidget(splitter, 1)
        return page

    def workspace_changed(self) -> None:
        self.search_model.set_rows([])
        self.similar_model.set_rows([])
        self.search_detail.clear()
        self.similar_detail.clear()
        self.similar_object.clear()
        self.submit(
            "object.list",
            callback=self._apply_objects,
            summary="Loading Objects for Similarity...",
        )

    def _apply_objects(self, outcome: OperationOutcome) -> None:
        rows = outcome.data if isinstance(outcome.data, list) else []
        self.similar_object.clear()
        for raw in rows:
            if not isinstance(raw, dict):
                continue
            object_id = raw.get("object_id")
            if not isinstance(object_id, str):
                continue
            name = str(raw.get("name") or object_id)
            primary = str(raw.get("primary_class") or raw.get("primary_class_id") or "")
            label = f"{name} [{primary}]" if primary else name
            self.similar_object.addItem(label, object_id)

    def run_search(self) -> str | None:
        query = self.search_query.text().strip()
        if not query:
            self.operation_status.setText("Enter a Search query first.")
            return None
        arguments: dict[str, object] = {
            "query": query,
            "mode": self.search_mode.currentText(),
            "semantic_runtime": self.semantic_runtime.isChecked(),
            "require_full_runtime": self.require_full_runtime.isChecked(),
            "limit": self.search_limit.value(),
            "include_archived": self.include_archived.isChecked(),
        }
        if self.candidate_limit.value() > 0:
            arguments["candidate_limit"] = self.candidate_limit.value()
        for key, widget in (
            ("primary_class", self.primary_class),
            ("additional_class", self.additional_class),
            ("ancestor_class", self.ancestor_class),
            ("facet", self.facet),
            ("version", self.version),
            ("temporal_scope", self.temporal_scope),
            ("valid_at", self.valid_at),
            ("derivation_kind", self.derivation_kind),
        ):
            value = _optional(widget.text())
            if value is not None:
                arguments[key] = value
        return self.submit(
            "search",
            arguments,
            callback=self._apply_search,
            summary=f"Searching Objects: {query}",
        )

    def _apply_search(self, outcome: OperationOutcome) -> None:
        payload = _plain(outcome.data)
        if not isinstance(payload, dict):
            self.search_model.set_rows([])
            self.search_detail.setPlainText(_json(payload))
            return
        results = payload.get("results", [])
        rows = []
        for raw in results if isinstance(results, list) else []:
            if not isinstance(raw, dict):
                continue
            row = dict(raw)
            row["channels"] = ", ".join(str(item) for item in raw.get("channels", []))
            row["matched_facets"] = ", ".join(
                str(item) for item in raw.get("matched_facets", [])
            )
            rows.append(row)
        self.search_model.set_rows(rows)
        degraded = payload.get("degraded_channels", [])
        if degraded:
            self.search_runtime_state.setText(
                "Degraded channels: " + ", ".join(str(item) for item in degraded)
            )
        else:
            self.search_runtime_state.setText(
                f"Mode: {payload.get('mode')} | Results: {len(rows)} | No degradation reported"
            )
        if rows:
            self.search_table.selectRow(0)
            self._show_search_row(0)
        else:
            self.search_detail.setPlainText(_json(payload))

    @Slot(QModelIndex, QModelIndex)
    def _search_row_changed(self, current: QModelIndex, _previous: QModelIndex) -> None:
        if current.isValid():
            self._show_search_row(current.row())

    def _show_search_row(self, row: int) -> None:
        value = self.search_model.row_data(row)
        if value is not None:
            self.search_detail.setPlainText(_json(value))

    def run_similarity(self) -> str | None:
        object_id = self.similar_object.currentData()
        if not isinstance(object_id, str) or not object_id:
            self.operation_status.setText("Select an Object for Similarity first.")
            return None
        arguments: dict[str, object] = {
            "object_id": object_id,
            "limit": self.similar_limit.value(),
            "cross_class": self.cross_class.isChecked(),
            "include_archived": self.similar_archived.isChecked(),
        }
        facet = _optional(self.similar_facet.text())
        version = _optional(self.similar_version.text())
        if facet is not None:
            arguments["facet"] = facet
        if version is not None:
            arguments["version"] = version
        return self.submit(
            "similar",
            arguments,
            callback=self._apply_similarity,
            summary="Finding similar Objects...",
        )

    def _apply_similarity(self, outcome: OperationOutcome) -> None:
        payload = _plain(outcome.data)
        if not isinstance(payload, dict):
            self.similar_model.set_rows([])
            self.similar_detail.setPlainText(_json(payload))
            return
        results = payload.get("results", [])
        rows = (
            [dict(item) for item in results if isinstance(item, dict)]
            if isinstance(results, list)
            else []
        )
        self.similar_model.set_rows(rows)
        self.similar_source.setText(
            "Source: "
            f"{payload.get('source_name', payload.get('source_object_id'))} | "
            f"Version: {payload.get('source_version_id')} | "
            f"Facet: {payload.get('facet') or 'overall'} | "
            f"Cross-class: {bool(payload.get('cross_class'))}"
        )
        if rows:
            self.similar_table.selectRow(0)
            self._show_similar_row(0)
        else:
            self.similar_detail.setPlainText(_json(payload))

    @Slot(QModelIndex, QModelIndex)
    def _similar_row_changed(self, current: QModelIndex, _previous: QModelIndex) -> None:
        if current.isValid():
            self._show_similar_row(current.row())

    def _show_similar_row(self, row: int) -> None:
        value = self.similar_model.row_data(row)
        if value is not None:
            self.similar_detail.setPlainText(_json(value))
