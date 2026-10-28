"""P-GUI-06 filter selector and temporal range coverage."""

from __future__ import annotations

import os

import pytest
from test_hybrid_search import _accepted, _class

from sgokb.repository import Repository

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _require_qt():
    pytest.importorskip("PySide6", reason="P-GUI-06 tests require the optional gui extra")


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
    assert not backend.is_busy, "Timed out waiting for P-GUI backend to become idle"


def _workspace(path):
    from sgokb.gui.workspace import WorkspaceState

    return WorkspaceState.opened(path, {})


def test_search_filter_selectors_and_validity_range_arguments(qt_app, tmp_path, monkeypatch):
    from sgokb.gui.views import SearchPage
    from sgokb.gui.worker import BackendCoordinator

    database = tmp_path / "gui-search-filter-selectors.sqlite"
    repository = Repository(database)
    try:
        object_id = repository.object_store.create_object(
            "Selector Hero",
            _class(repository, "character"),
            object_id="object-selector-hero",
        )
        version_id, records = _accepted(
            repository,
            object_id,
            "version-selector-1",
            statements=[
                {
                    "facet": "personality",
                    "text": "Selector Hero is careful during the selected period.",
                    "temporal": {
                        "valid_from": "2026-01-01",
                        "valid_to": "2026-12-31",
                    },
                }
            ],
        )
        temporal_scope_id = records[0]["temporal_scope_id"]
    finally:
        repository.close()

    backend = BackendCoordinator()
    page = SearchPage(backend)
    try:
        page.set_workspace(_workspace(database))
        _wait_idle(qt_app, backend)

        assert page.primary_class.findData("character") >= 0
        assert page.additional_class.findData("character") >= 0
        assert page.ancestor_class.findData("character") >= 0
        assert page.facet.findData("personality") >= 0
        assert page.version.findData(version_id) >= 0
        assert page.temporal_scope.findData(temporal_scope_id) >= 0

        object_index = page.similar_object.findData(object_id)
        assert object_index >= 0
        page.similar_object.setCurrentIndex(object_index)
        assert page.similar_facet.findData("personality") >= 0
        assert page.similar_version.findData(version_id) >= 0

        captured = []

        def fake_submit(operation_id, arguments=None, *, callback=None, summary=None):
            captured.append((operation_id, dict(arguments or {}), callback, summary))
            return "request-id"

        monkeypatch.setattr(page, "submit", fake_submit)
        page.search_query.setText("Selector Hero")
        page.search_mode.setCurrentText("lexical")
        page.primary_class.setCurrentIndex(page.primary_class.findData("character"))
        page.facet.setCurrentIndex(page.facet.findData("personality"))
        page.version.setCurrentIndex(page.version.findData(version_id))
        page.temporal_scope.setCurrentIndex(page.temporal_scope.findData(temporal_scope_id))
        page.valid_from.setText("2026-02-01")
        page.valid_to.setText("2026-11-30")
        page.run_search()

        operation_id, arguments, _callback, _summary = captured[-1]
        assert operation_id == "search"
        assert arguments["primary_class"] == "character"
        assert arguments["facet"] == "personality"
        assert arguments["version"] == version_id
        assert arguments["temporal_scope"] == temporal_scope_id
        assert arguments["valid_at"] == "2026-02-01..2026-11-30"

        page.similar_facet.setCurrentIndex(page.similar_facet.findData("personality"))
        page.similar_version.setCurrentIndex(page.similar_version.findData(version_id))
        page.run_similarity()
        operation_id, arguments, _callback, _summary = captured[-1]
        assert operation_id == "similar"
        assert arguments["object_id"] == object_id
        assert arguments["facet"] == "personality"
        assert arguments["version"] == version_id

        before = len(captured)
        page.valid_from.setText("2027-01-01")
        page.valid_to.setText("2026-01-01")
        assert page.run_search() is None
        assert len(captured) == before
        assert "From must not be after To" in page.operation_status.text()
    finally:
        page.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()
