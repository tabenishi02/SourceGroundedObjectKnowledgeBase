"""P-RUNTIME-05 semantic Runtime Dashboard for the System overview."""

from __future__ import annotations

from typing import Mapping

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from sgokb.gui.runtime_dashboard import build_runtime_dashboard

from .system_page import SystemPage


class RuntimeDashboardSystemPage(SystemPage):
    """SystemPage with a semantic-runtime readiness dashboard on Overview."""

    def _build_overview_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)

        self.runtime_summary = QLabel(
            "Runtime health is available after opening a Workspace.",
            page,
        )
        self.runtime_summary.setWordWrap(True)
        self.runtime_summary.setStyleSheet("font-weight: 600;")
        layout.addWidget(self.runtime_summary)

        readiness_group = QGroupBox("Semantic Search readiness", page)
        readiness_layout = QVBoxLayout(readiness_group)
        self.semantic_readiness = QLabel("UNKNOWN — open a Workspace to inspect runtime health.")
        self.semantic_readiness.setWordWrap(True)
        readiness_layout.addWidget(self.semantic_readiness)
        layout.addWidget(readiness_group)

        components_group = QGroupBox("Runtime components", page)
        components_form = QFormLayout(components_group)
        self.runtime_component_labels: dict[str, QLabel] = {}
        for key, label in (
            ("sqlite", "SQLite"),
            ("embedding", "Embedding"),
            ("qdrant", "Qdrant"),
            ("generation", "Search generation"),
            ("derived", "Derived state"),
        ):
            value = QLabel("unknown", components_group)
            value.setWordWrap(True)
            components_form.addRow(label, value)
            self.runtime_component_labels[key] = value
        layout.addWidget(components_group)

        self.runtime_lifecycle_note = QLabel(
            "Qdrant lifecycle ownership is external to SGOKB.", page
        )
        self.runtime_lifecycle_note.setWordWrap(True)
        layout.addWidget(self.runtime_lifecycle_note)

        self.runtime_mcp_note = QLabel(
            "MCP launch/configuration is shown on the MCP tab.", page
        )
        self.runtime_mcp_note.setWordWrap(True)
        layout.addWidget(self.runtime_mcp_note)

        troubleshooting_group = QGroupBox("Runtime issues / troubleshooting", page)
        troubleshooting_layout = QVBoxLayout(troubleshooting_group)
        self.runtime_troubleshooting = QPlainTextEdit(troubleshooting_group)
        self.runtime_troubleshooting.setReadOnly(True)
        self.runtime_troubleshooting.setMaximumHeight(150)
        troubleshooting_layout.addWidget(self.runtime_troubleshooting)
        layout.addWidget(troubleshooting_group)

        self.system_status_button = QPushButton("Refresh system status", page)
        self.integrity_button = QPushButton("Run integrity check", page)
        self.system_status_button.clicked.connect(self._run_system_status)
        self.integrity_button.clicked.connect(self._run_integrity)
        layout.addWidget(self._button_row(self.system_status_button, self.integrity_button))

        self.overview_output = self._readout(page)
        layout.addWidget(self.overview_output, 1)
        return page

    def _update_runtime_summary(self, status: object) -> None:
        runtime = status.get("runtime_health", {}) if isinstance(status, Mapping) else {}
        if not isinstance(runtime, Mapping) or not runtime:
            self.runtime_summary.setText(
                "Runtime health snapshot unavailable in current status data."
            )
            self.semantic_readiness.setText("UNKNOWN — no runtime-health snapshot is available.")
            for label in self.runtime_component_labels.values():
                label.setText("unknown")
            self.runtime_troubleshooting.setPlainText(
                "Refresh system status after opening a Workspace."
            )
            return

        presentation = build_runtime_dashboard(runtime)
        readiness = presentation.readiness
        self.runtime_summary.setText(
            f"Runtime health: overall={presentation.overall_status} | "
            f"Semantic Search={readiness.status}"
        )
        self.semantic_readiness.setText(
            f"{readiness.status.upper()} — {readiness.message}"
        )

        issue_lines: list[str] = []
        if readiness.blockers:
            issue_lines.append("Blockers:")
            issue_lines.extend(f"- {item}" for item in readiness.blockers)
        if readiness.warnings:
            if issue_lines:
                issue_lines.append("")
            issue_lines.append("Warnings:")
            issue_lines.extend(f"- {item}" for item in readiness.warnings)

        for component in presentation.components:
            label = self.runtime_component_labels[component.key]
            text = f"{component.status.upper()} — {component.summary}"
            if component.issue:
                text += f" — {component.issue}"
            label.setText(text)
            if component.troubleshooting and (component.issue or component.status != "healthy"):
                if issue_lines:
                    issue_lines.append("")
                issue_lines.append(f"{component.label}: {component.troubleshooting}")

        self.runtime_lifecycle_note.setText(presentation.lifecycle_note)
        self.runtime_mcp_note.setText(presentation.mcp_note)
        self.runtime_troubleshooting.setPlainText(
            "\n".join(issue_lines) if issue_lines else "No runtime issue requires troubleshooting."
        )
