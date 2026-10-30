"""P-GUI-09 System / Maintenance / MCP / Advanced GUI."""

from __future__ import annotations

import dataclasses
import json
from enum import Enum
from pathlib import Path
from typing import Mapping

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from sgokb.application_generation import LEGACY_GENERATION_ID
from sgokb.gui.operation_ux import equivalent_cli_command
from sgokb.operation_contracts import OperationOutcome

from .operation_page import OperationPage


def _jsonable(value):
    if dataclasses.is_dataclass(value):
        return _jsonable(dataclasses.asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _jsonable(value.to_dict())
    return value


def _json_text(value) -> str:
    return json.dumps(_jsonable(value), ensure_ascii=False, indent=2, sort_keys=True, default=str)


def _required_text(field: QLineEdit, label: str, status: QLabel) -> str | None:
    value = field.text().strip()
    if value:
        return value
    status.setText(f"{label} is required.")
    field.setFocus()
    return None


class SystemPage(OperationPage):
    """Expose public System operations and isolated Advanced maintenance controls."""

    def __init__(self, backend, parent=None) -> None:
        super().__init__(backend, parent)
        self._restore_plan_key: tuple[str, ...] | None = None
        self._restore_requires_ack = False
        self._composite_plan_key: tuple[str, ...] | None = None
        self._composite_requires_ack = False
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        title = QLabel("System / Maintenance", self)
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        root.addWidget(title)
        root.addWidget(self.operation_status)

        self.tabs = QTabWidget(self)
        self.tabs.addTab(self._build_overview_tab(), "Overview")
        self.tabs.addTab(self._build_derived_tab(), "Derived")
        self.tabs.addTab(self._build_index_tab(), "Vector Index")
        self.tabs.addTab(self._build_backup_tab(), "Backup")
        self.tabs.addTab(self._build_restore_tab(), "Restore")
        self.tabs.addTab(self._build_mcp_tab(), "MCP")
        self.tabs.addTab(self._build_generation_tab(), "Advanced Generation")
        root.addWidget(self.tabs, 1)

    @staticmethod
    def _readout(parent: QWidget) -> QPlainTextEdit:
        output = QPlainTextEdit(parent)
        output.setReadOnly(True)
        output.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        return output

    @staticmethod
    def _button_row(*buttons: QPushButton) -> QWidget:
        host = QWidget()
        layout = QHBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        for button in buttons:
            layout.addWidget(button)
        layout.addStretch(1)
        return host

    def _build_overview_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        self.runtime_summary = QLabel("Runtime health is available after opening a Workspace.", page)
        self.runtime_summary.setWordWrap(True)
        layout.addWidget(self.runtime_summary)
        self.system_status_button = QPushButton("Refresh system status", page)
        self.integrity_button = QPushButton("Run integrity check", page)
        self.system_status_button.clicked.connect(self._run_system_status)
        self.integrity_button.clicked.connect(self._run_integrity)
        layout.addWidget(self._button_row(self.system_status_button, self.integrity_button))
        self.overview_output = self._readout(page)
        layout.addWidget(self.overview_output, 1)
        return page

    def _build_derived_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        form = QFormLayout()
        self.derived_object = QLineEdit(page)
        self.derived_object.setPlaceholderText("optional object_id; blank = all current objects")
        self.derived_semantic = QCheckBox("Enable local Embedding + Qdrant semantic runtime", page)
        form.addRow("Object scope", self.derived_object)
        form.addRow("Runtime", self.derived_semantic)
        layout.addLayout(form)
        self.derived_status_button = QPushButton("Derived status", page)
        self.derived_sync_button = QPushButton("Sync derived state", page)
        self.derived_status_button.clicked.connect(self._run_derived_status)
        self.derived_sync_button.clicked.connect(self._run_derived_sync)
        layout.addWidget(self._button_row(self.derived_status_button, self.derived_sync_button))
        note = QLabel(
            "Sync changes replaceable derived state only. Semantic mode can load the local model "
            "and use Qdrant; no cloud fallback is performed.",
            page,
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        self.derived_output = self._readout(page)
        layout.addWidget(self.derived_output, 1)
        return page

    def _build_index_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        note = QLabel(
            "Index rebuild is an explicit MAINTENANCE operation. It requires the local semantic "
            "runtime and rebuilds replaceable Vector derived state.",
            page,
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        self.index_status_button = QPushButton("Index status", page)
        self.index_rebuild_button = QPushButton("Rebuild vector index", page)
        self.index_status_button.clicked.connect(self._run_index_status)
        self.index_rebuild_button.clicked.connect(self._run_index_rebuild)
        layout.addWidget(self._button_row(self.index_status_button, self.index_rebuild_button))
        self.index_output = self._readout(page)
        layout.addWidget(self.index_output, 1)
        return page

    def _build_backup_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)

        sqlite_group = QGroupBox("SQLite backup", page)
        sqlite_layout = QVBoxLayout(sqlite_group)
        form = QFormLayout()
        self.backup_root = QLineEdit("backups", sqlite_group)
        self.backup_output = QLineEdit(sqlite_group)
        self.backup_output.setPlaceholderText("optional explicit .sqlite output")
        form.addRow("Backup root", self.backup_root)
        form.addRow("Output", self.backup_output)
        sqlite_layout.addLayout(form)
        self.backup_status_button = QPushButton("List backups", sqlite_group)
        self.backup_create_button = QPushButton("Create SQLite backup", sqlite_group)
        self.backup_status_button.clicked.connect(self._run_backup_status)
        self.backup_create_button.clicked.connect(self._run_backup_create)
        sqlite_layout.addWidget(self._button_row(self.backup_status_button, self.backup_create_button))
        layout.addWidget(sqlite_group)

        composite_group = QGroupBox("Composite canonical backup", page)
        composite_layout = QVBoxLayout(composite_group)
        composite_form = QFormLayout()
        self.composite_incoming_root = QLineEdit("exchange/incoming", composite_group)
        self.composite_backup_root = QLineEdit("backups", composite_group)
        self.composite_backup_output = QLineEdit(composite_group)
        self.composite_backup_output.setPlaceholderText("optional output generation directory")
        self.composite_verify_path = QLineEdit(composite_group)
        self.composite_verify_path.setPlaceholderText("existing composite backup directory")
        composite_form.addRow("Incoming Result root", self.composite_incoming_root)
        composite_form.addRow("Backup root", self.composite_backup_root)
        composite_form.addRow("Output", self.composite_backup_output)
        composite_form.addRow("Verify backup", self.composite_verify_path)
        composite_layout.addLayout(composite_form)
        self.composite_create_button = QPushButton("Create composite backup", composite_group)
        self.composite_verify_button = QPushButton("Verify composite backup", composite_group)
        self.composite_create_button.clicked.connect(self._run_composite_backup_create)
        self.composite_verify_button.clicked.connect(self._run_composite_backup_verify)
        composite_layout.addWidget(
            self._button_row(self.composite_create_button, self.composite_verify_button)
        )
        layout.addWidget(composite_group)

        self.backup_output_view = self._readout(page)
        layout.addWidget(self.backup_output_view, 1)
        return page

    def _build_restore_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        warning = QLabel(
            "Restore is intentionally two-stage. Run Plan first, inspect the exact target and "
            "overwrite state, then acknowledge overwrite when required before Apply.",
            page,
        )
        warning.setWordWrap(True)
        warning.setStyleSheet("font-weight: 600;")
        layout.addWidget(warning)

        sqlite_group = QGroupBox("SQLite restore to active Workspace", page)
        sqlite_layout = QVBoxLayout(sqlite_group)
        form = QFormLayout()
        self.restore_backup = QLineEdit(sqlite_group)
        self.restore_backup.setPlaceholderText("backup .sqlite path")
        self.restore_target = QLineEdit(sqlite_group)
        self.restore_target.setReadOnly(True)
        self.restore_ack = QCheckBox("Acknowledge overwrite of existing Workspace DB", sqlite_group)
        form.addRow("Backup", self.restore_backup)
        form.addRow("Target", self.restore_target)
        form.addRow("Acknowledgement", self.restore_ack)
        sqlite_layout.addLayout(form)
        self.restore_plan_button = QPushButton("Plan SQLite restore", sqlite_group)
        self.restore_apply_button = QPushButton("Apply planned SQLite restore", sqlite_group)
        self.restore_apply_button.setEnabled(False)
        self.restore_plan_button.clicked.connect(self._run_restore_plan)
        self.restore_apply_button.clicked.connect(self._run_restore_apply)
        self.restore_backup.textChanged.connect(self._invalidate_restore_plan)
        sqlite_layout.addWidget(self._button_row(self.restore_plan_button, self.restore_apply_button))
        self.restore_plan_output = self._readout(sqlite_group)
        self.restore_plan_output.setMaximumHeight(190)
        sqlite_layout.addWidget(self.restore_plan_output)
        layout.addWidget(sqlite_group)

        composite_group = QGroupBox("Composite restore", page)
        composite_layout = QVBoxLayout(composite_group)
        cform = QFormLayout()
        self.composite_restore_backup = QLineEdit(composite_group)
        self.composite_restore_db = QLineEdit(composite_group)
        self.composite_restore_raw = QLineEdit(composite_group)
        self.composite_restore_incoming = QLineEdit(composite_group)
        self.composite_restore_ack = QCheckBox(
            "Acknowledge overwrite where the verified plan reports existing targets",
            composite_group,
        )
        cform.addRow("Backup generation", self.composite_restore_backup)
        cform.addRow("Database target", self.composite_restore_db)
        cform.addRow("Raw root", self.composite_restore_raw)
        cform.addRow("Incoming Result root", self.composite_restore_incoming)
        cform.addRow("Acknowledgement", self.composite_restore_ack)
        composite_layout.addLayout(cform)
        self.composite_plan_button = QPushButton("Plan composite restore", composite_group)
        self.composite_apply_button = QPushButton("Apply planned composite restore", composite_group)
        self.composite_apply_button.setEnabled(False)
        self.composite_plan_button.clicked.connect(self._run_composite_restore_plan)
        self.composite_apply_button.clicked.connect(self._run_composite_restore_apply)
        for field in (
            self.composite_restore_backup,
            self.composite_restore_db,
            self.composite_restore_raw,
            self.composite_restore_incoming,
        ):
            field.textChanged.connect(self._invalidate_composite_plan)
        composite_layout.addWidget(self._button_row(self.composite_plan_button, self.composite_apply_button))
        self.composite_plan_output = self._readout(composite_group)
        self.composite_plan_output.setMaximumHeight(210)
        composite_layout.addWidget(self.composite_plan_output)
        layout.addWidget(composite_group)
        layout.addStretch(1)
        return page

    def _build_mcp_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        self.mcp_state = QLabel(
            "Lifecycle state: external client-managed stdio process; GUI does not own a detached MCP daemon.",
            page,
        )
        self.mcp_state.setWordWrap(True)
        layout.addWidget(self.mcp_state)
        lifecycle = QLabel(
            "The current MCP transport is stdio. A useful server process is therefore launched and "
            "owned by the MCP client that connects to its stdin/stdout. Starting a detached copy from "
            "the SGOKB GUI would not expose a connectable endpoint, so P-GUI-09 provides the exact "
            "serve configuration/command instead of a misleading Start/Stop button. Closing the GUI "
            "does not stop MCP processes launched by external clients.",
            page,
        )
        lifecycle.setWordWrap(True)
        layout.addWidget(lifecycle)
        self.mcp_semantic = QCheckBox("Enable semantic runtime for MCP read tools", page)
        self.mcp_semantic.toggled.connect(self._refresh_mcp_command)
        layout.addWidget(self.mcp_semantic)
        self.mcp_command = QLineEdit(page)
        self.mcp_command.setReadOnly(True)
        layout.addWidget(QLabel("Client launch command", page))
        layout.addWidget(self.mcp_command)
        self.mcp_copy_button = QPushButton("Copy serve command", page)
        self.mcp_copy_button.clicked.connect(self._copy_mcp_command)
        layout.addWidget(self._button_row(self.mcp_copy_button))
        mcp_contract = QLabel(
            "MCP remains read-only. GUI configuration does not add canonical write tools and does "
            "not make MCP lifecycle part of the synchronous OperatorSession.",
            page,
        )
        mcp_contract.setWordWrap(True)
        layout.addWidget(mcp_contract)
        layout.addStretch(1)
        return page

    def _build_generation_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        warning = QLabel(
            "Advanced / Search Generation Maintenance. These actions are outside the public 67-operation "
            "sgokb parity surface and are intentionally isolated from the normal Search page.",
            page,
        )
        warning.setWordWrap(True)
        warning.setStyleSheet("font-weight: 600;")
        layout.addWidget(warning)

        form = QFormLayout()
        self.generation_id = QLineEdit(page)
        self.generation_id.setPlaceholderText("generation ID; rollback blank uses legacy generation")
        self.generation_reason = QLineEdit("GUI Advanced Search Generation maintenance", page)
        self.generation_smoke = QCheckBox("Run post-switch smoke verification", page)
        self.generation_smoke.setChecked(True)
        form.addRow("Generation ID", self.generation_id)
        form.addRow("Reason", self.generation_reason)
        form.addRow("Switch verification", self.generation_smoke)
        layout.addLayout(form)

        self.generation_status_button = QPushButton("Generation status", page)
        self.generation_bootstrap_button = QPushButton("Bootstrap legacy generation", page)
        self.generation_build_button = QPushButton("Build R2 candidate", page)
        self.generation_cutover_button = QPushButton("Cut over to generation", page)
        self.generation_rollback_button = QPushButton("Rollback generation", page)
        self.generation_recover_button = QPushButton("Recover interrupted builds", page)
        self.generation_status_button.clicked.connect(
            lambda: self._run_generation("generation.status", {})
        )
        self.generation_bootstrap_button.clicked.connect(self._run_generation_bootstrap)
        self.generation_build_button.clicked.connect(
            lambda: self._run_generation("generation.build", {})
        )
        self.generation_cutover_button.clicked.connect(self._run_generation_cutover)
        self.generation_rollback_button.clicked.connect(self._run_generation_rollback)
        self.generation_recover_button.clicked.connect(self._run_generation_recover)
        layout.addWidget(
            self._button_row(
                self.generation_status_button,
                self.generation_bootstrap_button,
                self.generation_build_button,
            )
        )
        layout.addWidget(
            self._button_row(
                self.generation_cutover_button,
                self.generation_rollback_button,
                self.generation_recover_button,
            )
        )
        self.generation_output = self._readout(page)
        layout.addWidget(self.generation_output, 1)
        return page

    def workspace_changed(self) -> None:
        if self.workspace.db_path is None:
            return
        self.restore_target.setText(str(self.workspace.db_path))
        if not self.composite_restore_db.text().strip():
            self.composite_restore_db.setText(str(self.workspace.db_path))
        self.overview_output.setPlainText(_json_text(self.workspace.status))
        self._update_runtime_summary(self.workspace.status)
        self._invalidate_restore_plan()
        self._invalidate_composite_plan()
        self._refresh_mcp_command()

    def _display(self, widget: QPlainTextEdit, outcome: OperationOutcome) -> None:
        widget.setPlainText(_json_text(outcome.data))

    def _update_runtime_summary(self, status: object) -> None:
        runtime = status.get("runtime_health", {}) if isinstance(status, Mapping) else {}
        components = runtime.get("components", {}) if isinstance(runtime, Mapping) else {}
        if not isinstance(components, Mapping) or not components:
            self.runtime_summary.setText("Runtime health snapshot unavailable in current status data.")
            return
        parts = []
        for name in ("sqlite", "embedding", "qdrant", "generation", "derived"):
            value = components.get(name)
            state = value.get("status", "unknown") if isinstance(value, Mapping) else "unknown"
            parts.append(f"{name}={state}")
        self.runtime_summary.setText("Runtime health: " + " | ".join(parts))

    def _run_system_status(self) -> None:
        self.submit("system.status", callback=self._on_system_status, summary="Refreshing system status...")

    def _on_system_status(self, outcome: OperationOutcome) -> None:
        self._display(self.overview_output, outcome)
        self._update_runtime_summary(outcome.data)

    def _run_integrity(self) -> None:
        self.submit("system.integrity", callback=lambda o: self._display(self.overview_output, o))

    def _derived_arguments(self) -> dict[str, object]:
        object_id = self.derived_object.text().strip()
        return {
            "object_id": object_id or None,
            "semantic_runtime": self.derived_semantic.isChecked(),
        }

    def _run_derived_status(self) -> None:
        self.submit(
            "system.derived.status",
            self._derived_arguments(),
            callback=lambda o: self._display(self.derived_output, o),
        )

    def _run_derived_sync(self) -> None:
        self.submit(
            "system.derived.sync",
            self._derived_arguments(),
            callback=lambda o: self._display(self.derived_output, o),
        )

    def _run_index_status(self) -> None:
        self.submit("system.index.status", callback=lambda o: self._display(self.index_output, o))

    def _run_index_rebuild(self) -> None:
        self.submit("system.index.rebuild", callback=lambda o: self._display(self.index_output, o))

    def _run_backup_status(self) -> None:
        root = self.backup_root.text().strip() or "backups"
        self.submit(
            "system.backup.status",
            {"root": root},
            callback=lambda o: self._display(self.backup_output_view, o),
        )

    def _run_backup_create(self) -> None:
        root = self.backup_root.text().strip() or "backups"
        output = self.backup_output.text().strip()
        self.submit(
            "system.backup.create",
            {"root": root, "output": output or None},
            callback=lambda o: self._display(self.backup_output_view, o),
        )

    def _run_composite_backup_create(self) -> None:
        incoming = _required_text(
            self.composite_incoming_root, "Incoming Result root", self.operation_status
        )
        if incoming is None:
            return
        root = self.composite_backup_root.text().strip() or "backups"
        output = self.composite_backup_output.text().strip()
        self.submit(
            "system.backup.composite.create",
            {"incoming_root": incoming, "root": root, "output": output or None},
            callback=lambda o: self._display(self.backup_output_view, o),
        )

    def _run_composite_backup_verify(self) -> None:
        backup = _required_text(self.composite_verify_path, "Composite backup", self.operation_status)
        if backup is None:
            return
        self.submit(
            "system.backup.composite.verify",
            {"backup": backup},
            callback=lambda o: self._display(self.backup_output_view, o),
        )

    def _restore_key(self) -> tuple[str, ...]:
        return (self.restore_backup.text().strip(),)

    def _invalidate_restore_plan(self, *_args) -> None:
        self._restore_plan_key = None
        self._restore_requires_ack = False
        self.restore_apply_button.setEnabled(False)
        self.restore_ack.setChecked(False)

    def _run_restore_plan(self) -> None:
        backup = _required_text(self.restore_backup, "Backup", self.operation_status)
        if backup is None:
            return
        self.submit(
            "system.restore.plan",
            {"backup": backup},
            callback=self._on_restore_plan,
            summary="Planning SQLite restore...",
        )

    def _on_restore_plan(self, outcome: OperationOutcome) -> None:
        self._display(self.restore_plan_output, outcome)
        self._restore_plan_key = self._restore_key()
        data = outcome.data if isinstance(outcome.data, Mapping) else {}
        self._restore_requires_ack = bool(data.get("requires_overwrite_acknowledgement", False))
        self.restore_ack.setChecked(False)
        self.restore_apply_button.setEnabled(True)
        if self._restore_requires_ack:
            self.operation_status.setText(
                "Restore plan ready. Existing target detected; overwrite acknowledgement is required."
            )
        else:
            self.operation_status.setText("Restore plan ready. Review it before Apply.")

    def _run_restore_apply(self) -> None:
        if self._restore_plan_key is None or self._restore_plan_key != self._restore_key():
            self.operation_status.setText("Run Restore Plan again for the current inputs before Apply.")
            self.restore_apply_button.setEnabled(False)
            return
        if self._restore_requires_ack and not self.restore_ack.isChecked():
            self.operation_status.setText("Explicit overwrite acknowledgement is required by the plan.")
            return
        backup = self.restore_backup.text().strip()
        self.submit(
            "system.restore.apply",
            {"backup": backup, "acknowledge_overwrite": self.restore_ack.isChecked()},
            callback=self._on_restore_applied,
            summary="Applying planned SQLite restore...",
        )

    def _on_restore_applied(self, outcome: OperationOutcome) -> None:
        self._display(self.restore_plan_output, outcome)
        self._invalidate_restore_plan()
        self.operation_status.setText(
            "SQLite restore applied. Reopen the Workspace before further canonical operations."
        )

    def _composite_key(self) -> tuple[str, ...]:
        return (
            self.composite_restore_backup.text().strip(),
            self.composite_restore_db.text().strip(),
            self.composite_restore_raw.text().strip(),
            self.composite_restore_incoming.text().strip(),
        )

    def _invalidate_composite_plan(self, *_args) -> None:
        self._composite_plan_key = None
        self._composite_requires_ack = False
        self.composite_apply_button.setEnabled(False)
        self.composite_restore_ack.setChecked(False)

    def _composite_arguments(self) -> dict[str, object] | None:
        values = []
        for field, label in (
            (self.composite_restore_backup, "Composite backup"),
            (self.composite_restore_db, "Database target"),
            (self.composite_restore_raw, "Raw root"),
            (self.composite_restore_incoming, "Incoming Result root"),
        ):
            value = _required_text(field, label, self.operation_status)
            if value is None:
                return None
            values.append(value)
        return {
            "backup": values[0],
            "db_target": values[1],
            "raw_root": values[2],
            "incoming_root": values[3],
        }

    def _run_composite_restore_plan(self) -> None:
        arguments = self._composite_arguments()
        if arguments is None:
            return
        self.submit(
            "system.restore.composite.plan",
            arguments,
            callback=self._on_composite_plan,
            summary="Planning composite restore...",
        )

    def _on_composite_plan(self, outcome: OperationOutcome) -> None:
        self._display(self.composite_plan_output, outcome)
        self._composite_plan_key = self._composite_key()
        data = outcome.data if isinstance(outcome.data, Mapping) else {}
        existing = data.get("existing", {})
        self._composite_requires_ack = bool(
            isinstance(existing, Mapping) and any(bool(value) for value in existing.values())
        )
        self.composite_restore_ack.setChecked(False)
        self.composite_apply_button.setEnabled(True)
        if self._composite_requires_ack:
            self.operation_status.setText(
                "Composite plan ready. Existing target(s) detected; overwrite acknowledgement is required."
            )
        else:
            self.operation_status.setText("Composite plan ready. Review every target before Apply.")

    def _run_composite_restore_apply(self) -> None:
        if self._composite_plan_key is None or self._composite_plan_key != self._composite_key():
            self.operation_status.setText(
                "Run Composite Restore Plan again for the current inputs before Apply."
            )
            self.composite_apply_button.setEnabled(False)
            return
        if self._composite_requires_ack and not self.composite_restore_ack.isChecked():
            self.operation_status.setText("Explicit overwrite acknowledgement is required by the plan.")
            return
        arguments = self._composite_arguments()
        if arguments is None:
            return
        arguments["acknowledge_overwrite"] = self.composite_restore_ack.isChecked()
        self.submit(
            "system.restore.composite.apply",
            arguments,
            callback=self._on_composite_restore_applied,
            summary="Applying planned composite restore...",
        )

    def _on_composite_restore_applied(self, outcome: OperationOutcome) -> None:
        self._display(self.composite_plan_output, outcome)
        self._invalidate_composite_plan()
        self.operation_status.setText(
            "Composite restore applied. Open the restored Workspace explicitly before continuing."
        )

    def _refresh_mcp_command(self, *_args) -> None:
        if not self.workspace.is_open or self.workspace.db_path is None:
            self.mcp_command.clear()
            return
        self.mcp_command.setText(
            equivalent_cli_command(
                self.workspace.db_path,
                "mcp.serve",
                {"semantic_runtime": self.mcp_semantic.isChecked()},
            )
        )

    def _copy_mcp_command(self) -> None:
        command = self.mcp_command.text()
        if command:
            QApplication.clipboard().setText(command)
            self.operation_status.setText("MCP serve command copied. Lifecycle remains external/client-owned.")

    def _run_generation(self, operation_id: str, arguments: dict[str, object]) -> None:
        self.submit(
            operation_id,
            arguments,
            callback=lambda o: self._display(self.generation_output, o),
        )

    def _generation_reason_text(self) -> str:
        return self.generation_reason.text().strip() or "GUI Advanced Search Generation maintenance"

    def _run_generation_bootstrap(self) -> None:
        self._run_generation(
            "generation.bootstrap",
            {"reason": self._generation_reason_text()},
        )

    def _run_generation_cutover(self) -> None:
        generation_id = _required_text(self.generation_id, "Generation ID", self.operation_status)
        if generation_id is None:
            return
        self._run_generation(
            "generation.cutover",
            {
                "generation_id": generation_id,
                "reason": self._generation_reason_text(),
                "smoke": self.generation_smoke.isChecked(),
            },
        )

    def _run_generation_rollback(self) -> None:
        generation_id = self.generation_id.text().strip() or LEGACY_GENERATION_ID
        self._run_generation(
            "generation.rollback",
            {
                "generation_id": generation_id,
                "reason": self._generation_reason_text(),
                "smoke": self.generation_smoke.isChecked(),
            },
        )

    def _run_generation_recover(self) -> None:
        self._run_generation(
            "generation.recover",
            {"reason": self._generation_reason_text()},
        )
