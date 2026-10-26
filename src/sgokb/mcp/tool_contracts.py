"""MCP read Tool contracts for Phase J / J-02.

The definitions are MCP-SDK-neutral. A later server binding can expose the same
name/title/description/inputSchema/outputSchema/annotations without coupling the
Knowledge Access contract to one MCP Python SDK release.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MCP_READ_TOOL_CONTRACT_VERSION = "sgokb.mcp-read-tools.v1"
JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
MCP_BATCH_OBJECT_LIMIT = 100
MCP_RESULT_LIMIT = 100
MCP_EVIDENCE_LIMIT = 500


@dataclass(frozen=True, slots=True)
class MCPToolContract:
    name: str
    title: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    annotations: dict[str, Any]
    availability: str = "active"

    def as_mcp_definition(self) -> dict[str, Any]:
        """Return the wire-shaped Tool definition fields used by MCP tools/list."""

        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "inputSchema": self.input_schema,
            "outputSchema": self.output_schema,
            "annotations": self.annotations,
        }


def _object_schema(properties: dict[str, Any], required: tuple[str, ...] = ()) -> dict[str, Any]:
    value: dict[str, Any] = {
        "$schema": JSON_SCHEMA_DIALECT,
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        value["required"] = list(required)
    return value


def _string(*, description: str | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {"type": "string", "minLength": 1}
    if description:
        value["description"] = description
    return value


def _nullable_string(*, description: str | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {"type": ["string", "null"]}
    if description:
        value["description"] = description
    return value


def _string_array(*, max_items: int = 100, unique: bool = True) -> dict[str, Any]:
    return {
        "type": "array",
        "items": {"type": "string", "minLength": 1},
        "maxItems": max_items,
        "uniqueItems": unique,
    }


def _annotations(title: str) -> dict[str, Any]:
    return {
        "title": title,
        "readOnlyHint": True,
        "openWorldHint": False,
    }


def _envelope(data_schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "$schema": JSON_SCHEMA_DIALECT,
        "type": "object",
        "properties": {
            "tool_contract_version": {"const": MCP_READ_TOOL_CONTRACT_VERSION},
            "application_contract_version": {"type": "string", "minLength": 1},
            "data": data_schema,
        },
        "required": ["tool_contract_version", "application_contract_version", "data"],
        "additionalProperties": False,
    }


SEARCH_FILTER_SCHEMA = {
    "type": "object",
    "properties": {
        "primary_class": _nullable_string(),
        "additional_class": _nullable_string(),
        "ancestor_class": _nullable_string(),
        "facet": _nullable_string(),
        "version_id": _nullable_string(),
        "temporal_scope_id": _nullable_string(),
        "knowledge_valid_at": _nullable_string(),
        "derivation_kind": {
            "type": ["string", "null"],
            "enum": [
                "direct_statement",
                "synthesis",
                "interpretation",
                "reported_view",
                None,
            ],
        },
        "include_archived": {"type": "boolean", "default": False},
    },
    "additionalProperties": False,
}

SEARCH_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "object_id": _string(),
        "name": {"type": "string"},
        "primary_class": {"type": "string"},
        "version_id": _nullable_string(),
        "rank": {"type": "integer", "minimum": 1},
        "fused_score": {"type": "number"},
        "score_type": {"type": "string"},
        "exact_identity": _nullable_string(),
        "channels": {"type": "array", "items": {"type": "string"}},
        "matched_facets": {"type": "array", "items": {"type": "string"}},
        "matches": {"type": "array", "items": {"type": "object"}},
    },
    "required": [
        "object_id",
        "name",
        "primary_class",
        "rank",
        "fused_score",
        "score_type",
        "channels",
        "matched_facets",
        "matches",
    ],
    "additionalProperties": True,
}

OBJECT_READ_SCHEMA = {
    "type": "object",
    "properties": {
        "contract_version": {"type": "string"},
        "object_id": _string(),
        "requested_version_id": _nullable_string(),
        "resolved_version_id": _string(),
        "is_current": {"type": "boolean"},
        "object_status": {"type": "string"},
        "name": {"type": "string"},
        "aliases": {"type": "array"},
        "primary_class": {"type": "object"},
        "additional_classes": {"type": "array"},
        "requested_scope": {"type": "object"},
        "knowledge": {"type": "object"},
        "warnings": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "contract_version",
        "object_id",
        "resolved_version_id",
        "is_current",
        "object_status",
        "requested_scope",
        "knowledge",
        "warnings",
    ],
    "additionalProperties": True,
}


SEARCH_OBJECTS = MCPToolContract(
    name="search_objects",
    title="Search SGOKB Objects",
    description=(
        "Discover SGOKB Objects from a text query. Use this when the Object ID is not already "
        "known. mode=hybrid is the default; mode=semantic provides semantic-only search and "
        "mode=lexical avoids the semantic runtime. Returns one result per Object."
    ),
    input_schema=_object_schema(
        {
            "query": _string(description="Natural-language, name, alias, or literal query."),
            "mode": {
                "type": "string",
                "enum": ["lexical", "semantic", "hybrid"],
                "default": "hybrid",
            },
            "filters": SEARCH_FILTER_SCHEMA,
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": MCP_RESULT_LIMIT,
                "default": 10,
            },
            "candidate_limit": {"type": ["integer", "null"], "minimum": 1, "maximum": 1000},
        },
        ("query",),
    ),
    output_schema=_envelope(
        {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "mode": {"type": "string", "enum": ["lexical", "semantic", "hybrid"]},
                "results": {"type": "array", "items": SEARCH_RESULT_SCHEMA},
                "degraded_channels": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["query", "mode", "results", "degraded_channels"],
            "additionalProperties": True,
        }
    ),
    annotations=_annotations("Search SGOKB Objects"),
)

FIND_SIMILAR_OBJECTS = MCPToolContract(
    name="find_similar_objects",
    title="Find Similar SGOKB Objects",
    description=(
        "Find Objects semantically similar to a known Object. Omit facet for overall similarity; "
        "set facet for same-Facet similarity. Missing Facets are not silently replaced by overall "
        "similarity. cross_class defaults to false."
    ),
    input_schema=_object_schema(
        {
            "object_id": _string(),
            "facet": _nullable_string(),
            "source_version_id": _nullable_string(),
            "cross_class": {"type": "boolean", "default": False},
            "include_archived": {"type": "boolean", "default": False},
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": MCP_RESULT_LIMIT,
                "default": 10,
            },
        },
        ("object_id",),
    ),
    output_schema=_envelope(
        {
            "type": "object",
            "properties": {
                "source_object_id": _string(),
                "source_name": {"type": "string"},
                "source_primary_class": {"type": "string"},
                "source_version_id": _string(),
                "source_representation_id": _string(),
                "facet": _nullable_string(),
                "cross_class": {"type": "boolean"},
                "results": {"type": "array", "items": {"type": "object"}},
            },
            "required": [
                "source_object_id",
                "source_version_id",
                "facet",
                "cross_class",
                "results",
            ],
            "additionalProperties": True,
        }
    ),
    annotations=_annotations("Find Similar SGOKB Objects"),
)

GET_OBJECT = MCPToolContract(
    name="get_object",
    title="Get SGOKB Object",
    description=(
        "Get one Object by stable object_id. Omit version_id for current accepted Knowledge or "
        "provide an accepted Version to pin the read. Optional facets limits semantic Facet "
        "content."
    ),
    input_schema=_object_schema(
        {
            "object_id": _string(),
            "version_id": _nullable_string(),
            "facets": {"anyOf": [{"type": "null"}, _string_array(max_items=50)]},
            "include_relations": {"type": "boolean", "default": True},
            "include_evidence_refs": {"type": "boolean", "default": True},
        },
        ("object_id",),
    ),
    output_schema=_envelope(OBJECT_READ_SCHEMA),
    annotations=_annotations("Get SGOKB Object"),
)

GET_OBJECTS = MCPToolContract(
    name="get_objects",
    title="Get Multiple SGOKB Objects",
    description=(
        "Batch-get known Objects by stable object_id. Use search_objects first when IDs are "
        "unknown. Each Object still reports the resolved Knowledge Version."
    ),
    input_schema=_object_schema(
        {
            "object_ids": {
                "type": "array",
                "items": _string(),
                "minItems": 1,
                "maxItems": MCP_BATCH_OBJECT_LIMIT,
            },
            "version_ids": {
                "type": ["object", "null"],
                "additionalProperties": _string(),
                "maxProperties": MCP_BATCH_OBJECT_LIMIT,
            },
            "facets": {"anyOf": [{"type": "null"}, _string_array(max_items=50)]},
            "include_relations": {"type": "boolean", "default": True},
            "include_evidence_refs": {"type": "boolean", "default": True},
        },
        ("object_ids",),
    ),
    output_schema=_envelope(
        {
            "type": "object",
            "properties": {
                "contract_version": {"type": "string"},
                "objects": {"type": "array", "items": OBJECT_READ_SCHEMA},
            },
            "required": ["contract_version", "objects"],
            "additionalProperties": True,
        }
    ),
    annotations=_annotations("Get Multiple SGOKB Objects"),
)

GET_OBJECT_RELATIONS = MCPToolContract(
    name="get_object_relations",
    title="Get SGOKB Object Relations",
    description=(
        "Get deterministic one-hop Relations for a known Object. Omit version_id to traverse the "
        "current accepted Relation graph from either endpoint, even when the queried Object has no "
        "Knowledge Version of its own. Provide version_id to pin the read to that Object's accepted "
        "Version. Canonical Relation direction is never inverted."
    ),
    input_schema=_object_schema(
        {
            "object_id": _string(),
            "version_id": _nullable_string(),
            "include_evidence_refs": {"type": "boolean", "default": True},
        },
        ("object_id",),
    ),
    output_schema=_envelope(
        {
            "type": "object",
            "properties": {
                "contract_version": {"type": "string"},
                "object_id": _string(),
                "scope": {
                    "type": "string",
                    "enum": ["current_relation_graph", "pinned_object_version"],
                },
                "requested_version_id": _nullable_string(),
                "object_current_version_id": _nullable_string(),
                "resolved_version_id": _nullable_string(),
                "is_current": {"type": "boolean"},
                "relations": {"type": "array", "items": {"type": "object"}},
                "warnings": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "object_id",
                "scope",
                "requested_version_id",
                "object_current_version_id",
                "resolved_version_id",
                "is_current",
                "relations",
                "warnings",
            ],
            "additionalProperties": True,
        }
    ),
    annotations=_annotations("Get SGOKB Object Relations"),
)

GET_OBJECT_EVIDENCE = MCPToolContract(
    name="get_object_evidence",
    title="Get Evidence for an SGOKB Object",
    description=(
        "Retrieve Evidence candidates relevant to one known Object, using its explicit Source "
        "associations, identity terms and optional semantic retrieval. Use search_evidence for an "
        "arbitrary Evidence query not anchored to one Object."
    ),
    input_schema=_object_schema(
        {
            "object_id": _string(),
            "max_candidates": {
                "type": "integer",
                "minimum": 1,
                "maximum": MCP_EVIDENCE_LIMIT,
                "default": 50,
            },
            "semantic": {"type": ["boolean", "null"], "default": None},
        },
        ("object_id",),
    ),
    output_schema=_envelope(
        {
            "type": "object",
            "properties": {
                "contract_version": {"type": "string"},
                "object_id": _string(),
                "name": {"type": "string"},
                "scope": {"type": "string"},
                "semantic": {"type": "boolean"},
                "candidate_count": {"type": "integer", "minimum": 0},
                "candidates": {"type": "array", "items": {"type": "object"}},
            },
            "required": ["object_id", "scope", "semantic", "candidate_count", "candidates"],
            "additionalProperties": True,
        }
    ),
    annotations=_annotations("Get Evidence for an SGOKB Object"),
)

SEARCH_EVIDENCE = MCPToolContract(
    name="search_evidence",
    title="Search SGOKB Evidence",
    description=(
        "Search the Evidence Store directly. Results are Evidence records with provenance, not "
        "accepted Object Knowledge. Effective Snapshot/Run generations are the default; historical "
        "Evidence requires include_historical=true."
    ),
    input_schema=_object_schema(
        {
            "query": _string(),
            "mode": {
                "type": "string",
                "enum": ["lexical", "semantic", "hybrid"],
                "default": "hybrid",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": MCP_RESULT_LIMIT,
                "default": 10,
            },
            "source_ids": _string_array(max_items=100),
            "object_id": _nullable_string(),
            "association_status": {
                "type": ["string", "null"],
                "enum": ["candidate", "confirmed", "excluded", None],
            },
            "language": _nullable_string(),
            "include_historical": {"type": "boolean", "default": False},
        },
        ("query",),
    ),
    output_schema=_envelope(
        {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "mode": {"type": "string", "enum": ["lexical", "semantic", "hybrid"]},
                "results": {"type": "array", "items": {"type": "object"}},
                "degraded_channels": {"type": "array", "items": {"type": "string"}},
                "include_historical": {"type": "boolean"},
            },
            "required": [
                "query",
                "mode",
                "results",
                "degraded_channels",
                "include_historical",
            ],
            "additionalProperties": True,
        }
    ),
    annotations=_annotations("Search SGOKB Evidence"),
)

# J-04 finalizes deterministic Context Builder semantics and activates the Tool.
BUILD_CONTEXT = MCPToolContract(
    name="build_context",
    title="Build SGOKB Context",
    description=(
        "Build deterministic purpose-scoped context from known Objects without LLM inference. "
        "Purpose selects a fixed Facet profile; explicit facets override that profile. "
        "A character budget limits selected Knowledge items without splitting statements."
    ),
    input_schema=_object_schema(
        {
            "object_ids": {
                "type": "array",
                "items": _string(),
                "minItems": 1,
                "maxItems": 20,
                "uniqueItems": True,
            },
            "purpose": {
                "type": "string",
                "enum": ["general", "analysis", "comparison", "roleplay", "creative"],
                "default": "general",
            },
            "version_ids": {
                "type": ["object", "null"],
                "additionalProperties": _string(),
                "maxProperties": 20,
            },
            "facets": {"anyOf": [{"type": "null"}, _string_array(max_items=50)]},
            "max_characters": {
                "type": "integer",
                "minimum": 512,
                "maximum": 200000,
                "default": 12000,
            },
            "include_attributes": {"type": ["boolean", "null"], "default": None},
            "include_relations": {"type": ["boolean", "null"], "default": None},
            "include_evidence_refs": {"type": ["boolean", "null"], "default": None},
        },
        ("object_ids",),
    ),
    output_schema=_envelope(
        {
            "type": "object",
            "properties": {
                "context_contract_version": {"type": "string"},
                "purpose": {
                    "type": "string",
                    "enum": ["general", "analysis", "comparison", "roleplay", "creative"],
                },
                "selection_policy": {"type": "object"},
                "objects": {"type": "array", "items": {"type": "object"}},
                "budget": {"type": "object"},
                "warnings": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "context_contract_version",
                "purpose",
                "selection_policy",
                "objects",
                "budget",
                "warnings",
            ],
            "additionalProperties": False,
        }
    ),
    annotations=_annotations("Build SGOKB Context"),
)

ACTIVE_READ_TOOL_CONTRACTS = (
    SEARCH_OBJECTS,
    FIND_SIMILAR_OBJECTS,
    GET_OBJECT,
    GET_OBJECTS,
    GET_OBJECT_RELATIONS,
    GET_OBJECT_EVIDENCE,
    SEARCH_EVIDENCE,
    BUILD_CONTEXT,
)
RESERVED_READ_TOOL_CONTRACTS: tuple[MCPToolContract, ...] = ()


def read_tool_contracts(*, include_reserved: bool = False) -> tuple[MCPToolContract, ...]:
    if include_reserved:
        return ACTIVE_READ_TOOL_CONTRACTS + RESERVED_READ_TOOL_CONTRACTS
    return ACTIVE_READ_TOOL_CONTRACTS


def read_tool_contract(name: str, *, include_reserved: bool = False) -> MCPToolContract:
    for contract in read_tool_contracts(include_reserved=include_reserved):
        if contract.name == name:
            return contract
    raise KeyError(f"Unknown or inactive MCP read Tool: {name}")
