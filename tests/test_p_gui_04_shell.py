"""P-GUI-04 GUI shell / Workspace / navigation acceptance coverage."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _require_qt():
    pytest.importorskip("PySide6", reason="P-GUI-04 tests require the optional gui extra")


@pytest.fixture
def qt_app():
    _require_qt()
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def _wait_for(signal, trigger, timeout_ms: int = 10000):
    """Wait for an asynchronous GUI signal without imposing a performance SLA.

    Since P-RUNTIME-03, opening a Workspace runs ``system.status`` with a bounded
    external Qdrant health probe. Five seconds was a historical shell-test helper
    timeout, not an accepted latency contract, and can expire on a loaded Windows
    runner while the backend is still correctly working. Ten seconds matches the
    later GUI asynchronous-operation acceptance budget without relaxing semantics.
    """

    _require_qt()
    from PySide6.QtCore import QEventLoop, QTimer

    loop = QEventLoop()
    received: list[tuple[object, ...]] = []

    def handler(*args):
        received.append(args)
        loop.quit()

    signal.connect(handler)
    QTimer.singleShot(timeout_ms, loop.quit)
    trigger()
    loop.exec()
    signal.disconnect(handler)
    assert received, "Timed out waiting for Qt signal"
    return received[0]


def _settings(path: Path):
    _require_qt()
    from PySide6.QtCore import QSettings

    return QSettings(str(path), QSettings.Format.IniFormat)


def test_workspace_settings_are_presentation_only_and_recent_first(qt_app, tmp_path):
    del qt_app
    from sgokb.gui.workspace import WorkspaceSettings

    settings = WorkspaceSettings(_settings(tmp_path / "gui.ini"), recent_limit=3)
    first = tmp_path / "first.sqlite"
    second = tmp_path / "second.sqlite"
    settings.record_workspace(first)
    settings.record_workspace(second)
    settings.record_workspace(first)

    assert settings.recent_paths() == (first.resolve(), second.resolve())
    assert settings.last_workspace() == first.resolve()


def test_backend_worker_opens_fresh_workspace_on_backend_thread(qt_app, tmp_path):
    del qt_app
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.operation_contracts import OperationOutcome

    backend = BackendCoordinator()
    database = tmp_path / "fresh.sqlite"
    try:
        _, outcome = _wait_for(
            backend.operation_finished,
            lambda: backend.submit(database, "system.status"),
        )
        assert isinstance(outcome, OperationOutcome)
        assert Path(outcome.data["database"]) == database.resolve()
        assert database.is_file()
        assert outcome.data["objects"]["count"] == 0
    finally:
        assert backend.shutdown()


def test_gui_bootstrap_preloads_semantic_native_stack_before_backend_thread(
    qt_app,
    tmp_path,
    monkeypatch,
):
    import sgokb.gui.bootstrap as bootstrap

    calls: list[str] = []
    real_backend = bootstrap.BackendCoordinator

    def fake_preload():
        calls.append("preload")
        return None

    class RecordingBackend(real_backend):
        def __init__(self, *args, **kwargs):
            calls.append("backend")
            assert calls[0] == "preload"
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(bootstrap, "preload_local_semantic_native_dependencies", fake_preload)
    monkeypatch.setattr(bootstrap, "BackendCoordinator", RecordingBackend)

    runtime = bootstrap.create_runtime(
        [],
        settings=_settings(tmp_path / "bootstrap.ini"),
        show_error_dialogs=False,
    )
    try:
        assert calls[:2] == ["preload", "backend"]
    finally:
        runtime.window.close()
        qt_app.processEvents()
        assert runtime.backend.shutdown()


def test_workspace_controller_preserves_current_workspace_when_candidate_fails(qt_app, tmp_path):
    del qt_app
    from sgokb.gui.controllers import WorkspaceController
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.gui.workspace import WorkspaceSettings
    from sgokb.operation_contracts import OperationFailure

    backend = BackendCoordinator()
    controller = WorkspaceController(
        backend,
        WorkspaceSettings(_settings(tmp_path / "controller.ini")),
    )
    good = tmp_path / "good.sqlite"
    bad = tmp_path / "prototype.sqlite"
    try:
        _wait_for(controller.state_changed, lambda: controller.open_workspace(good))
        assert controller.state.db_path == good.resolve()

        connection = sqlite3.connect(bad)
        connection.execute("CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY)")
        connection.execute("INSERT INTO schema_migrations VALUES(1)")
        connection.commit()
        connection.close()

        failed_path, failure = _wait_for(
            controller.open_failed,
            lambda: controller.open_workspace(bad),
        )
        assert Path(failed_path) == bad.resolve()
        assert isinstance(failure, OperationFailure)
        assert "Prototype DB rejected" in failure.message
        assert controller.state.db_path == good.resolve()
    finally:
        assert backend.shutdown()


def test_main_window_exposes_accepted_navigation(qt_app, tmp_path):
    from sgokb.gui.views import NAVIGATION_ITEMS, MainWindow
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.gui.workspace import WorkspaceSettings

    backend = BackendCoordinator()
    window = MainWindow(
        backend,
        WorkspaceSettings(_settings(tmp_path / "window.ini")),
        show_error_dialogs=False,
    )
    try:
        assert window.navigation.count() == len(NAVIGATION_ITEMS) == 11
        assert [window.navigation.item(i).text() for i in range(window.navigation.count())] == [
            label for _key, label in NAVIGATION_ITEMS
        ]
        assert window.workspace_status.text() == "No workspace"
        assert window.windowTitle() == "SGOKB"
    finally:
        window.close()
        qt_app.processEvents()
        assert not backend.is_busy
