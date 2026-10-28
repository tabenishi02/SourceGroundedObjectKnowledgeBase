from __future__ import annotations

import os

import pytest

from sgokb.operation_contracts import OperationFailure

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _require_qt():
    pytest.importorskip("PySide6", reason="P-GUI-06 tests require the optional gui extra")


@pytest.fixture
def qt_app():
    _require_qt()
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def test_new_search_clears_previous_results_and_failure_replaces_runtime_state(
    qt_app,
    monkeypatch,
):
    from sgokb.gui.views import SearchPage
    from sgokb.gui.worker import BackendCoordinator

    backend = BackendCoordinator()
    page = SearchPage(backend)
    try:
        page.search_model.set_rows(
            [
                {
                    "rank": 1,
                    "name": "Old Result",
                    "primary_class": "character",
                    "version_id": "old-v1",
                    "fused_score": 1.0,
                    "channels": "registry_lexical",
                    "matched_facets": "",
                }
            ]
        )
        page.search_detail.setPlainText("old detail")
        page.search_runtime_state.setText("Degraded channels: semantic:RuntimeError")
        page.search_query.setText("new query")
        page.search_mode.setCurrentText("hybrid")
        page.semantic_runtime.setChecked(True)

        def fake_submit(operation_id, arguments=None, *, callback=None, summary=None):
            assert operation_id == "search"
            assert arguments["semantic_runtime"] is True
            return "search-request-1"

        monkeypatch.setattr(page, "submit", fake_submit)
        request_id = page.run_search()

        assert request_id == "search-request-1"
        assert page.search_model.rowCount() == 0
        assert page.search_detail.toPlainText() == ""
        assert page.search_runtime_state.text() == "Running hybrid search..."

        failure = OperationFailure(
            "search",
            "runtime",
            "retrieval_runtime_unavailable",
            "Vector namespace is unavailable",
        )
        page._on_search_operation_failed(request_id, failure)

        assert page.search_model.rowCount() == 0
        assert page.search_detail.toPlainText() == ""
        assert "Vector namespace is unavailable" in page.search_runtime_state.text()
        assert "semantic:RuntimeError" not in page.search_runtime_state.text()
    finally:
        page.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()
