"""P-GUI-06 Search / Similarity / Registry / Version GUI acceptance coverage."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

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


def _workspace(path: Path):
    from sgokb.gui.workspace import WorkspaceState

    return WorkspaceState.opened(path, {})


def _seed_workspace(database: Path):
    from sgokb.repository import Repository

    repository = Repository(database)
    try:
        object_id = repository.object_store.create_object(
            "GUI Search Hero",
            "class:character",
            object_id="object-p-gui-06",
        )
        repository.object_store.register_relation_type(
            "gui_related",
            "GUI Related",
            relation_type_id="relation:gui-related",
        )
        first = repository.version_store.begin_candidate(
            object_id,
            None,
            version_id="version-p-gui-06-1",
        )
        repository.version_store.accept_candidate(first)
        second = repository.version_store.begin_candidate(
            object_id,
            first,
            version_id="version-p-gui-06-2",
        )
        repository.version_store.accept_candidate(second)
        return object_id, first, second
    finally:
        repository.close()


def test_search_page_runs_lexical_search_and_exposes_similarity_scope(qt_app, tmp_path, monkeypatch):
    from sgokb.gui.views import SearchPage
    from sgokb.gui.worker import BackendCoordinator

    database = tmp_path / "gui-search.sqlite"
    object_id, _first, _second = _seed_workspace(database)
    backend = BackendCoordinator()
    page = SearchPage(backend)
    try:
        page.set_workspace(_workspace(database))
        _wait_idle(qt_app, backend)
        assert page.similar_object.findData(object_id) >= 0

        page.search_query.setText("GUI Search Hero")
        page.search_mode.setCurrentText("lexical")
        page.run_search()
        _wait_idle(qt_app, backend)

        assert page.search_model.rowCount() >= 1
        names = {
            page.search_model.row_data(row)["name"]
            for row in range(page.search_model.rowCount())
        }
        assert "GUI Search Hero" in names
        assert "No degradation" in page.search_runtime_state.text()

        captured = []

        def fake_submit(operation_id, arguments=None, *, callback=None, summary=None):
            captured.append((operation_id, dict(arguments or {}), callback, summary))
            return "request-id"

        monkeypatch.setattr(page, "submit", fake_submit)
        page.similar_object.setCurrentIndex(page.similar_object.findData(object_id))
        page.similar_facet.setText("personality")
        page.similar_version.setText("version-p-gui-06-2")
        page.cross_class.setChecked(True)
        page.similar_archived.setChecked(True)
        page.run_similarity()

        operation_id, arguments, _callback, _summary = captured[-1]
        assert operation_id == "similar"
        assert arguments == {
            "object_id": object_id,
            "limit": 10,
            "cross_class": True,
            "include_archived": True,
            "facet": "personality",
            "version": "version-p-gui-06-2",
        }
    finally:
        page.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()


def test_registry_version_diff_and_render_round_trip(qt_app, tmp_path):
    from sgokb.gui.views import RegistryPage
    from sgokb.gui.worker import BackendCoordinator

    database = tmp_path / "gui-registry-version.sqlite"
    object_id, first, second = _seed_workspace(database)
    backend = BackendCoordinator()
    page = RegistryPage(backend)
    try:
        page.set_workspace(_workspace(database))
        _wait_idle(qt_app, backend)

        assert page.class_model.rowCount() > 0
        assert page.relation_model.rowCount() >= 1
        relation_ids = {
            page.relation_model.row_data(row)["id"]
            for row in range(page.relation_model.rowCount())
        }
        assert "relation:gui-related" in relation_ids

        page.show_version(second)
        _wait_idle(qt_app, backend)
        assert second in page.version_structured.toPlainText()
        assert object_id in page.version_structured.toPlainText()

        page.diff_versions(first, second)
        _wait_idle(qt_app, backend)
        structured = page.version_structured.toPlainText()
        markdown = page.version_markdown.toPlainText()
        assert first in structured
        assert second in structured
        assert "# Object Knowledge Diff" in markdown
        assert first in markdown
        assert second in markdown

        output_root = tmp_path / "rendered"
        page.render_markdown(object_id, kind="object", output_root=str(output_root))
        _wait_idle(qt_app, backend)
        assert object_id in page.render_result.toPlainText()
        assert "GUI Search Hero" in page.render_preview.toPlainText()
        assert list(output_root.rglob("*.md"))
    finally:
        page.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()


def test_registry_proposal_actions_keep_decision_and_apply_separate(qt_app, monkeypatch):
    from sgokb.gui.views import RegistryPage
    from sgokb.gui.worker import BackendCoordinator

    backend = BackendCoordinator()
    page = RegistryPage(backend)
    captured = []

    def fake_submit(operation_id, arguments=None, *, callback=None, summary=None):
        captured.append((operation_id, dict(arguments or {}), callback, summary))
        return "request-id"

    try:
        monkeypatch.setattr(page, "submit", fake_submit)
        page.decide_proposal("version-x:proposal-1", "accepted", "reviewed")
        page.decide_proposal("version-x:proposal-1", "rejected", "not suitable")
        page.apply_proposal("version-x:proposal-1")

        assert [item[0] for item in captured] == [
            "registry.proposal.accept",
            "registry.proposal.reject",
            "registry.proposal.apply",
        ]
        assert captured[0][1]["note"] == "reviewed"
        assert captured[1][1]["note"] == "not suitable"
        assert captured[2][1] == {"proposal_ref": "version-x:proposal-1"}
    finally:
        page.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()


def test_main_window_hosts_real_p_gui_06_pages(qt_app, tmp_path):
    from PySide6.QtCore import QSettings

    from sgokb.gui.views import MainWindow, RegistryPage, SearchPage
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.gui.workspace import WorkspaceSettings

    backend = BackendCoordinator()
    settings = WorkspaceSettings(QSettings(str(tmp_path / "gui.ini"), QSettings.Format.IniFormat))
    window = MainWindow(backend, settings, show_error_dialogs=False)
    try:
        assert isinstance(window.domain_pages["search"], SearchPage)
        assert isinstance(window.domain_pages["registry"], RegistryPage)
        assert {"objects", "sources", "evidence", "associations", "search", "registry"} <= set(
            window.domain_pages
        )
    finally:
        window.close()
        qt_app.processEvents()
        assert not backend.is_busy
