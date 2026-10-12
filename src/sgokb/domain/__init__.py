"""SGOKB domain package.

The symbols re-exported here preserve the prototype public import surface while
Phase E introduces the new Object domain contracts in dedicated modules.
"""

from ._prototype import (
    LLM,
    Block,
    Bundle,
    Embedder,
    EmbeddingSpace,
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
from .object import (
    AssignmentPolicy,
    ClassProposalStatus,
    LifecycleStatus,
    ObjectAliasRecord,
    ObjectClassRecord,
    ObjectRecord,
    ObjectRelationRecord,
    ObjectVersionRef,
    RelationTypeRecord,
    new_persistent_id,
)

__all__ = [
    "AssignmentPolicy",
    "Block",
    "Bundle",
    "ClassProposalStatus",
    "Embedder",
    "EmbeddingSpace",
    "LifecycleStatus",
    "LLM",
    "ObjectAliasRecord",
    "ObjectClassRecord",
    "ObjectRecord",
    "ObjectRelationRecord",
    "ObjectVersionRef",
    "RelationTypeRecord",
    "Reranker",
    "SearchFilter",
    "VectorIndex",
    "digest",
    "json_text",
    "new_persistent_id",
    "now",
    "uid",
    "validate_fragments",
    "validate_vectors",
]
