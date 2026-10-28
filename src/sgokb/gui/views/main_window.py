"""P-GUI QMainWindow shell, Workspace controls, and domain navigation."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from sgokb.gui.controllers import WorkspaceController
from sgokb.gui.views.association_page import AssociationPage
from sgokb.gui.views.evidence_page import EvidencePage
from sgokb.gui.views.object_page import ObjectPage
from sgokb.gui.views.operation_page import OperationPage
from sgokb.gui.views.registry_page import RegistryPage
from sgokb.gui.views.search_page import SearchPage
from sgokb.gui.views.source_page import SourcePage
from sgokb.gui.worker import BackendCoordinator
from sgokb.gui.workspace import WorkspaceSettings, WorkspaceState
from sgokb.operation_contracts import OperationFailure

NAVIGATION_ITEMS = (
    ("home", "Home / Dashboard"),
    ("objects", "Objects"),
    ("sources", "Sources"),
    ("evidence", "Evidence"),
    ("associations", "Associations"),
    ("search", "Search"),
    ("packages", "Packages"),
    ("results", "Results"),
    ("registry", "Registry"),
    ("system", "System"),
    ("settings", "Settings"),
)

_PAGE_DESCRIPTIONS = {
    "packages": "Package workflow is implemented after P-RAW in P-GUI-08.",
    "results": "Result workflow is implemented after P-RAW in P-GUI-08.",
    "system": "System / Maintenance controls are implemented in P-GUI-09.",
    "settings": "Presentation settings will expand as later GUI tasks land.",
}


class MainWindow(QMainWindow):
    """SGOKB desktop shell with safe Workspace activation and domain pages."""

    def __init__(
        self,
        backend: BackendCoordinator,
        settings: WorkspaceSettings,
        *,
        show_error_dialogs: bool = True,
    ) -> None:
        super().__init__()
        self.backend = backend
        self.settings = settings
        self.show_error_dialogs = show_error_dialogs
        self.workspace_controller = WorkspaceController(backend, settings, self)
        self._page_index: dict[str, int] = {}
        self.domain_pages: dict[str, OperationPage] = {}
        self._workspace = WorkspaceState.closed()

        self.setWindowTitle("SGOKB")
        self.resize(1180, 760)
        self._build_actions()
        self._build_menu()
        self._build_shell()
        self._connect_signals()
        self._restore_ui_state()
        self._apply_workspace_state(self._workspace)

    def _build_actions(self) -> None:
        self.open_action = QAction("Open Workspace...", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self._choose_existing_workspace)

        self.new_action = QAction("Create Workspace...", self)
        self.new_action.setShortcut("Ctrl+N")
        self.new_action.triggered.connect(self._choose_new_workspace)

        self.exit_action = QAction("Exit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        self.recent_menu = QMenu("Recent Workspaces", self)
        file_menu.addMenu(self.recent_menu)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        self._refresh_recent_menu()

    def _build_shell(self) -> None:
        root = QWidget(self)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.warning_label = QLabel(root)
        self.warning_label.setWordWrap(True)
        self.warning_label.setVisible(False)
        self.warning_label.setStyleSheet(
            "QLabel { padding: 8px; background: palette(alternate-base); font-weight: 600; }"
        )
        root_layout.addWidget(self.warning_label)

        body = QWidget(root)
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.navigation = QListWidget(body)
        self.navigation.setMinimumWidth(190)
        self.navigation.setMaximumWidth(260)
        for key, label in NAVIGATION_ITEMS:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.navigation.addItem(item)
        body_layout.addWidget(self.navigation)

        self.pages = QStackedWidget(body)
        for index, (key, label) in enumerate(NAVIGATION_ITEMS):
            self._page_index[key] = index
            page = self._build_page(key, label)
            self.pages.addWidget(page)
        body_layout.addWidget(self.pages, 1)
        root_layout.addWidget(body, 1)
        self.setCentralWidget(root)

        self.workspace_status = QLabel("No workspace")
        self.statusBar().addPermanentWidget(self.workspace_status)

    def _build_page(self, key: str, label: str) -> QWidget:
        if key == "home":
            return self._build_home_page()
        page: OperationPage | None = None
        if key == "objects":
            page = ObjectPage(self.backend, self)
        elif key == "sources":
            page = SourcePage(self.backend, self)
        elif key == "evidence":
            page = EvidencePage(self.backend, self)
        elif key == "associations":
            page = AssociationPage(self.backend, self)
        elif key == "search":
            page = SearchPage(self.backend, self)
        elif key == "registry":
            page = RegistryPage(self.backend, self)
        if page is not None:
            self.domain_pages[key] = page
            return page
        return self._build_placeholder(label, key)

    def _build_home_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title = QLabel("SGOKB Dashboard", page)
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(title)

        self.home_workspace = QLabel("Workspace: not open", page)
        self.home_workspace.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.home_workspace)

        self.home_summary = QLabel("Open or create a Workspace to inspect its status.", page)
        self.home_summary.setWordWrap(True)
        layout.addWidget(self.home_summary)

        actions = QWidget(page)
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        open_button = QPushButton("Open Workspace...", actions)
        open_button.clicked.connect(self._choose_existing_workspace)
        new_button = QPushButton("Create Workspace...", actions)
        new_button.clicked.connect(self._choose_new_workspace)
        actions_layout.addWidget(open_button)
        actions_layout.addWidget(new_button)
        actions_layout.addStretch(1)
        layout.addWidget(actions)
        layout.addStretch(1)
        return page

    def _build_placeholder(self, label: str, key: str) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        title = QLabel(label, page)
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        description = QLabel(_PAGE_DESCRIPTIONS[key], page)
        description.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch(1)
        return page

    def _connect_signals(self) -> None:
        self.navigation.currentRowChanged.connect(self._on_navigation_changed)
        self.workspace_controller.state_changed.connect(self._apply_workspace_state)
        self.workspace_controller.open_failed.connect(self._on_workspace_failed)
        self.backend.operation_warning.connect(self._on_backend_warning)
        self.backend.busy_changed.connect(self._on_busy_changed)

    def _restore_ui_state(self) -> None:
        geometry = self.settings.window_geometry()
        if geometry:
            self.restoreGeometry(geometry)
        state = self.settings.window_state()
        if state:
            self.restoreState(state)
        target = self.settings.last_page()
        row = self._page_index.get(target, self._page_index["home"])
        self.navigation.setCurrentRow(row)

    @Slot(int)
    def _on_navigation_changed(self, row: int) -> None:
        if row < 0 or row >= len(NAVIGATION_ITEMS):
            return
        self.pages.setCurrentIndex(row)
        key = str(self.navigation.item(row).data(Qt.ItemDataRole.UserRole))
        self.settings.save_last_page(key)

    def _choose_existing_workspace(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open SGOKB Workspace",
            "",
            "SQLite databases (*.sqlite *.db);;All files (*)",
        )
        if path:
            self.open_workspace(path)

    def _choose_new_workspace(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Create SGOKB Workspace",
            "sgokb.sqlite",
            "SQLite databases (*.sqlite *.db);;All files (*)",
        )
        if not path:
            return
        candidate = Path(path)
        if candidate.exists():
            self._show_failure(
                "Workspace already exists",
                (
                    "Use Open Workspace for an existing database; "
                    "Create Workspace never overwrites it."
                ),
            )
            return
        self.open_workspace(candidate)

    def open_workspace(self, path: str | Path) -> str | None:
        self._clear_warning()
        request_id = self.workspace_controller.open_workspace(path)
        if request_id is not None:
            self.statusBar().showMessage(f"Opening Workspace: {Path(path)}")
        return request_id

    @Slot(object)
    def _apply_workspace_state(self, state: WorkspaceState) -> None:
        self._workspace = state
        self._clear_warning()
        for page in self.domain_pages.values():
            page.set_workspace(state)
        if not state.is_open or state.db_path is None:
            self.workspace_status.setText("No workspace")
            self.home_workspace.setText("Workspace: not open")
            self.home_summary.setText("Open or create a Workspace to inspect its status.")
            return

        path_text = str(state.db_path)
        self.workspace_status.setText(path_text)
        self.home_workspace.setText(f"Workspace: {path_text}")
        objects = state.status.get("objects", {})
        migrations = state.status.get("schema_migrations", [])
        if isinstance(objects, dict):
            count = objects.get("count", "?")
            current = objects.get("with_current_version", "?")
        else:
            count = current = "?"
        migration_count = len(migrations) if isinstance(migrations, list) else "?"
        self.home_summary.setText(
            f"Objects: {count} | Objects with current Knowledge: {current} | "
            f"Applied migrations: {migration_count}"
        )
        self.statusBar().showMessage("Workspace ready", 3000)
        self.setWindowTitle(f"SGOKB — {state.display_label}")
        self._refresh_recent_menu()

    @Slot(str, object)
    def _on_workspace_failed(self, path: str, failure: object) -> None:
        if isinstance(failure, OperationFailure):
            message = f"[{failure.category}/{failure.code}] {failure.message}"
        else:
            message = str(failure)
        self._set_warning(f"Failed to open Workspace {path}: {message}")
        self.statusBar().showMessage("Workspace open failed", 5000)
        if self.show_error_dialogs:
            QMessageBox.critical(self, "Workspace open failed", message)

    @Slot(str, str)
    def _on_backend_warning(self, _request_id: str, message: str) -> None:
        self._set_warning(message)

    @Slot(bool)
    def _on_busy_changed(self, busy: bool) -> None:
        self.open_action.setEnabled(not busy)
        self.new_action.setEnabled(not busy)
        if busy:
            self.statusBar().showMessage("Backend operation running...")

    def _set_warning(self, message: str) -> None:
        self.warning_label.setText(message)
        self.warning_label.setVisible(True)

    def _clear_warning(self) -> None:
        self.warning_label.clear()
        self.warning_label.setVisible(False)

    def _show_failure(self, title: str, message: str) -> None:
        self._set_warning(message)
        if self.show_error_dialogs:
            QMessageBox.warning(self, title, message)

    def _refresh_recent_menu(self) -> None:
        self.recent_menu.clear()
        recent = self.settings.recent_paths()
        if not recent:
            empty = self.recent_menu.addAction("No recent Workspaces")
            empty.setEnabled(False)
            return
        for path in recent:
            action = self.recent_menu.addAction(str(path))
            action.triggered.connect(
                lambda _checked=False, selected=path: self.open_workspace(selected)
            )

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - Qt API
        if self.backend.is_busy:
            self._show_failure(
                "Operation in progress",
                "The application cannot close while a backend operation is running.",
            )
            event.ignore()
            return
        self.settings.save_window(self.saveGeometry(), self.saveState())
        if not self.backend.shutdown():
            self._show_failure(
                "Backend shutdown incomplete",
                "The backend thread did not stop cleanly; the window will remain open.",
            )
            event.ignore()
            return
        event.accept()
