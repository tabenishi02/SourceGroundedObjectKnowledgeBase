"""SGOKB domain package.

The symbols re-exported here preserve the prototype public import surface while
Phase E introduces the new Object domain contracts in dedicated modules.
"""

from ._prototype import (
    Block,
    Bundle,
    Embedder,
    EmbeddingSpace,
    LLM,
    Reranker,
    SearchFilter,
    VectorIndex,
    digest,
    json_text,
    now,
    uid,
    validate_fragments,
    validate_vectors,
)

__all__ = [
    "Block",
    "Bundle",
    "Embedder",
    "EmbeddingSpace",
    "LLM",
    "Reranker",
    "SearchFilter",
    "VectorIndex",
    "digest",
    "json_text",
    "now",
    "uid",
    "validate_fragments",
    "validate_vectors",
]
