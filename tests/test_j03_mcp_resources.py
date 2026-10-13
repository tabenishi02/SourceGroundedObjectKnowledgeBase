import json

import pytest

from sgokb.application_read import APPLICATION_READ_CONTRACT_VERSION, KnowledgeReadApplication
from sgokb.mcp import (
    MCP_RESOURCE_CONTRACT_VERSION,
    MCPReadAdapter,
    MCPResourceURIError,
    evidence_resource_uri,
    object_resource_uri,
    object_version_resource_uri,
    parse_resource_uri,
)
from sgokb.repository import Repository


class _ResourceApplication:
    contract_version = APPLICATION_READ_CONTRACT_VERSION

    def __init__(self):
        self.calls = []

    def get_object(self, object_id, **kwargs):
        self.calls.append(("get_object", object_id, kwargs))
        requested = kwargs.get("version_id")
        return {
            "contract_version": self.contract_version,
            "object_id": object_id,
            "requested_version_id": requested,
            "resolved_version_id": requested or "version:current",
            "is_current": requested is None,
            "object_status": "active",
            "requested_scope": {"facets": None},
            "knowledge": {},
            "warnings": [],
        }

    def get_evidence(self, evidence_id):
        self.calls.append(("get_evidence", evidence_id, {}))
        return {
            "contract_version": self.contract_version,
            "evidence": {"evidence_id": evidence_id, "content": "grounded text"},
            "snapshot": {"snapshot_id": "snapshot:1"},
            "source": {"source_id": "source:1"},
            "raw_artifact_ids": ["raw:1"],
            "context": {},
        }


def _payload(resource):
    assert resource["mimeType"] == "application/json"
    return json.loads(resource["text"])


def test_resource_templates_are_dynamic_and_do_not_enumerate_database_rows():
    adapter = MCPReadAdapter(_ResourceApplication())

    assert adapter.list_resources() == ()
    templates = adapter.list_resource_templates()
    assert [item["uriTemplate"] for item in templates] == [
        "sgokb://object/{object_id}",
        "sgokb://object/{object_id}/version/{version_id}",
        "sgokb://evidence/{evidence_id}",
    ]
    assert all(item["mimeType"] == "application/json" for item in templates)


def test_object_resources_dispatch_current_and_pinned_reads():
    application = _ResourceApplication()
    adapter = MCPReadAdapter(application)

    current_uri = object_resource_uri("object:alice")
    current = adapter.read_resource(current_uri)
    current_payload = _payload(current)
    assert current["uri"] == current_uri
    assert current_payload["resource_contract_version"] == MCP_RESOURCE_CONTRACT_VERSION
    assert current_payload["application_contract_version"] == APPLICATION_READ_CONTRACT_VERSION
    assert current_payload["data"]["resolved_version_id"] == "version:current"
    assert current_payload["data"]["is_current"] is True

    pinned_uri = object_version_resource_uri("object:alice", "version:alice:v1")
    pinned_payload = _payload(adapter.read_resource(pinned_uri))
    assert pinned_payload["data"]["requested_version_id"] == "version:alice:v1"
    assert pinned_payload["data"]["resolved_version_id"] == "version:alice:v1"
    assert pinned_payload["data"]["is_current"] is False

    assert application.calls == [
        ("get_object", "object:alice", {}),
        ("get_object", "object:alice", {"version_id": "version:alice:v1"}),
    ]


def test_evidence_resource_dereferences_provenance_without_search():
    application = _ResourceApplication()
    adapter = MCPReadAdapter(application)
    uri = evidence_resource_uri("evidence:α 1")

    parsed = parse_resource_uri(uri)
    assert parsed.evidence_id == "evidence:α 1"
    resource = adapter.read_resource(uri)
    payload = _payload(resource)

    assert resource["uri"] == uri
    assert payload["data"]["evidence"]["evidence_id"] == "evidence:α 1"
    assert payload["data"]["source"]["source_id"] == "source:1"
    assert application.calls == [("get_evidence", "evidence:α 1", {})]


@pytest.mark.parametrize(
    "uri",
    [
        "https://object/id",
        "sgokb://object/id?facet=values",
        "sgokb://object/id#fragment",
        "sgokb://object/id/relations",
        "sgokb://source/source-1",
        "sgokb://evidence/",
    ],
)
def test_resource_uri_rejects_tool_like_or_unknown_shapes(uri):
    with pytest.raises(MCPResourceURIError):
        parse_resource_uri(uri)


def test_application_direct_evidence_read_preserves_provenance(tmp_path):
    repo = Repository(tmp_path / "j03-evidence.sqlite")
    try:
        source_id = repo.source_store.create_source("Reference source")
        locator_id = repo.source_store.add_locator(
            source_id,
            "url",
            "https://example.test/reference",
            preferred=True,
        )
        snapshot_id = repo.source_store.create_snapshot(
            source_id,
            "2026-10-14T00:00:00Z",
            "fixture",
            observed_locator_id=locator_id,
            title="Reference title",
        )
        artifact_id = repo.source_store.add_raw_artifact(
            snapshot_id,
            "html",
            "memory://reference",
            "a" * 64,
            10,
        )
        run_id = repo.source_store.create_normalization_run(
            snapshot_id,
            "fixture",
            "1",
            [artifact_id],
        )
        evidence_id = repo.source_store.add_evidence(
            run_id,
            "Canonical evidence text.",
            "verbatim",
            language="en",
        )

        result = KnowledgeReadApplication(repo).get_evidence(evidence_id)
        assert result["contract_version"] == APPLICATION_READ_CONTRACT_VERSION
        assert result["evidence"]["evidence_id"] == evidence_id
        assert result["evidence"]["content"] == "Canonical evidence text."
        assert result["snapshot"]["snapshot_id"] == snapshot_id
        assert result["source"]["source_id"] == source_id
        assert result["raw_artifact_ids"] == [artifact_id]
        assert result["context"]["locators"][0]["value"] == "https://example.test/reference"
    finally:
        repo.close()
