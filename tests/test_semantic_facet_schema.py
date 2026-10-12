import sqlite3

import pytest

from sgokb.domain import (
    AttributeStatus,
    AttributeValueType,
    DerivationKind,
    FacetStatus,
    SearchRepresentationKind,
)
from sgokb.repository import Repository


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "semantic-schema.sqlite")
    yield value
    value.close()


def _class_id(repo, key):
    return repo.object_store.class_by_key(key).class_id


def _object_and_version(repo, class_key="character", *, suffix="a", version_number=1):
    object_id = repo.object_store.create_object(f"Object {suffix}", _class_id(repo, class_key))
    version_id = f"version-{suffix}"
    with repo.db:
        repo.db.execute(
            "INSERT INTO object_versions VALUES(?,?,?,?)",
            (version_id, object_id, version_number, "2026-10-12T00:00:00Z"),
        )
    return object_id, version_id


def test_initial_facet_registry_and_profiles(repo):
    assert repo.one("SELECT count(*) n FROM facet_definitions")["n"] == 18
    assert repo.one("SELECT count(*) n FROM class_facet_profiles")["n"] == 19

    overall = repo.semantic_store.facet_by_key("overall")
    assert overall.facet_id == "facet:overall"
    assert overall.is_common is True

    character = {
        x.key
        for x in repo.semantic_store.facets_for_classes([_class_id(repo, "character")])
    }
    assert {"overall", "personality", "values", "motivation", "behavior"} <= character
    assert {"relationships", "role", "themes", "abilities"} <= character

    work_edition = {
        x.key for x in repo.semantic_store.facets_for_classes([_class_id(repo, "work_edition")])
    }
    assert {"overall", "themes", "worldview", "narrative", "tone", "characters"} <= work_edition

    theme = {x.key for x in repo.semantic_store.facets_for_classes([_class_id(repo, "theme")])}
    assert {"overall", "definition", "properties", "implications", "related_concepts"} <= theme


def test_class_without_specialized_profile_uses_common_contract(repo):
    series = repo.semantic_store.facets_for_classes([_class_id(repo, "series")])
    assert [facet.key for facet in series] == ["overall"]


def test_facet_status_is_explicit_and_statements_require_content(repo):
    _, version_id = _object_and_version(repo)
    personality = repo.semantic_store.facet_by_key("personality").facet_id
    values = repo.semantic_store.facet_by_key("values").facet_id

    repo.semantic_store.set_version_facet(version_id, personality, FacetStatus.CONTENT)
    statement_id = repo.semantic_store.add_statement(
        version_id,
        "personality-1",
        "周囲の期待を意識して行動する。",
        DerivationKind.INTERPRETATION,
        facet_id=personality,
        language="ja",
    )
    assert repo.one("SELECT facet_id FROM knowledge_statements WHERE id=?", (statement_id,))[
        "facet_id"
    ] == personality

    with pytest.raises(sqlite3.IntegrityError, match="must remain content"):
        repo.semantic_store.set_version_facet(
            version_id, personality, FacetStatus.INSUFFICIENT_EVIDENCE
        )

    repo.semantic_store.set_version_facet(version_id, values, FacetStatus.INSUFFICIENT_EVIDENCE)
    with pytest.raises(sqlite3.IntegrityError, match="requires content facet"):
        repo.semantic_store.add_statement(
            version_id,
            "values-1",
            "根拠不足の内容",
            DerivationKind.SYNTHESIS,
            facet_id=values,
        )


def test_summary_statement_does_not_require_a_facet(repo):
    _, version_id = _object_and_version(repo)
    statement_id = repo.semantic_store.add_statement(
        version_id,
        "summary-1",
        "Object全体の要約。",
        DerivationKind.SYNTHESIS,
    )
    assert repo.one("SELECT facet_id FROM knowledge_statements WHERE id=?", (statement_id,))[
        "facet_id"
    ] is None


def test_typed_attributes_keep_value_type_and_analysis_state(repo):
    _, version_id = _object_and_version(repo)
    repo.semantic_store.register_attribute_definition(
        "release_date", "Release date", AttributeValueType.DATE
    )

    value_id = repo.semantic_store.add_attribute(
        version_id, "release_date", "2026-10-12"
    )
    row = repo.one("SELECT * FROM object_version_attributes WHERE id=?", (value_id,))
    assert row["value_text"] == "2026-10-12"
    assert row["value_integer"] is None

    unknown_id = repo.semantic_store.add_attribute(
        version_id,
        "release_date",
        status=AttributeStatus.INSUFFICIENT_EVIDENCE,
        ordinal=1,
    )
    unknown = repo.one("SELECT * FROM object_version_attributes WHERE id=?", (unknown_id,))
    assert unknown["status"] == "insufficient_evidence"
    assert unknown["value_text"] is None

    with pytest.raises(TypeError, match="requires str"):
        repo.semantic_store.add_attribute(version_id, "release_date", 20261012)


