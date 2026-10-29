"""P-GUI-08 Package / Result workflow for the Raw-grounded exchange contract."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Mapping

from PySide6.QtCore import QModelIndex, Slot
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
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


def _mapping(value: object) -> dict[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict"):
        candidate = value.to_dict()
        if isinstance(candidate, Mapping):
            return dict(candidate)
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {}


def _json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _csv_ids(text: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(item.strip() for item in text.split(",") if item.strip()))


def _load_manifest(path: str | Path) -> dict[str, Any]:
    root = Path(path)
    manifest_path = root / "manifest.json" if root.is_dir() else root
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Package manifest root must be an object")
    return value


def _raw_rows(manifest: Mapping[str, Any]) -> list[dict[str, object]]:
    raw = manifest.get("raw_grounding")
    if not isinstance(raw, Mapping):
        return []
    rows: list[dict[str, object]] = []
    for artifact in raw.get("artifacts", ()) or ():
        if not isinstance(artifact, Mapping):
            continue
        rows.append(
            {
                "raw_artifact_id": artifact.get("raw_artifact_id"),
                "media_type": artifact.get("media_type"),
                "byte_size": artifact.get("byte_size", artifact.get("size_bytes")),
                "sha256": artifact.get("sha256"),
                "package_path": artifact.get("package_path", artifact.get("path")),
                "source_id": artifact.get("source_id"),
                "snapshot_id": artifact.get("snapshot_id"),
                "normalization_run_id": artifact.get("normalization_run_id"),
            }
        )
    return rows


def _binding_rows(manifest: Mapping[str, Any]) -> list[dict[str, object]]:
    raw = manifest.get("raw_grounding")
    if not isinstance(raw, Mapping):
        return []
    rows: list[dict[str, object]] = []
    for binding in raw.get("evidence_bindings", ()) or ():
        if isinstance(binding, Mapping):
            rows.append(dict(binding))
    return rows


def _grounding_rows(review: Mapping[str, Any]) -> list[dict[str, object]]:
    diff = review.get("diff")
    if not isinstance(diff, Mapping):
        return []
    changes = diff.get("changes")
    if not isinstance(changes, Mapping):
        return []
    grounding = changes.get("grounding")
    if not isinstance(grounding, list):
        return []
    rows: list[dict[str, object]] = []
    for item in grounding:
        if not isinstance(item, Mapping):
            continue
        before = item.get("before") if isinstance(item.get("before"), Mapping) else {}
        after = item.get("after") if isinstance(item.get("after"), Mapping) else {}
        rows.append(
            {
                "target": item.get("key"),
                "before_kind": before.get("kind") if isinstance(before, Mapping) else None,
                "before_refs": before.get("refs") if isinstance(before, Mapping) else None,
                "after_kind": after.get("kind") if isinstance(after, Mapping) else None,
                "after_refs": after.get("refs") if isinstance(after, Mapping) else None,
            }
        )
    return rows


class PackagePage(OperationPage):
    """Build, inspect, stage, preflight, and export Object Packages."""

    def __init__(self, backend: BackendCoordinator, parent=None) -> None:
        super().__init__(backend, parent)
        self._built_path: str | None = None
        self._staged_path: str | None = None
        self._manifest: dict[str, Any] = {}
        self._preflight: dict[str, Any] = {}
        self.raw_model = DictTableModel(
            (
                ("raw_artifact_id", "Raw Artifact ID"),
                ("media_type", "Media Type"),
                ("byte_size", "Bytes"),
                ("sha256", "SHA-256"),
                ("package_path", "Package Path"),
            ),
            self,
        )
        self.binding_model = DictTableModel(
            (
                ("evidence_id", "Evidence ID"),
                ("raw_artifact_ids", "Raw Artifact IDs"),
                ("normalization_run_id", "Normalization Run"),
            ),
            self,
        )
        self._build_ui()
        self._update_actions()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        title_row = QHBoxLayout()
        title = QLabel("Packages", self)
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addWidget(QLabel("Object:", self))
        self.object_combo = QComboBox(self)
        self.object_combo.setMinimumWidth(300)
        self.object_combo.currentIndexChanged.connect(self._input_changed)
        title_row.addWidget(self.object_combo, 1)
        reload_objects = QPushButton("Reload Objects", self)
        reload_objects.clicked.connect(self.refresh_objects)
        title_row.addWidget(reload_objects)
        layout.addLayout(title_row)

        contract_row = QHBoxLayout()
        contract_row.addWidget(QLabel("Package contract:", self))
        self.package_version = QComboBox(self)
        self.package_version.addItem("v2 — Raw grounded (Phase P accepted)", "v2")
        self.package_version.addItem("v1 — Evidence grounded (legacy compatibility)", "v1")
        self.package_version.currentIndexChanged.connect(self._input_changed)
        contract_row.addWidget(self.package_version)
        self.contract_note = QLabel(
            "GUI sends an explicit version. The shared CLI/Application no-option default remains v1 "
            "until P-CLOSE-01.",
            self,
        )
        self.contract_note.setWordWrap(True)
        contract_row.addWidget(self.contract_note, 1)
        layout.addLayout(contract_row)

        form_box = QGroupBox("Selection and materialization budgets", self)
        form = QFormLayout(form_box)
        self.include_evidence = QLineEdit(form_box)
        self.include_evidence.setPlaceholderText("comma-separated Evidence IDs")
        self.exclude_evidence = QLineEdit(form_box)
        self.exclude_evidence.setPlaceholderText("comma-separated Evidence IDs")
        self.max_candidates = self._spin(form_box, 1, 10000, 500)
        self.max_items = self._spin(form_box, 1, 10000, 64)
        self.max_tokens = self._spin(form_box, 1, 10_000_000, 12000)
        self.max_bytes = self._spin(form_box, 1, 100_000_000, 65536)
        self.max_raw_artifacts = self._spin(form_box, 1, 10000, 64)
        self.max_total_raw_bytes = self._spin(form_box, 1, 1_000_000_000, 16 * 1024 * 1024)
        self.max_single_raw_bytes = self._spin(form_box, 1, 1_000_000_000, 8 * 1024 * 1024)
        self.knowledge_language = QLineEdit("ja", form_box)
        for widget in (
            self.include_evidence,
            self.exclude_evidence,
            self.max_candidates,
            self.max_items,
            self.max_tokens,
            self.max_bytes,
            self.max_raw_artifacts,
            self.max_total_raw_bytes,
            self.max_single_raw_bytes,
            self.knowledge_language,
        ):
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(self._input_changed)
            elif isinstance(widget, QSpinBox):
                widget.valueChanged.connect(self._input_changed)
        form.addRow("Manual include", self.include_evidence)
        form.addRow("Manual exclude", self.exclude_evidence)
        form.addRow("Max candidates", self.max_candidates)
        form.addRow("Max selected Evidence", self.max_items)
        form.addRow("Max estimated tokens", self.max_tokens)
        form.addRow("Max Evidence bytes", self.max_bytes)
        form.addRow("Max Raw artifacts", self.max_raw_artifacts)
        form.addRow("Max total Raw bytes", self.max_total_raw_bytes)
        form.addRow("Max single Raw bytes", self.max_single_raw_bytes)
        form.addRow("Knowledge language", self.knowledge_language)
        layout.addWidget(form_box)

        action_row = QHBoxLayout()
        self.build_button = QPushButton("1. Build / Resolve Raw", self)
        self.build_button.clicked.connect(self.build_package)
        self.stage_button = QPushButton("2. Stage", self)
        self.stage_button.clicked.connect(self.stage_package)
        self.preflight_button = QPushButton("3. Preflight", self)
        self.preflight_button.clicked.connect(self.preflight_package)
        self.export_button = QPushButton("4. Export", self)
        self.export_button.clicked.connect(self.export_package)
        action_row.addWidget(self.build_button)
        action_row.addWidget(self.stage_button)
        action_row.addWidget(self.preflight_button)
        action_row.addWidget(self.export_button)
        self.flow_state = QLabel("State: not built", self)
        action_row.addWidget(self.flow_state, 1)
        layout.addLayout(action_row)

        destination_row = QHBoxLayout()
        destination_row.addWidget(QLabel("External destination:", self))
        self.destination = QLineEdit(self)
        self.destination.setPlaceholderText("directory outside the local Package workspace")
        self.destination.textChanged.connect(self._destination_changed)
        destination_row.addWidget(self.destination, 1)
        browse_destination = QPushButton("Browse...", self)
        browse_destination.clicked.connect(self._browse_destination)
        destination_row.addWidget(browse_destination)
        layout.addLayout(destination_row)
        self.egress_ack = QCheckBox(
            "I reviewed the Raw inclusion list and the current preflight result for this export.",
            self,
        )
        self.egress_ack.toggled.connect(self._update_actions)
        layout.addWidget(self.egress_ack)

        splitter = QSplitter(self)
        left_tabs = QTabWidget(splitter)
        self.raw_table = QTableView(left_tabs)
        self.raw_table.setModel(self.raw_model)
        self.raw_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.raw_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.raw_table.horizontalHeader().setStretchLastSection(True)
        left_tabs.addTab(self.raw_table, "Raw Artifact Inclusion")
        self.binding_table = QTableView(left_tabs)
        self.binding_table.setModel(self.binding_model)
        self.binding_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.binding_table.horizontalHeader().setStretchLastSection(True)
        left_tabs.addTab(self.binding_table, "Evidence → Raw Bindings")
        splitter.addWidget(left_tabs)

        right_tabs = QTabWidget(splitter)
        self.summary_text = QTextEdit(right_tabs)
        self.summary_text.setReadOnly(True)
        self.summary_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.preflight_text = QTextEdit(right_tabs)
        self.preflight_text.setReadOnly(True)
        self.preflight_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        right_tabs.addTab(self.summary_text, "Package / Budget / Integrity")
        right_tabs.addTab(self.preflight_text, "Preflight")
        splitter.addWidget(right_tabs)
        splitter.setSizes([760, 520])
        layout.addWidget(splitter, 1)
        layout.addWidget(self.operation_status)

    @staticmethod
    def _spin(parent: QWidget, minimum: int, maximum: int, value: int) -> QSpinBox:
        widget = QSpinBox(parent)
        widget.setRange(minimum, maximum)
        widget.setValue(value)
        return widget

    def workspace_changed(self) -> None:
        self._reset_flow()
        self.refresh_objects()

    def refresh_objects(self) -> str | None:
        return self.submit(
            "object.list",
            callback=self._apply_objects,
            summary="Loading Objects for Package operations...",
        )

    def _apply_objects(self, outcome: OperationOutcome) -> None:
        current_id = self.object_combo.currentData()
        self.object_combo.blockSignals(True)
        self.object_combo.clear()
        target_index = -1
        rows = outcome.data if isinstance(outcome.data, list) else []
        for row in rows:
            if not isinstance(row, dict):
                continue
            object_id = row.get("object_id")
            if not isinstance(object_id, str):
                continue
            self.object_combo.addItem(f"{row.get('name')} [{object_id}]", object_id)
            if object_id == current_id:
                target_index = self.object_combo.count() - 1
        if target_index >= 0:
            self.object_combo.setCurrentIndex(target_index)
        elif self.object_combo.count():
            self.object_combo.setCurrentIndex(0)
        self.object_combo.blockSignals(False)
        self._update_actions()

    @Slot()
    def _input_changed(self, *_args) -> None:
        if self._built_path is not None:
            self._mark_stale("Package build inputs changed; rebuild before staging/export.")
        self._update_actions()

    def _destination_changed(self, _text: str) -> None:
        if self._preflight:
            self._preflight = {}
            self.preflight_text.setPlainText(
                "Destination changed. Run preflight again before export."
            )
            self.flow_state.setText("State: staged / preflight stale")
        self.egress_ack.setChecked(False)
        self._update_actions()

    def _selected_object_id(self) -> str | None:
        value = self.object_combo.currentData()
        if isinstance(value, str):
            return value
        self.operation_status.setText("Select an Object first.")
        return None

    def build_package(self) -> str | None:
        object_id = self._selected_object_id()
        if not object_id:
            return None
        arguments: dict[str, object] = {
            "object": object_id,
            "package_version": self.package_version.currentData(),
            "include_evidence": _csv_ids(self.include_evidence.text()),
            "exclude_evidence": _csv_ids(self.exclude_evidence.text()),
            "max_candidates": self.max_candidates.value(),
            "max_items": self.max_items.value(),
            "max_estimated_tokens": self.max_tokens.value(),
            "max_bytes": self.max_bytes.value(),
            "knowledge_language": self.knowledge_language.text().strip() or "ja",
            "max_raw_artifacts": self.max_raw_artifacts.value(),
            "max_total_raw_bytes": self.max_total_raw_bytes.value(),
            "max_single_raw_bytes": self.max_single_raw_bytes.value(),
        }
        self._reset_flow(keep_objects=True)
        return self.submit(
            "package.build",
            arguments,
            callback=self._apply_build,
            summary="Building Package and resolving selected Evidence to Raw provenance...",
        )

    def _apply_build(self, outcome: OperationOutcome) -> None:
        data = _mapping(outcome.data)
        path = data.get("path")
        if not isinstance(path, str):
            self.operation_status.setText("package.build returned no Package path")
            return
        try:
            manifest = _load_manifest(path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            self.operation_status.setText(f"Built Package manifest could not be inspected: {error}")
            return
        self._built_path = path
        self._manifest = manifest
        self.raw_model.set_rows(_raw_rows(manifest))
        self.binding_model.set_rows(_binding_rows(manifest))
        raw = manifest.get("raw_grounding") if isinstance(manifest.get("raw_grounding"), Mapping) else {}
        summary = {
            "build": data,
            "schema_version": manifest.get("schema_version"),
            "target": manifest.get("target"),
            "binding": manifest.get("binding"),
            "selection": manifest.get("selection"),
            "materialization": manifest.get("materialization"),
            "included_evidence_ids": (manifest.get("evidence") or {}).get(
                "included_evidence_ids", []
            )
            if isinstance(manifest.get("evidence"), Mapping)
            else [],
            "included_raw_artifact_ids": raw.get("included_raw_artifact_ids", [])
            if isinstance(raw, Mapping)
            else [],
            "grounding_set_sha256": (raw.get("integrity") or {}).get("grounding_set_sha256")
            if isinstance(raw, Mapping) and isinstance(raw.get("integrity"), Mapping)
            else None,
            "manifest_sha256": (manifest.get("integrity") or {}).get("manifest_sha256")
            if isinstance(manifest.get("integrity"), Mapping)
            else None,
        }
        self.summary_text.setPlainText(_json_text(summary))
        if str(manifest.get("schema_version", "")).endswith("/2.0"):
            self.flow_state.setText(
                f"State: built / Raw resolved ({self.raw_model.rowCount()} artifacts)"
            )
        else:
            self.flow_state.setText("State: built / legacy Evidence-grounded v1")
        self._update_actions()

    def stage_package(self) -> str | None:
        if self._built_path is None:
            self.operation_status.setText("Build a current Package before staging.")
            return None
        return self.submit(
            "package.stage",
            {"source": self._built_path},
            callback=self._apply_stage,
            summary="Staging Package with integrity verification...",
        )

    def _apply_stage(self, outcome: OperationOutcome) -> None:
        data = _mapping(outcome.data)
        path = data.get("path")
        if isinstance(path, str):
            self._staged_path = path
        self._preflight = {}
        self.preflight_text.setPlainText(_json_text(data))
        self.flow_state.setText("State: staged / preflight required")
        self.egress_ack.setChecked(False)
        self._update_actions()

    def preflight_package(self) -> str | None:
        package_path = self._staged_path or self._built_path
        if package_path is None:
            self.operation_status.setText("Build or stage a Package before preflight.")
            return None
        destination = self.destination.text().strip()
        if not destination:
            self.operation_status.setText("Choose an external destination before preflight.")
            return None
        return self.submit(
            "package.preflight",
            {"package": package_path, "destination": destination},
            callback=self._apply_preflight,
            summary="Running Package integrity / security / egress preflight...",
        )

    def _apply_preflight(self, outcome: OperationOutcome) -> None:
        data = _mapping(outcome.data)
        self._preflight = data
        self.preflight_text.setPlainText(_json_text(data))
        disposition = str(data.get("disposition", outcome.state))
        if disposition == "blocked" or outcome.state == "blocked":
            self.flow_state.setText("State: preflight BLOCKED")
        elif disposition == "review_required":
            self.flow_state.setText("State: preflight REVIEW REQUIRED")
        else:
            self.flow_state.setText("State: preflight allow / ready for egress acknowledgement")
        self.egress_ack.setChecked(False)
        self._update_actions()

    def export_package(self) -> str | None:
        package_path = self._staged_path
        destination = self.destination.text().strip()
        disposition = str(self._preflight.get("disposition", ""))
        if package_path is None:
            self.operation_status.setText("Stage the Package before export.")
            return None
        if disposition not in {"allow", "review_required"}:
            self.operation_status.setText("A non-blocked current preflight is required before export.")
            return None
        if not self.egress_ack.isChecked():
            self.operation_status.setText("Review and acknowledge Raw inclusion/preflight before export.")
            return None
        return self.submit(
            "package.export",
            {
                "package": package_path,
                "destination": destination,
                "acknowledge_review": True,
            },
            callback=self._apply_export,
            summary="Exporting reviewed Package across the external egress boundary...",
        )

    def _apply_export(self, outcome: OperationOutcome) -> None:
        data = _mapping(outcome.data)
        self.preflight_text.setPlainText(_json_text({"preflight": self._preflight, "export": data}))
        self.flow_state.setText("State: exported / awaiting external Result")
        self.egress_ack.setChecked(False)
        self._update_actions()

    def _browse_destination(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Select Package export destination")
        if selected:
            self.destination.setText(selected)

    def _mark_stale(self, message: str) -> None:
        self._built_path = None
        self._staged_path = None
        self._manifest = {}
        self._preflight = {}
        self.raw_model.set_rows([])
        self.binding_model.set_rows([])
        self.summary_text.setPlainText(message)
        self.preflight_text.clear()
        self.flow_state.setText("State: stale / rebuild required")
        self.egress_ack.setChecked(False)

    def _reset_flow(self, *, keep_objects: bool = False) -> None:
        self._built_path = None
        self._staged_path = None
        self._manifest = {}
        self._preflight = {}
        self.raw_model.set_rows([])
        self.binding_model.set_rows([])
        self.summary_text.clear()
        self.preflight_text.clear()
        self.flow_state.setText("State: not built")
        self.egress_ack.setChecked(False)
        if not keep_objects:
            self.object_combo.clear()
        self._update_actions()

    def _update_actions(self) -> None:
        has_object = isinstance(self.object_combo.currentData(), str)
        self.build_button.setEnabled(self.workspace.is_open and has_object)
        self.stage_button.setEnabled(self._built_path is not None)
        self.preflight_button.setEnabled(
            (self._staged_path is not None or self._built_path is not None)
            and bool(self.destination.text().strip())
        )
        disposition = str(self._preflight.get("disposition", ""))
        self.export_button.setEnabled(
            self._staged_path is not None
            and disposition in {"allow", "review_required"}
            and self.egress_ack.isChecked()
        )


class ResultPage(OperationPage):
    """Detect, receive, validate, review, and import external Object Results."""

    def __init__(self, backend: BackendCoordinator, parent=None) -> None:
        super().__init__(backend, parent)
        self.receipt_model = DictTableModel(
            (
                ("id", "Receipt ID"),
                ("package_id", "Package ID"),
                ("parsed_schema_version", "Result Schema"),
                ("parsed_result_status", "Result Status"),
                ("intake_state", "Intake"),
                ("validation_state", "Validation"),
                ("received_at", "Received At"),
            ),
            self,
        )
        self.detect_model = DictTableModel(
            (("path", "Detected Result"), ("name", "Name"), ("size", "Bytes")), self
        )
        self.grounding_model = DictTableModel(
            (
                ("target", "Knowledge Target"),
                ("before_kind", "Before"),
                ("before_refs", "Before refs"),
                ("after_kind", "After"),
                ("after_refs", "After refs"),
            ),
            self,
        )
        self._review: dict[str, Any] = {}
        self._build_ui()
        self._update_actions()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        title_row = QHBoxLayout()
        title = QLabel("Results", self)
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addWidget(QLabel("Incoming root:", self))
        self.incoming_root = QLineEdit("exchange/incoming", self)
        title_row.addWidget(self.incoming_root, 1)
        browse_root = QPushButton("Browse...", self)
        browse_root.clicked.connect(self._browse_incoming)
        title_row.addWidget(browse_root)
        self.detect_button = QPushButton("Detect", self)
        self.detect_button.clicked.connect(self.detect_results)
        title_row.addWidget(self.detect_button)
        layout.addLayout(title_row)

        receive_row = QHBoxLayout()
        receive_row.addWidget(QLabel("Result file:", self))
        self.result_path = QLineEdit(self)
        self.result_path.setPlaceholderText("external result.json")
        receive_row.addWidget(self.result_path, 1)
        browse_result = QPushButton("Browse...", self)
        browse_result.clicked.connect(self._browse_result)
        receive_row.addWidget(browse_result)
        receive_row.addWidget(QLabel("Package ID:", self))
        self.package_id = QLineEdit(self)
        self.package_id.setMinimumWidth(220)
        receive_row.addWidget(self.package_id)
        self.receive_button = QPushButton("Receive", self)
        self.receive_button.clicked.connect(self.receive_result)
        receive_row.addWidget(self.receive_button)
        layout.addLayout(receive_row)

        list_row = QHBoxLayout()
        self.list_button = QPushButton("List Receipts", self)
        self.list_button.clicked.connect(self.list_results)
        self.pending_button = QPushButton("Pending Only", self)
        self.pending_button.clicked.connect(self.list_pending)
        list_row.addWidget(self.list_button)
        list_row.addWidget(self.pending_button)
        list_row.addWidget(QLabel("Selected receipt:", self))
        self.receipt_id = QLineEdit(self)
        self.receipt_id.textChanged.connect(self._receipt_changed)
        list_row.addWidget(self.receipt_id, 1)
        self.force_validate = QCheckBox("Force revalidate", self)
        list_row.addWidget(self.force_validate)
        self.validate_button = QPushButton("Validate", self)
        self.validate_button.clicked.connect(self.validate_result)
        self.review_button = QPushButton("Review / Diff", self)
        self.review_button.clicked.connect(self.review_result)
        list_row.addWidget(self.validate_button)
        list_row.addWidget(self.review_button)
        layout.addLayout(list_row)

        import_row = QHBoxLayout()
        self.result_state = QLabel("State: no receipt selected", self)
        import_row.addWidget(self.result_state, 1)
        self.review_ack = QCheckBox(
            "Acknowledge review-required changes for import", self
        )
        self.review_ack.toggled.connect(self._update_actions)
        import_row.addWidget(self.review_ack)
        self.import_button = QPushButton("Import accepted Knowledge Version", self)
        self.import_button.clicked.connect(self.import_result)
        import_row.addWidget(self.import_button)
        layout.addLayout(import_row)

        splitter = QSplitter(self)
        left_tabs = QTabWidget(splitter)
        self.receipt_table = QTableView(left_tabs)
        self.receipt_table.setModel(self.receipt_model)
        self.receipt_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.receipt_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.receipt_table.horizontalHeader().setStretchLastSection(True)
        self.receipt_table.selectionModel().currentRowChanged.connect(self._receipt_row_changed)
        left_tabs.addTab(self.receipt_table, "Receipts / Pending")
        self.detect_table = QTableView(left_tabs)
        self.detect_table.setModel(self.detect_model)
        self.detect_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.detect_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.detect_table.horizontalHeader().setStretchLastSection(True)
        self.detect_table.selectionModel().currentRowChanged.connect(self._detect_row_changed)
        left_tabs.addTab(self.detect_table, "Detected Files")
        splitter.addWidget(left_tabs)

        right_tabs = QTabWidget(splitter)
        self.review_text = QTextEdit(right_tabs)
        self.review_text.setReadOnly(True)
        self.review_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.grounding_table = QTableView(right_tabs)
        self.grounding_table.setModel(self.grounding_model)
        self.grounding_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.grounding_table.horizontalHeader().setStretchLastSection(True)
        right_tabs.addTab(self.review_text, "Validation / Current Knowledge Diff")
        right_tabs.addTab(self.grounding_table, "Grounding Reference Diff")
        splitter.addWidget(right_tabs)
        splitter.setSizes([700, 580])
        layout.addWidget(splitter, 1)
        layout.addWidget(self.operation_status)

    def workspace_changed(self) -> None:
        self._review = {}
        self.receipt_model.set_rows([])
        self.detect_model.set_rows([])
        self.grounding_model.set_rows([])
        self.review_text.clear()
        self.receipt_id.clear()
        self.review_ack.setChecked(False)
        self.list_results()

    def detect_results(self) -> str | None:
        return self.submit(
            "result.detect",
            {"incoming_root": self.incoming_root.text().strip() or "exchange/incoming"},
            callback=self._apply_detected,
            summary="Detecting external Result files...",
        )

    def _apply_detected(self, outcome: OperationOutcome) -> None:
        rows: list[dict[str, object]] = []
        for item in outcome.data if isinstance(outcome.data, list) else []:
            if isinstance(item, str):
                path = Path(item)
                rows.append({"path": item, "name": path.name, "size": None})
            elif isinstance(item, Mapping):
                rows.append(dict(item))
        self.detect_model.set_rows(rows)
        if rows:
            self.detect_table.selectRow(0)
        self.result_state.setText(f"State: detected {len(rows)} candidate Result file(s)")

    def receive_result(self) -> str | None:
        path = self.result_path.text().strip()
        package_id = self.package_id.text().strip()
        if not path or not package_id:
            self.operation_status.setText("Result file and Package ID are required for receipt.")
            return None
        return self.submit(
            "result.receive",
            {
                "result": path,
                "package_id": package_id,
                "incoming_root": self.incoming_root.text().strip() or "exchange/incoming",
            },
            callback=self._apply_received,
            summary="Receiving immutable external Result artifact...",
        )

    def _apply_received(self, outcome: OperationOutcome) -> None:
        data = _mapping(outcome.data)
        receipt_id = data.get("receipt_id", data.get("id"))
        if isinstance(receipt_id, str):
            self.receipt_id.setText(receipt_id)
        self.review_text.setPlainText(_json_text(data))
        self.result_state.setText(
            f"State: received / intake {data.get('intake_state', 'recorded')} / validation pending"
        )
        self._review = {}
        self.review_ack.setChecked(False)
        self.list_results()

    def list_results(self) -> str | None:
        arguments: dict[str, object] = {}
        package_id = self.package_id.text().strip()
        if package_id:
            arguments["package_id"] = package_id
        return self.submit(
            "result.list",
            arguments,
            callback=self._apply_receipts,
            summary="Loading Result receipts...",
        )

    def list_pending(self) -> str | None:
        return self.submit(
            "result.pending",
            callback=self._apply_receipts,
            summary="Loading pending Result receipts...",
        )

    def _apply_receipts(self, outcome: OperationOutcome) -> None:
        rows = [dict(item) for item in outcome.data if isinstance(item, Mapping)] \
            if isinstance(outcome.data, list) else []
        selected = self.receipt_id.text().strip()
        self.receipt_model.set_rows(rows)
        for index, row in enumerate(rows):
            if row.get("id") == selected:
                self.receipt_table.selectRow(index)
                break

    def validate_result(self) -> str | None:
        receipt_id = self._selected_receipt_id()
        if not receipt_id:
            return None
        return self.submit(
            "result.validate",
            {
                "receipt_id": receipt_id,
                "incoming_root": self.incoming_root.text().strip() or "exchange/incoming",
                "force": self.force_validate.isChecked(),
            },
            callback=self._apply_validation,
            summary="Validating Result contract, binding, membership, and grounding...",
        )

    def _apply_validation(self, outcome: OperationOutcome) -> None:
        data = _mapping(outcome.data)
        self.review_text.setPlainText(_json_text(data))
        state = str(data.get("validation_state", outcome.state))
        if state == "valid" and outcome.state != "blocked":
            self.result_state.setText("State: validation valid / review required before import")
        else:
            self.result_state.setText(f"State: validation {state} / BLOCKED")
        self._review = {}
        self.grounding_model.set_rows([])
        self.review_ack.setChecked(False)
        self._update_actions()

    def review_result(self) -> str | None:
        receipt_id = self._selected_receipt_id()
        if not receipt_id:
            return None
        return self.submit(
            "result.review",
            {
                "receipt_id": receipt_id,
                "incoming_root": self.incoming_root.text().strip() or "exchange/incoming",
            },
            callback=self._apply_review,
            summary="Reviewing Result against current Knowledge and grounding...",
        )

    def _apply_review(self, outcome: OperationOutcome) -> None:
        data = _mapping(outcome.data)
        self._review = data
        self.review_text.setPlainText(_json_text(data))
        self.grounding_model.set_rows(_grounding_rows(data))
        review_state = str(data.get("review_state", "unknown"))
        validation_state = str(data.get("validation_state", "unknown"))
        if review_state == "review_required":
            self.result_state.setText(
                "State: REVIEW REQUIRED / inspect current Knowledge and grounding diff"
            )
        elif review_state == "blocked" or validation_state in {"invalid", "error"}:
            self.result_state.setText("State: BLOCKED / Result cannot be imported")
        elif review_state == "imported":
            self.result_state.setText("State: imported")
        else:
            self.result_state.setText(f"State: {review_state} / ready for import")
        self.review_ack.setChecked(False)
        self._update_actions()

    def import_result(self) -> str | None:
        receipt_id = self._selected_receipt_id()
        if not receipt_id:
            return None
        review_state = str(self._review.get("review_state", ""))
        if review_state not in {"ready_to_import", "review_required"}:
            self.operation_status.setText("Complete a non-blocked Result review before import.")
            return None
        if review_state == "review_required" and not self.review_ack.isChecked():
            self.operation_status.setText("Review-required changes must be explicitly acknowledged.")
            return None
        return self.submit(
            "result.import",
            {
                "receipt_id": receipt_id,
                "incoming_root": self.incoming_root.text().strip() or "exchange/incoming",
                "acknowledge_review": self.review_ack.isChecked(),
            },
            callback=self._apply_import,
            summary="Importing reviewed Result as an accepted Knowledge Version...",
        )

    def _apply_import(self, outcome: OperationOutcome) -> None:
        data = _mapping(outcome.data)
        self.review_text.setPlainText(_json_text({"review": self._review, "import": data}))
        version_id = data.get("version_id")
        self.result_state.setText(f"State: imported / accepted Version {version_id}")
        self._review["review_state"] = "imported"
        self.review_ack.setChecked(False)
        self._update_actions()
        self.list_results()

    def _selected_receipt_id(self) -> str | None:
        value = self.receipt_id.text().strip()
        if value:
            return value
        self.operation_status.setText("Select or enter a Result receipt ID first.")
        return None

    def _receipt_changed(self, _text: str) -> None:
        self._review = {}
        self.grounding_model.set_rows([])
        self.review_ack.setChecked(False)
        self.result_state.setText("State: receipt selected / validation-review state not loaded")
        self._update_actions()

    @Slot(QModelIndex, QModelIndex)
    def _receipt_row_changed(self, current: QModelIndex, _previous: QModelIndex) -> None:
        if not current.isValid():
            return
        row = self.receipt_model.row_data(current.row())
        if not row:
            return
        receipt_id = row.get("id")
        if isinstance(receipt_id, str):
            self.receipt_id.setText(receipt_id)
        package_id = row.get("package_id")
        if isinstance(package_id, str):
            self.package_id.setText(package_id)
        validation = row.get("validation_state")
        intake = row.get("intake_state")
        self.result_state.setText(f"State: intake {intake} / validation {validation}")
        self.review_text.setPlainText(_json_text(row))

    @Slot(QModelIndex, QModelIndex)
    def _detect_row_changed(self, current: QModelIndex, _previous: QModelIndex) -> None:
        if not current.isValid():
            return
        row = self.detect_model.row_data(current.row())
        path = row.get("path") if row else None
        if isinstance(path, str):
            self.result_path.setText(path)

    def _browse_incoming(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Select Result incoming directory")
        if selected:
            self.incoming_root.setText(selected)

    def _browse_result(self) -> None:
        selected, _filter = QFileDialog.getOpenFileName(
            self, "Select Object Result", "", "JSON files (*.json);;All files (*)"
        )
        if selected:
            self.result_path.setText(selected)

    def _update_actions(self) -> None:
        has_receipt = bool(self.receipt_id.text().strip())
        self.validate_button.setEnabled(has_receipt)
        self.review_button.setEnabled(has_receipt)
        review_state = str(self._review.get("review_state", ""))
        can_import = review_state == "ready_to_import" or (
            review_state == "review_required" and self.review_ack.isChecked()
        )
        self.import_button.setEnabled(has_receipt and can_import)
