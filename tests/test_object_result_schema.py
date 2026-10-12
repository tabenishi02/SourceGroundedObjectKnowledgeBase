import copy

import pytest

from sgokb.domain import AttributeValueType
from sgokb.exchange import (
    OBJECT_RESULT_SCHEMA_ID,
    OBJECT_RESULT_SCHEMA_VERSION,
    ClassExtensionContract,
    ObjectResultContract,
    ObjectResultValidationError,
    build_object_result_schema,
    collect_evidence_ids,
    load_object_result_schema,
    validate_object_result,
)
from sgokb.repository import Repository


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "object-result.sqlite")
    yield value
    value.close()


def _contract(repo, *, with_extension=False):
    primary = repo.object_store.class_by_key("character").class_id
    fictional = repo.object_store.class_by_key("fictional_entity").class_id
    object_id = repo.object_store.create_object("Character A", primary)
    repo.object_store.add_additional_class(object_id, fictional)
    facets = repo.semantic_store.facets_for_classes((primary, fictional))
    attribute_id = repo.semantic_store.register_attribute_definition(
        "official_designation_e05",
        "Official designation E05",
        AttributeValueType.TEXT,
    )
    relation_type_id = repo.object_store.register_relation_type("appears_in_e05", "appears in E05")
    extension_map = {}
    if with_extension:
        extension_map["urn:sgokb:class-extension:character:test-1"] = ClassExtensionContract(
            class_id=primary,
            schema_id="urn:sgokb:class-extension:character:test-1",
            schema={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": ["marker"],
                "properties": {"marker": {"const": "character-extension"}},
            },
        )
    return (
        ObjectResultContract(
            target_object_id=object_id,
            primary_class_id=primary,
            additional_class_ids=(fictional,),
            facet_ids=tuple(facet.facet_id for facet in facets),
            attribute_value_types={attribute_id: AttributeValueType.TEXT},
            relation_type_ids=frozenset({relation_type_id}),
            package_id="package-e05",
            package_schema_version="sgokb.evidence-package/1.0",
            manifest_sha256="a" * 64,
            base_version_id=None,
            class_extensions=extension_map,
        ),
        attribute_id,
        relation_type_id,
    )


def _result(contract, attribute_id, relation_type_id):
    facets = [
        {"facet_id": facet_id, "status": "not_analyzed", "statements": []}
        for facet_id in contract.facet_ids
    ]
    personality = next(
        (facet for facet in facets if facet["facet_id"] == "facet:personality"), None
    )
    if personality is not None:
        personality.update(
            {
                "status": "content",
                "statements": [
                    {
                        "local_key": "personality-1",
                        "text": "周囲への配慮を優先する傾向が描写される。",
                        "derivation_kind": "interpretation",
                        "evidence": [{"evidence_id": "evidence-2", "role": "supports"}],
                    }
                ],
            }
        )
    return {
        "schema_version": OBJECT_RESULT_SCHEMA_VERSION,
        "result_status": "complete",
        "target": {
            "object_id": contract.target_object_id,
            "primary_class_id": contract.primary_class_id,
            "additional_class_ids": list(contract.additional_class_ids),
        },
        "binding": {
            "package_id": "package-e05",
            "package_schema_version": "sgokb.evidence-package/1.0",
            "manifest_sha256": "a" * 64,
            "package_created_at": "2026-10-12T10:00:00Z",
            "base_version_id": None,
        },
        "generation": {
            "instructions_version": "object-analysis/1.0",
            "generator_kind": "interactive_ai",
            "application": "ChatGPT",
            "generated_at": "2026-10-12T10:05:00Z",
        },
        "knowledge": {
            "default_language": "ja",
            "summary": [
                {
                    "local_key": "summary-1",
                    "text": "Character Aの根拠付き要約。",
                    "derivation_kind": "synthesis",
                    "evidence": [{"evidence_id": "evidence-1", "role": "supports"}],
                }
            ],
            "facets": facets,
            "attributes": [
                {
                    "local_key": "designation-1",
                    "attribute_id": attribute_id,
                    "status": "known",
                    "value": "Designation A",
                    "evidence": [{"evidence_id": "evidence-3", "role": "supports"}],
                }
            ],
            "relations": [
                {
                    "local_key": "appears-in-1",
                    "subject_object_id": contract.target_object_id,
                    "relation_type_id": relation_type_id,
                    "object_object_id": "related-object-id",
                    "evidence": [{"evidence_id": "evidence-4", "role": "supports"}],
                }
            ],
        },
        "conflicts": [],
        "gaps": [],
        "unresolved_references": [],
        "registry_proposals": [],
        "class_extensions": [],
    }


def _assert_issue(exc_info, code):
    assert any(issue.code == code for issue in exc_info.value.issues)


def test_static_schema_is_canonical_draft_2020_12_contract():
    schema = load_object_result_schema()
    assert schema["$id"] == OBJECT_RESULT_SCHEMA_ID
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["schema_version"]["const"] == OBJECT_RESULT_SCHEMA_VERSION
    assert "version_id" not in schema["properties"]


