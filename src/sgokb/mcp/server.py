"""Official MCP Python SDK v2 binding for the SGOKB read adapter.

Phase J / J-06 binds the SDK-neutral contracts established in J-01..J-05 to
an actual local MCP transport. The binding remains thin: request validation and
Knowledge semantics stay in ``MCPReadAdapter`` / ``KnowledgeReadApplication``.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server, ServerRequestContext

from .adapter import MCPReadAdapter

MCP_SERVER_NAME = "sgokb"
MCP_SERVER_VERSION = "0.2.0"


def create_read_server(adapter: MCPReadAdapter) -> Server[Any]:
    """Create a low-level MCP v2 server that exposes only SGOKB read surfaces."""

    async def list_tools(
        ctx: ServerRequestContext[Any], params: types.PaginatedRequestParams | None
    ) -> types.ListToolsResult:
        del ctx, params
        return types.ListToolsResult(
            tools=[types.Tool.model_validate(item) for item in adapter.list_tools()]
        )

    async def call_tool(
        ctx: ServerRequestContext[Any], params: types.CallToolRequestParams
    ) -> types.CallToolResult:
        del ctx
        payload = adapter.call_tool(params.name, dict(params.arguments or {}))
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=json.dumps(payload, ensure_ascii=False, sort_keys=True),
                )
            ],
            structured_content=payload,
        )

    async def list_resources(
        ctx: ServerRequestContext[Any], params: types.PaginatedRequestParams | None
    ) -> types.ListResourcesResult:
        del ctx, params
        return types.ListResourcesResult(
            resources=[types.Resource.model_validate(item) for item in adapter.list_resources()]
        )

    async def list_resource_templates(
        ctx: ServerRequestContext[Any], params: types.PaginatedRequestParams | None
    ) -> types.ListResourceTemplatesResult:
        del ctx, params
        return types.ListResourceTemplatesResult(
            resource_templates=[
                types.ResourceTemplate.model_validate(item)
                for item in adapter.list_resource_templates()
            ]
        )

    async def read_resource(
        ctx: ServerRequestContext[Any], params: types.ReadResourceRequestParams
    ) -> types.ReadResourceResult:
        del ctx
        result = adapter.read_resource(str(params.uri))
        return types.ReadResourceResult(
            contents=[
                types.TextResourceContents(
                    uri=result["uri"],
                    mime_type=result["mimeType"],
                    text=result["text"],
                )
            ]
        )

    return Server(
        MCP_SERVER_NAME,
        version=MCP_SERVER_VERSION,
        title="Source Grounded Object Knowledge Base",
        description="Read-only local Knowledge Access Layer for SGOKB.",
        instructions=(
            "Use search tools when stable IDs are unknown; use get/resource reads when IDs are known. "
            "This server is read-only."
        ),
        on_list_tools=list_tools,
        on_call_tool=call_tool,
        on_list_resources=list_resources,
        on_list_resource_templates=list_resource_templates,
        on_read_resource=read_resource,
    )


async def run_stdio_server(server: Server[Any]) -> None:
    """Run one SGOKB MCP server on local stdio until the client disconnects."""

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def run_stdio(adapter: MCPReadAdapter) -> None:
    """Synchronous entry point for a local host that launches SGOKB over stdio."""

    asyncio.run(run_stdio_server(create_read_server(adapter)))
