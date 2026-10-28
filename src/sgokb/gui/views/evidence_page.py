"""P-GUI-05 Evidence retrieval, bounded selection, search, and provenance surface."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass

from PySide6.QtCore import QModelIndex, Slot
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sgokb.gui.models import DictTableModel
from sgokb.gui.views.operation_page import OperationPage
from sgokb.gui.worker import BackendCoordinator
from sgokb.operation_contracts import OperationOutcome


class EvidencePage(OperationPage):
    """Browse Evidence and build explicit bounded selections for one Object."""

    def __init__(self, backend: BackendCoordinator, parent=None) -> None:
        super().__init__(backend, parent)
        self.manual_include: set[str] = set()
        self.manual_exclude: set[str] = set()
        self._candidate_rows: list[dict[str, object]] = []
        self.candidate_model = DictTableModel(
            (
                ("manual_state", "Manual"),
                ("selection_state", "Selection"),
                ("evidence_id", "Evidence ID"),
                ("source_id", "Source ID"),
                ("retrieval_score", "Score"),
                ("content", "Content"),
            ),
            self,
        )
        self.search_model = DictTableModel(
            (
                ("evidence_id", "Evidence ID"),
                ("source_id", "Source ID"),
                ("snapshot_id", "Snapshot ID"),
                ("score", "Score"),
                ("lexical_score", "Lexical"),
                ("semantic_score", "Semantic"),
                ("content", "Content"),
            ),
            self,
        )
        self._build_ui()
        self._build_shortcuts()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        title_row = QHBoxLayout()
        title = QLabel("Evidence", self)
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addWidget(QLabel("Object:", self))
        self.object_combo = QComboBox(self)
        self.object_combo.setMinimumWidth(280)
        self.object_combo.currentIndexChanged.connect(self._object_changed)
        title_row.addWidget(self.object_combo)
        title_row.addStretch(1)
        refresh_objects = QPushButton("Reload Objects", self)
        refresh_objects.clicked.connect(self.refresh_objects)
        title_row.addWidget(refresh_objects)
        layout.addLayout(title_row)

        selection_controls = QHBoxLayout()
        self.max_candidates = QSpinBox(self)
        self.max_candidates.setRange(1, 10000)
        self.max_candidates.setValue(500)
        self.max_items = QSpinBox(self)
        self.max_items.setRange(1, 10000)
        self.max_items.setValue(64)
        self.max_tokens = QSpinBox(self)
        self.max_tokens.setRange(1, 10_000_000)
        self.max_tokens.setValue(12000)
        self.max_bytes = QSpinBox(self)
        self.max_bytes.setRange(1, 100_000_000)
        self.max_bytes.setValue(65536)
        self.semantic_candidates = QCheckBox("Semantic candidates", self)
        for label, widget in (
            ("Candidates", self.max_candidates),
            ("Items", self.max_items),
            ("Tokens", self.max_tokens),
            ("Bytes", self.max_bytes),
        ):
            selection_controls.addWidget(QLabel(f"{label}:", self))
            selection_controls.addWidget(widget)
        selection_controls.addWidget(self.semantic_candidates)
        retrieve = QPushButton("Retrieve Candidates", self)
        retrieve.clicked.connect(self.retrieve_candidates)
        select = QPushButton("Run Bounded Selection", self)
        select.clicked.connect(self.run_selection)
        selection_controls.addWidget(retrieve)
        selection_controls.addWidget(select)
        layout.addLayout(selection_controls)

        manual_row = QHBoxLayout()
        include = QPushButton("Include (Ctrl+I)", self)
        include.clicked.connect(self._include_current)
        exclude = QPushButton("Exclude (Ctrl+E)", self)
        exclude.clicked.connect(self._exclude_current)
        automatic = QPushButton("Automatic (Ctrl+0)", self)
        automatic.clicked.connect(self._automatic_current)
        manual_row.addWidget(include)
        manual_row.addWidget(exclude)
        manual_row.addWidget(automatic)
        self.budget_status = QLabel(
            "Selected: 0 | Estimated tokens: 0 | Bytes: 0 | Omitted: 0",
            self,
        )
        manual_row.addWidget(self.budget_status)
        manual_row.addStretch(1)
        layout.addLayout(manual_row)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Evidence search:", self))
        self.search_query = QLineEdit(self)
        self.search_query.setPlaceholderText("Search Evidence Store")
        self.search_query.returnPressed.connect(self.search_evidence)
        search_row.addWidget(self.search_query, 1)
        self.search_mode = QComboBox(self)
        self.search_mode.addItems(["lexical", "hybrid", "semantic"])
        self.search_mode.setCurrentText("hybrid")
        search_row.addWidget(self.search_mode)
        self.search_limit = QSpinBox(self)
        self.search_limit.setRange(1, 1000)
        self.search_limit.setValue(20)
        search_row.addWidget(self.search_limit)
        self.semantic_runtime = QCheckBox("Full local semantic runtime", self)
        search_row.addWidget(self.semantic_runtime)
        self.scope_object = QCheckBox("Scope to selected Object", self)
        search_row.addWidget(self.scope_object)
        self.include_historical = QCheckBox("Include historical", self)
        search_row.addWidget(self.include_historical)
        search_button = QPushButton("Search", self)
        search_button.clicked.connect(self.search_evidence)
        search_row.addWidget(search_button)
        layout.addLayout(search_row)

        splitter = QSplitter(self)
        left_tabs = QTabWidget(splitter)
        self.candidate_table = QTableView(left_tabs)
        self.candidate_table.setModel(self.candidate_model)
        self.candidate_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.candidate_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.candidate_table.setAlternatingRowColors(True)
        self.candidate_table.horizontalHeader().setStretchLastSection(True)
        self.candidate_table.selectionModel().currentRowChanged.connect(
            self._candidate_row_changed
        )
        left_tabs.addTab(self.candidate_table, "Candidates / Selection")

        self.search_table = QTableView(left_tabs)
        self.search_table.setModel(self.search_model)
        self.search_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.search_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.search_table.setAlternatingRowColors(True)
        self.search_table.horizontalHeader().setStretchLastSection(True)
        self.search_table.selectionModel().currentRowChanged.connect(self._search_row_changed)
        left_tabs.addTab(self.search_table, "Search Results")
        splitter.addWidget(left_tabs)

        detail_tabs = QTabWidget(splitter)
        self.detail_text = QTextEdit(detail_tabs)
        self.detail_text.setReadOnly(True)
        self.detail_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.provenance_text = QTextEdit(detail_tabs)
        self.provenance_text.setReadOnly(True)
        self.provenance_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        detail_tabs.addTab(self.detail_text, "Evidence Detail")
        detail_tabs.addTab(self.provenance_text, "Provenance")
        splitter.addWidget(detail_tabs)
        splitter.setSizes([720, 480])
        layout.addWidget(splitter, 1)
        layout.addWidget(self.operation_status)

    def _build_shortcuts(self) -> None:
        self.include_shortcut = QShortcut(QKeySequence("Ctrl+I"), self)
        self.include_shortcut.activated.connect(self._include_current)
        self.exclude_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        self.exclude_shortcut.activated.connect(self._exclude_current)
        self.auto_shortcut = QShortcut(QKeySequence("Ctrl+0"), self)
        self.auto_shortcut.activated.connect(self._automatic_current)

    def workspace_changed(self) -> None:
        self.manual_include.clear()
        self.manual_exclude.clear()
        self._candidate_rows = []
        self.candidate_model.set_rows([])
        self.search_model.set_rows([])
        self.detail_text.clear()
        self.provenance_text.clear()
        self._reset_budget_status()
        self.refresh_objects()

    def refresh_objects(self) -> str | None:
        return self.submit(
            "object.list",
            callback=self._apply_objects,
            summary="Loading Objects for Evidence operations...",
        )

    def _apply_objects(self, outcome: OperationOutcome) -> None:
        current_id = self.object_combo.currentData()
        self.object_combo.blockSignals(True)
        self.object_combo.clear()
        rows = outcome.data if isinstance(outcome.data, list) else []
        target_index = -1
        for row in rows:
            if not isinstance(row, dict):
                continue
            object_id = row.get("object_id")
            name = row.get("name")
            if not isinstance(object_id, str):
                continue
            self.object_combo.addItem(f"{name} [{object_id}]", object_id)
            if object_id == current_id:
                target_index = self.object_combo.count() - 1
        if target_index >= 0:
            self.object_combo.setCurrentIndex(target_index)
        self.object_combo.blockSignals(False)
        if self.object_combo.count() and self.object_combo.currentIndex() < 0:
            self.object_combo.setCurrentIndex(0)

    @Slot(int)
    def _object_changed(self, _index: int) -> None:
        self.manual_include.clear()
        self.manual_exclude.clear()
        self._candidate_rows = []
        self.candidate_model.set_rows([])
        self._reset_budget_status()

    def _selected_object_id(self) -> str | None:
        value = self.object_combo.currentData()
        if isinstance(value, str):
            return value
        self.operation_status.setText("Select an Object first.")
        return None

    def _candidate_arguments(self) -> dict[str, object] | None:
        object_id = self._selected_object_id()
        if not object_id:
            return None
        return {
            "object": object_id,
            "max_candidates": self.max_candidates.value(),
            "semantic": self.semantic_candidates.isChecked(),
            "include_evidence": tuple(sorted(self.manual_include)),
            "exclude_evidence": tuple(sorted(self.manual_exclude)),
        }

    def retrieve_candidates(self) -> str | None:
        arguments = self._candidate_arguments()
        if arguments is None:
            return None
        return self.submit(
            "evidence.candidates",
            arguments,
            callback=self._apply_candidates,
            summary="Retrieving Evidence candidates...",
        )

    def _apply_candidates(self, outcome: OperationOutcome) -> None:
        data = outcome.data if isinstance(outcome.data, dict) else {}
        candidates = data.get("candidates", [])
        rows = []
        for candidate in candidates if isinstance(candidates, list) else []:
            if not isinstance(candidate, dict):
                continue
            row = dict(candidate)
            row["selection_state"] = "candidate"
            rows.append(row)
        self._candidate_rows = rows
        self._refresh_candidate_model()

    def run_selection(self) -> str | None:
        arguments = self._candidate_arguments()
        if arguments is None:
            return None
        arguments.update(
            {
                "max_estimated_tokens": self.max_tokens.value(),
                "max_bytes": self.max_bytes.value(),
                "max_items": self.max_items.value(),
            }
        )
        return self.submit(
            "evidence.select",
            arguments,
            callback=self._apply_selection,
            summary="Selecting bounded Evidence set...",
        )

    def _apply_selection(self, outcome: OperationOutcome) -> None:
        data = outcome.data if isinstance(outcome.data, dict) else {}
        selected_state: dict[str, str] = {}
        selected = data.get("selected", [])
        if isinstance(selected, list):
            for item in selected:
                if not isinstance(item, dict):
                    continue
                candidate = item.get("candidate", {})
                evidence_id = candidate.get("evidence_id") if isinstance(candidate, dict) else None
                if isinstance(evidence_id, str):
                    selected_state[evidence_id] = f"selected:{item.get('selected_by', '')}"
        omitted = data.get("omitted", [])
        if isinstance(omitted, list):
            for item in omitted:
                if not isinstance(item, dict):
                    continue
                evidence_id = item.get("evidence_id")
                if isinstance(evidence_id, str) and evidence_id not in selected_state:
                    selected_state[evidence_id] = f"omitted:{item.get('reason', '')}"
        for row in self._candidate_rows:
            evidence_id = row.get("evidence_id")
            if isinstance(evidence_id, str):
                row["selection_state"] = selected_state.get(evidence_id, "candidate")
        self._refresh_candidate_model()

        usage = data.get("usage", {})
        usage = usage if isinstance(usage, dict) else {}
        selected_count = data.get("selected_count", len(selected) if isinstance(selected, list) else 0)
        token_count = usage.get("estimated_tokens", usage.get("tokens", 0))
        byte_count = usage.get("bytes", 0)
        omitted_count = len(omitted) if isinstance(omitted, list) else 0
        self.budget_status.setText(
            f"Selected: {selected_count} | Estimated tokens: {token_count} | "
            f"Bytes: {byte_count} | Omitted: {omitted_count}"
        )
        self.budget_status.setToolTip(
            json.dumps(data, ensure_ascii=False, indent=2, default=str)
        )

    def _refresh_candidate_model(self) -> None:
        rows = []
        for item in self._candidate_rows:
            row = dict(item)
            evidence_id = row.get("evidence_id")
            if evidence_id in self.manual_include:
                row["manual_state"] = "include"
            elif evidence_id in self.manual_exclude:
                row["manual_state"] = "exclude"
            else:
                row["manual_state"] = "auto"
            rows.append(row)
        self.candidate_model.set_rows(rows)

    def _current_candidate_id(self) -> str | None:
        index = self.candidate_table.currentIndex()
        if not index.isValid():
            self.operation_status.setText("Select an Evidence candidate first.")
            return None
        row = self.candidate_model.row_data(index.row())
        evidence_id = row.get("evidence_id") if row else None
        if isinstance(evidence_id, str):
            return evidence_id
        self.operation_status.setText("Selected row has no Evidence ID.")
        return None

    def _include_current(self) -> None:
        evidence_id = self._current_candidate_id()
        if not evidence_id:
            return
        self.manual_exclude.discard(evidence_id)
        self.manual_include.add(evidence_id)
        self._refresh_candidate_model()

    def _exclude_current(self) -> None:
        evidence_id = self._current_candidate_id()
        if not evidence_id:
            return
        self.manual_include.discard(evidence_id)
        self.manual_exclude.add(evidence_id)
        self._refresh_candidate_model()

    def _automatic_current(self) -> None:
        evidence_id = self._current_candidate_id()
        if not evidence_id:
            return
        self.manual_include.discard(evidence_id)
        self.manual_exclude.discard(evidence_id)
        self._refresh_candidate_model()

    def search_evidence(self) -> str | None:
        query = self.search_query.text().strip()
        if not query:
            self.operation_status.setText("Enter an Evidence search query.")
            return None
        mode = self.search_mode.currentText()
        arguments: dict[str, object] = {
            "query": query,
            "mode": mode,
            "limit": self.search_limit.value(),
            "include_historical": self.include_historical.isChecked(),
            "semantic_runtime": mode == "semantic"
            or (mode == "hybrid" and self.semantic_runtime.isChecked()),
        }
        if self.scope_object.isChecked():
            object_id = self._selected_object_id()
            if object_id:
                arguments["object"] = object_id
        return self.submit(
            "evidence.search",
            arguments,
            callback=self._apply_search,
            summary=f"Searching Evidence ({mode})...",
        )

    def _apply_search(self, outcome: OperationOutcome) -> None:
        data = outcome.data
        if is_dataclass(data):
            payload = asdict(data)
        elif isinstance(data, dict):
            payload = dict(data)
        else:
            payload = vars(data) if hasattr(data, "__dict__") else {}
        results = payload.get("results", [])
        rows = [dict(item) for item in results if isinstance(item, dict)]
        self.search_model.set_rows(rows)
        degraded = payload.get("degraded_channels", ())
        if degraded:
            self.operation_status.setText(
                "Evidence search completed with degraded channels: "
                + ", ".join(str(value) for value in degraded)
            )
        if rows:
            self.search_table.selectRow(0)
            self._load_evidence_from_row(rows[0])

    @Slot(QModelIndex, QModelIndex)
    def _candidate_row_changed(self, current: QModelIndex, _previous: QModelIndex) -> None:
        if current.isValid():
            row = self.candidate_model.row_data(current.row())
            if row:
                self._load_evidence_from_row(row)

    @Slot(QModelIndex, QModelIndex)
    def _search_row_changed(self, current: QModelIndex, _previous: QModelIndex) -> None:
        if current.isValid():
            row = self.search_model.row_data(current.row())
            if row:
                self._load_evidence_from_row(row)

    def _load_evidence_from_row(self, row: dict[str, object]) -> None:
        evidence_id = row.get("evidence_id")
        if isinstance(evidence_id, str):
            self.load_evidence(evidence_id)

    def load_evidence(self, evidence_id: str) -> None:
        self.submit(
            "evidence.show",
            {"evidence_id": evidence_id},
            callback=lambda outcome: self._set_json(self.detail_text, outcome.data),
            summary=f"Loading Evidence {evidence_id}...",
        )
        self.submit(
            "evidence.provenance",
            {"evidence_id": evidence_id},
            callback=lambda outcome: self._set_json(self.provenance_text, outcome.data),
        )

    @staticmethod
    def _set_json(widget: QTextEdit, value: object) -> None:
        widget.setPlainText(json.dumps(value, ensure_ascii=False, indent=2, default=str))

    def _reset_budget_status(self) -> None:
        self.budget_status.setText(
            "Selected: 0 | Estimated tokens: 0 | Bytes: 0 | Omitted: 0"
        )
