"""Post-release GUI startup and runtime-health regression coverage."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from sgokb.runtime_health import RuntimeHealthApplication

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "launch-sgokb-gui.vbs"

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_windows_launcher_uses_pythonw_and_hidden_detached_run() -> None:
    text = LAUNCHER.read_text(encoding="utf-8")

    assert ".venv\\Scripts\\pythonw.exe" in text
    assert "-m sgokb.gui.main" in text
    assert "shell.Run command, 0, False" in text
    assert "shell.CurrentDirectory = repoRoot" in text


def test_legacy_search_routing_is_healthy_when_current_knowledge_exists(monkeypatch) -> None:
    class FakeDb:
        def execute(self, _sql):
            class Cursor:
                @staticmethod
                def fetchone():
                    return (1,)

            return Cursor()

    class FakeRepository:
        db = FakeDb()

    class FakeGenerationApplication:
        def __init__(self, _repository):
            pass

        @staticmethod
        def status():
            return {
                "active_generation": None,
                "generations": [],
                "vector_bindings": [],
            }

    import sgokb.runtime_health as runtime_health

    monkeypatch.setattr(
        runtime_health,
        "KnowledgeSearchGenerationApplication",
        FakeGenerationApplication,
    )
    component = RuntimeHealthApplication(
        FakeRepository(),
        "test.sqlite",
        runtime_factory=object(),
    )._generation()

    assert component.status == "healthy"
    assert component.issue is None
    assert component.details["active_generation_id"] is None
    assert component.details["routing_mode"] == "legacy"
    assert component.details["current_object_count"] == 1


def test_runtime_dashboard_presents_legacy_generation_as_healthy() -> None:
    from sgokb.gui.runtime_dashboard import build_runtime_dashboard

    health = {
        "schema_version": "sgokb.runtime-health/1.0",
        "overall_status": "healthy",
        "lifecycle": {
            "qdrant_owner": "external",
            "observe": True,
            "start": False,
            "stop": False,
            "restart": False,
        },
        "components": {
            "sqlite": {
                "status": "healthy",
                "details": {"path": "test.sqlite", "journal_mode": "wal"},
                "issue": None,
            },
            "embedding": {
                "status": "healthy",
                "details": {"model": "test-model", "readiness": "configured_not_loaded"},
                "issue": None,
            },
            "qdrant": {
                "status": "healthy",
                "details": {
                    "endpoint": "http://localhost:6333",
                    "ready": True,
                    "version": "1.20.0",
                    "missing_collections": [],
                },
                "issue": None,
            },
            "generation": {
                "status": "healthy",
                "details": {
                    "active_generation_id": None,
                    "current_object_count": 1,
                    "source_catalog_current": None,
                    "routing_mode": "legacy",
                },
                "issue": None,
            },
            "derived": {
                "status": "healthy",
                "details": {
                    "current_object_count": 1,
                    "unhealthy_count": 0,
                    "kind_counts": {},
                },
                "issue": None,
            },
        },
    }

    dashboard = build_runtime_dashboard(health)
    generation = next(item for item in dashboard.components if item.key == "generation")

    assert generation.status == "healthy"
    assert generation.issue is None
    assert generation.troubleshooting is None
    assert generation.summary.startswith("active=none (legacy routing)")
    assert dashboard.readiness.status == "ready"


def _require_qt():
    pytest.importorskip("PySide6", reason="GUI startup tests require the optional gui extra")


def test_startup_splash_is_shown_before_runtime_imports_preload_and_backend(
    tmp_path,
    monkeypatch,
) -> None:
    _require_qt()
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication

    import sgokb.gui.bootstrap as bootstrap
    from sgokb.gui.views import MainWindow
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.gui.workspace import WorkspaceSettings

    app = QApplication.instance() or QApplication([])
    calls: list[str] = []
    fake_splash = object()

    def fake_show_splash(_app):
        calls.append("splash")
        return fake_splash

    def fake_update(_app, splash, message):
        assert splash is fake_splash
        calls.append(f"update:{message}")

    def fake_preload():
        calls.append("preload")

    class RecordingBackend(BackendCoordinator):
        def __init__(self, *args, **kwargs):
            calls.append("backend")
            super().__init__(*args, **kwargs)

    def fake_load_dependencies():
        calls.append("dependencies")
        return fake_preload, MainWindow, RecordingBackend, WorkspaceSettings

    monkeypatch.setattr(bootstrap, "_show_startup_splash", fake_show_splash)
    monkeypatch.setattr(bootstrap, "_update_startup_splash", fake_update)
    monkeypatch.setattr(bootstrap, "_load_runtime_dependencies", fake_load_dependencies)

    runtime = bootstrap.create_runtime(
        [],
        settings=QSettings(str(tmp_path / "startup.ini"), QSettings.Format.IniFormat),
        show_error_dialogs=False,
    )
    try:
        assert runtime.splash is fake_splash
        assert calls[:7] == [
            "splash",
            "update:Loading application modules...",
            "dependencies",
            "update:Loading local semantic runtime...",
            "preload",
            "update:Preparing workspace UI...",
            "backend",
        ]
    finally:
        runtime.window.close()
        app.processEvents()
        assert runtime.backend.shutdown()


def test_main_finishes_splash_after_showing_window(monkeypatch) -> None:
    _require_qt()
    import sgokb.gui.main as gui_main

    calls: list[str] = []

    class FakeWindow:
        def show(self):
            calls.append("show")

    class FakeSplash:
        def finish(self, window):
            assert isinstance(window, FakeWindow)
            calls.append("finish")

    class FakeApp:
        def processEvents(self):
            calls.append("events")

        def exec(self):
            calls.append("exec")
            return 0

    class FakeRuntime:
        app = FakeApp()
        window = FakeWindow()
        splash = FakeSplash()

    monkeypatch.setattr(gui_main, "create_runtime", lambda _argv=None: FakeRuntime())

    assert gui_main.main([]) == 0
    assert calls == ["show", "events", "finish", "exec"]
