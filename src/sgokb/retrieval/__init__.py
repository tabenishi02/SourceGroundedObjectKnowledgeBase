"""Canonical retrieval capabilities."""

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
from .evidence import EvidenceCandidate, EvidenceSelectionReason, ObjectEvidenceRetriever
from .evidence_search import (
    EvidenceSearch,
    EvidenceSearchMode,
    EvidenceSearchResponse,
    EvidenceSearchResult,
)
from .evaluation import (
    ExactVectorIndexAdapter,
    aggregate_metric_rows,
    ann_recall_at_k,
    latency_summary,
    ranked_retrieval_metrics,
)
from .hybrid_search import HybridObjectSearch, KnowledgeVectorIndexBuilder
from .package import (
    EvidenceBudget,
    EvidencePackageSelector,
    OmittedEvidence,
    SelectedEvidence,
    estimate_tokens,
)
from .search_representation import BuiltSearchRepresentation, SearchRepresentationBuilder
from .similarity import ObjectSimilaritySearch

__all__ = [
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

from .vector_index import (
    DEFAULT_QDRANT_EF_CONSTRUCT,
    DEFAULT_QDRANT_FULL_SCAN_THRESHOLD,
    DEFAULT_QDRANT_HNSW_M,
    DEFAULT_QDRANT_INDEXING_THRESHOLD,
    DEFAULT_QDRANT_SEARCH_EF,
    DEFAULT_VECTOR_INDEX_BACKEND,
    QdrantVectorIndexAdapter,
)