def test_valid_complete_result_uses_registry_specialized_schema(repo):
    contract, attribute_id, relation_type_id = _contract(repo)
    result = _result(contract, attribute_id, relation_type_id)

    validate_object_result(result, contract)
    specialized = build_object_result_schema(contract)
    assert specialized["properties"]["target"]["properties"]["object_id"]["const"] == (
        contract.target_object_id
    )
    assert specialized["properties"]["knowledge"]["properties"]["facets"]["minItems"] == len(
        contract.facet_ids
    )


def test_full_snapshot_requires_every_effective_facet_once(repo):
    contract, attribute_id, relation_type_id = _contract(repo)
    result = _result(contract, attribute_id, relation_type_id)
    result["knowledge"]["facets"].pop()

    with pytest.raises(ObjectResultValidationError) as exc:
        validate_object_result(result, contract)
    _assert_issue(exc, "schema")

    duplicate = _result(contract, attribute_id, relation_type_id)
    duplicate["knowledge"]["facets"][-1] = copy.deepcopy(duplicate["knowledge"]["facets"][0])
    with pytest.raises(ObjectResultValidationError) as exc:
        validate_object_result(duplicate, contract)
    _assert_issue(exc, "schema")


def test_target_package_and_base_binding_are_preconditions(repo):
    contract, attribute_id, relation_type_id = _contract(repo)
    result = _result(contract, attribute_id, relation_type_id)
    result["target"]["primary_class_id"] = "class:person"
    result["binding"]["package_id"] = "wrong-package"
    result["binding"]["base_version_id"] = "invented-version"

    with pytest.raises(ObjectResultValidationError) as exc:
        validate_object_result(result, contract)
    messages = " ".join(issue.message for issue in exc.value.issues)
    assert "class:character" in messages
    assert "package-e05" in messages
    assert "None" not in messages


def test_reported_view_requires_explicit_attribution(repo):
    contract, attribute_id, relation_type_id = _contract(repo)
    result = _result(contract, attribute_id, relation_type_id)
    statement = result["knowledge"]["summary"][0]
    statement["derivation_kind"] = "reported_view"

    with pytest.raises(ObjectResultValidationError):
        validate_object_result(result, contract)

    statement["attribution"] = {
        "kind": "community",
        "label": "Example community",
    }
    validate_object_result(result, contract)

    statement["derivation_kind"] = "synthesis"
    with pytest.raises(ObjectResultValidationError):
        validate_object_result(result, contract)


def test_non_content_facet_cannot_hide_statements(repo):
    contract, attribute_id, relation_type_id = _contract(repo)
    result = _result(contract, attribute_id, relation_type_id)
    facet = result["knowledge"]["facets"][0]
    facet["status"] = "insufficient_evidence"
    facet["statements"] = [
        {
            "local_key": "hidden-1",
            "text": "Should not be hidden under a non-content Facet.",
            "derivation_kind": "direct_statement",
            "evidence": [{"evidence_id": "evidence-5", "role": "supports"}],
        }
    ]

    with pytest.raises(ObjectResultValidationError):
        validate_object_result(result, contract)


def test_partial_or_insufficient_result_requires_gap_record(repo):
    contract, attribute_id, relation_type_id = _contract(repo)
    for status in ("partial", "insufficient_evidence"):
        result = _result(contract, attribute_id, relation_type_id)
        result["result_status"] = status
        with pytest.raises(ObjectResultValidationError):
            validate_object_result(result, contract)
        result["gaps"] = [
            {
                "local_key": "gap-1",
                "kind": "not_analyzed" if status == "partial" else "insufficient_evidence",
                "description": "Analysis coverage was limited.",
                "evidence": [],
            }
        ]
        validate_object_result(result, contract)


def test_known_attribute_uses_registry_type_and_grounding(repo):
    contract, attribute_id, relation_type_id = _contract(repo)
    result = _result(contract, attribute_id, relation_type_id)
    result["knowledge"]["attributes"][0]["value"] = 123

    with pytest.raises(ObjectResultValidationError) as exc:
        validate_object_result(result, contract)
    _assert_issue(exc, "attribute_type")

    unknown = _result(contract, attribute_id, relation_type_id)
    unknown["knowledge"]["attributes"][0]["attribute_id"] = "attribute:invented"
    with pytest.raises(ObjectResultValidationError) as exc:
        validate_object_result(unknown, contract)
    _assert_issue(exc, "unknown_attribute")

    ungrounded = _result(contract, attribute_id, relation_type_id)
    ungrounded["knowledge"]["attributes"][0]["evidence"] = []
    with pytest.raises(ObjectResultValidationError) as exc:
        validate_object_result(ungrounded, contract)
    _assert_issue(exc, "schema")


