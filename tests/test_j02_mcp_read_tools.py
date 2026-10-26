import pytest

from sgokb.mcp import MCPReadAdapter, MCPToolArgumentsError, read_tool_contracts


class FakeReadApplication:
    contract_version = "sgokb.application-read.v1"

    def __init__(self):
        self.calls = []

    def search_objects(self, query, **kwargs):
        self.calls.append(("search_objects", query, kwargs))
        return {
            "query": query,
            "mode": kwargs["mode"],
            "results": [],
            "degraded_channels": (),
        }

    def find_similar_objects(self, object_id, **kwargs):
        self.calls.append(("find_similar_objects", object_id, kwargs))
        return {
            "source_object_id": object_id,
            "source_name": "Source",
            "source_primary_class": "Character",
            "source_version_id": "ver-1",
            "source_representation_id": "rep-1",
            "facet": kwargs.get("facet"),
            "cross_class": kwargs.get("cross_class", False),
            "results": (),
        }

    def get_object(self, object_id, **kwargs):
        self.calls.append(("get_object", object_id, kwargs))
        return {
            "contract_version": self.contract_version,
            "object_id": object_id,
            "requested_version_id": kwargs.get("version_id"),
            "resolved_version_id": kwargs.get("version_id") or "ver-current",
            "is_current": kwargs.get("version_id") is None,
            "object_status": "active",
            "name": "Object",
            "aliases": [],
            "primary_class": {},
            "additional_classes": [],
            "requested_scope": {},
            "knowledge": {},
            "warnings": [],
        }

    def get_objects(self, object_ids, **kwargs):
        self.calls.append(("get_objects", tuple(object_ids), kwargs))
        return {
            "contract_version": self.contract_version,
            "objects": [self.get_object(object_id) for object_id in object_ids],
        }

    def get_object_relations(self, object_id, **kwargs):
        self.calls.append(("get_object_relations", object_id, kwargs))
        version_id = kwargs.get("version_id")
        return {
            "contract_version": self.contract_version,
            "object_id": object_id,
            "scope": "pinned_object_version" if version_id else "current_relation_graph",
            "requested_version_id": version_id,
            "object_current_version_id": None if object_id == "obj-unversioned" else "ver-current",
            "resolved_version_id": version_id or (
                None if object_id == "obj-unversioned" else "ver-current"
            ),
            "is_current": version_id is None,
            "relations": [],
            "warnings": [],
        }

    def get_object_evidence(self, object_id, **kwargs):
        self.calls.append(("get_object_evidence", object_id, kwargs))
        return {
            "contract_version": self.contract_version,
            "object_id": object_id,
            "name": "Object",
            "scope": "effective_snapshot_and_run",
            "semantic": False,
            "candidate_count": 0,
            "candidates": [],
        }

    def build_context(self, object_ids, **kwargs):
        values = tuple(object_ids)
        self.calls.append(("build_context", values, kwargs))
        return {
            "context_contract_version": "sgokb.context-builder.v1",
            "purpose": kwargs["purpose"],
            "selection_policy": {},
            "objects": [],
            "budget": {},
            "warnings": [],
        }

    def search_evidence(self, query, **kwargs):
        self.calls.append(("search_evidence", query, kwargs))
        return {
            "query": query,
            "mode": kwargs["mode"],
            "results": (),
            "degraded_channels": (),
            "include_historical": kwargs.get("include_historical", False),
        }


def test_active_read_tool_set_is_small_and_non_overlapping():
    contracts = read_tool_contracts()
    names = [contract.name for contract in contracts]
    assert names == [
        "search_objects",
        "find_similar_objects",
        "get_object",
        "get_objects",
        "get_object_relations",
        "get_object_evidence",
        "search_evidence",
        "build_context",
    ]
    assert "semantic_search_objects" not in names
    for contract in contracts:
        definition = contract.as_mcp_definition()
        assert definition["annotations"]["readOnlyHint"] is True
        assert definition["annotations"]["openWorldHint"] is False
        assert definition["inputSchema"]["$schema"].endswith("2020-12/schema")
        assert definition["outputSchema"]["$schema"].endswith("2020-12/schema")


def test_build_context_is_active_after_j04():
    contracts = read_tool_contracts(include_reserved=True)
    context = next(item for item in contracts if item.name == "build_context")
    assert context.availability == "active"
    adapter = MCPReadAdapter(FakeReadApplication())
    response = adapter.call_tool(
        "build_context",
        {"object_ids": ["obj-1"], "purpose": "general", "max_characters": 2000},
    )
    assert response["data"]["context_contract_version"] == "sgokb.context-builder.v1"


def test_search_objects_uses_mode_instead_of_duplicate_semantic_tool():
    app = FakeReadApplication()
    adapter = MCPReadAdapter(app)
    response = adapter.call_tool(
        "search_objects",
        {
            "query": "自己犠牲",
            "mode": "semantic",
            "filters": {"facet": "values"},
            "limit": 5,
        },
    )
    assert response["tool_contract_version"] == "sgokb.mcp-read-tools.v1"
    assert response["application_contract_version"] == app.contract_version
    assert response["data"]["mode"] == "semantic"
    _, query, kwargs = app.calls[-1]
    assert query == "自己犠牲"
    assert kwargs["mode"] == "semantic"
    assert kwargs["filters"].facet == "values"


def test_facet_similarity_is_parameterized_not_a_second_tool():
    app = FakeReadApplication()
    adapter = MCPReadAdapter(app)
    response = adapter.call_tool(
        "find_similar_objects",
        {"object_id": "obj-1", "facet": "personality", "limit": 3},
    )
    assert response["data"]["facet"] == "personality"
    assert app.calls[-1][2]["facet"] == "personality"


def test_relation_tool_allows_current_graph_for_object_without_knowledge_version():
    adapter = MCPReadAdapter(FakeReadApplication())
    response = adapter.call_tool("get_object_relations", {"object_id": "obj-unversioned"})

    assert response["data"]["scope"] == "current_relation_graph"
    assert response["data"]["object_current_version_id"] is None
    assert response["data"]["resolved_version_id"] is None
    assert response["data"]["is_current"] is True


def test_tool_input_schema_rejects_unknown_fields_and_large_result_limit():
    adapter = MCPReadAdapter(FakeReadApplication())
    with pytest.raises(MCPToolArgumentsError):
        adapter.call_tool("search_objects", {"query": "x", "unknown": True})
    with pytest.raises(MCPToolArgumentsError):
        adapter.call_tool("search_objects", {"query": "x", "limit": 101})


def test_get_objects_has_mcp_batch_limit():
    adapter = MCPReadAdapter(FakeReadApplication())
    with pytest.raises(MCPToolArgumentsError):
        adapter.call_tool("get_objects", {"object_ids": [f"obj-{i}" for i in range(101)]})


def test_search_evidence_is_separate_from_object_evidence_retrieval():
    app = FakeReadApplication()
    adapter = MCPReadAdapter(app)
    response = adapter.call_tool(
        "search_evidence",
        {
            "query": "winter protector",
            "mode": "lexical",
            "object_id": "obj-1",
            "association_status": "confirmed",
        },
    )
    assert response["data"]["mode"] == "lexical"
    assert app.calls[-1][0] == "search_evidence"
    assert app.calls[-1][2]["association_status"] == "confirmed"
