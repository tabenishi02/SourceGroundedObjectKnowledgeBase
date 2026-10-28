"""Small reusable model for read-only dictionary rows."""

from __future__ import annotations

import json
from collections.abc import Iterable
from enum import Enum

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class DictTableModel(QAbstractTableModel):
    """Expose plain dictionary rows through Qt's model/view API."""

    def __init__(self, columns: Iterable[tuple[str, str]], parent=None) -> None:
        super().__init__(parent)
        self.columns = tuple(columns)
        self._rows: list[dict[str, object]] = []

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802 - Qt API
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802 - Qt API
        return 0 if parent.isValid() else len(self.columns)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._rows):
            return None
        row = self._rows[index.row()]
        if role == Qt.ItemDataRole.UserRole:
            return row
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        key = self.columns[index.column()][0]
        return self._display(row.get(key))

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal and section < len(self.columns):
            return self.columns[section][1]
        return str(section + 1)

    def set_rows(self, rows: Iterable[dict[str, object]]) -> None:
        self.beginResetModel()
        self._rows = [dict(row) for row in rows]
        self.endResetModel()

    def row_data(self, row: int) -> dict[str, object] | None:
        if row < 0 or row >= len(self._rows):
            return None
        return self._rows[row]

    @staticmethod
    def _display(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, Enum):
            return str(value.value)
        if isinstance(value, bool):
            return "yes" if value else "no"
        if isinstance(value, (dict, list, tuple)):
            return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        return str(value)
