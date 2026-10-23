"""Transport-neutral Knowledge Access application boundary for Phase J.

CLI, MCP and future clients should use this module instead of reaching into
SQLite repositories or Phase I retrieval implementations directly. Runtime
providers/indexes are injected here, outside every transport adapter.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from .domain import ObjectSearchFilters, ObjectSearchMode
from .retrieval import (
    EvidenceSearch,
    EvidenceSearchMode,
    HybridObjectSearch,
    ObjectEvidenceRetriever,
    ObjectSimilaritySearch,
)
from .retrieval.context_builder import (
    CONTEXT_DEFAULT_MAX_CHARACTERS,
    CONTEXT_MAX_OBJECTS,
    ContextBuilder,
    context_facets_for_purpose,
    context_purpose_profile,
)
from .retrieval.object_read import ObjectKnowledgeReader

APPLICATION_READ_CONTRACT_VERSION = "sgokb.application-read.v1"


class KnowledgeRequestError(ValueError):
    """Invalid transport-neutral Knowledge request."""

    code = "invalid_knowledge_request"


class RetrievalRuntimeUnavailableError(RuntimeError):
    """Required local retrieval runtime dependency was unavailable or not configured."""

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
        from .retrieval.generation import route_generation_vector_index

        self._vector_index = route_generation_vector_index(repository, vector_index)
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

        try:
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
        except ValueError as exc:
            raise KnowledgeRequestError(str(exc)) from exc
        except RuntimeError as exc:
            raise RetrievalRuntimeUnavailableError(str(exc)) from exc

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
        try:
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
        except ValueError as exc:
            raise KnowledgeRequestError(str(exc)) from exc
        except RuntimeError as exc:
            raise RetrievalRuntimeUnavailableError(str(exc)) from exc

    def build_context(
        self,
        object_ids: Iterable[str],
        *,
        purpose: str = "general",
        version_ids: dict[str, str] | None = None,
        facets: Iterable[str] | None = None,
        max_characters: int = CONTEXT_DEFAULT_MAX_CHARACTERS,
        include_attributes: bool | None = None,
        include_relations: bool | None = None,
        include_evidence_refs: bool | None = None,
    ) -> dict:
        """Build deterministic purpose-scoped Knowledge context without LLM inference."""

        ids = tuple(object_ids)
        if not ids:
            raise KnowledgeRequestError("Context Builder requires at least one Object")
        if len(ids) > CONTEXT_MAX_OBJECTS:
            raise KnowledgeRequestError(
                f"Context Builder supports at most {CONTEXT_MAX_OBJECTS} Objects"
            )
        if len(set(ids)) != len(ids):
            raise KnowledgeRequestError("Context Builder object_ids must be unique")
        version_ids = version_ids or {}
        unknown_version_keys = sorted(set(version_ids) - set(ids))
        if unknown_version_keys:
            raise KnowledgeRequestError(
                "version_ids contains Objects outside object_ids: "
                + ", ".join(unknown_version_keys)
            )

        try:
            profile = context_purpose_profile(purpose)
            selected_facets = context_facets_for_purpose(purpose, facets)
        except ValueError as exc:
            raise KnowledgeRequestError(str(exc)) from exc
        resolved_relations = (
            profile.include_relations if include_relations is None else include_relations
        )
        resolved_evidence = (
            profile.include_evidence_refs
            if include_evidence_refs is None
            else include_evidence_refs
        )

        objects = [
            self.get_object(
                object_id,
                version_id=version_ids.get(object_id),
                facets=selected_facets,
                include_relations=resolved_relations,
                include_evidence_refs=resolved_evidence,
            )
            for object_id in ids
        ]
        try:
            return ContextBuilder().build(
                objects,
                purpose=purpose,
                facets=facets,
                max_characters=max_characters,
                include_attributes=include_attributes,
                include_relations=include_relations,
                include_evidence_refs=include_evidence_refs,
            )
        except ValueError as exc:
            raise KnowledgeRequestError(str(exc)) from exc

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

        try:
            payload = self._object_reader.get_object(
                object_id,
                version_id=version_id,
                facets=facets,
                include_relations=include_relations,
                include_evidence_refs=include_evidence_refs,
            )
        except ValueError as exc:
            raise KnowledgeRequestError(str(exc)) from exc
        requested_scope = payload.pop("scope")
        return {
            "contract_version": self.contract_version,
            **payload,
            "requested_scope": requested_scope,
        }

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
        try:
            payload = self._object_reader.get_relations(
                object_id,
                version_id=version_id,
                include_evidence_refs=include_evidence_refs,
            )
        except ValueError as exc:
            raise KnowledgeRequestError(str(exc)) from exc
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
        """Expose Object-oriented Evidence retrieval without exposing storage."""

        try:
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
        except ValueError as exc:
            raise KnowledgeRequestError(str(exc)) from exc
        except RuntimeError as exc:
            raise RetrievalRuntimeUnavailableError(str(exc)) from exc
        return {
            "contract_version": self.contract_version,
            **result,
            "candidates": [asdict(candidate) for candidate in result["candidates"]],
        }

    def get_evidence(self, evidence_id: str) -> dict:
        """Read one canonical Evidence record with its provenance chain."""

        try:
            provenance = self._repository.source_store.evidence_provenance(evidence_id)
            context = self._repository.source_store.evidence_context(evidence_id)
        except ValueError as exc:
            raise KnowledgeRequestError(str(exc)) from exc
        return {
            "contract_version": self.contract_version,
            "evidence": asdict(provenance.evidence),
            "snapshot": asdict(provenance.snapshot),
            "source": asdict(provenance.source),
            "raw_artifact_ids": list(provenance.raw_artifact_ids),
            "context": context,
        }

    def search_evidence(
        self,
        query: str,
        *,
        mode: EvidenceSearchMode | str = EvidenceSearchMode.HYBRID,
        limit: int = 10,
        source_ids: Iterable[str] = (),
        object_id: str | None = None,
        association_status: str | None = None,
        language: str | None = None,
        include_historical: bool = False,
        semantic_batch_size: int = 32,
    ):
        """Search the Evidence Store independently from accepted Object Knowledge."""

        try:
            return EvidenceSearch(
                self._repository,
                self._evidence_embedder,
            ).search(
                query,
                mode=mode,
                limit=limit,
                source_ids=source_ids,
                object_id=object_id,
                association_status=association_status,
                language=language,
                include_historical=include_historical,
                semantic_batch_size=semantic_batch_size,
            )
        except ValueError as exc:
            raise KnowledgeRequestError(str(exc)) from exc
        except RuntimeError as exc:
            raise RetrievalRuntimeUnavailableError(str(exc)) from exc
