"""P-GUI-06 Search-page amendments layered over the base implementation."""

from __future__ import annotations

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QComboBox, QFormLayout

from sgokb.gui.views.search_page import SearchPage as _BaseSearchPage
from sgokb.gui.worker import BackendCoordinator
from sgokb.operation_contracts import OperationFailure, OperationOutcome

_DERIVATION_KINDS = (
    "direct_statement",
    "synthesis",
    "interpretation",
    "reported_view",
)


class _DerivationKindCombo(QComboBox):
    """Fixed Derivation Kind selector with QLineEdit-compatible ``text`` access."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.addItem("Any", None)
        for value in _DERIVATION_KINDS:
            self.addItem(value, value)
        self.setToolTip(
            "How a Knowledge Statement was derived from Evidence. "
            "Choose Any or one of the four schema-defined Derivation Kinds."
        )

    def text(self) -> str:
        value = self.currentData()
        return value if isinstance(value, str) else ""


class SearchPage(_BaseSearchPage):
    """Search page with fixed Derivation Kind and non-stale execution state."""

    def __init__(self, backend: BackendCoordinator, parent=None) -> None:
        super().__init__(backend, parent)
        self._active_search_request_id: str | None = None
        self.backend.operation_failed.connect(self._on_search_operation_failed)

        old = self.derivation_kind
        container = old.parentWidget()
        layout = container.layout() if container is not None else None
        if not isinstance(layout, QFormLayout):
            raise RuntimeError("Derivation Kind filter must be hosted by the Hard filters form")
        row, role = layout.getWidgetPosition(old)
        if row < 0:
            raise RuntimeError("Derivation Kind filter was not found in the Hard filters form")

        selector = _DerivationKindCombo(container)
        layout.removeWidget(old)
        old.deleteLater()
        layout.setWidget(row, role, selector)
        self.derivation_kind = selector

    def run_search(self) -> str | None:
        request_id = super().run_search()
        if request_id is None:
            return None
        self._active_search_request_id = request_id
        self.search_model.set_rows([])
        self.search_detail.clear()
        self.search_runtime_state.setText(
            f"Running {self.search_mode.currentText()} search..."
        )
        return request_id

    def _apply_search(self, outcome: OperationOutcome) -> None:
        self._active_search_request_id = None
        super()._apply_search(outcome)

    @Slot(str, object)
    def _on_search_operation_failed(self, request_id: str, failure: object) -> None:
        if request_id != self._active_search_request_id:
            return
        self._active_search_request_id = None
        self.search_model.set_rows([])
        self.search_detail.clear()
        if isinstance(failure, OperationFailure):
            message = f"[{failure.category}/{failure.code}] {failure.message}"
        else:
            message = str(failure)
        self.search_runtime_state.setText(f"Search failed: {message}")
