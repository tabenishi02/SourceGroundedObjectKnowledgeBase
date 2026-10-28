"""P-GUI-06 fixed Derivation Kind selector coverage."""

from __future__ import annotations

import os

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


def test_derivation_kind_is_fixed_selector_and_submits_schema_value(qt_app, monkeypatch):
    from PySide6.QtWidgets import QComboBox

    from sgokb.gui.views import SearchPage
    from sgokb.gui.worker import BackendCoordinator

    backend = BackendCoordinator()
    page = SearchPage(backend)
    try:
        assert isinstance(page.derivation_kind, QComboBox)
        assert not page.derivation_kind.isEditable()
        assert [
            page.derivation_kind.itemData(index)
            for index in range(page.derivation_kind.count())
        ] == [
            None,
            "direct_statement",
            "synthesis",
            "interpretation",
            "reported_view",
        ]

        captured = []

        def fake_submit(operation_id, arguments=None, *, callback=None, summary=None):
            captured.append((operation_id, dict(arguments or {}), callback, summary))
            return "request-id"

        monkeypatch.setattr(page, "submit", fake_submit)
        page.search_query.setText("test query")
        page.search_mode.setCurrentText("lexical")

        page.derivation_kind.setCurrentIndex(
            page.derivation_kind.findData("interpretation")
        )
        page.run_search()
        operation_id, arguments, _callback, _summary = captured[-1]
        assert operation_id == "search"
        assert arguments["derivation_kind"] == "interpretation"

        page.derivation_kind.setCurrentIndex(0)
        page.run_search()
        _operation_id, arguments, _callback, _summary = captured[-1]
        assert "derivation_kind" not in arguments
    finally:
        page.deleteLater()
        qt_app.processEvents()
        assert backend.shutdown()
