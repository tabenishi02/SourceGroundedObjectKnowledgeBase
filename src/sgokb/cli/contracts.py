"""Stable CLI output/error contract for Phase M."""

from __future__ import annotations

import dataclasses
import enum
import json
import sys
from pathlib import Path

SCHEMA_VERSION = "sgokb.cli/1.0"

EXIT_SUCCESS = 0
EXIT_INTERNAL = 1
EXIT_INPUT = 2
EXIT_NOT_FOUND = 3
EXIT_BLOCKED = 4
EXIT_RUNTIME = 5
EXIT_IO = 6
EXIT_INTEGRITY = 7
EXIT_PARTIAL = 8


def jsonable(value):
    if dataclasses.is_dataclass(value):
        return {key: jsonable(item) for key, item in dataclasses.asdict(value).items()}
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(item) for item in value]
    return value


def emit_success(
    command: str, data, *, warnings=(), output_format: str = "json", exit_code: int = EXIT_SUCCESS
) -> int:
    data = jsonable(data)
    warnings = [str(item) for item in warnings]
    if output_format == "text":
        if isinstance(data, str):
            print(data)
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        if warnings:
            print("\nWarnings:", file=sys.stderr)
            for warning in warnings:
                print(f"- {warning}", file=sys.stderr)
        return exit_code
    payload = {
        "schema_version": SCHEMA_VERSION,
        "ok": True,
        "command": command,
        "data": data,
        "warnings": warnings,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return exit_code


def emit_error(
    command: str,
    code: str,
    message: str,
    *,
    details=None,
    exit_code: int = EXIT_INTERNAL,
    output_format: str = "json",
) -> int:
    if output_format == "text":
        print(f"{code}: {message}", file=sys.stderr)
        if details:
            print(json.dumps(jsonable(details), ensure_ascii=False, indent=2), file=sys.stderr)
        return exit_code
    payload = {
        "schema_version": SCHEMA_VERSION,
        "ok": False,
        "command": command,
        "error": {
            "code": code,
            "message": message,
            "details": jsonable(details or {}),
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
    return exit_code
