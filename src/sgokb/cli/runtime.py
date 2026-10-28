"""CLI compatibility shims for shared local runtime composition.

The canonical composition policy lives in :mod:`sgokb.runtime`. These symbols
remain patchable for existing CLI tests and downstream callers during the
transport-neutral cutover.
"""

from __future__ import annotations

import sys

from sgokb.application_read import RetrievalRuntimeUnavailableError
from sgokb.retrieval import QdrantVectorIndexAdapter, default_sentence_transformer_provider
from sgokb.runtime import RuntimeConfig, RuntimeFactory


def _base_runtime_factory() -> RuntimeFactory:
    """Build the default shared factory from CLI-module patchable factories."""

    return RuntimeFactory(
        RuntimeConfig.from_environment(),
        provider_factory=default_sentence_transformer_provider,
        vector_factory=QdrantVectorIndexAdapter,
    )


def semantic_runtime():
    """Build the frozen local semantic runtime; never fall back to cloud."""

    return _base_runtime_factory().semantic_runtime()


def build_read_application(repository, *, with_semantic: bool = False):
    return _base_runtime_factory().build_read_application(
        repository, with_semantic=with_semantic
    )


class _CliCompatibilityRuntimeFactory(RuntimeFactory):
    """Shared RuntimeFactory that honors historical CLI monkeypatch hooks.

    The hooks are presentation-adapter compatibility only. Normal execution still
    routes through the transport-neutral RuntimeFactory/Application boundary.
    """

    @staticmethod
    def _hook(name: str, default):
        module = sys.modules.get("sgokb.cli.main")
        if module is None:
            return default
        hook = getattr(module, name, default)
        return default if hook is default else hook

    def semantic_runtime(self):
        return self._hook("semantic_runtime", semantic_runtime)()

    def build_read_application(self, repository, *, with_semantic: bool = False):
        hook = self._hook("build_read_application", build_read_application)
        return hook(repository, with_semantic=with_semantic)


def runtime_factory() -> RuntimeFactory:
    """Build the CLI adapter factory while keeping shared runtime semantics."""

    return _CliCompatibilityRuntimeFactory(RuntimeConfig.from_environment())


__all__ = [
    "QdrantVectorIndexAdapter",
    "RetrievalRuntimeUnavailableError",
    "RuntimeConfig",
    "RuntimeFactory",
    "build_read_application",
    "default_sentence_transformer_provider",
    "runtime_factory",
    "semantic_runtime",
]
