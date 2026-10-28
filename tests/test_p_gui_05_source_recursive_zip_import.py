"""P-GUI-05 regression coverage for recursive Source folder ZIP import."""

from __future__ import annotations

import json
import os
import shutil
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


def test_source_folder_dialog_imports_all_zip_files_recursively(
    qt_app,
    tmp_path,
    make_bundle,
    monkeypatch,
):
    from PySide6.QtWidgets import QFileDialog

    from sgokb.gui.views import SourcePage
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.repository import Repository

    database = tmp_path / "gui-source-recursive.sqlite"
    import_root = tmp_path / "captures"
    nested = import_root / "nested" / "deeper"
    nested.mkdir(parents=True)

    first_bundle = make_bundle(
        url="https://example.test/first",
        timestamp="2026-01-01T00:00:00.000Z",
    )
    second_bundle = make_bundle(
        url="https://example.test/second",
        timestamp="2026-01-02T00:00:00.000Z",
    )

    # WebCaptureImporter intentionally requires the canonical bundle filename
    # encoded by manifest captured_at + capture_id. Preserve that validation
    # while placing valid bundles at different recursive depths.
    first_target = import_root / first_bundle.name
    second_target = nested / second_bundle.name
    shutil.copy2(first_bundle, first_target)
    shutil.copy2(second_bundle, second_target)

    # The folder scan targets every ZIP. Invalid ZIPs are attempted and reported
    # as partial failures without preventing valid bundles from importing.
    invalid_zip = import_root / "not-a-webcapture.zip"
    invalid_zip.write_text("not a capture bundle", encoding="utf-8")
    (import_root / "ignore.txt").write_text("not a capture bundle", encoding="utf-8")

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *_args, **_kwargs: str(import_root),
    )

    backend = BackendCoordinator()
    page = SourcePage(backend)
    try:
        page.set_workspace(_workspace(database))
        _wait_idle(qt_app, backend)

        page._import_folder_dialog()
        _wait_idle(qt_app, backend)

        assert page.snapshot_model.rowCount() == 2
        snapshot_ids = {
            page.snapshot_model.row_data(row)["id"]
            for row in range(page.snapshot_model.rowCount())
        }
        assert len(snapshot_ids) == 2

        batch_result = json.loads(page.operation_status.toolTip())
        invalid_result = next(
            item for item in batch_result if item.get("input") == str(invalid_zip)
        )
        assert invalid_result["error"] == "BadZipFile"
        assert invalid_result["reason"] == "File is not a zip file"

        repository = Repository(database)
        try:
            snapshots = repository.source_store.snapshots()
            assert len(snapshots) == 2
            storage_refs = {
                Path(raw["storage_ref"])
                for snapshot in snapshots
                for raw in repository.source_store.raw_artifacts(snapshot.snapshot_id)
            }
            assert first_target in storage_refs
            assert second_target in storage_refs
        finally:
            repository.close()
    finally:
        page.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()
