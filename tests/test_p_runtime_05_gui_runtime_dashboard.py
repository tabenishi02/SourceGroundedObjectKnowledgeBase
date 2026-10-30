"""P-RUNTIME-05 GUI Runtime Dashboard acceptance coverage."""

from __future__ import annotations

import os

import pytest

from sgokb.gui.runtime_dashboard import build_runtime_dashboard

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _component(status="healthy", details=None, issue=None):
    return {"status": status, "details": dict(details or {}), "issue": issue}


def _health():
    return {
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
            "sqlite": _component(details={"path": "test.sqlite", "journal_mode": "wal"}),
            "embedding": _component(
                details={"model": "model", "readiness": "configured_not_loaded", "loaded": False}
            ),
            "qdrant": _component(
                details={
                    "endpoint": "http://localhost:6333",
                    "ready": True,
                    "version": "1.19.2",
                    "missing_collections": [],
                }
            ),
            "generation": _component(
                details={
                    "active_generation_id": "search-generation:test",
                    "current_object_count": 1,
                    "source_catalog_current": True,
                    "vector_bindings": [{"status": "ready"}],
                }
            ),
            "derived": _component(
                details={
                    "current_object_count": 1,
                    "unhealthy_count": 0,
                    "kind_counts": {
                        "search_representation": {"ready": 1},
                        "embedding": {"ready": 1},
                        "vector_index": {"ready": 1},
                        "rendering": {"ready": 1},
                    },
                }
            ),
        },
    }


def test_dashboard_reports_ready_semantic_runtime_and_observer_only_boundary():
    dashboard = build_runtime_dashboard(_health())
    assert dashboard.readiness.status == "ready"
    assert dashboard.readiness.blockers == ()
    assert [item.key for item in dashboard.components] == [
        "sqlite",
        "embedding",
        "qdrant",
        "generation",
        "derived",
    ]
    assert "owner: external" in dashboard.lifecycle_note
    assert "start/stop/restart=false/false/false" in dashboard.lifecycle_note
    assert "not part of sgokb.runtime-health/1.0" in dashboard.mcp_note


@pytest.mark.parametrize("component", ["sqlite", "embedding"])
def test_dashboard_blocks_when_local_semantic_dependency_is_unavailable(component):
    health = _health()
    health["components"][component] = _component(
        "unavailable",
        issue={"code": f"{component}_unavailable", "message": f"{component} unavailable"},
    )
    dashboard = build_runtime_dashboard(health)
    assert dashboard.readiness.status == "blocked"
    assert any(f"{component} unavailable" in item for item in dashboard.readiness.blockers)


def test_dashboard_blocks_when_qdrant_is_not_ready_or_active_collection_is_missing():
    health = _health()
    health["components"]["qdrant"] = _component(
        "degraded",
        details={
            "endpoint": "http://localhost:6333",
            "ready": True,
            "version": "1.19.2",
            "missing_collections": ["generation-test"],
        },
        issue={
            "code": "qdrant_collection_unavailable",
            "message": "Active Search generation references a missing Qdrant collection",
        },
    )
    dashboard = build_runtime_dashboard(health)
    assert dashboard.readiness.status == "blocked"
    assert "missing Qdrant collection" in dashboard.readiness.blockers[0]


def test_generation_not_active_is_degraded_not_blocked_because_legacy_routing_exists():
    health = _health()
    health["overall_status"] = "degraded"
    health["components"]["generation"] = _component(
        "degraded",
        details={
            "active_generation_id": None,
            "current_object_count": 5,
            "source_catalog_current": None,
            "vector_bindings": [],
        },
        issue={
            "code": "generation_not_active",
            "message": "Knowledge exists but no active Search generation is selected",
        },
    )
    dashboard = build_runtime_dashboard(health)
    assert dashboard.readiness.status == "degraded"
    assert dashboard.readiness.blockers == ()
    assert any("legacy vector routing" in item for item in dashboard.readiness.warnings)


