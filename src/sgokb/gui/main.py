"""GUI launcher with only startup/event-loop responsibilities."""

from __future__ import annotations

import sys
from typing import Sequence

from .bootstrap import create_runtime


def main(argv: Sequence[str] | None = None) -> int:
    try:
        runtime = create_runtime(argv)
    except Exception as exc:  # pragma: no cover - startup guard
        print(f"SGOKB GUI startup failed: {exc}", file=sys.stderr)
        return 1
    runtime.window.show()
    runtime.app.processEvents()
    if runtime.splash is not None:
        runtime.splash.finish(runtime.window)
    return int(runtime.app.exec())


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
