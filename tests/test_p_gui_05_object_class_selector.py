"""P-GUI-05 regression coverage for Add Object Class selection."""

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


def test_add_object_dialog_selects_existing_class_from_registry(
    qt_app,
    tmp_path,
    monkeypatch,
):
    from PySide6.QtWidgets import QInputDialog

    from sgokb.gui.views import ObjectPage
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.repository import Repository

    database = tmp_path / "gui-object-class-selector.sqlite"
    backend = BackendCoordinator()
    page = ObjectPage(backend)
    text_answers = iter(
        [
            ("Dropdown Hero", True),
            ("Dropdown Alias", True),
        ]
    )
    observed_class_labels: list[str] = []

    def fake_get_text(*_args, **_kwargs):
        return next(text_answers)

    def fake_get_item(*args, **kwargs):
        labels = list(args[3])
        observed_class_labels.extend(labels)
        assert kwargs.get("editable") is False
        return next(label for label in labels if label == "Character [character]"), True

    monkeypatch.setattr(QInputDialog, "getText", fake_get_text)
    monkeypatch.setattr(QInputDialog, "getItem", fake_get_item)

    try:
        page.set_workspace(_workspace(database))
        _wait_idle(qt_app, backend)

        page._add_dialog()
        _wait_idle(qt_app, backend)

        assert "Character [character]" in observed_class_labels
        assert page.model.rowCount() == 1
        row = page.model.row_data(0)
        assert row is not None
        object_id = row["object_id"]

        repository = Repository(database)
        try:
            record = repository.object_store.get_object(object_id)
            assert record.name == "Dropdown Hero"
            assert record.primary_class_id == "class:character"
            assert {alias.value for alias in record.aliases} == {"Dropdown Alias"}
        finally:
            repository.close()
    finally:
        page.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()
