"""Transport-neutral operator session for Advanced Search Generation maintenance.

The R2 generation lifecycle is deliberately outside the public ``sgokb`` 67-operation
surface, but CLI and GUI still share this boundary.  Presentation adapters must not
reimplement generation state transitions or shell out to each other.
"""

from __future__ import annotations

from pathlib import Path

from .application_generation import LEGACY_GENERATION_ID, KnowledgeSearchGenerationApplication
from .operation_contracts import OperationOutcome, OperationRequest, normalize_operation_error
from .repository import Repository
from .runtime import RuntimeFactory

GENERATION_OPERATION_IDS = frozenset(
    {
        "generation.status",
        "generation.bootstrap",
        "generation.build",
        "generation.cutover",
        "generation.rollback",
        "generation.recover",
    }
)


class GenerationOperatorSession:
    """Open a Repository per generation operation and preserve the R2 lifecycle contract."""

    def __init__(
        self,
        workspace_path: str | Path,
        *,
        runtime_factory: RuntimeFactory | None = None,
    ) -> None:
        self.workspace_path = Path(workspace_path)
        self.runtime_factory = runtime_factory or RuntimeFactory()

    def execute(self, request: OperationRequest) -> OperationOutcome:
        op = request.operation_id
        if op not in GENERATION_OPERATION_IDS:
            raise normalize_operation_error(
                op,
                ValueError(f"Unknown generation operator operation: {op}"),
            )
        try:
            repository = Repository(self.workspace_path)
            try:
                return self._execute(repository, request)
            finally:
                repository.close()
        except Exception as exc:
            raise normalize_operation_error(op, exc) from exc

    def _execute(self, repository, request: OperationRequest) -> OperationOutcome:
        op = request.operation_id
        a = dict(request.arguments)

        if op == "generation.status":
            app = KnowledgeSearchGenerationApplication(repository)
            return OperationOutcome(op, app.status())

        provider, vector = self.runtime_factory.semantic_runtime()
        app = KnowledgeSearchGenerationApplication(
            repository,
            embedding_provider=provider,
            vector_index=vector,
        )

        if op == "generation.bootstrap":
            data = app.bootstrap_legacy(reason=a.get("reason", "R2-07 legacy bootstrap"))
        elif op == "generation.build":
            data = app.build_r2_candidate()
        elif op == "generation.cutover":
            data = app.cutover(
                a["generation_id"],
                reason=a.get("reason", "R2-07 cutover"),
                smoke=bool(a.get("smoke", True)),
            )
        elif op == "generation.rollback":
            data = app.rollback(
                a.get("generation_id") or LEGACY_GENERATION_ID,
                reason=a.get("reason", "R2-07 rollback rehearsal"),
                smoke=bool(a.get("smoke", True)),
            )
        else:
            data = {
                "recovered_generation_count": app.recover_interrupted_builds(
                    reason=a.get("reason", "R2-07 interrupted build recovery")
                )
            }
        return OperationOutcome(op, data)
