"""P-GUI-08 Result presentation amendments for exchange records."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QModelIndex, Slot

from sgokb.operation_contracts import OperationOutcome

from .package_result_page import ResultPage as _BaseResultPage
from .package_result_page import _json_text, _mapping


class ResultPage(_BaseResultPage):
    """Normalize exchange dataclasses and preserve receipt lifecycle presentation."""

    def _apply_detected(self, outcome: OperationOutcome) -> None:
        rows: list[dict[str, object]] = []
        items = outcome.data if isinstance(outcome.data, list) else []
        for item in items:
            if isinstance(item, str):
                path = Path(item)
                rows.append({"path": item, "name": path.name, "size": None})
                continue
            row = _mapping(item)
            path = row.get("path")
            if not isinstance(path, str):
                continue
            row["name"] = Path(path).name
            row["size"] = row.get("byte_count")
            rows.append(row)
        self.detect_model.set_rows(rows)
        if rows:
            self.detect_table.selectRow(0)
        self.result_state.setText(f"State: detected {len(rows)} candidate Result file(s)")

    @Slot(QModelIndex, QModelIndex)
    def _receipt_row_changed(self, current: QModelIndex, _previous: QModelIndex) -> None:
        if not current.isValid():
            return
        row = self.receipt_model.row_data(current.row())
        if not row:
            return
        receipt_id = row.get("id")
        if isinstance(receipt_id, str):
            self.receipt_id.setText(receipt_id)
        package_id = row.get("package_id")
        if isinstance(package_id, str):
            self.package_id.setText(package_id)
        if self._review.get("review_state") == "imported":
            return
        validation = row.get("validation_state")
        intake = row.get("intake_state")
        self.result_state.setText(
            f"State: received / intake {intake} / validation {validation}"
        )
        self.review_text.setPlainText(_json_text(row))
