"""P-GUI-06 Derivation Kind selector amendment for the Search page."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QFormLayout

from sgokb.gui.views.search_page import SearchPage as _BaseSearchPage
from sgokb.gui.worker import BackendCoordinator

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
    """Search page with a fixed-value Derivation Kind dropdown."""

    def __init__(self, backend: BackendCoordinator, parent=None) -> None:
        super().__init__(backend, parent)
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
