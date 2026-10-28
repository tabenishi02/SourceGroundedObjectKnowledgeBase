"""Transport-neutral local runtime composition for Search/Similarity/Maintenance.

The runtime is local-only and never falls back to a cloud provider.  CLI and GUI
may supply configuration differently while sharing this factory.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable

from .application_read import KnowledgeReadApplication, RetrievalRuntimeUnavailableError
from .retrieval import (
    QdrantVectorIndexAdapter,
    default_sentence_transformer_provider,
    route_generation_vector_index,
)


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    model_cache: str = ".local/models"
    model_local_only: bool = False
    qdrant_url: str = "http://localhost:6333"
    qdrant_grpc_port: int = 6334
    qdrant_prefer_grpc: bool = True
    qdrant_collection_prefix: str = "sgokb_vector"

    @classmethod
    def from_environment(cls) -> "RuntimeConfig":
        return cls(
            model_cache=os.environ.get("SGOKB_MODEL_CACHE", ".local/models"),
            model_local_only=os.environ.get("SGOKB_MODEL_LOCAL_ONLY", "0") == "1",
            qdrant_url=os.environ.get("SGOKB_QDRANT_URL", "http://localhost:6333"),
            qdrant_grpc_port=int(os.environ.get("SGOKB_QDRANT_GRPC_PORT", "6334")),
            qdrant_prefer_grpc=os.environ.get("SGOKB_QDRANT_PREFER_GRPC", "1") != "0",
            qdrant_collection_prefix=os.environ.get(
                "SGOKB_QDRANT_COLLECTION_PREFIX", "sgokb_vector"
            ),
        )


class RuntimeFactory:
    """Lazy local semantic runtime factory shared by presentation adapters."""

    def __init__(
        self,
        config: RuntimeConfig | None = None,
        *,
        provider_factory: Callable[..., object] = default_sentence_transformer_provider,
        vector_factory: Callable[..., object] = QdrantVectorIndexAdapter,
        semantic_builder: Callable[[], tuple[object, object]] | None = None,
    ) -> None:
        self.config = config or RuntimeConfig.from_environment()
        self._provider_factory = provider_factory
        self._vector_factory = vector_factory
        self._semantic_builder = semantic_builder
        self._cached_semantic: tuple[object, object] | None = None

    def semantic_runtime(self) -> tuple[object, object]:
        if self._cached_semantic is not None:
            return self._cached_semantic
        try:
            if self._semantic_builder is not None:
                pair = self._semantic_builder()
            else:
                provider = self._provider_factory(
                    cache_folder=self.config.model_cache,
                    local_files_only=self.config.model_local_only,
                )
                vector = self._vector_factory(
                    url=self.config.qdrant_url,
                    grpc_port=self.config.qdrant_grpc_port,
                    prefer_grpc=self.config.qdrant_prefer_grpc,
                    collection_prefix=self.config.qdrant_collection_prefix,
                )
                pair = (provider, vector)
        except (ImportError, RuntimeError) as exc:
            if isinstance(exc, ImportError) or isinstance(exc.__cause__, ImportError):
                raise RetrievalRuntimeUnavailableError(str(exc)) from exc
            raise
        self._cached_semantic = pair
        return pair

    def routed_semantic_runtime(self, repository) -> tuple[object, object]:
        provider, vector = self.semantic_runtime()
        return provider, route_generation_vector_index(repository, vector)

    def build_read_application(
        self, repository, *, with_semantic: bool = False
    ) -> KnowledgeReadApplication:
        if not with_semantic:
            return KnowledgeReadApplication(repository)
        provider, vector = self.routed_semantic_runtime(repository)
        return KnowledgeReadApplication(
            repository,
            embedding_provider=provider,
            vector_index=vector,
            embedding_space=provider.space,
            evidence_embedder=provider,
        )

    def clear_cache(self) -> None:
        self._cached_semantic = None
