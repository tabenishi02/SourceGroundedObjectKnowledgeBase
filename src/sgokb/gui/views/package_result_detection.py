"""P-GUI-08 Result detection amendment for dataclass-backed detection records."""

from __future__ import annotations

from pathlib import Path

from sgokb.operation_contracts import OperationOutcome

from .package_result_page import ResultPage as _BaseResultPage
from .package_result_page import _mapping


class ResultPage(_BaseResultPage):
    """Present DetectedResult dataclasses through the generic dictionary table."""

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
