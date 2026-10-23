"""Canonical retrieval capabilities."""

from .context_builder import (
    CONTEXT_BUILDER_CONTRACT_VERSION,
    CONTEXT_DEFAULT_MAX_CHARACTERS,
    CONTEXT_MAX_CHARACTERS,
    CONTEXT_MAX_OBJECTS,
    CONTEXT_PURPOSE_PROFILES,
    ContextBuilder,
    ContextPurposeProfile,
    context_facets_for_purpose,
    context_purpose_profile,
)
from .embedding import (
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_EMBEDDING_MAX_SEQUENCE_LENGTH,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_REVISION,
    DEFAULT_RETRIEVAL_INSTRUCTION,
    FastEmbedEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
    default_sentence_transformer_provider,
    exact_cosine_scores,
)
from .evaluation import (
    ExactVectorIndexAdapter,
    aggregate_metric_rows,
    ann_recall_at_k,
    latency_summary,
    ranked_retrieval_metrics,
)
from .evidence import EvidenceCandidate, EvidenceSelectionReason, ObjectEvidenceRetriever
from .evidence_search import (
    EvidenceSearch,
    EvidenceSearchMode,
    EvidenceSearchResponse,
    EvidenceSearchResult,
)
from .hybrid_search_r2 import HybridObjectSearch
from .package import (
    EvidenceBudget,
    EvidencePackageSelector,
    OmittedEvidence,
    SelectedEvidence,
    estimate_tokens,
)
from .search_representation import BuiltSearchRepresentation, SearchRepresentationBuilder
from .similarity_r2 import ObjectSimilaritySearch
from .vector_index import (
    DEFAULT_QDRANT_EF_CONSTRUCT,
    DEFAULT_QDRANT_FULL_SCAN_THRESHOLD,
    DEFAULT_QDRANT_HNSW_M,
    DEFAULT_QDRANT_INDEXING_THRESHOLD,
    DEFAULT_QDRANT_SEARCH_EF,
    DEFAULT_VECTOR_INDEX_BACKEND,
    QdrantVectorIndexAdapter,
)
from .vector_maintenance import KnowledgeVectorMaintenanceBuilder

KnowledgeVectorIndexBuilder = KnowledgeVectorMaintenanceBuilder

__all__ = [
    "CONTEXT_BUILDER_CONTRACT_VERSION",
    "CONTEXT_DEFAULT_MAX_CHARACTERS",
    "CONTEXT_MAX_CHARACTERS",
    "CONTEXT_MAX_OBJECTS",
    "CONTEXT_PURPOSE_PROFILES",
    "ContextBuilder",
    "ContextPurposeProfile",
    "context_facets_for_purpose",
    "context_purpose_profile",
    "DEFAULT_EMBEDDING_DIMENSION",
    "DEFAULT_EMBEDDING_MAX_SEQUENCE_LENGTH",
    "DEFAULT_EMBEDDING_MODEL",
    "DEFAULT_EMBEDDING_REVISION",
    "DEFAULT_RETRIEVAL_INSTRUCTION",
    "default_sentence_transformer_provider",
    "FastEmbedEmbeddingProvider",
    "SentenceTransformerEmbeddingProvider",
    "exact_cosine_scores",
    "ExactVectorIndexAdapter",
    "aggregate_metric_rows",
    "ann_recall_at_k",
    "latency_summary",
    "ranked_retrieval_metrics",
    "HybridObjectSearch",
    "KnowledgeVectorIndexBuilder",
    "KnowledgeVectorMaintenanceBuilder",
    "EvidenceBudget",
    "EvidenceCandidate",
    "EvidencePackageSelector",
    "EvidenceSearch",
    "EvidenceSearchMode",
    "EvidenceSearchResponse",
    "EvidenceSearchResult",
    "EvidenceSelectionReason",
    "ObjectEvidenceRetriever",
    "OmittedEvidence",
    "SelectedEvidence",
    "BuiltSearchRepresentation",
    "SearchRepresentationBuilder",
    "ObjectSimilaritySearch",
    "DEFAULT_QDRANT_EF_CONSTRUCT",
    "DEFAULT_QDRANT_FULL_SCAN_THRESHOLD",
    "DEFAULT_QDRANT_HNSW_M",
    "DEFAULT_QDRANT_INDEXING_THRESHOLD",
    "DEFAULT_QDRANT_SEARCH_EF",
    "DEFAULT_VECTOR_INDEX_BACKEND",
    "QdrantVectorIndexAdapter",
    "estimate_tokens",
]
