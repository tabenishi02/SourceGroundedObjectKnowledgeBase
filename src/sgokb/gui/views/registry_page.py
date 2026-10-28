"""P-GUI-06 Registry, Version, Diff, and Render surface."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path

from PySide6.QtCore import QModelIndex, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableView,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QInputDialog,
)

from sgokb.gui.models import DictTableModel
from sgokb.gui.views.operation_page import OperationPage
from sgokb.gui.worker import BackendCoordinator
from sgokb.operation_contracts import OperationOutcome
from sgokb.review import DiffReviewMarkdownRenderer


def _plain(value):
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _plain(value.to_dict())
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


class RegistryPage(OperationPage):
    """Browse Registry data and review immutable Versions without hidden write composition."""

    def __init__(self, backend: BackendCoordinator, parent=None) -> None:
        super().__init__(backend, parent)
        self.class_model = DictTableModel(
            (
                ("class_id", "Class ID"),
                ("key", "Key"),
                ("name", "Name"),
                ("assignment_policy", "Assignment Policy"),
                ("status", "Status"),
            ),
            self,
        )
        self.relation_model = DictTableModel(
            (
                ("id", "Relation Type ID"),
                ("key", "Key"),
                ("name", "Name"),
                ("status", "Status"),
            ),
            self,
        )
        self.proposal_model = DictTableModel(
            (
                ("proposal_ref", "Proposal Ref"),
                ("proposal_kind", "Kind"),
                ("decision", "Decision"),
                ("object_id", "Object ID"),
                ("version_id", "Version ID"),
                ("applied_at", "Applied At"),
            ),
            self,
        )
        self.selected_proposal: dict[str, object] | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        title = QLabel("Registry / Versions / Render", self)
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(title)

        self.tabs = QTabWidget(self)
        self.tabs.addTab(self._build_classes_tab(), "Classes")
        self.tabs.addTab(self._build_relations_tab(), "Relation Types")
        self.tabs.addTab(self._build_proposals_tab(), "Proposals")
        self.tabs.addTab(self._build_versions_tab(), "Versions / Diff")
        self.tabs.addTab(self._build_render_tab(), "Render")
        layout.addWidget(self.tabs, 1)
        layout.addWidget(self.operation_status)

    def _table_split(self, model: DictTableModel, detail: QTextEdit, parent: QWidget) -> QSplitter:
        splitter = QSplitter(parent)
        table = QTableView(splitter)
        table.setModel(model)
        table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setStretchLastSection(True)
        splitter.addWidget(table)
        splitter.addWidget(detail)
        splitter.setSizes([700, 480])
        return splitter

    def _build_classes_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        row = QHBoxLayout()
        refresh = QPushButton("Refresh Classes", page)
        refresh.clicked.connect(self.refresh_classes)
        row.addWidget(refresh)
        row.addStretch(1)
        layout.addLayout(row)
        self.class_detail = QTextEdit(page)
        self.class_detail.setReadOnly(True)
        self.class_detail.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        splitter = self._table_split(self.class_model, self.class_detail, page)
        self.class_table = splitter.widget(0)
        self.class_table.selectionModel().currentRowChanged.connect(self._class_changed)
        layout.addWidget(splitter, 1)
        return page

    def _build_relations_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        row = QHBoxLayout()
        refresh = QPushButton("Refresh Relation Types", page)
        refresh.clicked.connect(self.refresh_relations)
        row.addWidget(refresh)
        row.addStretch(1)
        layout.addLayout(row)
        self.relation_detail = QTextEdit(page)
        self.relation_detail.setReadOnly(True)
        self.relation_detail.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        splitter = self._table_split(self.relation_model, self.relation_detail, page)
        self.relation_table = splitter.widget(0)
        self.relation_table.selectionModel().currentRowChanged.connect(self._relation_changed)
        layout.addWidget(splitter, 1)
        return page

    def _build_proposals_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        controls = QHBoxLayout()
        self.proposal_filter = QComboBox(page)
        self.proposal_filter.addItem("All", None)
        self.proposal_filter.addItem("Pending", "pending")
        self.proposal_filter.addItem("Accepted", "accepted")
        self.proposal_filter.addItem("Rejected", "rejected")
        self.proposal_filter.currentIndexChanged.connect(self.refresh_proposals)
        refresh = QPushButton("Refresh", page)
        refresh.clicked.connect(self.refresh_proposals)
        self.accept_button = QPushButton("Accept...", page)
        self.accept_button.clicked.connect(lambda: self._proposal_decision_dialog("accepted"))
        self.reject_button = QPushButton("Reject...", page)
        self.reject_button.clicked.connect(lambda: self._proposal_decision_dialog("rejected"))
        self.apply_button = QPushButton("Apply...", page)
        self.apply_button.clicked.connect(self._proposal_apply_dialog)
        controls.addWidget(QLabel("Decision:", page))
        controls.addWidget(self.proposal_filter)
        controls.addWidget(refresh)
        controls.addStretch(1)
        controls.addWidget(self.accept_button)
        controls.addWidget(self.reject_button)
        controls.addWidget(self.apply_button)
        layout.addLayout(controls)

        self.proposal_detail = QTextEdit(page)
        self.proposal_detail.setReadOnly(True)
        self.proposal_detail.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        splitter = self._table_split(self.proposal_model, self.proposal_detail, page)
        self.proposal_table = splitter.widget(0)
        self.proposal_table.selectionModel().currentRowChanged.connect(self._proposal_changed)
        layout.addWidget(splitter, 1)
        self._update_proposal_actions(None)
        return page

    def _build_versions_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)

        show_row = QHBoxLayout()
        self.version_id = QLineEdit(page)
        self.version_id.setPlaceholderText("Accepted Version ID")
        show = QPushButton("Show Version", page)
        show.clicked.connect(self.show_version)
        show_row.addWidget(QLabel("Version:", page))
        show_row.addWidget(self.version_id, 1)
        show_row.addWidget(show)
        layout.addLayout(show_row)

        diff_row = QHBoxLayout()
        self.before_version = QLineEdit(page)
        self.before_version.setPlaceholderText("Before Version ID")
        self.after_version = QLineEdit(page)
        self.after_version.setPlaceholderText("After Version ID")
        diff = QPushButton("Diff Versions", page)
        diff.clicked.connect(self.diff_versions)
        diff_row.addWidget(QLabel("Before:", page))
        diff_row.addWidget(self.before_version, 1)
        diff_row.addWidget(QLabel("After:", page))
        diff_row.addWidget(self.after_version, 1)
        diff_row.addWidget(diff)
        layout.addLayout(diff_row)

        output_tabs = QTabWidget(page)
        self.version_structured = QTextEdit(output_tabs)
        self.version_structured.setReadOnly(True)
        self.version_structured.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.version_markdown = QTextEdit(output_tabs)
        self.version_markdown.setReadOnly(True)
        self.version_markdown.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        output_tabs.addTab(self.version_structured, "Structured")
        output_tabs.addTab(self.version_markdown, "Markdown Diff")
        layout.addWidget(output_tabs, 1)
        return page

    def _build_render_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        controls = QHBoxLayout()
        self.render_kind = QComboBox(page)
        self.render_kind.addItem("Object", "object")
        self.render_kind.addItem("Version", "version")
        self.render_target = QLineEdit(page)
        self.render_target.setPlaceholderText("Object ID or Version ID")
        self.render_root = QLineEdit(page)
        self.render_root.setPlaceholderText("Default: derived/rendered")
        browse = QPushButton("Output Root...", page)
        browse.clicked.connect(self._choose_render_root)
        render = QPushButton("Render / Export", page)
        render.clicked.connect(self.render_markdown)
        controls.addWidget(QLabel("Target:", page))
        controls.addWidget(self.render_kind)
        controls.addWidget(self.render_target, 1)
        controls.addWidget(QLabel("Output root:", page))
        controls.addWidget(self.render_root, 1)
        controls.addWidget(browse)
        controls.addWidget(render)
        layout.addLayout(controls)
        note = QLabel(
            "Render is a derived export. Editing the generated Markdown does not mutate canonical Knowledge.",
            page,
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        self.render_result = QTextEdit(page)
        self.render_result.setReadOnly(True)
        self.render_result.setMaximumHeight(150)
        self.render_preview = QTextEdit(page)
        self.render_preview.setReadOnly(True)
        self.render_preview.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.render_result)
        layout.addWidget(self.render_preview, 1)
        return page

    def workspace_changed(self) -> None:
        self.class_model.set_rows([])
        self.relation_model.set_rows([])
        self.proposal_model.set_rows([])
        self.class_detail.clear()
        self.relation_detail.clear()
        self.proposal_detail.clear()
        self.version_structured.clear()
        self.version_markdown.clear()
        self.render_result.clear()
        self.render_preview.clear()
        self.selected_proposal = None
        self._update_proposal_actions(None)
        self.refresh_classes()
        self.refresh_relations()
        self.refresh_proposals()

    def refresh_classes(self) -> str | None:
        return self.submit(
            "registry.class.list",
            callback=self._apply_classes,
            summary="Loading Registry Classes...",
        )

    def _apply_classes(self, outcome: OperationOutcome) -> None:
        rows = outcome.data if isinstance(outcome.data, list) else []
        normalized = [dict(row) for row in rows if isinstance(row, dict)]
        self.class_model.set_rows(normalized)
        if normalized:
            self.class_table.selectRow(0)

    @Slot(QModelIndex, QModelIndex)
    def _class_changed(self, current: QModelIndex, _previous: QModelIndex) -> None:
        if not current.isValid():
            return
        row = self.class_model.row_data(current.row())
        class_ref = row.get("class_id") if row else None
        if isinstance(class_ref, str):
            self.submit(
                "registry.class.show",
                {"class_ref": class_ref},
                callback=lambda outcome: self.class_detail.setPlainText(_json(outcome.data)),
                summary=f"Loading Class: {class_ref}",
            )

    def refresh_relations(self) -> str | None:
        return self.submit(
            "registry.relation-type.list",
            callback=self._apply_relations,
            summary="Loading Relation Types...",
        )

    def _apply_relations(self, outcome: OperationOutcome) -> None:
        rows = outcome.data if isinstance(outcome.data, list) else []
        normalized = [dict(row) for row in rows if isinstance(row, dict)]
        self.relation_model.set_rows(normalized)
        if normalized:
            self.relation_table.selectRow(0)

    @Slot(QModelIndex, QModelIndex)
    def _relation_changed(self, current: QModelIndex, _previous: QModelIndex) -> None:
        if not current.isValid():
            return
        row = self.relation_model.row_data(current.row())
        relation_ref = row.get("id") if row else None
        if isinstance(relation_ref, str):
            self.submit(
                "registry.relation-type.show",
                {"relation_ref": relation_ref},
                callback=lambda outcome: self.relation_detail.setPlainText(_json(outcome.data)),
                summary=f"Loading Relation Type: {relation_ref}",
            )

    def refresh_proposals(self) -> str | None:
        arguments: dict[str, object] = {}
        decision = self.proposal_filter.currentData()
        if isinstance(decision, str):
            arguments["decision"] = decision
        return self.submit(
            "registry.proposal.list",
            arguments,
            callback=self._apply_proposals,
            summary="Loading Registry Proposals...",
        )

    def _apply_proposals(self, outcome: OperationOutcome) -> None:
        rows = outcome.data if isinstance(outcome.data, list) else []
        normalized = [dict(row) for row in rows if isinstance(row, dict)]
        self.proposal_model.set_rows(normalized)
        self.selected_proposal = None
        self._update_proposal_actions(None)
        if normalized:
            self.proposal_table.selectRow(0)

    @Slot(QModelIndex, QModelIndex)
    def _proposal_changed(self, current: QModelIndex, _previous: QModelIndex) -> None:
        if not current.isValid():
            self.selected_proposal = None
            self._update_proposal_actions(None)
            return
        row = self.proposal_model.row_data(current.row())
        proposal_ref = row.get("proposal_ref") if row else None
        if not isinstance(proposal_ref, str):
            return
        self.submit(
            "registry.proposal.show",
            {"proposal_ref": proposal_ref},
            callback=self._apply_proposal_detail,
            summary=f"Loading Registry Proposal: {proposal_ref}",
        )

    def _apply_proposal_detail(self, outcome: OperationOutcome) -> None:
        payload = _plain(outcome.data)
        self.selected_proposal = payload if isinstance(payload, dict) else None
        self.proposal_detail.setPlainText(_json(payload))
        self._update_proposal_actions(self.selected_proposal)

    def _update_proposal_actions(self, proposal: dict[str, object] | None) -> None:
        if proposal is None:
            self.accept_button.setEnabled(False)
            self.reject_button.setEnabled(False)
            self.apply_button.setEnabled(False)
            return
        applied = proposal.get("applied_at") is not None
        decision = proposal.get("decision")
        self.accept_button.setEnabled(not applied)
        self.reject_button.setEnabled(not applied)
        self.apply_button.setEnabled(not applied and decision == "accepted")

    def _selected_proposal_ref(self) -> str | None:
        value = self.selected_proposal.get("proposal_ref") if self.selected_proposal else None
        if not isinstance(value, str):
            self.operation_status.setText("Select a Registry Proposal first.")
            return None
        return value

    def decide_proposal(self, proposal_ref: str, decision: str, note: str = "") -> str | None:
        operation = (
            "registry.proposal.accept" if decision == "accepted" else "registry.proposal.reject"
        )
        return self.submit(
            operation,
            {"proposal_ref": proposal_ref, "note": note},
            callback=self._after_proposal_write,
            summary=f"Recording Registry Proposal decision: {decision}",
        )

    def _proposal_decision_dialog(self, decision: str) -> None:
        proposal_ref = self._selected_proposal_ref()
        if proposal_ref is None:
            return
        note, ok = QInputDialog.getText(
            self,
            "Registry Proposal Decision",
            f"Review note for {decision} decision (optional):",
        )
        if ok:
            self.decide_proposal(proposal_ref, decision, note.strip())

    def apply_proposal(self, proposal_ref: str) -> str | None:
        return self.submit(
            "registry.proposal.apply",
            {"proposal_ref": proposal_ref},
            callback=self._after_proposal_write,
            summary="Applying accepted Registry Proposal...",
        )

    def _proposal_apply_dialog(self) -> None:
        proposal_ref = self._selected_proposal_ref()
        if proposal_ref is None:
            return
        answer = QMessageBox.question(
            self,
            "Apply Registry Proposal",
            (
                "Apply the selected accepted Registry Proposal to canonical Registry/Object data?\n\n"
                f"{proposal_ref}\n\nAccept and Apply are intentionally separate operations."
            ),
            QMessageBox.StandardButton.Apply | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Apply:
            self.apply_proposal(proposal_ref)

    def _after_proposal_write(self, outcome: OperationOutcome) -> None:
        self.proposal_detail.setPlainText(_json(outcome.data))
        self.refresh_proposals()

    def show_version(self, version_id: str | None = None) -> str | None:
        target = (version_id or self.version_id.text()).strip()
        if not target:
            self.operation_status.setText("Enter an accepted Version ID first.")
            return None
        return self.submit(
            "version.show",
            {"version_id": target},
            callback=self._apply_version_show,
            summary=f"Loading Version: {target}",
        )

    def _apply_version_show(self, outcome: OperationOutcome) -> None:
        self.version_structured.setPlainText(_json(outcome.data))
        self.version_markdown.setPlainText(
            "Markdown Diff is available after comparing two accepted Versions."
        )

    def diff_versions(
        self,
        before_version_id: str | None = None,
        after_version_id: str | None = None,
    ) -> str | None:
        before = (before_version_id or self.before_version.text()).strip()
        after = (after_version_id or self.after_version.text()).strip()
        if not before or not after:
            self.operation_status.setText("Enter both Before and After Version IDs.")
            return None
        return self.submit(
            "version.diff",
            {"before_version_id": before, "after_version_id": after},
            callback=self._apply_version_diff,
            summary=f"Diffing Versions: {before} -> {after}",
        )

    def _apply_version_diff(self, outcome: OperationOutcome) -> None:
        payload = _plain(outcome.data)
        self.version_structured.setPlainText(_json(payload))
        if isinstance(payload, dict):
            self.version_markdown.setPlainText(DiffReviewMarkdownRenderer().render_diff(payload))
        else:
            self.version_markdown.setPlainText("Version Diff returned an unsupported result shape.")

    def _choose_render_root(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Render Output Root", "")
        if path:
            self.render_root.setText(path)

    def render_markdown(
        self,
        target: str | None = None,
        *,
        kind: str | None = None,
        output_root: str | None = None,
    ) -> str | None:
        resolved_target = (target or self.render_target.text()).strip()
        if not resolved_target:
            self.operation_status.setText("Enter an Object ID or Version ID to render.")
            return None
        resolved_kind = kind or str(self.render_kind.currentData())
        arguments: dict[str, object] = {resolved_kind: resolved_target}
        resolved_root = (output_root or self.render_root.text()).strip()
        if resolved_root:
            arguments["output_root"] = resolved_root
        return self.submit(
            "render",
            arguments,
            callback=self._apply_render,
            summary=f"Rendering {resolved_kind}: {resolved_target}",
        )

    def _apply_render(self, outcome: OperationOutcome) -> None:
        payload = _plain(outcome.data)
        self.render_result.setPlainText(_json(payload))
        path_value = payload.get("output_path") if isinstance(payload, dict) else None
        if not isinstance(path_value, str):
            self.render_preview.setPlainText("Render completed without a readable output path.")
            return
        path = Path(path_value)
        try:
            self.render_preview.setPlainText(path.read_text(encoding="utf-8"))
        except OSError as exc:
            self.render_preview.setPlainText(
                f"Render output was created but preview could not be read: {exc}"
            )
