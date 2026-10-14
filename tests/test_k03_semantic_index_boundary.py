from __future__ import annotations

from pathlib import Path

import pytest

from sgokb.application_read import KnowledgeReadApplication
from sgokb.domain import EmbeddingSpaceSpec, SearchRepresentationKind
from sgokb.mcp import MCPReadAdapter, MCPToolArgumentsError, read_tool_contracts
from sgokb.repository import Repository
from sgokb.retrieval import (
    ExactVectorIndexAdapter,
    KnowledgeVectorIndexBuilder,
    SearchRepresentationBuilder,
)

PERSONAL_FIELDS = {
    "selection_event_id",
    "semantic_observation",
    "pattern",
    "preference_hypothesis",
    "preference_probability",
    "preference_confidence",
    "preference_embedding",
    "taste_vector",
    "user_profile",
    "personal_ranking_signal",
}


def _class_id(repo: Repository) -> str:
    return repo.object_store.class_by_key("character").class_id


def _accepted(repo: Repository, object_id: str, version_id: str) -> str:
    candidate = repo.version_store.begin_candidate(object_id, None, version_id=version_id)
    repo.version_store.accept_candidate(candidate)
    SearchRepresentationBuilder(repo).materialize_version(candidate)
    return candidate


def _space() -> EmbeddingSpaceSpec:
    return EmbeddingSpaceSpec(
        provider_key="k03-test",
        provider_version="1",
        model="k03-boundary-model",
        model_revision="1",
        dimension=3,
        native_dimension=3,
        preprocessing_key="sgokb-search-representation",
        preprocessing_version="2",
        max_sequence_length=1024,
    )


def _schema_property_names(value: object) -> set[str]:
    if isinstance(value, dict):
        names = set(value.get("properties", {}))
        for child in value.values():
            names.update(_schema_property_names(child))
        return names
    if isinstance(value, list):
        result: set[str] = set()
        for child in value:
            result.update(_schema_property_names(child))
        return result
    return set()


def test_sgokb_semantic_representation_kinds_are_world_object_scoped():
    assert {kind.value for kind in SearchRepresentationKind} == {
        "object_overall",
        "facet",
        "statement",
        "evidence",
    }
    assert not ({kind.value for kind in SearchRepresentationKind} & PERSONAL_FIELDS)


def test_mcp_read_contract_has_no_personal_inference_input_fields():
    for contract in read_tool_contracts():
        property_names = _schema_property_names(contract.input_schema)
        assert not property_names & PERSONAL_FIELDS, contract.name


def test_mcp_rejects_personal_profile_or_preference_fields(tmp_path):
    repo = Repository(tmp_path / "k03-mcp-boundary.sqlite")
    try:
        adapter = MCPReadAdapter(KnowledgeReadApplication(repo))

        with pytest.raises(MCPToolArgumentsError):
            adapter.call_tool(
                "search_objects",
                {"query": "self sacrifice", "user_profile": {"likes": ["tragic"]}},
            )
        with pytest.raises(MCPToolArgumentsError):
            adapter.call_tool(
                "find_similar_objects",
                {"object_id": "object:any", "preference_probability": 0.9},
            )
        with pytest.raises(MCPToolArgumentsError):
            adapter.call_tool(
                "get_objects",
                {
                    "object_ids": ["object:any"],
                    "preference_hypothesis": "user likes self-sacrifice",
                },
            )
        with pytest.raises(MCPToolArgumentsError):
            adapter.call_tool(
                "build_context",
                {"object_ids": ["object:any"], "personal_ranking_signal": 1.0},
            )
    finally:
        repo.close()


def test_vector_index_metadata_contains_world_object_scope_only(tmp_path):
    repo = Repository(tmp_path / "k03-vector-boundary.sqlite")
    try:
        object_id = repo.object_store.create_object("Boundary Character", _class_id(repo))
        _accepted(repo, object_id, "version:k03:v1")

        space = _space()
        for membership in repo.semantic_store.knowledge_search_memberships():
            repo.embedding_store.save_representation_embedding(
                space,
                membership["representation_id"],
                [1.0, 0.0, 0.0],
            )

        points = KnowledgeVectorIndexBuilder(repo, ExactVectorIndexAdapter()).points(space)
        assert points
        for point in points:
            metadata_keys = set(point.metadata)
            assert not metadata_keys & PERSONAL_FIELDS
            assert point.metadata["object_id"] == object_id
            assert point.metadata["version_id"] == "version:k03:v1"
            assert point.metadata["kind"] in {
                "object_overall",
                "facet",
                "statement",
            }
    finally:
        repo.close()


def test_similarity_score_remains_semantic_retrieval_signal(tmp_path):
    repo = Repository(tmp_path / "k03-similarity.sqlite")
    try:
        left = repo.object_store.create_object("Left Character", _class_id(repo))
        right = repo.object_store.create_object("Right Character", _class_id(repo))
        _accepted(repo, left, "version:k03:left")
        _accepted(repo, right, "version:k03:right")

        space = _space()
        vectors = {left: [1.0, 0.0, 0.0], right: [0.9, 0.1, 0.0]}
        for membership in repo.semantic_store.knowledge_search_memberships():
            repo.embedding_store.save_representation_embedding(
                space,
                membership["representation_id"],
                vectors[membership["object_id"]],
            )

        index = ExactVectorIndexAdapter()
        KnowledgeVectorIndexBuilder(repo, index).rebuild(space)
        response = KnowledgeReadApplication(
            repo,
            embedding_space=space,
            vector_index=index,
        ).find_similar_objects(left, limit=5)

        result = response.results[0]
        assert result.object_id == right
        assert result.score_type == "cosine_similarity"
        assert isinstance(result.score, float)
        assert not hasattr(result, "preference_probability")
        assert not hasattr(result, "preference_confidence")
    finally:
        repo.close()


def test_sgokb_source_does_not_import_upds_personal_models():
    root = Path("src/sgokb")
    forbidden_tokens = (
        "PreferenceHypothesis",
        "SelectionEvent",
        "PreferenceEmbedding",
        "TasteVector",
        "UserPreferenceDiscoverySystem",
    )
    matches: list[str] = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            if token in text:
                matches.append(f"{path}:{token}")
    assert matches == []
