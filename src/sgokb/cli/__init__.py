"""Operator-facing SGOKB CLI package."""

from importlib import import_module

from .runtime import build_read_application, semantic_runtime

_main_module = import_module(".main", __name__)
_main_module.build_read_application = build_read_application
_main_module.semantic_runtime = semantic_runtime

main = _main_module.main
parser = _main_module.parser

__all__ = ["main", "parser"]
