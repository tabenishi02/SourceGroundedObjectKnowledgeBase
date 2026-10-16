"""Composition roots for local Search/Similarity/MCP runtime."""

from __future__ import annotations

import os

from sgokb.application_read import KnowledgeReadApplication
from sgokb.retrieval import QdrantVectorIndexAdapter, default_sentence_transformer_provider


def semantic_runtime():
    """Build the frozen Phase I local semantic runtime; never fall back to cloud."""

    provider = default_sentence_transformer_provider(
        cache_folder=os.environ.get("SGOKB_MODEL_CACHE", ".local/models"),
        local_files_only=os.environ.get("SGOKB_MODEL_LOCAL_ONLY", "0") == "1",
    )
    vector = QdrantVectorIndexAdapter(
        url=os.environ.get("SGOKB_QDRANT_URL", "http://localhost:6333"),
        grpc_port=int(os.environ.get("SGOKB_QDRANT_GRPC_PORT", "6334")),
        prefer_grpc=os.environ.get("SGOKB_QDRANT_PREFER_GRPC", "1") != "0",
        collection_prefix=os.environ.get("SGOKB_QDRANT_COLLECTION_PREFIX", "sgokb_vector"),
    )
    return provider, vector


def build_read_application(repository, *, with_semantic: bool = False):
    if not with_semantic:
        return KnowledgeReadApplication(repository)
    provider, vector = semantic_runtime()
    return KnowledgeReadApplication(
        repository,
        embedding_provider=provider,
        vector_index=vector,
        embedding_space=provider.space,
        evidence_embedder=provider,
    )
