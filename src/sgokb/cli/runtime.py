"""CLI compatibility shims for shared local runtime composition.

The canonical composition policy lives in :mod:`sgokb.runtime`.  These symbols
remain patchable for existing CLI tests and downstream callers during the
transport-neutral cutover.
"""

from __future__ import annotations

from sgokb.application_read import RetrievalRuntimeUnavailableError
from sgokb.retrieval import QdrantVectorIndexAdapter, default_sentence_transformer_provider
from sgokb.runtime import RuntimeConfig, RuntimeFactory


def runtime_factory() -> RuntimeFactory:
    """Build a shared RuntimeFactory using CLI-module patchable factories."""

    return RuntimeFactory(
        RuntimeConfig.from_environment(),
        provider_factory=default_sentence_transformer_provider,
        vector_factory=QdrantVectorIndexAdapter,
    )


def semantic_runtime():
    """Build the frozen local semantic runtime; never fall back to cloud."""

    return runtime_factory().semantic_runtime()


def build_read_application(repository, *, with_semantic: bool = False):
    return runtime_factory().build_read_application(repository, with_semantic=with_semantic)


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
