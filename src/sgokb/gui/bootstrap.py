"""Composition root for the optional PySide6 desktop client."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Sequence

from PySide6.QtCore import QCoreApplication, QSettings
from PySide6.QtWidgets import QApplication

from .views import MainWindow
from .worker import BackendCoordinator
from .workspace import WorkspaceSettings


@dataclass(slots=True)
class GuiRuntime:
    app: QApplication
    backend: BackendCoordinator
    window: MainWindow


def create_runtime(
    argv: Sequence[str] | None = None,
    *,
    settings: QSettings | None = None,
    show_error_dialogs: bool = True,
) -> GuiRuntime:
    """Construct QApplication, backend lane, settings, and top-level window."""

    app = QApplication.instance()
    if app is None:
        app = QApplication(list(argv) if argv is not None else sys.argv)
    if not isinstance(app, QApplication):  # pragma: no cover - defensive embedding guard
        raise RuntimeError("A non-GUI QCoreApplication already exists")

    QCoreApplication.setOrganizationName("SGOKB")
    QCoreApplication.setOrganizationDomain("sgokb.local")
    QCoreApplication.setApplicationName("SGOKB")
    QCoreApplication.setApplicationVersion("1.1.0")

    workspace_settings = WorkspaceSettings(settings)
    backend = BackendCoordinator()
    window = MainWindow(
        backend,
        workspace_settings,
        show_error_dialogs=show_error_dialogs,
    )
    return GuiRuntime(app=app, backend=backend, window=window)
