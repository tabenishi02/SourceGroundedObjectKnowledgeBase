"""Explicit operator entrypoint for R2 Derived Search generation lifecycle.

This module is intentionally separate from normal read commands. It can be invoked
with ``python -m sgokb.cli.generation`` during R2-07 operational verification.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
from enum import Enum
from pathlib import Path

from sgokb.application_generation import (
    LEGACY_GENERATION_ID,
    KnowledgeSearchGenerationApplication,
)
from sgokb.repository import Repository

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


def run(arguments=None):
    args = parser().parse_args(arguments)
    repository = Repository(args.db)
    try:
        if args.action == "status":
            app = KnowledgeSearchGenerationApplication(repository)
            return app.status()

        provider, vector = semantic_runtime()
        app = KnowledgeSearchGenerationApplication(
            repository,
            embedding_provider=provider,
            vector_index=vector,
        )
        if args.action == "bootstrap":
            return app.bootstrap_legacy(reason=args.reason)
        if args.action == "build":
            return app.build_r2_candidate()
        if args.action == "cutover":
            return app.cutover(
                args.generation_id,
                reason=args.reason,
                smoke=not args.no_smoke,
            )
        if args.action == "rollback":
            return app.rollback(
                args.generation_id,
                reason=args.reason,
                smoke=not args.no_smoke,
            )
        if args.action == "recover":
            return {
                "recovered_generation_count": app.recover_interrupted_builds(reason=args.reason)
            }
        raise AssertionError(f"Unknown generation action: {args.action}")
    finally:
        repository.close()


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
