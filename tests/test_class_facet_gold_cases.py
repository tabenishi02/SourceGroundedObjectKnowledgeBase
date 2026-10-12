import json
from pathlib import Path

import pytest

from sgokb.repository import Repository

FIXTURE = Path("tests/fixtures/class_facet_gold_cases.json")


def _gold():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "facet-gold.sqlite")
    yield value
    value.close()


def _facet_keys(repo, class_key):
    row = repo.one("SELECT id FROM object_classes WHERE key=?", (class_key,))
    assert row is not None
    return {x.key for x in repo.semantic_store.facets_for_classes([row["id"]])}


def test_gold_fixture_covers_registry_and_frozen_vocabulary(repo):
    gold = _gold()
    classes = repo.rows("SELECT id,key,assignment_policy FROM object_classes ORDER BY key")
    gold_classes = {x["class_id"]: x for x in gold["class_cases"]}
    assert len(classes) == len(gold_classes) == 62
    assert {x["id"] for x in classes} == set(gold_classes)

    for row in classes:
        case = gold_classes[row["id"]]
        assert case["assignment_policy"] == row["assignment_policy"]
        assert case["positive_example"].strip()
        assert case["negative_example"].strip()
        placement = case["representative_placement"]
        if placement["expected_kind"] == "facet":
            assert placement["expected_facet"] in gold["facet_vocabulary"]["all_55"]

    frozen = gold["facet_vocabulary"]["all_55"]
    assert len(frozen) == len(set(frozen)) == 55
    runtime = {x["key"] for x in repo.rows("SELECT key FROM facet_definitions")}
    assert runtime == set(frozen)
    assert repo.one("SELECT count(*) n FROM facet_definitions WHERE is_common=1")["n"] == 1
    assert repo.semantic_store.facet_by_key("overall").is_common is True
    assert repo.semantic_store.facet_by_key("provenance") is None


def test_profile_inheritance_matches_gold_design(repo):
    assert _facet_keys(repo, "agent") == {"overall"}
    assert _facet_keys(repo, "fictional_entity") == {"overall"}

    expected = {
        "team": {"overall", "purpose", "history", "activities", "relationships"},
        "work_edition": {
            "overall",
            "themes",
            "worldview",
            "narrative",
            "tone",
            "characters",
            "relationships",
            "setting",
            "production",
            "reception",
            "changes",
        },
        "episode": {
            "overall",
            "narrative",
            "themes",
            "tone",
            "characters",
            "setting",
            "significance",
        },
        "world": {
            "overall",
            "geography",
            "environment",
            "history",
            "culture",
            "function",
            "significance",
            "structure",
            "society",
            "rules",
        },
        "product": {
            "overall",
            "design",
            "appearance",
            "function",
            "history",
            "significance",
            "properties",
            "usage",
            "variants",
            "reception",
        },
        "fictional_race": {
            "overall",
            "properties",
            "behavior",
            "environment",
            "distribution",
            "history",
            "culture",
            "society",
            "abilities",
        },
        "theme": {
            "overall",
            "definition",
            "properties",
            "implications",
            "related_concepts",
            "examples",
            "manifestations",
            "interpretations",
        },
        "ability": {
            "overall",
            "definition",
            "mechanism",
            "effects",
            "requirements",
            "constraints",
            "variants",
            "conditions",
        },
        "era": {
            "overall",
            "scope",
            "chronology",
            "properties",
            "changes",
            "culture",
            "society",
            "significance",
        },
        "software": {
            "overall",
            "purpose",
            "structure",
            "rules",
            "behavior",
            "constraints",
            "properties",
            "usage",
            "history",
        },
        "substance": {
            "overall",
            "properties",
            "composition",
            "behavior",
            "usage",
            "safety",
            "distribution",
        },
        "social_phenomenon": {
            "overall",
            "mechanism",
            "causes",
            "conditions",
            "effects",
            "measurement",
            "examples",
            "manifestations",
            "history",
        },
        "language": {"overall", "structure", "rules", "usage", "history", "vocabulary", "variants"},
        "writing_system": {
            "overall",
            "structure",
            "rules",
            "usage",
            "history",
            "symbols",
            "variants",
        },
    }
    for class_key, facets in expected.items():
        assert facets <= _facet_keys(repo, class_key), class_key


def test_boundary_gold_cases_cover_required_regressions():
    gold = _gold()
    ids = {x["id"] for x in gold["boundary_cases"]}
    required = {
        "purpose_function_usage",
        "history_chronology_changes",
        "structure_relation_components",
        "properties_vs_attribute",
        "rules_constraints_conditions",
        "mechanism_procedure_behavior",
        "causes_effects_implications",
        "relation_not_collection_facet",
        "overall_not_catchall",
        "work_component_inheritance",
        "capability_inheritance",
        "temporal_inheritance",
        "symbolic_inheritance",
        "concept_subclass_direct",
        "provenance_reserved",
        "cross_class_shared",
        "narrow_similarity_scope",
        "missing_profile_no_fallback",
        "structural_not_primary",
        "fictional_additional_only",
        "adaptation_edition_version",
        "event_phenomenon_process",
        "artifact_product_type",
        "taxon_species_race_creature",
        "language_writing_system",
    }
    assert ids == required
    assert len(ids) == 25


def test_all_gold_facet_references_use_frozen_vocabulary():
    gold = _gold()
    allowed = set(gold["facet_vocabulary"]["all_55"])
    found = set()
    for case in gold["class_cases"]:
        placement = case["representative_placement"]
        if placement["expected_kind"] == "facet":
            found.add(placement["expected_facet"])
    for case in gold["boundary_cases"]:
        for expected in case.get("expect", []):
            facet = expected.get("facet")
            if facet:
                found.add(facet)
    assert found <= allowed
    assert {"purpose", "function", "usage"} <= found
    assert {"history", "chronology", "changes"} <= found
    assert {"rules", "constraints", "conditions"} <= found
    assert {"mechanism", "procedure", "behavior"} <= found
    assert {"causes", "effects", "implications"} <= found
