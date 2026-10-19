"""SDK-neutral MCP Resource contracts for Phase J / J-03."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, unquote, urlsplit

MCP_RESOURCE_CONTRACT_VERSION = "sgokb.mcp-resources.v1"
MCP_RESOURCE_MIME_TYPE = "application/json"


class MCPResourceURIError(ValueError):
    """A requested SGOKB Resource URI is invalid or unsupported."""

    code = "invalid_resource_uri"


@dataclass(frozen=True, slots=True)
class MCPResourceTemplateContract:
    """Transport-neutral definition matching MCP Resource Template fields."""

    uri_template: str
    name: str
    title: str
    description: str
    mime_type: str = MCP_RESOURCE_MIME_TYPE

    def as_mcp_definition(self) -> dict[str, Any]:
        return {
            "uriTemplate": self.uri_template,
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "mimeType": self.mime_type,
        }


@dataclass(frozen=True, slots=True)
class ParsedResourceURI:
    kind: str
    canonical_uri: str
    object_id: str | None = None
    version_id: str | None = None
    evidence_id: str | None = None


def _encode_segment(value: str) -> str:
    value = value.strip()
    if not value:
        raise MCPResourceURIError("Resource ID must not be empty")
    return quote(value, safe="")


def _decode_segment(value: str) -> str:
    decoded = unquote(value)
    if not decoded or "/" in decoded:
        raise MCPResourceURIError("Resource URI contains an invalid path segment")
    return decoded


def object_resource_uri(object_id: str) -> str:
    return f"sgokb://object/{_encode_segment(object_id)}"


def object_version_resource_uri(object_id: str, version_id: str) -> str:
    return f"sgokb://object/{_encode_segment(object_id)}/version/{_encode_segment(version_id)}"


def evidence_resource_uri(evidence_id: str) -> str:
    return f"sgokb://evidence/{_encode_segment(evidence_id)}"


OBJECT_CURRENT_RESOURCE = MCPResourceTemplateContract(
    uri_template="sgokb://object/{object_id}",
    name="sgokb-object-current",
    title="SGOKB Object — Current Knowledge",
    description=(
        "Read the current accepted Knowledge snapshot for one stable SGOKB object_id. "
        "The response always identifies the resolved Knowledge Version."
    ),
)

OBJECT_VERSION_RESOURCE = MCPResourceTemplateContract(
    uri_template="sgokb://object/{object_id}/version/{version_id}",
    name="sgokb-object-version",
    title="SGOKB Object — Pinned Knowledge Version",
    description=(
        "Read one immutable accepted Knowledge Version for a stable SGOKB object_id. "
        "Use this URI when reproducibility requires a pinned version."
    ),
)

EVIDENCE_RESOURCE = MCPResourceTemplateContract(
    uri_template="sgokb://evidence/{evidence_id}",
    name="sgokb-evidence",
    title="SGOKB Evidence",
    description=(
        "Read one canonical Evidence record together with Source, Snapshot and Raw Artifact "
        "provenance."
    ),
)

_RESOURCE_TEMPLATES = (
    OBJECT_CURRENT_RESOURCE,
    OBJECT_VERSION_RESOURCE,
    EVIDENCE_RESOURCE,
)


def resource_template_contracts() -> tuple[MCPResourceTemplateContract, ...]:
    return _RESOURCE_TEMPLATES


def parse_resource_uri(uri: str) -> ParsedResourceURI:
    """Parse only canonical SGOKB Resource URIs.

    Query strings and fragments are deliberately rejected. Parameterized retrieval
    belongs to MCP Tools rather than being smuggled into Resource URIs.
    """

    try:
        parsed = urlsplit(uri)
    except ValueError as exc:
        raise MCPResourceURIError(str(exc)) from exc
    if parsed.scheme != "sgokb":
        raise MCPResourceURIError("Resource URI scheme must be sgokb")
    if parsed.query or parsed.fragment:
        raise MCPResourceURIError("SGOKB Resource URIs do not accept query or fragment parts")

    segments = [segment for segment in parsed.path.split("/") if segment]
    if parsed.netloc == "object":
        if len(segments) == 1:
            object_id = _decode_segment(segments[0])
            return ParsedResourceURI(
                kind="object_current",
                canonical_uri=object_resource_uri(object_id),
                object_id=object_id,
            )
        if len(segments) == 3 and segments[1] == "version":
            object_id = _decode_segment(segments[0])
            version_id = _decode_segment(segments[2])
            return ParsedResourceURI(
                kind="object_version",
                canonical_uri=object_version_resource_uri(object_id, version_id),
                object_id=object_id,
                version_id=version_id,
            )
    elif parsed.netloc == "evidence" and len(segments) == 1:
        evidence_id = _decode_segment(segments[0])
        return ParsedResourceURI(
            kind="evidence",
            canonical_uri=evidence_resource_uri(evidence_id),
            evidence_id=evidence_id,
        )

    raise MCPResourceURIError(f"Unsupported SGOKB Resource URI: {uri}")