def test_attribute_database_guard_rejects_wrong_physical_value_column(repo):
    _, version_id = _object_and_version(repo)
    attribute_id = repo.semantic_store.register_attribute_definition(
        "component_number", "Component number", AttributeValueType.INTEGER
    )
    with pytest.raises(sqlite3.IntegrityError, match="declared type"):
        with repo.db:
            repo.db.execute(
                """INSERT INTO object_version_attributes
                   (id,version_id,attribute_id,ordinal,status,value_text,value_integer,
                    value_real,value_boolean,value_json,language,temporal_scope_id,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    "bad-attribute",
                    version_id,
                    attribute_id,
                    0,
                    "known",
                    "not-an-integer",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    "2026-10-12T00:00:00Z",
                ),
            )


def test_temporal_scope_is_version_scoped_for_statements_and_attributes(repo):
    _, version_a = _object_and_version(repo, suffix="a")
    _, version_b = _object_and_version(repo, suffix="b")
    scope_a = repo.semantic_store.create_temporal_scope(
        version_a, valid_from="2020-01-01", valid_to="2020-12-31", label="2020 state"
    )

    repo.semantic_store.add_statement(
        version_a,
        "summary-temporal",
        "2020年時点の状態。",
        DerivationKind.DIRECT_STATEMENT,
        temporal_scope_id=scope_a,
    )
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        repo.semantic_store.add_statement(
            version_b,
            "wrong-version",
            "別Versionからscopeを参照してはならない。",
            DerivationKind.DIRECT_STATEMENT,
            temporal_scope_id=scope_a,
        )

    repo.semantic_store.register_attribute_definition("state", "State", AttributeValueType.TEXT)
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        repo.semantic_store.add_attribute(
            version_b, "state", "old", temporal_scope_id=scope_a
        )


def test_relation_temporal_scope_must_match_relation_version(repo):
    subject, version_a = _object_and_version(repo, suffix="subject")
    target, version_b = _object_and_version(repo, class_key="work", suffix="target")
    relation_type = repo.object_store.register_relation_type("appears_in", "appears in")
    with repo.db:
        repo.db.execute(
            "INSERT INTO object_relations VALUES(?,?,?,?,?,?)",
            (
                "relation-temporal",
                version_a,
                subject,
                relation_type,
                target,
                "2026-10-12T00:00:00Z",
            ),
        )

    scope_a = repo.semantic_store.create_temporal_scope(version_a, as_of="2025-01-01")
    repo.semantic_store.set_relation_temporal_scope("relation-temporal", scope_a)
    assert repo.one(
        "SELECT temporal_scope_id FROM relation_temporal_scopes WHERE relation_id=?",
        ("relation-temporal",),
    )["temporal_scope_id"] == scope_a

    scope_b = repo.semantic_store.create_temporal_scope(version_b, as_of="2026-01-01")
    with pytest.raises(sqlite3.IntegrityError, match="relation version"):
        repo.semantic_store.set_relation_temporal_scope("relation-temporal", scope_b)


def test_search_representations_are_derived_and_version_membership_is_explicit(repo):
    object_a, version_a = _object_and_version(repo, suffix="a")
    object_b, version_b = _object_and_version(repo, suffix="b")

    representation_a = repo.semantic_store.get_or_create_search_representation(
        SearchRepresentationKind.OBJECT,
        "object-overall",
        "1",
        "same deterministic representation",
    )
    representation_b = repo.semantic_store.get_or_create_search_representation(
        SearchRepresentationKind.OBJECT,
        "object-overall",
        "1",
        "same deterministic representation",
    )
    assert representation_a == representation_b

    repo.semantic_store.link_search_representation(
        version_a, representation_a, SearchRepresentationKind.OBJECT, object_a
    )
    repo.semantic_store.link_search_representation(
        version_b, representation_b, SearchRepresentationKind.OBJECT, object_b
    )
    memberships = repo.rows(
        "SELECT version_id,target_ref FROM search_representation_memberships "
        "WHERE representation_id=? ORDER BY version_id",
        (representation_a,),
    )
    assert memberships == [
        {"version_id": version_a, "target_ref": object_a},
        {"version_id": version_b, "target_ref": object_b},
    ]


def test_facet_and_statement_representation_membership_is_validated(repo):
    _, version_id = _object_and_version(repo)
    personality = repo.semantic_store.facet_by_key("personality").facet_id
    repo.semantic_store.set_version_facet(version_id, personality, FacetStatus.CONTENT)
    statement_id = repo.semantic_store.add_statement(
        version_id,
        "personality-search",
        "仲間を優先する。",
        DerivationKind.SYNTHESIS,
        facet_id=personality,
    )

    facet_representation = repo.semantic_store.get_or_create_search_representation(
        SearchRepresentationKind.FACET, "facet-context", "1", "personality: 仲間を優先する"
    )
    repo.semantic_store.link_search_representation(
        version_id, facet_representation, SearchRepresentationKind.FACET, personality
    )

    statement_representation = repo.semantic_store.get_or_create_search_representation(
        SearchRepresentationKind.STATEMENT,
        "statement-context",
        "1",
        "Object / personality / 仲間を優先する。",
    )
    repo.semantic_store.link_search_representation(
        version_id,
        statement_representation,
        SearchRepresentationKind.STATEMENT,
        statement_id,
    )

    with pytest.raises(sqlite3.IntegrityError, match="kind must match"):
        repo.semantic_store.link_search_representation(
            version_id,
            facet_representation,
            SearchRepresentationKind.STATEMENT,
            statement_id,
        )


def test_search_representation_tracks_builder_version_and_content_hash(repo):
    first = repo.semantic_store.get_or_create_search_representation(
        SearchRepresentationKind.STATEMENT, "statement-context", "1", "same text"
    )
    second = repo.semantic_store.get_or_create_search_representation(
        SearchRepresentationKind.STATEMENT, "statement-context", "2", "same text"
    )
    assert first != second
    first_row = repo.semantic_store.search_representation(first)
    second_row = repo.semantic_store.search_representation(second)
    assert first_row.content_hash == second_row.content_hash
    assert first_row.builder_version == "1"
    assert second_row.builder_version == "2"
