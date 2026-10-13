from __future__ import annotations

import pytest

from sgokb.mcp import MCPReadAdapter, read_tool_contracts
from sgokb.mcp.write_policy import (
    MCP_WRITE_POLICY,
    MCP_WRITE_POLICY_VERSION,
    MCP_WRITE_STAGING_TARGET,
    MCP_WRITE_TOOL_CONTRACT_VERSION,
    MCPWriteAdapter,
    MCPWriteDisabledError,
)


class FakeReadApplication:
    contract_version = "sgokb.application-read.v1"


def test_mvp_write_surface_is_disabled_and_has_independent_version():
    adapter = MCPWriteAdapter()

    assert adapter.tool_contract_version == MCP_WRITE_TOOL_CONTRACT_VERSION
    assert MCP_WRITE_POLICY.policy_version == MCP_WRITE_POLICY_VERSION
    assert MCP_WRITE_POLICY.mvp_enabled is False
    assert adapter.list_tools() == ()


def test_write_policy_forbids_canonical_mutation_and_automatic_promotion():
    assert MCP_WRITE_POLICY.canonical_mutation_allowed is False
    assert MCP_WRITE_POLICY.automatic_promotion_allowed is False
    assert MCP_WRITE_POLICY.staging_target == MCP_WRITE_STAGING_TARGET == "proposal_staging"
    assert MCP_WRITE_POLICY.require_explicit_server_enable is True
    assert MCP_WRITE_POLICY.require_authorization_scope is True
    assert MCP_WRITE_POLICY.require_audit_record is True


def test_disabled_write_adapter_rejects_future_capability_names():
    adapter = MCPWriteAdapter()

    with pytest.raises(MCPWriteDisabledError, match="proposal staging only"):
        adapter.call_tool("propose_object", {"name": "Example"})


def test_read_adapter_remains_read_only_and_does_not_publish_write_tools():
    read_names = {contract.name for contract in read_tool_contracts()}
    assert "propose_object" not in read_names
    assert "import_object_result" not in read_names
    assert "apply_object_proposal" not in read_names
    assert "delete_object" not in read_names

    adapter = MCPReadAdapter(FakeReadApplication())
    listed = adapter.list_tools()
    assert {item["name"] for item in listed} == read_names
    assert all(item["annotations"]["readOnlyHint"] is True for item in listed)
    assert all(item["annotations"]["openWorldHint"] is False for item in listed)
