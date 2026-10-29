"""P-GUI-08 Package / Result GUI acceptance coverage."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _require_qt():
    pytest.importorskip("PySide6", reason="P-GUI-08 tests require the optional gui extra")


@pytest.fixture
def qt_app():
    _require_qt()
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def _wait_idle(qt_app, backend, timeout_ms: int = 30000):
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
    assert not backend.is_busy, "Timed out waiting for P-GUI-08 backend operation"


def _workspace(path: Path):
    from sgokb.gui.workspace import WorkspaceState

    return WorkspaceState.opened(path, {})


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _setup_raw_object(repository, tmp_path: Path):
    object_id = repository.object_store.create_object(
        "孫悟空 P-GUI-08 acceptance",
        "class:character",
        object_id="object-pgui08-goku",
    )
    source_id = repository.source_store.create_source(
        "孫悟空 P-GUI-08 source",
        source_id="source-pgui08-goku",
    )
    locator = repository.source_store.ensure_locator(
        source_id,
        "url",
        "https://example.test/pgui08-goku",
    )
    snapshot_id = "snapshot-pgui08-goku"
    repository.source_store.create_snapshot(
        source_id,
        "2026-10-30T10:00:00Z",
        "test_fixture",
        observed_locator_id=locator,
        title="孫悟空 P-GUI-08 source",
        snapshot_id=snapshot_id,
    )
    raw = (
        "<html><body>孫悟空はドラゴンボールの主人公として描かれる"
        "架空のキャラクターである。</body></html>"
    ).encode("utf-8")
    raw_path = tmp_path / "pgui08-goku.html"
    raw_path.write_bytes(raw)
    raw_id = repository.source_store.add_raw_artifact(
        snapshot_id,
        "rendered_dom",
        str(raw_path),
        _sha256(raw),
        len(raw),
        media_type="text/html",
        artifact_id="raw-pgui08-goku",
    )
    run_id = "run-pgui08-goku"
    repository.source_store.create_normalization_run(
        snapshot_id,
        "fixture",
        "1",
        (raw_id,),
        run_id=run_id,
    )
    evidence_id = "evidence-pgui08-goku"
    repository.source_store.add_evidence(
        run_id,
        "孫悟空は架空のキャラクターである。",
        "normalized",
        evidence_id=evidence_id,
    )
    repository.source_store.select_effective_snapshot(
        source_id,
        snapshot_id,
        reason="P-GUI-08 acceptance fixture",
    )
    repository.source_store.select_effective_run(
        snapshot_id,
        run_id,
        reason="P-GUI-08 acceptance fixture",
    )
    repository.source_store.associate_object(
        source_id,
        object_id,
        "confirmed",
        subject_relationship="primary_subject",
    )
    return object_id, evidence_id


def _valid_v2_result(repository, manifest):
    target = manifest["target"]
    raw_id = manifest["raw_grounding"]["included_raw_artifact_ids"][0]
    facets = repository.semantic_store.facets_for_classes(
        (target["primary_class_id"], *target["additional_class_ids"])
    )
    return {
        "schema_version": "sgokb.object-result/2.0",
        "result_status": "complete",
        "target": {
            "object_id": target["object_id"],
            "primary_class_id": target["primary_class_id"],
            "additional_class_ids": target["additional_class_ids"],
        },
        "binding": {
            "package_id": manifest["package_id"],
            "package_schema_version": manifest["schema_version"],
            "manifest_sha256": manifest["integrity"]["manifest_sha256"],
            "package_created_at": manifest["created_at"],
            "base_version_id": manifest["binding"]["base_version_id"],
            "grounding_contract": manifest["binding"]["grounding_contract"],
            "grounding_set_sha256": manifest["raw_grounding"]["integrity"][
                "grounding_set_sha256"
            ],
        },
        "generation": {
            "instructions_version": manifest["binding"]["instructions_version"],
            "generator_kind": "interactive_ai",
            "application": "ChatGPT",
            "generated_at": "2026-10-30T10:05:00Z",
        },
        "knowledge": {
            "default_language": "ja",
            "summary": [
                {
                    "local_key": "summary-1",
                    "text": "孫悟空は架空のキャラクターである。",
                    "derivation_kind": "direct_statement",
                    "grounding": [
                        {
                            "raw_artifact_id": raw_id,
                            "role": "supports",
                            "locator": {"text_quote": "孫悟空"},
                        }
                    ],
                }
            ],
            "facets": [
                {
                    "facet_id": facet.facet_id,
                    "status": "not_analyzed",
                    "statements": [],
                }
                for facet in facets
            ],
            "attributes": [],
            "relations": [],
        },
        "conflicts": [],
        "gaps": [],
        "unresolved_references": [],
        "registry_proposals": [],
        "class_extensions": [],
    }


def test_package_gui_defaults_to_explicit_v2_without_changing_shared_default(
    qt_app,
    tmp_path,
    monkeypatch,
):
    from sgokb.gui.views import PackagePage
    from sgokb.gui.worker import BackendCoordinator

    backend = BackendCoordinator()
    page = PackagePage(backend)
    captured: list[tuple[str, dict[str, object]]] = []
    try:
        page.object_combo.addItem("GUI Object [object-1]", "object-1")

        def fake_submit(operation_id, arguments=None, **_kwargs):
            captured.append((operation_id, dict(arguments or {})))
            return "request-test"

        monkeypatch.setattr(page, "submit", fake_submit)
        page.build_package()
        assert captured[-1][0] == "package.build"
        assert captured[-1][1]["package_version"] == "v2"

        page.package_version.setCurrentIndex(1)
        page.build_package()
        assert captured[-1][1]["package_version"] == "v1"
    finally:
        page.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()


def test_raw_and_review_projection_expose_grounding_identity():
    from sgokb.gui.views.package_result_page import _grounding_rows, _raw_rows

    manifest = {
        "raw_grounding": {
            "artifacts": [
                {
                    "raw_artifact_id": "raw-1",
                    "media_type": "text/plain",
                    "byte_size": 12,
                    "sha256": "a" * 64,
                    "package_path": "raw/artifact_0001/payload",
                }
            ]
        }
    }
    rows = _raw_rows(manifest)
    assert rows[0]["raw_artifact_id"] == "raw-1"
    assert rows[0]["package_path"] == "raw/artifact_0001/payload"

    review = {
        "diff": {
            "changes": {
                "grounding": [
                    {
                        "key": "statement:summary-1",
                        "before": None,
                        "after": {
                            "kind": "raw",
                            "refs": [{"raw_artifact_id": "raw-1", "role": "supports"}],
                        },
                    }
                ]
            }
        }
    }
    grounding = _grounding_rows(review)
    assert grounding[0]["target"] == "statement:summary-1"
    assert grounding[0]["after_kind"] == "raw"
    assert grounding[0]["after_refs"][0]["raw_artifact_id"] == "raw-1"


def test_main_window_hosts_real_p_gui_08_pages(qt_app, tmp_path):
    from PySide6.QtCore import QSettings

    from sgokb.gui.views import MainWindow, PackagePage, ResultPage
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.gui.workspace import WorkspaceSettings

    backend = BackendCoordinator()
    settings = WorkspaceSettings(QSettings(str(tmp_path / "gui.ini"), QSettings.Format.IniFormat))
    window = MainWindow(
        backend,
        settings,
        show_error_dialogs=False,
        confirm_operations=False,
    )
    try:
        assert isinstance(window.domain_pages["packages"], PackagePage)
        assert isinstance(window.domain_pages["results"], ResultPage)
        assert window.domain_pages["packages"].package_version.currentData() == "v2"
    finally:
        window.close()
        qt_app.processEvents()
        assert not backend.is_busy


def test_raw_package_to_result_import_round_trip_through_gui(
    qt_app,
    tmp_path,
    monkeypatch,
):
    from sgokb.gui.views import PackagePage, ResultPage
    from sgokb.gui.worker import BackendCoordinator
    from sgokb.repository import Repository

    monkeypatch.chdir(tmp_path)
    database = tmp_path / "pgui08.sqlite"
    repository = Repository(database)
    try:
        object_id, evidence_id = _setup_raw_object(repository, tmp_path)
    finally:
        repository.close()

    backend = BackendCoordinator()
    package_page = PackagePage(backend)
    result_page = ResultPage(backend)
    try:
        package_page.set_workspace(_workspace(database))
        _wait_idle(qt_app, backend)
        index = package_page.object_combo.findData(object_id)
        assert index >= 0
        package_page.object_combo.setCurrentIndex(index)
        package_page.include_evidence.setText(evidence_id)
        assert package_page.package_version.currentData() == "v2"

        package_page.build_package()
        _wait_idle(qt_app, backend)
        assert package_page._built_path is not None
        assert package_page._manifest["schema_version"] == "sgokb.object-evidence-package/2.0"
        assert package_page.raw_model.rowCount() >= 1
        assert package_page.binding_model.rowCount() >= 1
        assert "grounding_set_sha256" in package_page.summary_text.toPlainText()

        package_page.stage_package()
        _wait_idle(qt_app, backend)
        assert package_page._staged_path is not None

        export_root = tmp_path / "external-export"
        package_page.destination.setText(str(export_root))
        package_page.preflight_package()
        _wait_idle(qt_app, backend)
        assert package_page._preflight["disposition"] == "allow"
        package_page.egress_ack.setChecked(True)
        package_page.export_package()
        _wait_idle(qt_app, backend)
        assert "exported" in package_page.flow_state.text().lower()

        repository = Repository(database)
        try:
            result = _valid_v2_result(repository, package_page._manifest)
        finally:
            repository.close()
        incoming = tmp_path / "incoming"
        drop = incoming / "drop" / package_page._manifest["package_id"]
        drop.mkdir(parents=True)
        result_path = drop / "result.json"
        result_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        result_page.set_workspace(_workspace(database))
        _wait_idle(qt_app, backend)
        result_page.incoming_root.setText(str(incoming))
        result_page.detect_results()
        _wait_idle(qt_app, backend)
        assert result_page.detect_model.rowCount() == 1
        assert result_page.result_path.text().endswith("result.json")

        result_page.package_id.setText(package_page._manifest["package_id"])
        result_page.receive_result()
        _wait_idle(qt_app, backend)
        receipt_id = result_page.receipt_id.text()
        assert receipt_id
        assert "received" in result_page.result_state.text().lower()

        result_page.validate_result()
        _wait_idle(qt_app, backend)
        assert "valid" in result_page.result_state.text().lower()

        result_page.review_result()
        _wait_idle(qt_app, backend)
        assert result_page._review["review_state"] in {"ready_to_import", "review_required"}
        assert result_page.grounding_model.rowCount() >= 1
        grounding = result_page.grounding_model.row_data(0)
        assert grounding is not None
        assert grounding["after_kind"] == "raw"
        if result_page._review["review_state"] == "review_required":
            result_page.review_ack.setChecked(True)

        result_page.import_result()
        _wait_idle(qt_app, backend)
        assert "imported" in result_page.result_state.text().lower()

        repository = Repository(database)
        try:
            current = repository.version_store.current_version_id(object_id)
            assert current is not None
            raw_links = repository.db.execute(
                "SELECT COUNT(*) AS n FROM raw_grounding_links WHERE version_id=?",
                (current,),
            ).fetchone()
            evidence_links = repository.db.execute(
                "SELECT COUNT(*) AS n FROM evidence_links WHERE version_id=?",
                (current,),
            ).fetchone()
            assert raw_links["n"] >= 1
            assert evidence_links["n"] == 0
        finally:
            repository.close()
    finally:
        package_page.deleteLater()
        result_page.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()
