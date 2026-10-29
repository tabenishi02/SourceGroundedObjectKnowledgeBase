"""P-GUI-08 MainWindow amendment for Package / Result domain pages."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from .main_window import MainWindow as _BaseMainWindow
from .package_result_page import PackagePage, ResultPage


class MainWindow(_BaseMainWindow):
    """Extend the accepted shell with P-GUI-08 Package / Result pages."""

    def _build_page(self, key: str, label: str) -> QWidget:
        if key == "packages":
            page = PackagePage(self.backend, self)
            page.set_confirmation_enabled(self.confirm_operations)
            self.domain_pages[key] = page
            return page
        if key == "results":
            page = ResultPage(self.backend, self)
            page.set_confirmation_enabled(self.confirm_operations)
            self.domain_pages[key] = page
            return page
        return super()._build_page(key, label)