def test_broken_active_generation_blocks_semantic_readiness():
    health = _health()
    health["components"]["generation"] = _component(
        "degraded",
        details={"active_generation_id": "missing", "current_object_count": 1},
        issue={
            "code": "active_generation_missing",
            "message": "The active generation pointer references a missing generation",
        },
    )
    dashboard = build_runtime_dashboard(health)
    assert dashboard.readiness.status == "blocked"
    assert "missing generation" in dashboard.readiness.blockers[0]


def test_rendering_only_derived_degradation_is_warning_not_semantic_blocker():
    health = _health()
    health["components"]["derived"] = _component(
        "degraded",
        details={
            "current_object_count": 1,
            "unhealthy_count": 1,
            "kind_counts": {
                "search_representation": {"ready": 1},
                "embedding": {"ready": 1},
                "vector_index": {"ready": 1},
                "rendering": {"pending": 1},
            },
        },
        issue={
            "code": "derived_state_incomplete",
            "message": "One or more current Objects have incomplete derived state",
        },
    )
    dashboard = build_runtime_dashboard(health)
    assert dashboard.readiness.status == "degraded"
    assert dashboard.readiness.blockers == ()
    assert dashboard.readiness.warnings


def test_semantic_derived_degradation_is_explicit_warning():
    health = _health()
    health["components"]["derived"] = _component(
        "degraded",
        details={
            "current_object_count": 1,
            "unhealthy_count": 1,
            "kind_counts": {"vector_index": {"pending": 1}},
        },
        issue={"code": "derived_state_incomplete", "message": "Derived incomplete"},
    )
    dashboard = build_runtime_dashboard(health)
    assert dashboard.readiness.status == "degraded"
    assert "vector_index=1" in dashboard.readiness.warnings[0]


def test_unknown_runtime_schema_does_not_claim_readiness():
    health = _health()
    health["schema_version"] = "sgokb.runtime-health/99.0"
    dashboard = build_runtime_dashboard(health)
    assert dashboard.readiness.status == "unknown"
    assert dashboard.readiness.blockers


def _require_qt():
    pytest.importorskip("PySide6", reason="P-RUNTIME-05 GUI tests require the optional gui extra")


@pytest.fixture
def qt_app():
    _require_qt()
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def test_runtime_dashboard_system_page_binds_snapshot_without_lifecycle_controls(qt_app):
    from sgokb.gui.views.runtime_dashboard_system_page import RuntimeDashboardSystemPage
    from sgokb.gui.worker import BackendCoordinator

    backend = BackendCoordinator()
    page = RuntimeDashboardSystemPage(backend)
    try:
        page._update_runtime_summary({"runtime_health": _health()})
        assert "Semantic Search=ready" in page.runtime_summary.text()
        assert page.semantic_readiness.text().startswith("READY")
        assert "HEALTHY" in page.runtime_component_labels["qdrant"].text()
        assert "external" in page.runtime_lifecycle_note.text()
        assert "MCP runtime state is not part" in page.runtime_mcp_note.text()
        assert page.runtime_troubleshooting.toPlainText() == "No runtime issue requires troubleshooting."
        assert not hasattr(page, "qdrant_start_button")
        assert not hasattr(page, "qdrant_stop_button")
        assert not hasattr(page, "qdrant_restart_button")
    finally:
        page.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()


def test_main_window_uses_runtime_dashboard_system_page(qt_app, tmp_path):
    from PySide6.QtCore import QSettings

    from sgokb.gui.views import MainWindow
    from sgokb.gui.views.runtime_dashboard_system_page import RuntimeDashboardSystemPage
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.gui.workspace import WorkspaceSettings

    backend = BackendCoordinator()
    settings = WorkspaceSettings(QSettings(str(tmp_path / "runtime.ini"), QSettings.Format.IniFormat))
    window = MainWindow(backend, settings, show_error_dialogs=False)
    try:
        assert isinstance(window.domain_pages["system"], RuntimeDashboardSystemPage)
    finally:
        window.close()
        qt_app.processEvents()
        assert backend.shutdown()
