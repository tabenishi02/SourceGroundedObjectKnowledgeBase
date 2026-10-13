from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

mcp = pytest.importorskip("mcp", reason="J-06 requires the optional mcp extra")

from mcp import Client, StdioServerParameters

from sgokb.application_read import KnowledgeReadApplication
from sgokb.repository import Repository


FIXTURE_SERVER = Path(__file__).with_name("j06_mcp_fixture_server.py")
EXPECTED_TOOLS = {
    "search_objects",
    "find_similar_objects",
    "get_object",
    "get_objects",
    "get_object_relations",
    "get_object_evidence",
    "search_evidence",
    "build_context",
}
EXPECTED_TEMPLATES = {
    "sgokb://object/{object_id}",
    "sgokb://object/{object_id}/version/{version_id}",
    "sgokb://evidence/{evidence_id}",
}


def _structured(result):
    assert result.is_error is False
    assert result.structured_content is not None
    return result.structured_content


@pytest.mark.anyio
async def test_local_stdio_client_acceptance_surface():
    params = StdioServerParameters(command=sys.executable, args=[str(FIXTURE_SERVER)])

    async with Client(params) as client:
        assert client.protocol_version == "2026-07-28"
        assert client.server_info is not None
        assert client.server_info.name == "sgokb"

        listed_tools = await client.list_tools()
        assert {tool.name for tool in listed_tools.tools} == EXPECTED_TOOLS
        assert all(tool.annotations is not None for tool in listed_tools.tools)
        assert all(tool.annotations.read_only_hint is True for tool in listed_tools.tools)

        templates = await client.list_resource_templates()
        assert {str(item.uri_template) for item in templates.resource_templates} == EXPECTED_TEMPLATES
        assert (await client.list_resources()).resources == []

        object_result = _structured(
            await client.call_tool("get_object", {"object_id": "object:alpha"})
        )
        assert object_result["data"]["object_id"] == "object:alpha"
        assert object_result["data"]["resolved_version_id"] == "version:object:alpha:current"

        batch_result = _structured(
            await client.call_tool(
                "get_objects", {"object_ids": ["object:alpha", "object:beta"]}
            )
        )
        assert [item["object_id"] for item in batch_result["data"]["objects"]] == [
            "object:alpha",
            "object:beta",
        ]

        semantic = _structured(
            await client.call_tool(
                "search_objects",
                {"query": "calm character", "mode": "semantic", "limit": 5},
            )
        )
        assert semantic["data"]["mode"] == "semantic"
        assert semantic["data"]["results"][0]["object_id"] == "object:alpha"

        similar = _structured(
            await client.call_tool(
                "find_similar_objects", {"object_id": "object:alpha", "limit": 5}
            )
        )
        assert similar["data"]["source_object_id"] == "object:alpha"
        assert similar["data"]["results"][0]["object_id"] == "object:beta"

        context = _structured(
            await client.call_tool(
                "build_context",
                {
                    "object_ids": ["object:alpha", "object:beta"],
                    "purpose": "analysis",
                    "max_characters": 2048,
                },
            )
        )
        assert context["data"]["purpose"] == "analysis"
        assert context["data"]["budget"]["limit_characters"] == 2048
        assert context["data"]["budget"]["used_characters"] <= 2048

        resource = await client.read_resource("sgokb://object/object%3Aalpha")
        assert len(resource.contents) == 1
        payload = json.loads(resource.contents[0].text)
        assert payload["data"]["object_id"] == "object:alpha"
        assert payload["resource_contract_version"] == "sgokb.mcp-resources.v1"


def _class_id(repo: Repository) -> str:
    return repo.object_store.class_by_key("character").class_id


def test_canonical_read_and_cli_continue_without_mcp_process(tmp_path):
    repo = Repository(tmp_path / "j06-fallback.sqlite")
    try:
        object_id = repo.object_store.create_object("Fallback Object", _class_id(repo))
        version_id = repo.version_store.begin_candidate(object_id, None, version_id="version:fallback:v1")
        repo.version_store.accept_candidate(version_id)

        direct = KnowledgeReadApplication(repo).get_object(object_id)
        assert direct["object_id"] == object_id
        assert direct["resolved_version_id"] == version_id
    finally:
        repo.close()

    completed = subprocess.run(
        [sys.executable, "-m", "sgokb", "--help"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
