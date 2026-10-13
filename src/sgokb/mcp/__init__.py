"""MCP Knowledge Access adapter package."""

from .adapter import MCPReadAdapter, MCPToolArgumentsError
from .tool_contracts import (
    MCP_READ_TOOL_CONTRACT_VERSION,
    MCPToolContract,
    read_tool_contract,
    read_tool_contracts,
)

__all__ = [
    "MCP_READ_TOOL_CONTRACT_VERSION",
    "MCPReadAdapter",
    "MCPToolArgumentsError",
    "MCPToolContract",
    "read_tool_contract",
    "read_tool_contracts",
]
