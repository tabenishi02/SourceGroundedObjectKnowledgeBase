"""P-GUI-09 System / Maintenance / MCP / Advanced GUI acceptance coverage."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _require_qt():
    pytest.importorskip("PySide6", reason="P-GUI-09 tests require the optional gui extra")


@pytest.fixture
def qt_app():
    _require_qt()
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def _wait_idle(qt_app, backend, timeout_ms: int = 15000):
    _require_qt()
    from PySide6.QtCore import QEventLoop, QTimer

    qt_app.processEvents()
    if not backend.is_busy:
        return
    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)

    def changed(busy):
        if not busy:
            loop.quit()

    backend.busy_changed.connect(changed)
    timer.start(timeout_ms)
    loop.exec()
    backend.busy_changed.disconnect(changed)
    assert not backend.is_busy, "Timed out waiting for P-GUI-09 backend operation"


def _settings(path: Path):
    _require_qt()
    from PySide6.QtCore import QSettings

    return QSettings(str(path), QSettings.Format.IniFormat)


def _fresh_db(path: Path) -> None:
    from sgokb.repository import Repository

    repository = Repository(path)
    repository.close()


def test_main_window_replaces_system_placeholder_with_p_gui_09_page(qt_app, tmp_path):
    from sgokb.gui.views import MainWindow, SystemPage
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.gui.workspace import WorkspaceSettings

    backend = BackendCoordinator()
    window = MainWindow(
        backend,
        WorkspaceSettings(_settings(tmp_path / "window.ini")),
        show_error_dialogs=False,
    )
    try:
        assert isinstance(window.domain_pages["system"], SystemPage)
        assert window.domain_pages["system"].tabs.count() == 7
        assert window.domain_pages["system"].tabs.tabText(5) == "MCP"
        assert window.domain_pages["system"].tabs.tabText(6) == "Advanced Generation"
    finally:
        window.close()
        qt_app.processEvents()
        assert backend.shutdown()


def test_system_status_and_integrity_execute_through_shared_backend(qt_app, tmp_path):
    from sgokb.gui.views import SystemPage
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.gui.workspace import WorkspaceState

    db = tmp_path / "system.sqlite"
    _fresh_db(db)
    backend = BackendCoordinator()
    page = SystemPage(backend)
    page.set_workspace(WorkspaceState.opened(db, {}))
    try:
        page._run_system_status()
        _wait_idle(qt_app, backend)
        status_text = page.overview_output.toPlainText()
        assert '"runtime_health"' in status_text
        assert '"sqlite"' in status_text
        assert "Runtime health:" in page.runtime_summary.text()

        page._run_integrity()
        _wait_idle(qt_app, backend)
        assert '"ok": true' in page.overview_output.toPlainText().lower()
    finally:
        page.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()


def test_restore_apply_requires_current_plan_and_overwrite_ack(qt_app, tmp_path):
    from sgokb.application_operator import OperatorSession
    from sgokb.gui.views import SystemPage
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.gui.workspace import WorkspaceState
    from sgokb.operation_contracts import OperationRequest

    db = tmp_path / "restore.sqlite"
    backup = tmp_path / "backup.sqlite"
    _fresh_db(db)
    OperatorSession(db).execute(
        OperationRequest(
            "system.backup.create",
            {"output": str(backup), "root": str(tmp_path / "backups")},
        )
    )

    backend = BackendCoordinator()
    page = SystemPage(backend)
    page.set_workspace(WorkspaceState.opened(db, {}))
    try:
        page.restore_backup.setText(str(backup))
        page._run_restore_apply()
        assert "Run Restore Plan" in page.operation_status.text()
        assert not page.restore_apply_button.isEnabled()

        page._run_restore_plan()
        _wait_idle(qt_app, backend)
        assert page.restore_apply_button.isEnabled()
        assert page._restore_requires_ack is True
        assert "acknowledgement" in page.operation_status.text().lower()

        page.restore_backup.setText(str(tmp_path / "different.sqlite"))
        assert not page.restore_apply_button.isEnabled()
        assert page._restore_plan_key is None
    finally:
        page.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()


def test_mcp_surface_reports_external_stdio_lifecycle_and_exact_command(qt_app, tmp_path):
    from sgokb.gui.views import SystemPage
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.gui.workspace import WorkspaceState

    db = tmp_path / "mcp.sqlite"
    _fresh_db(db)
    backend = BackendCoordinator()
    page = SystemPage(backend)
    page.set_workspace(WorkspaceState.opened(db, {}))
    try:
        command = page.mcp_command.text()
        assert command.startswith("sgokb --db ")
        assert command.endswith("mcp serve")
        assert "external client-managed stdio" in page.mcp_state.text()
        assert "detached MCP daemon" in page.mcp_state.text()

        page.mcp_semantic.setChecked(True)
        qt_app.processEvents()
        assert page.mcp_command.text().endswith("mcp serve --semantic-runtime")
    finally:
        page.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()


def test_generation_cli_and_gui_share_transport_neutral_session(tmp_path):
    from sgokb.application_generation_operator import (
        GENERATION_OPERATION_IDS,
        GenerationOperatorSession,
    )
    from sgokb.cli.generation import run as generation_cli_run
    from sgokb.gui.operation_ux import equivalent_cli_command, operation_policy
    from sgokb.operation_contracts import OperationRequest

    db = tmp_path / "generation.sqlite"
    _fresh_db(db)
    direct = GenerationOperatorSession(db).execute(OperationRequest("generation.status", {})).data
    via_cli = generation_cli_run(["--db", str(db), "status"])
    assert direct == via_cli
    assert len(GENERATION_OPERATION_IDS) == 6
    assert operation_policy("generation.status").effect == "READ"
    assert operation_policy("generation.cutover").effect == "MAINTENANCE"
    assert operation_policy("generation.cutover").confirmation_required is True

    command = equivalent_cli_command(
        db,
        "generation.cutover",
        {"generation_id": "search-generation:test", "reason": "test", "smoke": False},
    )
    assert command.startswith("python -m sgokb.cli.generation --db ")
    assert " cutover search-generation:test " in f" {command} "
    assert "--reason test" in command
    assert "--no-smoke" in command


def test_system_page_reaches_all_system_and_advanced_generation_actions(
    qt_app,
    tmp_path,
    monkeypatch,
):
    from sgokb.gui.views import SystemPage
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.gui.workspace import WorkspaceState

    expected_system = {
        "system.status",
        "system.integrity",
        "system.derived.status",
        "system.derived.sync",
        "system.index.status",
        "system.index.rebuild",
        "system.backup.status",
        "system.backup.create",
        "system.backup.composite.create",
        "system.backup.composite.verify",
        "system.restore.plan",
        "system.restore.apply",
        "system.restore.composite.plan",
        "system.restore.composite.apply",
    }
    expected_generation = {
        "generation.status",
        "generation.bootstrap",
        "generation.build",
        "generation.cutover",
        "generation.rollback",
        "generation.recover",
    }

    db = tmp_path / "inventory.sqlite"
    _fresh_db(db)
    backend = BackendCoordinator()
    page = SystemPage(backend)
    page.set_workspace(WorkspaceState.opened(db, {}))
    submitted: list[tuple[str, dict[str, object]]] = []

    def capture(operation_id, arguments=None, **_kwargs):
        submitted.append((operation_id, dict(arguments or {})))
        return "captured"

    monkeypatch.setattr(page, "submit", capture)
    try:
        page.composite_incoming_root.setText(str(tmp_path / "incoming"))
        page.composite_verify_path.setText(str(tmp_path / "composite"))
        page.restore_backup.setText(str(tmp_path / "backup.sqlite"))
        page.composite_restore_backup.setText(str(tmp_path / "composite"))
        page.composite_restore_db.setText(str(tmp_path / "restored.sqlite"))
        page.composite_restore_raw.setText(str(tmp_path / "raw"))
        page.composite_restore_incoming.setText(str(tmp_path / "incoming-restored"))
        page.generation_id.setText("search-generation:test")

        page._run_system_status()
        page._run_integrity()
        page._run_derived_status()
        page._run_derived_sync()
        page._run_index_status()
        page._run_index_rebuild()
        page._run_backup_status()
        page._run_backup_create()
        page._run_composite_backup_create()
        page._run_composite_backup_verify()
        page._run_restore_plan()
        page._restore_plan_key = page._restore_key()
        page._restore_requires_ack = False
        page._run_restore_apply()
        page._run_composite_restore_plan()
        page._composite_plan_key = page._composite_key()
        page._composite_requires_ack = False
        page._run_composite_restore_apply()

        page._run_generation("generation.status", {})
        page._run_generation_bootstrap()
        page._run_generation("generation.build", {})
        page._run_generation_cutover()
        page._run_generation_rollback()
        page._run_generation_recover()

        seen = {operation_id for operation_id, _arguments in submitted}
        assert expected_system <= seen
        assert expected_generation <= seen
        assert len(expected_system) == 14
        assert len(expected_generation) == 6
    finally:
        page.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()
