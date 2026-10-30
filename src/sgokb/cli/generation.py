"""Explicit operator entrypoint for R2 Derived Search generation lifecycle.

This module is intentionally separate from normal read commands. It can be invoked
with ``python -m sgokb.cli.generation``.  P-GUI-09 keeps CLI and GUI on the same
transport-neutral generation operator session.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
from enum import Enum
from pathlib import Path

from sgokb.application_generation import LEGACY_GENERATION_ID
from sgokb.application_generation_operator import GenerationOperatorSession
from sgokb.operation_contracts import OperationRequest
from sgokb.runtime import RuntimeFactory

from .runtime import semantic_runtime


def _jsonable(value):
    if dataclasses.is_dataclass(value):
        return {key: _jsonable(item) for key, item in dataclasses.asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="SGOKB R2 Knowledge Search generation operator")
    root.add_argument("--db", required=True, type=Path)
    actions = root.add_subparsers(dest="action", required=True)
    actions.add_parser("status")

    bootstrap = actions.add_parser("bootstrap")
    bootstrap.add_argument("--reason", default="R2-07 legacy bootstrap")

    actions.add_parser("build")

    cutover = actions.add_parser("cutover")
    cutover.add_argument("generation_id")
    cutover.add_argument("--reason", default="R2-07 cutover")
    cutover.add_argument("--no-smoke", action="store_true")

    rollback = actions.add_parser("rollback")
    rollback.add_argument("generation_id", nargs="?", default=LEGACY_GENERATION_ID)
    rollback.add_argument("--reason", default="R2-07 rollback rehearsal")
    rollback.add_argument("--no-smoke", action="store_true")

    recover = actions.add_parser("recover")
    recover.add_argument("--reason", default="R2-07 interrupted build recovery")
    return root


def _request(args) -> OperationRequest:
    arguments: dict[str, object] = {}
    if args.action in {"bootstrap", "cutover", "rollback", "recover"}:
        arguments["reason"] = args.reason
    if args.action in {"cutover", "rollback"}:
        arguments["generation_id"] = args.generation_id
        arguments["smoke"] = not args.no_smoke
    return OperationRequest(f"generation.{args.action}", arguments)


def run(arguments=None):
    args = parser().parse_args(arguments)
    # Keep the historical module-level ``semantic_runtime`` hook patchable for tests
    # while sharing the actual lifecycle dispatcher with the GUI.
    factory = RuntimeFactory(semantic_builder=lambda: semantic_runtime())
    outcome = GenerationOperatorSession(args.db, runtime_factory=factory).execute(_request(args))
    return outcome.data


def main() -> int:
    try:
        result = run()
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": {
                        "type": type(exc).__name__,
                        "message": str(exc),
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1
    print(json.dumps({"ok": True, "data": _jsonable(result)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
