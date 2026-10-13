import pytest

from sgokb.application_read import APPLICATION_READ_CONTRACT_VERSION, KnowledgeReadApplication
from sgokb.mcp import MCPReadAdapter
from sgokb.repository import Repository
from sgokb.retrieval.context_builder import (
    CONTEXT_BUILDER_CONTRACT_VERSION,
    ContextBuilder,
)


def _statement(key: str, text: str, *, evidence=True):
    return {
        "statement_id": f"statement:{key}",
        "local_key": key,
        "text": text,
        "derivation_kind": "direct_statement",
        "language": "ja",
        "facet": key,
        "temporal_scope": None,
        "attribution": None,
        "evidence": [{"evidence_id": f"evidence:{key}", "role": "supports"}] if evidence else [],
    }


def _facet(key: str, text: str):
    return {
        "facet_id": f"facet:{key}",
        "key": key,
        "name": key.title(),
        "status": "known",
        "statements": [_statement(key, text)],
    }


def _object_payload(object_id="object:1"):
    return {
        "contract_version": APPLICATION_READ_CONTRACT_VERSION,
        "object_id": object_id,
        "name": "Example",
        "aliases": [],
        "object_status": "active",
        "requested_version_id": None,
        "resolved_version_id": "version:current",
        "is_current": True,
        "primary_class": {"id": "class:character", "key": "character", "name": "Character"},
        "additional_classes": [],
        "requested_scope": {},
        "knowledge": {
            "default_language": "ja",
            "result_status": "complete",
            "summary": [_statement("summary", "概要です。")],
            "facets": [
                _facet("personality", "冷静で慎重。"),
                _facet("values", "仲間を重視する。"),
                _facet("mechanism", "内部機構によって作動する。"),
                _facet("effects", "周囲に影響を与える。"),
                _facet("production", "制作背景がある。"),
                _facet("tone", "静かな調子。"),
                _facet("properties", "安定した特徴を持つ。"),
                _facet("history", "長い経歴がある。"),
            ],
            "attributes": [
                {
                    "attribute_value_id": "attribute-value:1",
                    "attribute_id": "attribute:height",
                    "key": "height",
                    "name": "Height",
                    "value_type": "integer",
                    "ordinal": 0,
                    "status": "known",
                    "value": 170,
                    "language": None,
                    "temporal_scope": None,
                    "evidence": [{"evidence_id": "evidence:height", "role": "supports"}],
                }
            ],
            "relations": [
                {
                    "relation_id": "relation:1",
                    "relation_type_id": "relation-type:friend",
                    "relation_key": "friend_of",
                    "relation_name": "Friend of",
                    "subject_object_id": object_id,
                    "object_object_id": "object:2",
                    "object_name": "Other",
                    "temporal_scope": None,
                    "evidence": [{"evidence_id": "evidence:relation", "role": "supports"}],
                }
            ],
        },
        "warnings": [],
    }


def _facet_keys(result):
    return [item["key"] for item in result["objects"][0]["knowledge"]["facets"]]


def test_purpose_profiles_select_different_facets_without_inference():
    builder = ContextBuilder()
    payload = _object_payload()

    roleplay = builder.build([payload], purpose="roleplay", max_characters=20_000)
    analysis = builder.build([payload], purpose="analysis", max_characters=20_000)
    comparison = builder.build([payload], purpose="comparison", max_characters=20_000)

    assert roleplay["context_contract_version"] == CONTEXT_BUILDER_CONTRACT_VERSION
    assert "personality" in _facet_keys(roleplay)
    assert "tone" not in _facet_keys(roleplay)
    assert "mechanism" not in _facet_keys(roleplay)

    assert "mechanism" in _facet_keys(analysis)
    assert "effects" in _facet_keys(analysis)
    assert "production" in _facet_keys(analysis)

    assert "properties" in _facet_keys(comparison)
    assert "history" in _facet_keys(comparison)
    assert "production" not in _facet_keys(comparison)
    assert comparison["selection_policy"]["include_relations"] is False


def test_explicit_facets_override_purpose_profile_and_preserve_order():
    result = ContextBuilder().build(
        [_object_payload()],
        purpose="roleplay",
        facets=("mechanism", "personality"),
        max_characters=20_000,
    )

    assert result["selection_policy"]["facet_source"] == "explicit"
    assert _facet_keys(result) == ["mechanism", "personality"]


