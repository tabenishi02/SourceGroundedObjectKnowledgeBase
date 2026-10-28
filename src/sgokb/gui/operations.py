"""GUI transport DTOs layered over the shared operator contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from sgokb.operation_contracts import OperationRequest


@dataclass(frozen=True, slots=True)
class GuiOperationRequest:
    """Correlate one GUI request with a target Workspace and shared operation."""

    request_id: str
    workspace_path: Path
    operation: OperationRequest

    @classmethod
    def create(
        cls,
        workspace_path: str | Path,
        operation_id: str,
        arguments: dict[str, object] | None = None,
    ) -> "GuiOperationRequest":
        return cls(
            request_id=str(uuid4()),
            workspace_path=Path(workspace_path).expanduser(),
            operation=OperationRequest(operation_id, arguments or {}),
        )
