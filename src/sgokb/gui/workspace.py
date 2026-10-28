"""Presentation-only Workspace state and Qt settings persistence."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from PySide6.QtCore import QSettings


@dataclass(frozen=True, slots=True)
class WorkspaceState:
    """Noncanonical active-workspace presentation state."""

    db_path: Path | None = None
    display_label: str = "No workspace"
    is_open: bool = False
    status: Mapping[str, object] = field(default_factory=dict)

    @classmethod
    def closed(cls) -> "WorkspaceState":
        return cls()

    @classmethod
    def opened(cls, path: str | Path, status: Mapping[str, object]) -> "WorkspaceState":
        resolved = Path(path).expanduser().resolve()
        return cls(
            db_path=resolved,
            display_label=resolved.name or str(resolved),
            is_open=True,
            status=dict(status),
        )


class WorkspaceSettings:
    """Persist presentation-only workspace/window preferences through QSettings."""

    RECENT_KEY = "workspace/recent_paths"
    LAST_KEY = "workspace/last_path"
    GEOMETRY_KEY = "window/geometry"
    STATE_KEY = "window/state"
    PAGE_KEY = "navigation/last_page"

    def __init__(self, settings: QSettings | None = None, *, recent_limit: int = 10) -> None:
        self.settings = settings or QSettings()
        self.recent_limit = recent_limit

    def recent_paths(self) -> tuple[Path, ...]:
        raw = self.settings.value(self.RECENT_KEY, [])
        if raw is None:
            return ()
        if isinstance(raw, str):
            values = [raw]
        else:
            values = list(raw)
        result: list[Path] = []
        seen: set[str] = set()
        for value in values:
            text = str(value).strip()
            if not text:
                continue
            path = Path(text).expanduser()
            key = str(path).casefold()
            if key in seen:
                continue
            seen.add(key)
            result.append(path)
        return tuple(result[: self.recent_limit])

    def record_workspace(self, path: str | Path) -> None:
        resolved = Path(path).expanduser().resolve()
        merged = [resolved]
        merged.extend(item for item in self.recent_paths() if item != resolved)
        self.settings.setValue(self.RECENT_KEY, [str(item) for item in merged[: self.recent_limit]])
        self.settings.setValue(self.LAST_KEY, str(resolved))
        self.settings.sync()

    def last_workspace(self) -> Path | None:
        value = str(self.settings.value(self.LAST_KEY, "")).strip()
        return Path(value) if value else None

    def save_window(self, geometry: bytes, state: bytes) -> None:
        self.settings.setValue(self.GEOMETRY_KEY, geometry)
        self.settings.setValue(self.STATE_KEY, state)

    def window_geometry(self):
        return self.settings.value(self.GEOMETRY_KEY)

    def window_state(self):
        return self.settings.value(self.STATE_KEY)

    def save_last_page(self, page_key: str) -> None:
        self.settings.setValue(self.PAGE_KEY, page_key)

    def last_page(self, default: str = "home") -> str:
        return str(self.settings.value(self.PAGE_KEY, default))