def test_creative_profile_drops_evidence_refs_by_default():
    result = ContextBuilder().build(
        [_object_payload()],
        purpose="creative",
        max_characters=20_000,
    )
    object_result = result["objects"][0]

    assert result["selection_policy"]["include_evidence_refs"] is False
    assert object_result["knowledge"]["summary"][0]["evidence"] == []
    assert object_result["knowledge"]["attributes"][0]["evidence"] == []
    assert object_result["knowledge"]["relations"][0]["evidence"] == []


def test_budget_is_equal_share_and_never_partially_truncates_items():
    first = _object_payload("object:1")
    second = _object_payload("object:2")
    for payload in (first, second):
        payload["knowledge"]["summary"] = [
            _statement(f"long-{index}", "x" * 400) for index in range(8)
        ]

    result = ContextBuilder().build(
        [first, second],
        purpose="general",
        max_characters=1_200,
    )

    assert result["budget"]["limit_characters"] == 1_200
    assert result["budget"]["used_characters"] <= 1_200
    assert result["budget"]["truncated"] is True
    assert [item["budget"]["limit_characters"] for item in result["objects"]] == [600, 600]
    assert all(item["budget"]["used_characters"] <= 600 for item in result["objects"])
    assert result["selection_policy"]["partial_statement_truncation"] is False


def test_context_builder_rejects_invalid_purpose_and_budget():
    builder = ContextBuilder()
    with pytest.raises(ValueError, match="Unknown Context purpose"):
        builder.build([_object_payload()], purpose="unknown")
    with pytest.raises(ValueError, match="max_characters"):
        builder.build([_object_payload()], max_characters=511)


def _class_id(repo, key="character"):
    return repo.object_store.class_by_key(key).class_id


def _accepted(repo, object_id, version_id, base=None):
    value = repo.version_store.begin_candidate(object_id, base, version_id=version_id)
    repo.version_store.accept_candidate(value)
    return value


def test_application_build_context_resolves_pinned_versions(tmp_path):
    repo = Repository(tmp_path / "j04-context.sqlite")
    try:
        object_id = repo.object_store.create_object("Context Object", _class_id(repo))
        version_1 = _accepted(repo, object_id, "version:context:v1")
        _accepted(repo, object_id, "version:context:v2", base=version_1)

        result = KnowledgeReadApplication(repo).build_context(
            [object_id],
            purpose="comparison",
            version_ids={object_id: version_1},
            max_characters=4_000,
        )

        assert result["context_contract_version"] == CONTEXT_BUILDER_CONTRACT_VERSION
        assert result["objects"][0]["resolved_version_id"] == version_1
        assert result["objects"][0]["is_current"] is False
    finally:
        repo.close()


class _ContextApplication:
    contract_version = APPLICATION_READ_CONTRACT_VERSION

    def __init__(self):
        self.calls = []

    def build_context(self, object_ids, **kwargs):
        ids = tuple(object_ids)
        self.calls.append((ids, kwargs))
        return {
            "context_contract_version": CONTEXT_BUILDER_CONTRACT_VERSION,
            "purpose": kwargs["purpose"],
            "selection_policy": {},
            "objects": [],
            "budget": {
                "metric": "serialized_json_characters",
                "limit_characters": kwargs["max_characters"],
                "used_characters": 0,
                "omitted_items": 0,
                "truncated": False,
            },
            "warnings": [],
        }


def test_mcp_build_context_is_active_and_delegates_to_application():
    app = _ContextApplication()
    adapter = MCPReadAdapter(app)
    names = [item["name"] for item in adapter.list_tools()]
    assert "build_context" in names

    response = adapter.call_tool(
        "build_context",
        {
            "object_ids": ["object:1", "object:2"],
            "purpose": "analysis",
            "facets": ["mechanism", "effects"],
            "max_characters": 8_000,
            "include_relations": False,
        },
    )

    assert response["data"]["purpose"] == "analysis"
    ids, kwargs = app.calls[-1]
    assert ids == ("object:1", "object:2")
    assert kwargs["facets"] == ["mechanism", "effects"]
    assert kwargs["include_relations"] is False
