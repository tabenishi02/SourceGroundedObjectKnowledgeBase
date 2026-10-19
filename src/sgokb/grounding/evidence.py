"""Acceptance/debug evidence writer for grounded-generation runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class GroundingEvidenceLogger:
    """Persist explicit run artifacts without mutating canonical SGOKB Knowledge."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def write_json(self, relative_path: str | Path, payload: Any) -> Path:
        path = self.root / Path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def write_attempt(
        self,
        case_id: str,
        attempt: int,
        *,
        request: Any,
        response: Any,
        validation: Any,
    ) -> tuple[Path, Path, Path]:
        if attempt not in {1, 2}:
            raise ValueError("grounded-generation attempt must be 1 or 2")
        base = Path(case_id) / f"attempt-{attempt}"
        return (
            self.write_json(base / "request.json", request),
            self.write_json(base / "response.json", response),
            self.write_json(base / "validation.json", validation),
        )

    def write_v3_decision(
        self,
        case_id: str,
        attempt: int,
        *,
        material_result: Any,
        terminal_decision: Any,
        rendered_output: str | None = None,
    ) -> tuple[Path, Path, Path | None]:
        if attempt not in {1, 2}:
            raise ValueError("grounded-generation attempt must be 1 or 2")
        base = Path(case_id) / f"attempt-{attempt}"
        material_path = self.write_json(base / "material-result.json", material_result)
        terminal_path = self.write_json(base / "terminal-decision.json", terminal_decision)
        rendered_path: Path | None = None
        if rendered_output is not None:
            rendered_path = self.root / base / "rendered-response.txt"
            rendered_path.parent.mkdir(parents=True, exist_ok=True)
            rendered_path.write_text(rendered_output + "\n", encoding="utf-8")
        return material_path, terminal_path, rendered_path
