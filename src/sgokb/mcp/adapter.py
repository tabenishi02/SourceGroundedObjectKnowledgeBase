"""Thin MCP-facing adapter over the transport-neutral Application read boundary.

This module intentionally has no storage, SQL, provider, Vector Index or MCP SDK
imports. J-02 may bind these capabilities to concrete MCP Tools without changing
the dependency direction established here.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Protocol

from sgokb.domain import ObjectSearchFilters, ObjectSearchMode


class KnowledgeReadApplicationPort(Protocol):
    """Minimum Application surface an MCP transport is allowed to call."""

    contract_version: str

    def search_objects(
        self,
        query: str,
        *,
        filters: ObjectSearchFilters = ObjectSearchFilters(),
        limit: int = 10,
        mode: ObjectSearchMode | str = ObjectSearchMode.HYBRID,
        candidate_limit: int | None = None,
    ) -> Any: ...

    def find_similar_objects(
        self,
        object_id: str,
        *,
        facet: str | None = None,
        limit: int = 10,
        cross_class: bool = False,
        source_version_id: str | None = None,
        include_archived: bool = False,
    ) -> Any: ...

    def get_object(
        self,
        object_id: str,
        *,
        version_id: str | None = None,
        facets: Iterable[str] | None = None,
        include_relations: bool = True,
        include_evidence_refs: bool = True,
    ) -> dict: ...

    def get_objects(
        self,
        object_ids: Iterable[str],
        *,
        version_ids: dict[str, str] | None = None,
        facets: Iterable[str] | None = None,
        include_relations: bool = True,
        include_evidence_refs: bool = True,
    ) -> dict: ...

    def get_object_relations(
        self,
        object_id: str,
        *,
        version_id: str | None = None,
        include_evidence_refs: bool = True,
    ) -> dict: ...

    def get_object_evidence(
        self,
        object_id: str,
        *,
        max_candidates: int = 500,
        semantic: bool | None = None,
        semantic_batch_size: int = 32,
        manual_include: Iterable[str] = (),
        manual_exclude: Iterable[str] = (),
    ) -> dict: ...


class MCPReadAdapter:
    """Delegate MCP read capabilities exclusively to an Application port.

    These Python method names are internal adapter capabilities, not a commitment
    to the final public MCP Tool names or JSON Schemas. J-02 owns that contract.
    """

    __slots__ = ("_application",)

    def __init__(self, application: KnowledgeReadApplicationPort) -> None:
        self._application = application

    @property
    def contract_version(self) -> str:
        return self._application.contract_version

    def search_objects(
        self,
        query: str,
        *,
        filters: ObjectSearchFilters = ObjectSearchFilters(),
        limit: int = 10,
        mode: ObjectSearchMode | str = ObjectSearchMode.HYBRID,
        candidate_limit: int | None = None,
    ) -> Any:
        return self._application.search_objects(
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
    ) -> Any:
        return self._application.find_similar_objects(
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
        return self._application.get_object(
            object_id,
            version_id=version_id,
            facets=facets,
            include_relations=include_relations,
            include_evidence_refs=include_evidence_refs,
        )

    def get_objects(
        self,
        object_ids: Iterable[str],
        *,
        version_ids: dict[str, str] | None = None,
        facets: Iterable[str] | None = None,
        include_relations: bool = True,
        include_evidence_refs: bool = True,
    ) -> dict:
        return self._application.get_objects(
            object_ids,
            version_ids=version_ids,
            facets=facets,
            include_relations=include_relations,
            include_evidence_refs=include_evidence_refs,
        )

    def get_object_relations(
        self,
        object_id: str,
        *,
        version_id: str | None = None,
        include_evidence_refs: bool = True,
    ) -> dict:
        return self._application.get_object_relations(
            object_id,
            version_id=version_id,
            include_evidence_refs=include_evidence_refs,
        )

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
        return self._application.get_object_evidence(
            object_id,
            max_candidates=max_candidates,
            semantic=semantic,
            semantic_batch_size=semantic_batch_size,
            manual_include=manual_include,
            manual_exclude=manual_exclude,
        )
