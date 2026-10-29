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


def _optional(text: str) -> str | None:
    value = text.strip()
    return value or None


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

        # The experimental P-GUI-06 From/To range filter was removed after
        # interactive validation showed that its semantics were not reliable for
        # operator use. Keep the base widgets inert only for compatibility with
        # the layered page implementation; they are not presented and cannot
        # contribute a ``valid_at`` argument to GUI Search requests.
        for widget in (self.valid_from, self.valid_to):
            label = layout.labelForField(widget)
            if label is not None:
                label.hide()
            widget.clear()
            widget.setEnabled(False)
            widget.hide()

    def run_search(self) -> str | None:
        query = self.search_query.text().strip()
        if not query:
            self.operation_status.setText("Enter a Search query first.")
            return None

        arguments: dict[str, object] = {
            "query": query,
            "mode": self.search_mode.currentText(),
            "semantic_runtime": self.semantic_runtime.isChecked(),
            "require_full_runtime": self.require_full_runtime.isChecked(),
            "limit": self.search_limit.value(),
            "include_archived": self.include_archived.isChecked(),
        }
        if self.candidate_limit.value() > 0:
            arguments["candidate_limit"] = self.candidate_limit.value()
        for key, widget in (
            ("primary_class", self.primary_class),
            ("additional_class", self.additional_class),
            ("ancestor_class", self.ancestor_class),
            ("facet", self.facet),
            ("version", self.version),
            ("temporal_scope", self.temporal_scope),
        ):
            value = self._combo_value(widget)
            if value is not None:
                arguments[key] = value
        derivation = _optional(self.derivation_kind.text())
        if derivation is not None:
            arguments["derivation_kind"] = derivation

        request_id = self.submit(
            "search",
            arguments,
            callback=self._apply_search,
            summary=f"Searching Objects: {query}",
        )
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
