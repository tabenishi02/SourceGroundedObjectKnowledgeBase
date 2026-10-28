"""P-GUI-05 regression coverage for Object Class mutation selectors."""

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


def _class_label_for_key(labels: list[str], key: str) -> str:
    return next(label for label in labels if f"[{key}]" in label)


def test_object_class_controls_use_registry_scoped_dropdowns(
    qt_app,
    tmp_path,
    monkeypatch,
):
    from PySide6.QtWidgets import QInputDialog

    from sgokb.gui.views import ObjectPage
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.repository import Repository

    database = tmp_path / "gui-object-class-controls.sqlite"
    backend = BackendCoordinator()
    page = ObjectPage(backend)
    observed: dict[str, list[str]] = {}

    def fake_get_item(*args, **kwargs):
        title = str(args[1])
        labels = list(args[3])
        observed[title] = labels
        assert kwargs.get("editable") is False
        if title == "Set Primary Class":
            return _class_label_for_key(labels, "work"), True
        if title == "Add Additional Class":
            return _class_label_for_key(labels, "concept"), True
        if title == "Remove Additional Class":
            return _class_label_for_key(labels, "concept"), True
        raise AssertionError(f"Unexpected Class dialog: {title}")

    monkeypatch.setattr(QInputDialog, "getItem", fake_get_item)

    try:
        page.set_workspace(_workspace(database))
        _wait_idle(qt_app, backend)
        page.add_object("Class Control Hero", "class:character")
        _wait_idle(qt_app, backend)

        row = page.model.row_data(0)
        assert row is not None
        object_id = row["object_id"]
        assert page.remove_class_button.isEnabled() is False

        repository = Repository(database)
        try:
            classes = repository.object_store.classes()
            class_count = len(classes)
        finally:
            repository.close()

        page._primary_class_dialog()
        _wait_idle(qt_app, backend)

        primary_labels = observed["Set Primary Class"]
        assert len(primary_labels) == class_count
        assert _class_label_for_key(primary_labels, "character")
        assert _class_label_for_key(primary_labels, "work")
        assert _class_label_for_key(primary_labels, "concept")

        repository = Repository(database)
        try:
            record = repository.object_store.get_object(object_id)
            assert record.primary_class_id == "class:work"
        finally:
            repository.close()

        page._add_class_dialog()
        _wait_idle(qt_app, backend)

        add_labels = observed["Add Additional Class"]
        assert len(add_labels) == class_count - 1
        assert not any("[work]" in label for label in add_labels)
        assert _class_label_for_key(add_labels, "character")
        assert _class_label_for_key(add_labels, "concept")

        repository = Repository(database)
        try:
            record = repository.object_store.get_object(object_id)
            assert "class:concept" in record.additional_class_ids
            assigned_before_remove = set(record.additional_class_ids)
            class_by_id = {
                item.class_id: item.key
                for item in repository.object_store.classes()
            }
        finally:
            repository.close()

        assert page.remove_class_button.isEnabled() is True
        page._remove_class_dialog()
        _wait_idle(qt_app, backend)

        remove_labels = observed["Remove Additional Class"]
        expected_keys = {class_by_id[class_id] for class_id in assigned_before_remove}
        assert len(remove_labels) == len(assigned_before_remove)
        for key in expected_keys:
            assert _class_label_for_key(remove_labels, key)

        repository = Repository(database)
        try:
            record = repository.object_store.get_object(object_id)
            assert "class:concept" not in record.additional_class_ids
            has_remaining_additional = bool(record.additional_class_ids)
        finally:
            repository.close()

        assert page.remove_class_button.isEnabled() is has_remaining_additional
    finally:
        page.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()
