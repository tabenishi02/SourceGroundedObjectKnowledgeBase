"""Transport-neutral Knowledge Access application boundary for Phase J / J-01.

CLI, MCP and future clients should use this module instead of reaching into
SQLite repositories or Phase I retrieval implementations directly. Runtime
providers/indexes are injected here, outside every transport adapter.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from .domain import ObjectSearchFilters, ObjectSearchMode
from .retrieval import HybridObjectSearch, ObjectEvidenceRetriever, ObjectSimilaritySearch
from .retrieval.object_read import ObjectKnowledgeReader

APPLICATION_READ_CONTRACT_VERSION = "sgokb.application-read.v1"


class KnowledgeAccessError(RuntimeError):
    """Base error that a transport may map without knowing storage/backend details."""

    code = "knowledge_access_error"


class RetrievalRuntimeUnavailableError(KnowledgeAccessError):
    """Required local retrieval runtime dependency was not configured."""

    code = "retrieval_runtime_unavailable"


class KnowledgeReadApplication:
    """One read boundary shared by CLI, MCP and other SGOKB clients.

    The class owns composition of the Retrieval Core. It deliberately does not
    construct embedding providers, Vector Index backends, network transports or
    MCP servers. Those runtime dependencies must be supplied by the composition
    root and may therefore fail explicitly rather than silently switching backend.
    """

    contract_version = APPLICATION_READ_CONTRACT_VERSION

    def __init__(
        self,
        repository,
        *,
        embedding_provider=None,
        vector_index=None,
        embedding_space=None,
        evidence_embedder=None,
    ) -> None:
        self._repository = repository
        self._embedding_provider = embedding_provider
        self._vector_index = vector_index
        self._embedding_space = embedding_space
        self._evidence_embedder = evidence_embedder
        self._object_reader = ObjectKnowledgeReader(repository)

    def search_objects(
        self,
        query: str,
        *,
        filters: ObjectSearchFilters = ObjectSearchFilters(),
        limit: int = 10,
        mode: ObjectSearchMode | str = ObjectSearchMode.HYBRID,
        candidate_limit: int | None = None,
    ):
        """Run the canonical Phase I Object Search through the Application boundary."""

        return HybridObjectSearch(
            self._repository,
            embedding_provider=self._embedding_provider,
            vector_index=self._vector_index,
        ).search(
            query,
            filters=filters,
            limit=limit,
            mode=mode,
            candidate_limit=candidate_limit,
        )

    def find_similar_objects(
        self,
        object_id: str,
        *,
        facet: str | None = None,
        limit: int = 10,
        cross_class: bool = False,
        source_version_id: str | None = None,
        include_archived: bool = False,
    ):
        """Run canonical overall/Facet similarity with explicitly injected runtime."""

        if self._embedding_space is None or self._vector_index is None:
            raise RetrievalRuntimeUnavailableError(
                "Object similarity requires an injected Embedding Space and Vector Index"
            )
        return ObjectSimilaritySearch(
            self._repository,
            space=self._embedding_space,
            vector_index=self._vector_index,
        ).find_similar_objects(
            object_id,
            facet=facet,
            limit=limit,
            cross_class=cross_class,
            source_version_id=source_version_id,
            include_archived=include_archived,
        )

    def get_object(
        self,
        object_id: str,
        *,
        version_id: str | None = None,
        facets: Iterable[str] | None = None,
        include_relations: bool = True,
        include_evidence_refs: bool = True,
    ) -> dict:
        """Read current or explicitly pinned accepted Object Knowledge."""

        payload = self._object_reader.get_object(
            object_id,
            version_id=version_id,
            facets=facets,
            include_relations=include_relations,
            include_evidence_refs=include_evidence_refs,
        )
        return {"contract_version": self.contract_version, **payload}

    def get_objects(
        self,
        object_ids: Iterable[str],
        *,
        version_ids: dict[str, str] | None = None,
        facets: Iterable[str] | None = None,
        include_relations: bool = True,
        include_evidence_refs: bool = True,
    ) -> dict:
        """Read multiple Objects through the same single-Object contract.

        Order is preserved and duplicate IDs are preserved intentionally so an
        upstream caller can correlate responses without relying on DB ordering.
        """

        version_ids = version_ids or {}
        objects = [
            self.get_object(
                object_id,
                version_id=version_ids.get(object_id),
                facets=facets,
                include_relations=include_relations,
                include_evidence_refs=include_evidence_refs,
            )
            for object_id in object_ids
        ]
        return {"contract_version": self.contract_version, "objects": objects}

    def get_object_relations(
        self,
        object_id: str,
        *,
        version_id: str | None = None,
        include_evidence_refs: bool = True,
    ) -> dict:
        payload = self._object_reader.get_relations(
            object_id,
            version_id=version_id,
            include_evidence_refs=include_evidence_refs,
        )
        return {"contract_version": self.contract_version, **payload}

    def get_object_evidence(
        self,
        object_id: str,
        *,
        max_candidates: int = 500,
        semantic: bool | None = None,
        semantic_batch_size: int = 32,
        manual_include: Iterable[str] = (),
        manual_exclude: Iterable[str] = (),
    ) -> dict:
        """Expose canonical Evidence retrieval without exposing Source/SQLite storage."""

        result = ObjectEvidenceRetriever(
            self._repository,
            self._evidence_embedder,
        ).retrieve(
            object_id,
            max_candidates=max_candidates,
            semantic=semantic,
            semantic_batch_size=semantic_batch_size,
            manual_include=manual_include,
            manual_exclude=manual_exclude,
        )
        return {
            "contract_version": self.contract_version,
            **result,
            "candidates": [asdict(candidate) for candidate in result["candidates"]],
        }
