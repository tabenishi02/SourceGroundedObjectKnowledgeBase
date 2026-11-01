"""Composition root for the optional PySide6 desktop client."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Sequence

from PySide6.QtCore import QCoreApplication, QSettings, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from sgokb.runtime import preload_local_semantic_native_dependencies

from .views import MainWindow
from .worker import BackendCoordinator
from .workspace import WorkspaceSettings


@dataclass(slots=True)
class GuiRuntime:
    app: QApplication
    backend: BackendCoordinator
    window: MainWindow
    splash: QSplashScreen | None = None


def _show_startup_splash(app: QApplication) -> QSplashScreen:
    """Show a paintable startup surface before native semantic preload begins."""

    pixmap = QPixmap(520, 180)
    pixmap.fill(app.palette().window().color())
    splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
    splash.setWindowTitle("SGOKB")
    splash.showMessage(
        "SGOKB\nStarting...",
        Qt.AlignmentFlag.AlignCenter,
        app.palette().windowText().color(),
    )
    splash.show()
    app.processEvents()
    return splash


def _update_startup_splash(
    app: QApplication,
    splash: QSplashScreen | None,
    message: str,
) -> None:
    if splash is None:
        return
    splash.showMessage(
        f"SGOKB\n{message}",
        Qt.AlignmentFlag.AlignCenter,
        app.palette().windowText().color(),
    )
    app.processEvents()


def create_runtime(
    argv: Sequence[str] | None = None,
    *,
    settings: QSettings | None = None,
    show_error_dialogs: bool = True,
    show_splash: bool = True,
) -> GuiRuntime:
    """Construct QApplication, startup splash, backend lane, settings, and window."""

    app = QApplication.instance()
    if app is None:
        app = QApplication(list(argv) if argv is not None else sys.argv)
    if not isinstance(app, QApplication):  # pragma: no cover - defensive embedding guard
        raise RuntimeError("A non-GUI QCoreApplication already exists")

    QCoreApplication.setOrganizationName("SGOKB")
    QCoreApplication.setOrganizationDomain("sgokb.local")
    QCoreApplication.setApplicationName("SGOKB")
    QCoreApplication.setApplicationVersion("1.1.0")

    splash = _show_startup_splash(app) if show_splash else None

    # Load PyTorch / Transformers / Sentence Transformers native modules on the
    # Qt main thread before BackendCoordinator starts its worker QThread. Any
    # ordinary dependency failure is cached and surfaced only if Semantic runtime
    # is requested; GUI startup itself remains available for lexical workflows.
    _update_startup_splash(app, splash, "Loading local semantic runtime...")
    preload_local_semantic_native_dependencies()

    _update_startup_splash(app, splash, "Preparing workspace UI...")
    workspace_settings = WorkspaceSettings(settings)
    backend = BackendCoordinator()
    window = MainWindow(
        backend,
        workspace_settings,
        show_error_dialogs=show_error_dialogs,
    )
    return GuiRuntime(app=app, backend=backend, window=window, splash=splash)
