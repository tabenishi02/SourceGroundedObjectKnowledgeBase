"""MCP mutation boundary policy for Phase J / J-05.

The initial SGOKB MCP surface is deliberately read-only. This module exists so
future mutation capabilities have a separate contract and adapter boundary
instead of being added to :class:`MCPReadAdapter` opportunistically.

J-05 does not implement any mutation Tool. Future write Tools may create
proposal/staging data only; they must not mutate canonical Object Knowledge,
accepted Knowledge Versions, Registry state, or derived indexes directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MCP_WRITE_POLICY_VERSION = "sgokb.mcp-write-policy.v1"
MCP_WRITE_TOOL_CONTRACT_VERSION = "sgokb.mcp-write-tools.v1"
MCP_WRITE_STAGING_TARGET = "proposal_staging"


@dataclass(frozen=True, slots=True)
class MCPWritePolicy:
    """Security/authority policy for any future MCP mutation surface."""

    policy_version: str = MCP_WRITE_POLICY_VERSION
    mvp_enabled: bool = False
    canonical_mutation_allowed: bool = False
    staging_target: str = MCP_WRITE_STAGING_TARGET
    require_explicit_server_enable: bool = True
    require_authorization_scope: bool = True
    require_audit_record: bool = True
    automatic_promotion_allowed: bool = False


MCP_WRITE_POLICY = MCPWritePolicy()


class MCPWriteDisabledError(RuntimeError):
    """Raised when a caller attempts to use the disabled MVP write surface."""

    code = "mcp_write_disabled"


class MCPWriteAdapter:
    """Separate future mutation adapter; intentionally exposes zero MVP Tools.

    Keeping this adapter distinct from ``MCPReadAdapter`` prevents a future
    proposal capability from accidentally inheriting the read Application port
    or becoming visible in the read Tool list. A later task may add an injected
    proposal/staging Application port here, but canonical import/apply services
    must remain outside this boundary.
    """

    __slots__ = ()

    @property
    def policy(self) -> MCPWritePolicy:
        return MCP_WRITE_POLICY

    @property
    def tool_contract_version(self) -> str:
        return MCP_WRITE_TOOL_CONTRACT_VERSION

    def list_tools(self) -> tuple[dict[str, Any], ...]:
        """Return no mutation Tools for the initial read-only MCP MVP."""

        return ()

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        """Reject every mutation call until a proposal-only surface is enabled."""

        del arguments
        raise MCPWriteDisabledError(
            f"MCP write Tools are disabled in the SGOKB MVP: {name}. "
            "Future mutation capabilities must target proposal staging only."
        )
