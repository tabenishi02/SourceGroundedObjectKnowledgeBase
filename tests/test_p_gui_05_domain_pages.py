"""P-GUI-05 Object / Source / Evidence / Association GUI acceptance coverage."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _require_qt():
    pytest.importorskip("PySide6", reason="P-GUI-05 tests require the optional gui extra")


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


def test_object_page_mutations_use_stable_id_and_preserve_canonical_effect(qt_app, tmp_path):
    from sgokb.gui.views import ObjectPage
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.repository import Repository

    database = tmp_path / "gui-object.sqlite"
    backend = BackendCoordinator()
    page = ObjectPage(backend)
    try:
        page.set_workspace(_workspace(database))
        _wait_idle(qt_app, backend)

        page.add_object("GUI Hero", "character", ("Hero Alias",))
        _wait_idle(qt_app, backend)
        assert page.model.rowCount() == 1
        row = page.model.row_data(0)
        assert row is not None
        object_id = row["object_id"]
        assert isinstance(object_id, str)

        page.rename_object(object_id, "GUI Hero Renamed")
        _wait_idle(qt_app, backend)
        page.add_alias(object_id, "Second Alias", language="en")
        _wait_idle(qt_app, backend)
        page.set_primary_class(object_id, "character")
        _wait_idle(qt_app, backend)
        page.add_class(object_id, "concept")
        _wait_idle(qt_app, backend)
        page.remove_class(object_id, "concept")
        _wait_idle(qt_app, backend)
        page.set_status(object_id, "archived")
        _wait_idle(qt_app, backend)
        page.load_object(object_id)
        _wait_idle(qt_app, backend)

        repository = Repository(database)
        try:
            record = repository.object_store.get_object(object_id)
            assert record.name == "GUI Hero Renamed"
            assert record.status.value == "archived"
            assert {alias.value for alias in record.aliases} == {"Hero Alias", "Second Alias"}
            assert record.additional_class_ids == ()
            events = repository.object_store.registry_events(object_id)
            assert any(event["event_type"] == "alias_added" for event in events)
        finally:
            repository.close()
        assert "GUI Hero Renamed" in page.detail_text.toPlainText()
        assert "Second Alias" in page.alias_text.toPlainText()
    finally:
        page.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()


def test_source_page_import_process_selection_and_raw_inspection(qt_app, tmp_path, make_bundle):
    from sgokb.gui.views import SourcePage
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.repository import Repository

    database = tmp_path / "gui-source.sqlite"
    bundle = make_bundle()
    backend = BackendCoordinator()
    page = SourcePage(backend)
    try:
        page.set_workspace(_workspace(database))
        _wait_idle(qt_app, backend)
        page.import_path(bundle)
        _wait_idle(qt_app, backend)
        assert page.snapshot_model.rowCount() == 1
        snapshot = page.snapshot_model.row_data(0)
        assert snapshot is not None
        source_id = snapshot["source_id"]
        snapshot_id = snapshot["id"]
        assert page.raw_model.rowCount() > 0
        raw = page.raw_model.row_data(0)
        assert raw is not None
        for key in ("id", "logical_path", "storage_ref", "media_type", "sha256", "byte_count"):
            assert key in raw

        page.process_snapshot(str(snapshot_id))
        _wait_idle(qt_app, backend)
        assert page.run_model.rowCount() >= 1
        run = page.run_model.row_data(0)
        assert run is not None
        run_id = run["id"]

        page.select_snapshot(str(source_id), str(snapshot_id), "P-GUI-05 acceptance")
        _wait_idle(qt_app, backend)
        page.select_run(str(snapshot_id), str(run_id), "P-GUI-05 acceptance")
        _wait_idle(qt_app, backend)

        repository = Repository(database)
        try:
            effective_snapshot = repository.source_store.effective_snapshot(str(source_id))
            effective_run = repository.source_store.effective_run(str(snapshot_id))
            assert effective_snapshot is not None
            assert effective_snapshot.snapshot_id == snapshot_id
            assert effective_run is not None
            assert effective_run["id"] == run_id
            assert repository.source_store.status()["evidence"] > 0
        finally:
            repository.close()
    finally:
        page.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()


def test_evidence_and_association_pages_round_trip(qt_app, tmp_path, make_bundle):
    from sgokb.application import Application
    from sgokb.gui.views import AssociationPage, EvidencePage
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.repository import Repository

    database = tmp_path / "gui-evidence-association.sqlite"
    repository = Repository(database)
    try:
        object_id = repository.object_store.create_object("架空太郎", "class:character")
        app = Application(repository)
        imported = app.import_source_path(make_bundle())
        processed = app.process_source_snapshot(imported["snapshot"])
        source_id = imported["source"]
        evidence_id = processed["evidence_ids"][0]
    finally:
        repository.close()

    backend = BackendCoordinator()
    association_page = AssociationPage(backend)
    evidence_page = EvidencePage(backend)
    try:
        state = _workspace(database)
        association_page.set_workspace(state)
        evidence_page.set_workspace(state)
        _wait_idle(qt_app, backend)

        association_page.set_association(
            object_id,
            source_id,
            "confirmed",
            subject_relationship="subject",
            note="GUI acceptance",
        )
        _wait_idle(qt_app, backend)
        assert association_page.model.rowCount() == 1
        association = association_page.model.row_data(0)
        assert association is not None
        assert association["status"] == "confirmed"

        association_page.suggest_associations()
        _wait_idle(qt_app, backend)
        assert association_page.model.rowCount() >= 1

        index = evidence_page.object_combo.findData(object_id)
        assert index >= 0
        evidence_page.object_combo.setCurrentIndex(index)
        evidence_page.retrieve_candidates()
        _wait_idle(qt_app, backend)
        assert evidence_page.candidate_model.rowCount() >= 1
        candidate_ids = {
            evidence_page.candidate_model.row_data(row)["evidence_id"]
            for row in range(evidence_page.candidate_model.rowCount())
        }
        assert evidence_id in candidate_ids

        evidence_page.candidate_table.selectRow(0)
        evidence_page._include_current()
        evidence_page.run_selection()
        _wait_idle(qt_app, backend)
        assert "Selected:" in evidence_page.budget_status.text()
        assert evidence_page.manual_include

        evidence_page.search_query.setText("架空太郎")
        evidence_page.search_mode.setCurrentText("lexical")
        evidence_page.search_evidence()
        _wait_idle(qt_app, backend)
        assert evidence_page.search_model.rowCount() >= 1

        evidence_page.load_evidence(evidence_id)
        _wait_idle(qt_app, backend)
        assert evidence_id in evidence_page.detail_text.toPlainText()
        assert source_id in evidence_page.provenance_text.toPlainText()

        association_page.clear_association(object_id, source_id)
        _wait_idle(qt_app, backend)
        repository = Repository(database)
        try:
            assert (
                repository.source_store.association_for_object_source(object_id, source_id)
                is None
            )
        finally:
            repository.close()
    finally:
        association_page.deleteLater()
        evidence_page.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()


def test_main_window_hosts_real_p_gui_05_pages(qt_app, tmp_path):
    from PySide6.QtCore import QSettings

    from sgokb.gui.views import AssociationPage, EvidencePage, MainWindow, ObjectPage, SourcePage
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.gui.workspace import WorkspaceSettings

    backend = BackendCoordinator()
    settings = WorkspaceSettings(QSettings(str(tmp_path / "gui.ini"), QSettings.Format.IniFormat))
    window = MainWindow(backend, settings, show_error_dialogs=False)
    try:
        assert isinstance(window.domain_pages["objects"], ObjectPage)
        assert isinstance(window.domain_pages["sources"], SourcePage)
        assert isinstance(window.domain_pages["evidence"], EvidencePage)
        assert isinstance(window.domain_pages["associations"], AssociationPage)
        assert set(window.domain_pages) == {"objects", "sources", "evidence", "associations"}
    finally:
        window.close()
        qt_app.processEvents()
        assert not backend.is_busy
