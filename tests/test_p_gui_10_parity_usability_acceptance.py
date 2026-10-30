"""P-GUI-10 final GUI parity / usability / regression acceptance coverage."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _require_qt():
    pytest.importorskip("PySide6", reason="P-GUI-10 tests require the optional gui extra")


@pytest.fixture
def qt_app():
    _require_qt()
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def _settings(path: Path):
    _require_qt()
    from PySide6.QtCore import QSettings

    return QSettings(str(path), QSettings.Format.IniFormat)


def _fresh_db(path: Path) -> None:
    from sgokb.repository import Repository

    repository = Repository(path)
    repository.close()


def _backend_outcome(qt_app, backend, database: Path, operation_id: str, arguments=None):
    _require_qt()
    from PySide6.QtCore import QEventLoop, QTimer

    loop = QEventLoop()
    result: list[object] = []
    request_id = backend.submit(database, operation_id, dict(arguments or {}))

    def finished(candidate_id, outcome):
        if candidate_id == request_id:
            result.append(outcome)
            loop.quit()

    def failed(candidate_id, failure):
        if candidate_id == request_id:
            result.append(failure)
            loop.quit()

    backend.operation_finished.connect(finished)
    backend.operation_failed.connect(failed)
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    timer.start(15000)
    loop.exec()
    backend.operation_finished.disconnect(finished)
    backend.operation_failed.disconnect(failed)
    qt_app.processEvents()
    assert result, f"Timed out waiting for {operation_id}"
    return result[0]


def test_all_67_public_operations_have_final_gui_reachability_contract():
    from sgokb.application_operator import (
        PUBLIC_OPERATION_IDS,
        SHARED_OPERATION_IDS,
        TRANSPORT_OPERATION_IDS,
    )

    assert len(PUBLIC_OPERATION_IDS) == 67
    assert TRANSPORT_OPERATION_IDS == {"mcp.serve"}
    assert len(SHARED_OPERATION_IDS) == 66

    view_root = Path("src/sgokb/gui/views")
    view_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(view_root.glob("*.py"))
    )
    missing = sorted(
        operation_id
        for operation_id in SHARED_OPERATION_IDS
        if f'"{operation_id}"' not in view_source and f"'{operation_id}'" not in view_source
    )
    assert not missing, f"Shared public operations without GUI reachability: {missing}"

    system_source = (view_root / "system_page.py").read_text(encoding="utf-8")
    assert "mcp serve" in system_source
    assert "external client-managed stdio" in system_source
    assert "detached MCP daemon" in system_source


def test_gui_views_have_no_direct_canonical_persistence_or_shell_write_bypass():
    view_root = Path("src/sgokb/gui/views")
    forbidden = {
        "sqlite3.connect(": "direct SQLite connection",
        "Repository(": "direct Repository construction",
        ".db.execute(": "direct repository SQL execution",
        "subprocess.run(": "subprocess execution",
        "subprocess.Popen(": "subprocess execution",
        "os.system(": "shell execution",
    }
    findings: list[str] = []
    for path in sorted(view_root.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        for token, description in forbidden.items():
            if token in source:
                findings.append(f"{path.name}: {description} ({token})")
    assert not findings, "GUI canonical-write bypass detected: " + "; ".join(findings)


def test_shared_backend_matches_direct_application_for_representative_reads(qt_app, tmp_path):
    from sgokb.application_operator import OperatorSession
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.operation_contracts import OperationOutcome, OperationRequest

    database = tmp_path / "parity.sqlite"
    _fresh_db(database)
    direct = OperatorSession(database)
    direct.execute(
        OperationRequest(
            "object.add",
            {"name": "Parity Object", "primary_class": "character", "alias": ()},
        )
    )
    backend = BackendCoordinator()
    try:
        for operation_id in ("object.list", "registry.class.list", "system.integrity"):
            expected = direct.execute(OperationRequest(operation_id, {}))
            actual = _backend_outcome(qt_app, backend, database, operation_id)
            assert isinstance(actual, OperationOutcome)
            assert actual.operation_id == expected.operation_id
            assert actual.state == expected.state
            assert actual.data == expected.data
    finally:
        assert backend.shutdown()


def test_keyboard_navigation_shortcuts_and_restart_restore_presentation_state(qt_app, tmp_path):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    from sgokb.gui.views import MainWindow
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.gui.workspace import WorkspaceSettings

    ini = tmp_path / "gui.ini"
    backend = BackendCoordinator()
    window = MainWindow(
        backend,
        WorkspaceSettings(_settings(ini)),
        show_error_dialogs=False,
        confirm_operations=False,
    )
    window.show()
    qt_app.processEvents()
    try:
        window.navigation.setCurrentRow(0)
        QTest.keyClick(window.navigation, Qt.Key.Key_Down)
        qt_app.processEvents()
        assert window.navigation.currentRow() == 1
        assert window.pages.currentIndex() == 1

        QTest.keyClick(window.navigation, Qt.Key.Key_End)
        qt_app.processEvents()
        assert window.navigation.currentRow() == window.navigation.count() - 1
        assert window.pages.currentIndex() == window.pages.count() - 1

        assert window.open_action.shortcut().toString() == "Ctrl+O"
        assert window.new_action.shortcut().toString() == "Ctrl+N"
        assert window.undo_action.shortcut().toString() == "Ctrl+Z"
        assert window.redo_action.shortcut().toString() == "Ctrl+Y"

        system_row = window._page_index["system"]
        window.navigation.setCurrentRow(system_row)
        qt_app.processEvents()
        assert window.settings.last_page() == "system"
    finally:
        window.close()
        qt_app.processEvents()
        assert not backend.is_busy

    backend2 = BackendCoordinator()
    restored = MainWindow(
        backend2,
        WorkspaceSettings(_settings(ini)),
        show_error_dialogs=False,
        confirm_operations=False,
    )
    try:
        assert restored.navigation.currentRow() == restored._page_index["system"]
        assert restored.pages.currentIndex() == restored._page_index["system"]
    finally:
        restored.close()
        qt_app.processEvents()
        assert not backend2.is_busy


def test_scaled_dpi_layout_smoke(qt_app, tmp_path):
    from sgokb.gui.views import MainWindow
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.gui.workspace import WorkspaceSettings

    backend = BackendCoordinator()
    window = MainWindow(
        backend,
        WorkspaceSettings(_settings(tmp_path / "dpi.ini")),
        show_error_dialogs=False,
        confirm_operations=False,
    )
    window.show()
    qt_app.processEvents()
    try:
        scale = float(os.environ.get("QT_SCALE_FACTOR", "1"))
        assert window.devicePixelRatioF() >= 1.0
        if scale > 1.0:
            assert window.devicePixelRatioF() > 1.0
        assert window.navigation.width() >= window.navigation.minimumWidth()
        assert window.pages.width() > 400
        assert window.pages.height() > 300
        assert window.operation_center.minimumSizeHint().height() >= 0
        for page in window.domain_pages.values():
            assert page.sizeHint().width() >= 0
            assert page.sizeHint().height() >= 0
    finally:
        window.close()
        qt_app.processEvents()
        assert not backend.is_busy


def test_backend_failure_does_not_poison_followup_operation(qt_app, tmp_path):
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.operation_contracts import OperationFailure, OperationOutcome

    database = tmp_path / "recovery.sqlite"
    _fresh_db(database)
    backend = BackendCoordinator()
    try:
        failure = _backend_outcome(
            qt_app,
            backend,
            database,
            "object.show",
            {"object_id": "missing-object"},
        )
        assert isinstance(failure, OperationFailure)
        assert not backend.is_busy

        outcome = _backend_outcome(qt_app, backend, database, "object.list")
        assert isinstance(outcome, OperationOutcome)
        assert outcome.state == "success"
        assert outcome.data == []
        assert not backend.is_busy
    finally:
        assert backend.shutdown()
