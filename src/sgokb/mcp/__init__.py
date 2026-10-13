"""MCP Knowledge Access adapter package."""

from .adapter import MCPReadAdapter, MCPToolArgumentsError
from .resource_contracts import (
    MCP_RESOURCE_CONTRACT_VERSION,
    MCPResourceTemplateContract,
    MCPResourceURIError,
    evidence_resource_uri,
    object_resource_uri,
    object_version_resource_uri,
    parse_resource_uri,
    resource_template_contracts,
)
from .tool_contracts import (
    MCP_READ_TOOL_CONTRACT_VERSION,
    MCPToolContract,
    read_tool_contract,
    read_tool_contracts,
)

__all__ = [
    "MCP_RESOURCE_CONTRACT_VERSION",
    "MCPResourceTemplateContract",
    "MCPResourceURIError",
    "evidence_resource_uri",
    "object_resource_uri",
    "object_version_resource_uri",
    "parse_resource_uri",
    "resource_template_contracts",
    "MCP_READ_TOOL_CONTRACT_VERSION",
    "MCPReadAdapter",
    "MCPToolArgumentsError",
    "MCPToolContract",
    "read_tool_contract",
    "read_tool_contracts",
]
