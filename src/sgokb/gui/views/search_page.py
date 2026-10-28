"""P-GUI-06 Object Search and Similarity surface."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, is_dataclass
from datetime import date
from enum import Enum

from PySide6.QtCore import QModelIndex, QSignalBlocker, Slot
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


def _validity_expression(valid_from: str | None, valid_to: str | None) -> str | None:
    if valid_from is None and valid_to is None:
        return None
    try:
        start = date.fromisoformat(valid_from) if valid_from is not None else None
        end = date.fromisoformat(valid_to) if valid_to is not None else None
    except ValueError as exc:
        raise ValueError("Knowledge validity dates must use YYYY-MM-DD") from exc
    if start is not None and end is not None and start > end:
        raise ValueError("Knowledge valid From must not be after To")
    return f"{valid_from or ''}..{valid_to or ''}"


class _EditableComboBox(QComboBox):
    """Editable selector with tiny text compatibility helpers for GUI tests/callers."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

    def setText(self, value: str) -> None:  # noqa: N802 - compatibility helper
        self.setEditText(value)

    def text(self) -> str:
        return self.currentText()


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
        self._reference_generation = 0
        self._class_options: dict[str, dict[str, object]] = {}
        self._facet_options: dict[str, dict[str, object]] = {}
        self._version_options: dict[str, dict[str, object]] = {}
        self._temporal_options: dict[str, dict[str, object]] = {}
        self._facets_by_object: dict[str, dict[str, dict[str, object]]] = defaultdict(dict)
        self._versions_by_object: dict[str, dict[str, dict[str, object]]] = defaultdict(dict)
        self._loaded_version_ids: set[str] = set()
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

    @staticmethod
    def _plain_combo(parent: QWidget) -> QComboBox:
        combo = QComboBox(parent)
        combo.addItem("Any", None)
        return combo

    @staticmethod
    def _editable_combo(parent: QWidget, tooltip: str) -> _EditableComboBox:
        combo = _EditableComboBox(parent)
        combo.addItem("Any", None)
        combo.setToolTip(tooltip)
        return combo

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
        filters.setMaximumWidth(390)
        form = QFormLayout(filters)
        self.primary_class = self._plain_combo(filters)
        self.additional_class = self._plain_combo(filters)
        self.ancestor_class = self._plain_combo(filters)
        self.facet = self._editable_combo(
            filters,
            "Dropdown candidates come from current accepted Knowledge. "
            "A known historical Facet key may also be typed.",
        )
        self.version = self._editable_combo(
            filters,
            "Dropdown candidates are current accepted Version IDs. "
            "A historical accepted Version ID may also be typed.",
        )
        self.temporal_scope = self._editable_combo(
            filters,
            "Dropdown candidates come from temporal scopes in loaded accepted Knowledge. "
            "A known historical Temporal Scope ID may also be typed.",
        )
        self.valid_from = QLineEdit(filters)
        self.valid_from.setPlaceholderText("YYYY-MM-DD")
        self.valid_from.setClearButtonEnabled(True)
        self.valid_to = QLineEdit(filters)
        self.valid_to.setPlaceholderText("YYYY-MM-DD")
        self.valid_to.setClearButtonEnabled(True)
        self.derivation_kind = QLineEdit(filters)
        self.derivation_kind.setPlaceholderText(
            "direct_statement / synthesis / interpretation / reported_view"
        )
        self.include_archived = QCheckBox("Include archived Objects", filters)
        form.addRow("Primary Class:", self.primary_class)
        form.addRow("Additional Class:", self.additional_class)
        form.addRow("Ancestor Class:", self.ancestor_class)
        form.addRow("Facet:", self.facet)
        form.addRow("Version ID:", self.version)
        form.addRow("Temporal Scope ID:", self.temporal_scope)
        form.addRow("Knowledge valid From:", self.valid_from)
        form.addRow("Knowledge valid To:", self.valid_to)
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
        body.setSizes([330, 870])
        layout.addWidget(body, 1)
        return page

    def _build_similarity_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)

        controls = QHBoxLayout()
        self.similar_object = QComboBox(page)
        self.similar_object.setMinimumWidth(260)
        self.similar_object.currentIndexChanged.connect(self._refresh_similarity_references)
        self.similar_facet = self._editable_combo(
            page,
            "Facet candidates are scoped to the selected Object's loaded current accepted Version. "
            "A known historical Facet key may also be typed.",
        )
        self.similar_version = self._editable_combo(
            page,
            "Version candidates are scoped to the selected Object. "
            "A historical accepted Version ID may also be typed.",
        )
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
        self._reference_generation += 1
        generation = self._reference_generation
        self.search_model.set_rows([])
        self.similar_model.set_rows([])
        self.search_detail.clear()
        self.similar_detail.clear()
        self.similar_object.clear()
        self._class_options.clear()
        self._facet_options.clear()
        self._version_options.clear()
        self._temporal_options.clear()
        self._facets_by_object.clear()
        self._versions_by_object.clear()
        self._loaded_version_ids.clear()
        self._refresh_reference_combos()
        self.submit(
            "registry.class.list",
            callback=lambda outcome, gen=generation: self._apply_classes(outcome, gen),
            summary="Loading Search Class choices...",
        )
        self.submit(
            "object.list",
            callback=lambda outcome, gen=generation: self._apply_objects(outcome, gen),
            summary="Loading Search / Similarity references...",
        )

    def _apply_classes(self, outcome: OperationOutcome, generation: int) -> None:
        if generation != self._reference_generation:
            return
        rows = outcome.data if isinstance(outcome.data, list) else []
        self._class_options = {
            str(row["key"]): dict(row)
            for row in rows
            if isinstance(row, dict) and isinstance(row.get("key"), str)
        }
        self._refresh_reference_combos()

    def _apply_objects(self, outcome: OperationOutcome, generation: int) -> None:
        if generation != self._reference_generation:
            return
        rows = outcome.data if isinstance(outcome.data, list) else []
        blocker = QSignalBlocker(self.similar_object)
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
            version_id = raw.get("current_version_id")
            if not isinstance(version_id, str) or not version_id:
                continue
            option = {
                "version_id": version_id,
                "object_id": object_id,
                "object_name": name,
                "version_number": None,
            }
            self._version_options[version_id] = option
            self._versions_by_object[object_id][version_id] = option
            if version_id not in self._loaded_version_ids:
                self._loaded_version_ids.add(version_id)
                self.submit(
                    "version.show",
                    {"version_id": version_id},
                    callback=lambda result, vid=version_id, gen=generation: (
                        self._apply_version_reference(result, vid, gen)
                    ),
                    summary=f"Loading Search references from Version: {version_id}",
                )
        del blocker
        self._refresh_reference_combos()
        self._refresh_similarity_references()

    def _apply_version_reference(
        self,
        outcome: OperationOutcome,
        version_id: str,
        generation: int,
    ) -> None:
        if generation != self._reference_generation:
            return
        payload = _plain(outcome.data)
        if not isinstance(payload, dict):
            return
        object_id = payload.get("object_id")
        if not isinstance(object_id, str):
            return
        info = self._version_options.get(version_id, {"version_id": version_id})
        info.update(
            {
                "object_id": object_id,
                "object_name": str(payload.get("name") or object_id),
                "version_number": payload.get("version_number"),
            }
        )
        self._version_options[version_id] = info
        self._versions_by_object[object_id][version_id] = info

        knowledge = payload.get("knowledge")
        if not isinstance(knowledge, dict):
            self._refresh_reference_combos()
            return
        facets = knowledge.get("facets")
        if isinstance(facets, list):
            for facet in facets:
                if not isinstance(facet, dict) or not isinstance(facet.get("key"), str):
                    continue
                key = str(facet["key"])
                option = {
                    "key": key,
                    "name": str(facet.get("name") or key),
                }
                self._facet_options[key] = option
                self._facets_by_object[object_id][key] = option

        statements: list[dict] = []
        summary = knowledge.get("summary")
        if isinstance(summary, list):
            statements.extend(item for item in summary if isinstance(item, dict))
        if isinstance(facets, list):
            for facet in facets:
                if not isinstance(facet, dict):
                    continue
                values = facet.get("statements")
                if isinstance(values, list):
                    statements.extend(item for item in values if isinstance(item, dict))
        for statement in statements:
            scope = statement.get("temporal_scope")
            if not isinstance(scope, dict):
                continue
            scope_id = scope.get("temporal_scope_id")
            if not isinstance(scope_id, str) or not scope_id:
                continue
            self._temporal_options[scope_id] = {
                **scope,
                "temporal_scope_id": scope_id,
                "object_id": object_id,
                "object_name": str(payload.get("name") or object_id),
                "version_id": version_id,
            }
        self._refresh_reference_combos()
        self._refresh_similarity_references()

    @staticmethod
    def _combo_value(combo: QComboBox) -> str | None:
        data = combo.currentData()
        if isinstance(data, str) and data:
            return data
        if not combo.isEditable():
            return None
        text = combo.currentText().strip()
        index = combo.currentIndex()
        if index >= 0 and combo.itemData(index) is None and text == combo.itemText(index):
            return None
        return text or None

    @staticmethod
    def _replace_combo(
        combo: QComboBox,
        entries: list[tuple[str, str]],
        *,
        blank_label: str = "Any",
    ) -> None:
        previous_data = combo.currentData()
        previous_text = combo.currentText().strip()
        blocker = QSignalBlocker(combo)
        combo.clear()
        combo.addItem(blank_label, None)
        for label, value in entries:
            combo.addItem(label, value)
        if isinstance(previous_data, str):
            index = combo.findData(previous_data)
            if index >= 0:
                combo.setCurrentIndex(index)
            elif combo.isEditable():
                combo.setEditText(previous_data)
        elif combo.isEditable() and previous_text and previous_text != blank_label:
            combo.setEditText(previous_text)
        del blocker

    def _refresh_reference_combos(self) -> None:
        class_entries = [
            (f"{item.get('name') or key} [{key}]", key)
            for key, item in sorted(
                self._class_options.items(),
                key=lambda pair: str(pair[1].get("name") or pair[0]),
            )
        ]
        for combo in (self.primary_class, self.additional_class, self.ancestor_class):
            self._replace_combo(combo, class_entries)

        facet_entries = [
            (f"{item.get('name') or key} [{key}]", key)
            for key, item in sorted(
                self._facet_options.items(),
                key=lambda pair: str(pair[1].get("name") or pair[0]),
            )
        ]
        self._replace_combo(self.facet, facet_entries)

        version_entries = []
        for version_id, item in sorted(
            self._version_options.items(),
            key=lambda pair: str(pair[1].get("object_name") or pair[0]),
        ):
            number = item.get("version_number")
            prefix = f"v{number}" if number is not None else "current"
            version_entries.append(
                (
                    f"{item.get('object_name') or item.get('object_id')} — "
                    f"{prefix} [{version_id}]",
                    version_id,
                )
            )
        self._replace_combo(self.version, version_entries)

        temporal_entries = [
            (self._temporal_label(scope_id, item), scope_id)
            for scope_id, item in sorted(self._temporal_options.items())
        ]
        self._replace_combo(self.temporal_scope, temporal_entries)

    @staticmethod
    def _temporal_label(scope_id: str, item: dict[str, object]) -> str:
        if item.get("label"):
            scope = str(item["label"])
        elif item.get("valid_from") or item.get("valid_to"):
            scope = f"{item.get('valid_from') or '…'} → {item.get('valid_to') or '…'}"
        elif item.get("as_of"):
            scope = f"as of {item['as_of']}"
        else:
            scope = "unbounded"
        owner = item.get("object_name") or item.get("object_id") or "Object"
        return f"{owner}: {scope} [{scope_id}]"

    @Slot()
    def _refresh_similarity_references(self) -> None:
        object_id = self.similar_object.currentData()
        if not isinstance(object_id, str):
            self._replace_combo(self.similar_facet, [])
            self._replace_combo(
                self.similar_version,
                [],
                blank_label="Current accepted Version",
            )
            return
        facet_entries = [
            (f"{item.get('name') or key} [{key}]", key)
            for key, item in sorted(
                self._facets_by_object.get(object_id, {}).items(),
                key=lambda pair: str(pair[1].get("name") or pair[0]),
            )
        ]
        self._replace_combo(self.similar_facet, facet_entries)
        version_entries = []
        for version_id, item in self._versions_by_object.get(object_id, {}).items():
            number = item.get("version_number")
            prefix = f"v{number}" if number is not None else "current"
            version_entries.append((f"{prefix} [{version_id}]", version_id))
        self._replace_combo(
            self.similar_version,
            version_entries,
            blank_label="Current accepted Version",
        )

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
        ):
            value = self._combo_value(widget)
            if value is not None:
                arguments[key] = value
        derivation = _optional(self.derivation_kind.text())
        if derivation is not None:
            arguments["derivation_kind"] = derivation
        try:
            valid_at = _validity_expression(
                _optional(self.valid_from.text()),
                _optional(self.valid_to.text()),
            )
        except ValueError as exc:
            self.operation_status.setText(str(exc))
            return None
        if valid_at is not None:
            arguments["valid_at"] = valid_at
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
        facet = self._combo_value(self.similar_facet)
        version = self._combo_value(self.similar_version)
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