def test_relation_type_and_target_endpoint_are_registry_driven(repo):
    contract, attribute_id, relation_type_id = _contract(repo)
    result = _result(contract, attribute_id, relation_type_id)
    relation = result["knowledge"]["relations"][0]
    relation["relation_type_id"] = "relation:invented"
    relation["subject_object_id"] = "object-b"
    relation["object_object_id"] = "object-c"

    with pytest.raises(ObjectResultValidationError) as exc:
        validate_object_result(result, contract)
    codes = {issue.code for issue in exc.value.issues}
    assert {"unknown_relation_type", "target_not_relation_endpoint"} <= codes


def test_duplicate_local_statement_key_and_bad_conflict_reference_are_rejected(repo):
    contract, attribute_id, relation_type_id = _contract(repo)
    result = _result(contract, attribute_id, relation_type_id)
    result["knowledge"]["summary"].append(copy.deepcopy(result["knowledge"]["summary"][0]))

    with pytest.raises(ObjectResultValidationError) as exc:
        validate_object_result(result, contract)
    _assert_issue(exc, "duplicate_local_key")

    result = _result(contract, attribute_id, relation_type_id)
    result["conflicts"] = [
        {
            "local_key": "conflict-1",
            "description": "Two sources disagree.",
            "related_knowledge": [{"kind": "statement", "local_key": "missing-statement"}],
            "evidence": [
                {"evidence_id": "evidence-6", "role": "supports"},
                {"evidence_id": "evidence-7", "role": "contradicts"},
            ],
        }
    ]
    with pytest.raises(ObjectResultValidationError) as exc:
        validate_object_result(result, contract)
    _assert_issue(exc, "unknown_local_reference")


def test_unresolved_reference_has_no_persistent_object_id_field(repo):
    contract, attribute_id, relation_type_id = _contract(repo)
    result = _result(contract, attribute_id, relation_type_id)
    result["unresolved_references"] = [
        {
            "local_key": "unresolved-1",
            "label": "Unknown Organization",
            "candidate_class_id": "class:organization",
            "evidence": [{"evidence_id": "evidence-8", "role": "supports"}],
        }
    ]
    validate_object_result(result, contract)

    result["unresolved_references"][0]["object_id"] = "invented-object-id"
    with pytest.raises(ObjectResultValidationError):
        validate_object_result(result, contract)


def test_class_extension_is_optional_and_validated_only_when_registered(repo):
    contract, attribute_id, relation_type_id = _contract(repo, with_extension=True)
    result = _result(contract, attribute_id, relation_type_id)
    validate_object_result(result, contract)

    result["class_extensions"] = [
        {
            "class_id": contract.primary_class_id,
            "schema_id": "urn:sgokb:class-extension:character:test-1",
            "data": {"marker": "character-extension"},
        }
    ]
    validate_object_result(result, contract)

    result["class_extensions"][0]["data"]["marker"] = "wrong"
    with pytest.raises(ObjectResultValidationError) as exc:
        validate_object_result(result, contract)
    _assert_issue(exc, "class_extension_schema")


def test_result_without_dedicated_extension_works_for_other_registered_class(repo):
    primary = repo.object_store.class_by_key("person").class_id
    object_id = repo.object_store.create_object("Person A", primary)
    facets = repo.semantic_store.facets_for_classes((primary,))
    contract = ObjectResultContract(
        target_object_id=object_id,
        primary_class_id=primary,
        additional_class_ids=(),
        facet_ids=tuple(facet.facet_id for facet in facets),
        package_id="package-e05",
        package_schema_version="sgokb.evidence-package/1.0",
        manifest_sha256="a" * 64,
        base_version_id=None,
    )
    result = _result(contract, "unused", "unused")
    result["knowledge"]["attributes"] = []
    result["knowledge"]["relations"] = []
    validate_object_result(result, contract)


def test_collect_evidence_ids_covers_knowledge_and_review_metadata(repo):
    contract, attribute_id, relation_type_id = _contract(repo)
    result = _result(contract, attribute_id, relation_type_id)
    result["gaps"] = [
        {
            "local_key": "gap-1",
            "kind": "open_question",
            "description": "Needs more evidence.",
            "evidence": [{"evidence_id": "evidence-gap", "role": "contextualizes"}],
        }
    ]
    result["registry_proposals"] = [
        {
            "local_key": "proposal-1",
            "proposal_kind": "object_alias",
            "rationale": "The source uses another stable name.",
            "payload": {"value": "Alias A", "language": "en"},
            "evidence": [{"evidence_id": "evidence-proposal", "role": "supports"}],
        }
    ]

    evidence = collect_evidence_ids(result)
    assert {
        "evidence-1",
        "evidence-2",
        "evidence-3",
        "evidence-4",
        "evidence-gap",
        "evidence-proposal",
    } <= evidence


def test_unknown_top_level_field_and_version_id_are_rejected(repo):
    contract, attribute_id, relation_type_id = _contract(repo)
    result = _result(contract, attribute_id, relation_type_id)
    result["version_id"] = "ai-must-not-issue-persistent-version-id"
    result["write_to"] = "C:/unsafe"

    with pytest.raises(ObjectResultValidationError) as exc:
        validate_object_result(result, contract)
    _assert_issue(exc, "schema")
