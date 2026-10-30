"""P-GUI-09 MainWindow amendment for System / Maintenance / Advanced controls."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from .main_window_package_result import MainWindow as _BaseMainWindow
from .system_page import SystemPage


class MainWindow(_BaseMainWindow):
    """Extend the accepted shell with the P-GUI-09 System page."""

    def _build_page(self, key: str, label: str) -> QWidget:
        if key == "system":
            page = SystemPage(self.backend, self)
            page.set_confirmation_enabled(self.confirm_operations)
            self.domain_pages[key] = page
            return page
        return super()._build_page(key, label)
