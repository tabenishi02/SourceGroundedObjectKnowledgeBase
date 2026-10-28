"""P-GUI-05 Object master-detail and registry mutation surface."""

from __future__ import annotations

import json
from collections.abc import Iterable

from PySide6.QtCore import QModelIndex, Slot
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPushButton,
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


class ObjectPage(OperationPage):
    """Operate the Object registry while preserving stable-ID write targeting."""

    def __init__(self, backend: BackendCoordinator, parent=None) -> None:
        super().__init__(backend, parent)
        self.selected_object_id: str | None = None
        self.model = DictTableModel(
            (
                ("name", "Name"),
                ("object_id", "Object ID"),
                ("status", "Status"),
                ("primary_class_id", "Primary Class"),
                ("current_version_id", "Current Version"),
            ),
            self,
        )
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        title_row = QHBoxLayout()
        title = QLabel("Objects", self)
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch(1)
        refresh = QPushButton("Refresh", self)
        refresh.clicked.connect(self.refresh_objects)
        add = QPushButton("Add Object", self)
        add.clicked.connect(self._add_dialog)
        title_row.addWidget(refresh)
        title_row.addWidget(add)
        layout.addLayout(title_row)

        action_row = QHBoxLayout()
        for label, handler in (
            ("Rename", self._rename_dialog),
            ("Set Status", self._status_dialog),
            ("Add Alias", self._alias_dialog),
        ):
            button = QPushButton(label, self)
            button.clicked.connect(handler)
            action_row.addWidget(button)

        self.set_primary_class_button = QPushButton("Set Primary Class", self)
        self.set_primary_class_button.clicked.connect(self._primary_class_dialog)
        action_row.addWidget(self.set_primary_class_button)

        self.add_class_button = QPushButton("Add Class", self)
        self.add_class_button.clicked.connect(self._add_class_dialog)
        action_row.addWidget(self.add_class_button)

        self.remove_class_button = QPushButton("Remove Class", self)
        self.remove_class_button.clicked.connect(self._remove_class_dialog)
        self.remove_class_button.setEnabled(False)
        action_row.addWidget(self.remove_class_button)

        action_row.addStretch(1)
        layout.addLayout(action_row)

        splitter = QSplitter(self)
        self.table = QTableView(splitter)
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.selectionModel().currentRowChanged.connect(self._row_changed)
        splitter.addWidget(self.table)

        self.tabs = QTabWidget(splitter)
        self.detail_text = self._read_only_text()
        self.alias_text = self._read_only_text()
        self.events_text = self._read_only_text()
        self.relations_text = self._read_only_text()
        self.tabs.addTab(self.detail_text, "Registry / Knowledge")
        self.tabs.addTab(self.alias_text, "Aliases")
        self.tabs.addTab(self.events_text, "Events")
        self.tabs.addTab(self.relations_text, "Relations (read-only)")
        splitter.addWidget(self.tabs)
        splitter.setSizes([520, 620])
        layout.addWidget(splitter, 1)
        layout.addWidget(self.operation_status)

    def _read_only_text(self) -> QTextEdit:
        widget = QTextEdit(self)
        widget.setReadOnly(True)
        widget.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        return widget

    def workspace_changed(self) -> None:
        self.selected_object_id = None
        self.remove_class_button.setEnabled(False)
        self.model.set_rows([])
        for widget in (self.detail_text, self.alias_text, self.events_text, self.relations_text):
            widget.clear()
        self.refresh_objects()

    def refresh_objects(self, *, select_id: str | None = None) -> str | None:
        return self.submit(
            "object.list",
            callback=lambda outcome: self._apply_object_list(outcome, select_id),
            summary="Loading Objects...",
        )

    def _apply_object_list(self, outcome: OperationOutcome, select_id: str | None) -> None:
        rows = outcome.data if isinstance(outcome.data, list) else []
        normalized = [dict(row) for row in rows if isinstance(row, dict)]
        self.model.set_rows(normalized)
        if not normalized:
            self.selected_object_id = None
            self.remove_class_button.setEnabled(False)
            return
        target = select_id or self.selected_object_id
        if target:
            self._select_object_row(target)
        else:
            self.table.selectRow(0)
            self._load_selected_from_row(0)

    def _select_object_row(self, object_id: str) -> None:
        for row in range(self.model.rowCount()):
            item = self.model.row_data(row)
            if item and item.get("object_id") == object_id:
                self.table.selectRow(row)
                self.table.setCurrentIndex(self.model.index(row, 0))
                self._load_selected_from_row(row)
                return

    @Slot(QModelIndex, QModelIndex)
    def _row_changed(self, current: QModelIndex, _previous: QModelIndex) -> None:
        if current.isValid():
            self._load_selected_from_row(current.row())

    def _load_selected_from_row(self, row: int) -> None:
        item = self.model.row_data(row)
        if not item:
            return
        object_id = item.get("object_id")
        if not isinstance(object_id, str):
            return
        self.selected_object_id = object_id
        self._update_remove_class_button(item)
        self.load_object(object_id)

    def _update_remove_class_button(self, item: dict[str, object] | None) -> None:
        additional = item.get("additional_class_ids", ()) if item else ()
        has_additional = isinstance(additional, (list, tuple)) and any(
            isinstance(value, str) and bool(value) for value in additional
        )
        self.remove_class_button.setEnabled(bool(self.selected_object_id) and has_additional)

    def _selected_object_record(self) -> dict[str, object] | None:
        object_id = self.selected_object_id
        if not object_id:
            return None
        for row in range(self.model.rowCount()):
            item = self.model.row_data(row)
            if item and item.get("object_id") == object_id:
                return item
        return None

    def load_object(self, object_id: str) -> None:
        self.submit(
            "object.show",
            {"object_id": object_id, "knowledge": True},
            callback=lambda outcome: self._set_json(self.detail_text, outcome.data),
            summary=f"Loading Object {object_id}...",
        )
        self.submit(
            "object.alias.list",
            {"object_id": object_id},
            callback=lambda outcome: self._set_json(self.alias_text, outcome.data),
        )
        self.submit(
            "object.events",
            {"object_id": object_id},
            callback=lambda outcome: self._set_json(self.events_text, outcome.data),
        )
        self.submit(
            "object.relations",
            {"object_id": object_id},
            callback=lambda outcome: self._set_json(self.relations_text, outcome.data),
        )

    @staticmethod
    def _set_json(widget: QTextEdit, value: object) -> None:
        widget.setPlainText(json.dumps(value, ensure_ascii=False, indent=2, default=str))

    def add_object(
        self,
        name: str,
        primary_class: str,
        aliases: Iterable[str] = (),
    ) -> str | None:
        return self.submit(
            "object.add",
            {"name": name, "primary_class": primary_class, "alias": tuple(aliases)},
            callback=self._after_object_mutation,
            summary=f"Adding Object: {name}",
        )

    def rename_object(self, object_id: str, new_name: str) -> str | None:
        return self.submit(
            "object.rename",
            {"object_id": object_id, "to": new_name},
            callback=self._after_object_mutation,
            summary=f"Renaming Object {object_id}...",
        )

    def set_status(self, object_id: str, status: str) -> str | None:
        return self.submit(
            "object.status",
            {"object_id": object_id, "set": status},
            callback=self._after_object_mutation,
            summary=f"Setting Object status: {status}",
        )

    def add_alias(
        self,
        object_id: str,
        value: str,
        *,
        language: str | None = None,
        kind: str = "alias",
    ) -> str | None:
        return self.submit(
            "object.alias.add",
            {
                "object_id": object_id,
                "value": value,
                "language": language or None,
                "kind": kind,
            },
            callback=lambda outcome: self._after_alias_mutation(object_id, outcome),
            summary=f"Adding alias to {object_id}...",
        )

    def set_primary_class(self, object_id: str, class_ref: str) -> str | None:
        return self._class_mutation("object.class.set-primary", object_id, class_ref)

    def add_class(self, object_id: str, class_ref: str) -> str | None:
        return self._class_mutation("object.class.add", object_id, class_ref)

    def remove_class(self, object_id: str, class_ref: str) -> str | None:
        return self._class_mutation("object.class.remove", object_id, class_ref)

    def _class_mutation(self, operation_id: str, object_id: str, class_ref: str) -> str | None:
        return self.submit(
            operation_id,
            {"object_id": object_id, "class_ref": class_ref},
            callback=self._after_object_mutation,
            summary=f"Updating Object Class: {class_ref}",
        )

    def _after_object_mutation(self, outcome: OperationOutcome) -> None:
        data = outcome.data if isinstance(outcome.data, dict) else {}
        object_id = data.get("object_id")
        if isinstance(object_id, str):
            self.selected_object_id = object_id
        self.refresh_objects(select_id=self.selected_object_id)

    def _after_alias_mutation(self, object_id: str, outcome: OperationOutcome) -> None:
        self._set_json(self.alias_text, outcome.data)
        self.refresh_objects(select_id=object_id)

    def _require_selected(self) -> str | None:
        if not self.selected_object_id:
            self.operation_status.setText("Select an Object first.")
            return None
        return self.selected_object_id

    def _add_dialog(self) -> None:
        name, ok = QInputDialog.getText(self, "Add Object", "Canonical name:")
        if not ok or not name.strip():
            return
        canonical_name = name.strip()
        self.submit(
            "registry.class.list",
            callback=lambda outcome: self._continue_add_dialog(canonical_name, outcome),
            summary="Loading Object Classes...",
        )

    @staticmethod
    def _class_choices(
        value: object,
        *,
        active_only: bool = False,
        include_ids: Iterable[str] | None = None,
        exclude_ids: Iterable[str] = (),
    ) -> list[tuple[str, str]]:
        rows = value if isinstance(value, list) else []
        include_set = set(include_ids) if include_ids is not None else None
        exclude_set = set(exclude_ids)
        choices: list[tuple[str, str]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            status = row.get("status")
            if hasattr(status, "value"):
                status = status.value
            if active_only and status not in {None, "active"}:
                continue
            class_id = row.get("class_id")
            key = row.get("key")
            name = row.get("name")
            if not isinstance(class_id, str) or not class_id:
                continue
            if include_set is not None and class_id not in include_set:
                continue
            if class_id in exclude_set:
                continue
            label_name = name if isinstance(name, str) and name else class_id
            label_key = key if isinstance(key, str) and key else class_id
            label = f"{label_name} [{label_key}]"
            if not active_only and status not in {None, "active"}:
                label += f" ({status})"
            choices.append((label, class_id))
        return sorted(choices, key=lambda item: item[0].casefold())

    def _choose_class(
        self,
        *,
        title: str,
        prompt: str,
        choices: list[tuple[str, str]],
        empty_message: str,
    ) -> str | None:
        if not choices:
            self.operation_status.setText(empty_message)
            return None
        labels = [label for label, _class_id in choices]
        selected, ok = QInputDialog.getItem(
            self,
            title,
            prompt,
            labels,
            0,
            editable=False,
        )
        if not ok:
            return None
        class_id = dict(choices).get(selected)
        if class_id is None:
            self.operation_status.setText("Selected Object Class is no longer available.")
            return None
        return class_id

    def _continue_add_dialog(self, name: str, outcome: OperationOutcome) -> None:
        choices = self._class_choices(outcome.data, active_only=True)
        primary_class = self._choose_class(
            title="Add Object",
            prompt="Primary Class:",
            choices=choices,
            empty_message="No active Object Classes are available.",
        )
        if primary_class is None:
            return
        aliases_text, ok = QInputDialog.getText(
            self,
            "Add Object",
            "Aliases (comma-separated, optional):",
        )
        if not ok:
            return
        aliases = tuple(value.strip() for value in aliases_text.split(",") if value.strip())
        self.add_object(name, primary_class, aliases)

    def _rename_dialog(self) -> None:
        object_id = self._require_selected()
        if not object_id:
            return
        name, ok = QInputDialog.getText(self, "Rename Object", "New canonical name:")
        if ok and name.strip():
            self.rename_object(object_id, name.strip())

    def _status_dialog(self) -> None:
        object_id = self._require_selected()
        if not object_id:
            return
        status, ok = QInputDialog.getItem(
            self,
            "Set Object Status",
            "Status:",
            ["active", "archived"],
            editable=False,
        )
        if ok:
            self.set_status(object_id, status)

    def _alias_dialog(self) -> None:
        object_id = self._require_selected()
        if not object_id:
            return
        value, ok = QInputDialog.getText(self, "Add Alias", "Alias value:")
        if not ok or not value.strip():
            return
        language, ok = QInputDialog.getText(self, "Add Alias", "Language (optional):")
        if not ok:
            return
        self.add_alias(object_id, value.strip(), language=language.strip() or None)

    def _primary_class_dialog(self) -> None:
        object_id = self._require_selected()
        if not object_id:
            return
        self.submit(
            "registry.class.list",
            callback=lambda outcome: self._continue_primary_class_dialog(object_id, outcome),
            summary="Loading Object Classes...",
        )

    def _continue_primary_class_dialog(
        self,
        object_id: str,
        outcome: OperationOutcome,
    ) -> None:
        choices = self._class_choices(outcome.data)
        class_id = self._choose_class(
            title="Set Primary Class",
            prompt="Primary Class:",
            choices=choices,
            empty_message="No Object Classes are available.",
        )
        if class_id is not None:
            self.set_primary_class(object_id, class_id)

    def _add_class_dialog(self) -> None:
        object_id = self._require_selected()
        if not object_id:
            return
        record = self._selected_object_record()
        primary_class_id = record.get("primary_class_id") if record else None
        if not isinstance(primary_class_id, str):
            self.operation_status.setText("Selected Object has no valid Primary Class.")
            return
        self.submit(
            "registry.class.list",
            callback=lambda outcome: self._continue_add_class_dialog(
                object_id,
                primary_class_id,
                outcome,
            ),
            summary="Loading Object Classes...",
        )

    def _continue_add_class_dialog(
        self,
        object_id: str,
        primary_class_id: str,
        outcome: OperationOutcome,
    ) -> None:
        choices = self._class_choices(outcome.data, exclude_ids=(primary_class_id,))
        class_id = self._choose_class(
            title="Add Additional Class",
            prompt="Additional Class:",
            choices=choices,
            empty_message="No additional Object Classes are available.",
        )
        if class_id is not None:
            self.add_class(object_id, class_id)

    def _remove_class_dialog(self) -> None:
        object_id = self._require_selected()
        if not object_id:
            return
        record = self._selected_object_record()
        additional = record.get("additional_class_ids", ()) if record else ()
        additional_ids = tuple(
            value
            for value in additional
            if isinstance(value, str) and value
        ) if isinstance(additional, (list, tuple)) else ()
        if not additional_ids:
            self.remove_class_button.setEnabled(False)
            self.operation_status.setText("Selected Object has no Additional Class to remove.")
            return
        self.submit(
            "registry.class.list",
            callback=lambda outcome: self._continue_remove_class_dialog(
                object_id,
                additional_ids,
                outcome,
            ),
            summary="Loading assigned Object Classes...",
        )

    def _continue_remove_class_dialog(
        self,
        object_id: str,
        additional_class_ids: tuple[str, ...],
        outcome: OperationOutcome,
    ) -> None:
        choices = self._class_choices(outcome.data, include_ids=additional_class_ids)
        class_id = self._choose_class(
            title="Remove Additional Class",
            prompt="Additional Class:",
            choices=choices,
            empty_message="No assigned Additional Classes are available.",
        )
        if class_id is not None:
            self.remove_class(object_id, class_id)
