import importlib
import inspect

import pytest

from sgokb.application_read import (
    APPLICATION_READ_CONTRACT_VERSION,
    KnowledgeReadApplication,
    RetrievalRuntimeUnavailableError,
)
from sgokb.domain import ObjectSearchMode
from sgokb.mcp import MCPReadAdapter
from sgokb.repository import Repository


def _class_id(repo, key="character"):
    return repo.object_store.class_by_key(key).class_id


def _accepted(repo, object_id, version_id, base=None):
    value = repo.version_store.begin_candidate(object_id, base, version_id=version_id)
    repo.version_store.accept_candidate(value)
    return value


def test_application_object_search_uses_phase_i_core_without_semantic_runtime(tmp_path):
    repo = Repository(tmp_path / "j01-search.sqlite")
    try:
        object_id = repo.object_store.create_object(
            "Alice",
            _class_id(repo),
            aliases=("Alicia",),
        )
        _accepted(repo, object_id, "version:alice:v1")

        app = KnowledgeReadApplication(repo)
        response = app.search_objects("Alice", mode=ObjectSearchMode.LEXICAL)

        assert response.mode is ObjectSearchMode.LEXICAL
        assert response.results[0].object_id == object_id
        assert response.results[0].exact_identity == "name"
    finally:
        repo.close()


def test_application_read_resolves_current_and_pinned_accepted_versions(tmp_path):
    repo = Repository(tmp_path / "j01-read.sqlite")
    try:
        object_id = repo.object_store.create_object("Versioned", _class_id(repo))
        version_1 = _accepted(repo, object_id, "version:read:v1")
        version_2 = _accepted(repo, object_id, "version:read:v2", base=version_1)
        app = KnowledgeReadApplication(repo)

        current = app.get_object(object_id)
        pinned = app.get_object(object_id, version_id=version_1)
        batch = app.get_objects(
            (object_id, object_id),
            version_ids={object_id: version_1},
            include_relations=False,
        )

        assert current["contract_version"] == APPLICATION_READ_CONTRACT_VERSION
        assert current["resolved_version_id"] == version_2
        assert current["is_current"] is True
        assert pinned["resolved_version_id"] == version_1
        assert pinned["is_current"] is False
        assert pinned["primary_class"]["key"] == "character"
        assert batch["contract_version"] == APPLICATION_READ_CONTRACT_VERSION
        assert [item["resolved_version_id"] for item in batch["objects"]] == [
            version_1,
            version_1,
        ]
    finally:
        repo.close()


def test_pinned_version_must_belong_to_requested_object(tmp_path):
    repo = Repository(tmp_path / "j01-pin.sqlite")
    try:
        left = repo.object_store.create_object("Left", _class_id(repo))
        right = repo.object_store.create_object("Right", _class_id(repo))
        _accepted(repo, left, "version:left:v1")
        right_version = _accepted(repo, right, "version:right:v1")

        with pytest.raises(ValueError, match="does not belong"):
            KnowledgeReadApplication(repo).get_object(left, version_id=right_version)
    finally:
        repo.close()


def test_similarity_has_no_silent_runtime_fallback(tmp_path):
    repo = Repository(tmp_path / "j01-runtime.sqlite")
    try:
        object_id = repo.object_store.create_object("Runtime", _class_id(repo))
        _accepted(repo, object_id, "version:runtime:v1")

        with pytest.raises(RetrievalRuntimeUnavailableError, match="injected"):
            KnowledgeReadApplication(repo).find_similar_objects(object_id)
    finally:
        repo.close()


class _FakeReadApplication:
    contract_version = APPLICATION_READ_CONTRACT_VERSION

    def __init__(self):
        self.calls = []

    def search_objects(self, query, **kwargs):
        self.calls.append(("search_objects", query, kwargs))
        return {"search": query}

    def find_similar_objects(self, object_id, **kwargs):
        self.calls.append(("find_similar_objects", object_id, kwargs))
        return {"similar": object_id}

    def get_object(self, object_id, **kwargs):
        self.calls.append(("get_object", object_id, kwargs))
        return {"object_id": object_id}

    def get_objects(self, object_ids, **kwargs):
        values = tuple(object_ids)
        self.calls.append(("get_objects", values, kwargs))
        return {"objects": list(values)}

    def get_object_relations(self, object_id, **kwargs):
        self.calls.append(("get_object_relations", object_id, kwargs))
        return {"relations": object_id}

    def get_object_evidence(self, object_id, **kwargs):
        self.calls.append(("get_object_evidence", object_id, kwargs))
        return {"evidence": object_id}


def test_mcp_adapter_only_delegates_to_application_port():
    application = _FakeReadApplication()
    adapter = MCPReadAdapter(application)

    assert adapter.contract_version == APPLICATION_READ_CONTRACT_VERSION
    assert adapter.search_objects("query", mode="lexical") == {"search": "query"}
    assert adapter.find_similar_objects("object:1", facet="personality") == {"similar": "object:1"}
    assert adapter.get_object("object:1", version_id="version:1") == {"object_id": "object:1"}
    assert adapter.get_objects(("object:1", "object:2")) == {"objects": ["object:1", "object:2"]}
    assert adapter.get_object_relations("object:1") == {"relations": "object:1"}
    assert adapter.get_object_evidence("object:1", semantic=False) == {"evidence": "object:1"}
    assert not hasattr(adapter, "repository")
    assert not hasattr(adapter, "db")

    module_source = inspect.getsource(importlib.import_module("sgokb.mcp.adapter"))
    assert "import sqlite3" not in module_source
    assert "sgokb.repository" not in module_source
    assert "sgokb.storage" not in module_source

    assert [call[0] for call in application.calls] == [
        "search_objects",
        "find_similar_objects",
        "get_object",
        "get_objects",
        "get_object_relations",
        "get_object_evidence",
    ]
