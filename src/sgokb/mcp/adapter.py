"""Thin MCP-facing adapter over the transport-neutral Application read boundary.

This module intentionally has no storage, SQL, provider, Vector Index or MCP SDK
imports. It owns only Tool contract validation/serialization and delegates every
Knowledge operation to the Application port established by J-01.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, Protocol

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from sgokb.domain import ObjectSearchFilters, ObjectSearchMode

from .tool_contracts import (
    MCP_READ_TOOL_CONTRACT_VERSION,
    read_tool_contract,
    read_tool_contracts,
)


class MCPToolArgumentsError(ValueError):
    """Arguments do not satisfy the public MCP Tool contract."""

    code = "invalid_tool_arguments"


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

    def search_evidence(
        self,
        query: str,
        *,
        mode: str = "hybrid",
        limit: int = 10,
        source_ids: Iterable[str] = (),
        object_id: str | None = None,
        association_status: str | None = None,
        language: str | None = None,
        include_historical: bool = False,
        semantic_batch_size: int = 32,
    ) -> Any: ...


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


class MCPReadAdapter:
    """Public read Tool adapter delegating exclusively to an Application port."""

    __slots__ = ("_application",)

    def __init__(self, application: KnowledgeReadApplicationPort) -> None:
        self._application = application

    @property
    def contract_version(self) -> str:
        """Application read contract version kept for J-01 compatibility."""

        return self._application.contract_version

    @property
    def tool_contract_version(self) -> str:
        return MCP_READ_TOOL_CONTRACT_VERSION

    def list_tools(self) -> tuple[dict[str, Any], ...]:
        """Return active MCP Tool definitions in tools/list-compatible shape."""

        return tuple(contract.as_mcp_definition() for contract in read_tool_contracts())

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        """Validate, dispatch and serialize one active read Tool invocation.

        An MCP SDK binding may call this method from its tools/call handler. The
        reserved J-04 build_context contract is intentionally unavailable here.
        """

        arguments = dict(arguments or {})
        try:
            contract = read_tool_contract(name)
        except KeyError as exc:
            raise MCPToolArgumentsError(str(exc)) from exc
        try:
            Draft202012Validator(contract.input_schema).validate(arguments)
        except ValidationError as exc:
            path = ".".join(str(item) for item in exc.absolute_path)
            detail = f"{path}: {exc.message}" if path else exc.message
            raise MCPToolArgumentsError(detail) from exc

        data = self._dispatch(name, arguments)
        payload = {
            "tool_contract_version": self.tool_contract_version,
            "application_contract_version": self.contract_version,
            "data": _jsonable(data),
        }
        try:
            Draft202012Validator(contract.output_schema).validate(payload)
        except ValidationError as exc:
            raise RuntimeError(
                f"Application result violated MCP Tool output contract for {name}: {exc.message}"
            ) from exc
        return payload

    def _dispatch(self, name: str, arguments: dict[str, Any]) -> Any:
        if name == "search_objects":
            filters = ObjectSearchFilters(**arguments.get("filters", {}))
            return self.search_objects(
                arguments["query"],
                filters=filters,
                limit=arguments.get("limit", 10),
                mode=arguments.get("mode", "hybrid"),
                candidate_limit=arguments.get("candidate_limit"),
            )
        if name == "find_similar_objects":
            return self.find_similar_objects(
                arguments["object_id"],
                facet=arguments.get("facet"),
                limit=arguments.get("limit", 10),
                cross_class=arguments.get("cross_class", False),
                source_version_id=arguments.get("source_version_id"),
                include_archived=arguments.get("include_archived", False),
            )
        if name == "get_object":
            return self.get_object(
                arguments["object_id"],
                version_id=arguments.get("version_id"),
                facets=arguments.get("facets"),
                include_relations=arguments.get("include_relations", True),
                include_evidence_refs=arguments.get("include_evidence_refs", True),
            )
        if name == "get_objects":
            return self.get_objects(
                arguments["object_ids"],
                version_ids=arguments.get("version_ids"),
                facets=arguments.get("facets"),
                include_relations=arguments.get("include_relations", True),
                include_evidence_refs=arguments.get("include_evidence_refs", True),
            )
        if name == "get_object_relations":
            return self.get_object_relations(
                arguments["object_id"],
                version_id=arguments.get("version_id"),
                include_evidence_refs=arguments.get("include_evidence_refs", True),
            )
        if name == "get_object_evidence":
            return self.get_object_evidence(
                arguments["object_id"],
                max_candidates=arguments.get("max_candidates", 50),
                semantic=arguments.get("semantic"),
            )
        if name == "search_evidence":
            return self.search_evidence(
                arguments["query"],
                mode=arguments.get("mode", "hybrid"),
                limit=arguments.get("limit", 10),
                source_ids=arguments.get("source_ids", ()),
                object_id=arguments.get("object_id"),
                association_status=arguments.get("association_status"),
                language=arguments.get("language"),
                include_historical=arguments.get("include_historical", False),
            )
        raise MCPToolArgumentsError(f"Unknown MCP read Tool: {name}")

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

    def search_evidence(
        self,
        query: str,
        *,
        mode: str = "hybrid",
        limit: int = 10,
        source_ids: Iterable[str] = (),
        object_id: str | None = None,
        association_status: str | None = None,
        language: str | None = None,
        include_historical: bool = False,
        semantic_batch_size: int = 32,
    ) -> Any:
        return self._application.search_evidence(
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
