"""P-GUI-07 progress / error / safety / audit UX coverage."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _require_qt():
    pytest.importorskip("PySide6", reason="P-GUI-07 tests require the optional gui extra")


@pytest.fixture
def qt_app():
    _require_qt()
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def _wait_idle(qt_app, backend, timeout_ms: int = 10000):
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
    assert not backend.is_busy, "Timed out waiting for P-GUI-07 backend operation"


def _settings(path: Path):
    _require_qt()
    from PySide6.QtCore import QSettings

    return QSettings(str(path), QSettings.Format.IniFormat)


def test_operation_policy_and_equivalent_cli_preserve_safety_boundaries(tmp_path):
    from sgokb.gui.operation_ux import (
        EFFECT_EXTERNAL,
        EFFECT_MAINTENANCE,
        EFFECT_READ,
        EFFECT_WRITE,
        equivalent_cli_command,
        operation_policy,
    )

    assert operation_policy("search").effect == EFFECT_READ
    assert operation_policy("object.rename").effect == EFFECT_WRITE
    assert operation_policy("object.rename").confirmation_required is False
    assert operation_policy("object.status").confirmation_required is True
    assert operation_policy("package.export").effect == EFFECT_EXTERNAL
    assert operation_policy("package.export").confirmation_required is True
    restore = operation_policy("system.restore.apply")
    assert restore.effect == EFFECT_MAINTENANCE
    assert restore.confirmation_required is True
    assert restore.cancellable is False

    database = tmp_path / "workspace.sqlite"
    command = equivalent_cli_command(
        database,
        "object.rename",
        {"object_id": "object-1", "to": "Renamed Object"},
    )
    assert command.startswith("sgokb --db ")
    assert " object rename " in f" {command} "
    assert "--object object-1" in command
    assert "--to 'Renamed Object'" in command


def test_operation_page_confirms_high_impact_write_before_submission(
    qt_app,
    tmp_path,
    monkeypatch,
):
    from PySide6.QtWidgets import QMessageBox

    from sgokb.gui.views.operation_page import OperationPage
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.gui.workspace import WorkspaceState

    backend = BackendCoordinator()
    page = OperationPage(backend)
    page.set_workspace(WorkspaceState.opened(tmp_path / "confirm.sqlite", {}))
    page.set_confirmation_enabled(True)
    seen: list[str] = []

    def cancel(_parent, _title, message, *_args, **_kwargs):
        seen.append(message)
        return QMessageBox.StandardButton.Cancel

    monkeypatch.setattr(QMessageBox, "warning", cancel)
    try:
        request_id = page.submit(
            "object.status",
            {"object_id": "object-1", "set": "archived"},
        )
        assert request_id is None
        assert not backend.is_busy
        assert seen and "Safety class: WRITE" in seen[0]
        assert "Equivalent CLI command:" in seen[0]
        assert "never reverses a submitted canonical operation" in seen[0]
    finally:
        page.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()


def test_operation_center_records_lifecycle_cli_and_normalized_events(qt_app, tmp_path):
    from sgokb.gui.views.operation_center import OperationCenter
    from sgokb.gui.worker import BackendCoordinator

    backend = BackendCoordinator()
    center = OperationCenter(backend)
    database = tmp_path / "audit.sqlite"
    try:
        backend.submit(database, "system.status")
        _wait_idle(qt_app, backend)

        assert center.operation_count == 1
        row = center.operations.topLevelItem(0)
        assert row.text(1) == "system.status"
        assert row.text(2) == "READ"
        assert row.text(3) == "success"
        assert row.text(4) == "Unavailable"
        center.operations.setCurrentItem(row)
        qt_app.processEvents()
        detail = center.operation_detail.toPlainText()
        assert "Equivalent CLI command:" in detail
        assert "system status" in detail
        assert "session-local presentation state" in detail
    finally:
        center.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()


def test_operation_center_surfaces_warning_partial_and_error(qt_app, tmp_path):
    from sgokb.gui.operations import GuiOperationRequest
    from sgokb.gui.views.operation_center import OperationCenter
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.operation_contracts import OperationFailure, OperationOutcome

    backend = BackendCoordinator()
    center = OperationCenter(backend)
    request = GuiOperationRequest.create(
        tmp_path / "events.sqlite",
        "source.import",
        {"path": "x"},
    )
    try:
        backend.operation_submitted.emit(request.request_id, request)
        backend.operation_warning.emit(request.request_id, "one item failed")
        backend.operation_finished.emit(
            request.request_id,
            OperationOutcome("source.import", [], state="partial"),
        )
        backend.operation_failed.emit(
            request.request_id,
            OperationFailure("source.import", "io", "file_not_found", "missing input"),
        )
        qt_app.processEvents()

        assert center.event_count == 3
        kinds = {
            center.events.topLevelItem(index).text(2)
            for index in range(center.events.topLevelItemCount())
        }
        assert {"warning/degradation", "partial", "error"} <= kinds
        assert center.operations.topLevelItem(0).text(3) == "failed:io/file_not_found"
    finally:
        center.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()


def test_main_window_exposes_progress_operation_center_and_form_only_undo(
    qt_app,
    tmp_path,
    monkeypatch,
):
    import sgokb.gui.views.main_window as main_window_module
    from sgokb.gui.views import MainWindow
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.gui.workspace import WorkspaceSettings

    backend = BackendCoordinator()
    window = MainWindow(
        backend,
        WorkspaceSettings(_settings(tmp_path / "window.ini")),
        show_error_dialogs=False,
        confirm_operations=False,
    )
    try:
        assert window.operation_center.windowTitle() == "Operation Center"
        assert "submitted operations" in window.undo_action.statusTip()

        # Qt's offscreen platform does not guarantee native focus transfer. Test the
        # MainWindow contract directly by controlling the focus-manager return value.
        edit = window.domain_pages["search"].search_query
        edit.setText("first")
        edit.end(False)
        edit.insert(" second")

        class FocusProxy:
            @staticmethod
            def focusWidget():
                return edit

        monkeypatch.setattr(main_window_module, "QApplication", FocusProxy)
        window._edit_focused_widget("undo")
        assert edit.text() == "first"

        backend.submit(tmp_path / "progress.sqlite", "system.status")
        qt_app.processEvents()
        if backend.is_busy:
            assert not window.operation_progress.isHidden()
        _wait_idle(qt_app, backend)
        assert window.operation_center.operation_count >= 1
    finally:
        window.close()
        qt_app.processEvents()
        assert not backend.is_busy
