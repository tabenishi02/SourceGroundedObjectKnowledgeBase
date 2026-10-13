import hashlib

import pytest

from sgokb.domain import (
    DerivationKind,
    DerivedState,
    EvidenceExtractionMode,
    EvidenceTargetKind,
    FacetStatus,
    SearchRepresentationKind,
)
from sgokb.repository import Repository
from sgokb.retrieval import SearchRepresentationBuilder


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "search-representation.sqlite")
    yield value
    value.close()


def _class_id(repo, key="character"):
    return repo.object_store.class_by_key(key).class_id


def _evidence(repo, *, suffix="a", content="根拠となる本文。"):
    source_id = repo.source_store.create_source(f"Source {suffix}")
    locator_id = repo.source_store.add_locator(
        source_id, "url", f"https://example.test/{suffix}", preferred=True
    )
    snapshot_id = repo.source_store.create_snapshot(
        source_id,
        "2026-10-13T00:00:00Z",
        "test",
        observed_locator_id=locator_id,
        title=f"Profile {suffix}",
    )
    artifact_id = repo.source_store.add_raw_artifact(
        snapshot_id,
        "html",
        f"memory://{suffix}",
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
        content,
        EvidenceExtractionMode.NORMALIZED,
        language="ja",
    )
    return {
        "source_id": source_id,
        "snapshot_id": snapshot_id,
        "run_id": run_id,
        "evidence_id": evidence_id,
    }


def _accepted_version(
    repo,
    object_id,
    evidence_id,
    *,
    version_id,
    base_version_id=None,
    statement_text="仲間を優先する。",
    with_temporal=True,
    include_summary=True,
):
    version_id = repo.version_store.begin_candidate(
        object_id, base_version_id, version_id=version_id
    )
    personality = repo.semantic_store.facet_by_key("personality").facet_id
    values = repo.semantic_store.facet_by_key("values").facet_id
    repo.semantic_store.set_version_facet(version_id, personality, FacetStatus.CONTENT)
    repo.semantic_store.set_version_facet(
        version_id, values, FacetStatus.INSUFFICIENT_EVIDENCE
    )
    temporal_scope_id = None
    if with_temporal:
        temporal_scope_id = repo.semantic_store.create_temporal_scope(
            version_id, as_of="2026-01-01", label="2026 arc"
        )
    statement_id = repo.semantic_store.add_statement(
        version_id,
        "personality-1",
        statement_text,
        DerivationKind.INTERPRETATION,
        facet_id=personality,
        language="ja",
        temporal_scope_id=temporal_scope_id,
    )
    repo.source_store.link_evidence(
        version_id,
        EvidenceTargetKind.STATEMENT,
        statement_id,
        evidence_id,
    )
    summary_id = None
    if include_summary:
        summary_id = repo.semantic_store.add_statement(
            version_id,
            "summary-1",
            "冷静で仲間思いの人物。",
            DerivationKind.SYNTHESIS,
            language="ja",
        )
        repo.source_store.link_evidence(
            version_id,
            EvidenceTargetKind.STATEMENT,
            summary_id,
            evidence_id,
        )
    repo.version_store.accept_candidate(version_id)
    return {
        "version_id": version_id,
        "statement_id": statement_id,
        "summary_id": summary_id,
        "personality": personality,
        "values": values,
    }


def test_builder_covers_all_four_representation_kinds_and_hash_is_deterministic(repo):
    evidence = _evidence(repo)
    object_id = repo.object_store.create_object(
        "架空太郎", _class_id(repo), aliases=["Taro Example"]
    )
    version = _accepted_version(
        repo, object_id, evidence["evidence_id"], version_id="version-a"
    )
    builder = SearchRepresentationBuilder(repo)

    overall = builder.build_object_overall(version["version_id"])
    facet = builder.build_facet(version["version_id"], version["personality"])
    statement = builder.build_statement(version["statement_id"])
    evidence_representation = builder.build_evidence(evidence["evidence_id"])

    assert overall.kind is SearchRepresentationKind.OBJECT_OVERALL
    assert facet.kind is SearchRepresentationKind.FACET
    assert statement.kind is SearchRepresentationKind.STATEMENT
    assert evidence_representation.kind is SearchRepresentationKind.EVIDENCE
    assert builder.build_statement(version["statement_id"]) == statement

    representation_id = builder.materialize_evidence(evidence["evidence_id"])
    stored = repo.semantic_store.search_representation(representation_id)
    assert stored.content == evidence_representation.content
    assert stored.content_hash == hashlib.sha256(
        evidence_representation.content.encode("utf-8")
    ).hexdigest()


def test_statement_builder_adds_semantic_context_without_stable_ids(repo):
    evidence = _evidence(repo)
    object_id = repo.object_store.create_object("架空太郎", _class_id(repo))
    version = _accepted_version(
        repo, object_id, evidence["evidence_id"], version_id="version-a"
    )

    built = SearchRepresentationBuilder(repo).build_statement(version["statement_id"])
    assert built.content == "\n".join(
        [
            "Object: 架空太郎",
            "Primary Class: character (Character)",
            "Facet: Personality (personality)",
            "Temporal Scope: 2026 arc; as_of=2026-01-01",
            "Derivation: interpretation",
            "Statement: 仲間を優先する。",
        ]
    )
    assert object_id not in built.content
    assert version["version_id"] not in built.content
    assert version["statement_id"] not in built.content


def test_non_content_facets_do_not_get_semantic_representations(repo):
    evidence = _evidence(repo)
    object_id = repo.object_store.create_object("架空太郎", _class_id(repo))
    version = _accepted_version(
        repo, object_id, evidence["evidence_id"], version_id="version-a"
    )
    builder = SearchRepresentationBuilder(repo)

    assert builder.build_facet(version["version_id"], version["values"]) is None
    builder.materialize_version(version["version_id"])
    values_memberships = repo.rows(
        """SELECT * FROM knowledge_search_representation_memberships
           WHERE version_id=? AND facet_id=?""",
        (version["version_id"], version["values"]),
    )
    assert values_memberships == []


def test_identical_content_reuses_representation_but_not_version_membership(repo):
    evidence = _evidence(repo)
    object_id = repo.object_store.create_object("架空太郎", _class_id(repo))
    builder = SearchRepresentationBuilder(repo)

    first = _accepted_version(
        repo,
        object_id,
        evidence["evidence_id"],
        version_id="version-1",
        with_temporal=False,
    )
    builder.materialize_version(first["version_id"])
    first_membership = repo.one(
        """SELECT representation_id FROM knowledge_search_representation_memberships
           WHERE version_id=? AND statement_id=?""",
        (first["version_id"], first["statement_id"]),
    )

    second = _accepted_version(
        repo,
        object_id,
        evidence["evidence_id"],
        version_id="version-2",
        base_version_id=first["version_id"],
        with_temporal=False,
    )
    builder.materialize_version(second["version_id"])
    second_membership = repo.one(
        """SELECT representation_id FROM knowledge_search_representation_memberships
           WHERE version_id=? AND statement_id=?""",
        (second["version_id"], second["statement_id"]),
    )

    assert first_membership["representation_id"] == second_membership["representation_id"]
    memberships = repo.rows(
        """SELECT version_id,statement_id FROM knowledge_search_representation_memberships
           WHERE representation_id=? AND target_kind='statement' ORDER BY version_id""",
        (first_membership["representation_id"],),
    )
    assert memberships == [
        {"version_id": "version-1", "statement_id": first["statement_id"]},
        {"version_id": "version-2", "statement_id": second["statement_id"]},
    ]

    current = repo.semantic_store.knowledge_search_memberships(
        object_id=object_id, current_only=True
    )
    assert current
    assert {row["version_id"] for row in current} == {"version-2"}
    historical = repo.semantic_store.knowledge_search_memberships(version_id="version-1")
    assert historical
    assert {row["version_id"] for row in historical} == {"version-1"}


def test_evidence_membership_preserves_canonical_generation_identity(repo):
    evidence = _evidence(repo, content="証拠本文。")
    builder = SearchRepresentationBuilder(repo)
    representation_id = builder.materialize_evidence(evidence["evidence_id"])

    membership = repo.semantic_store.evidence_search_memberships(
        evidence_id=evidence["evidence_id"]
    )[0]
    assert membership["representation_id"] == representation_id
    assert membership["source_id"] == evidence["source_id"]
    assert membership["snapshot_id"] == evidence["snapshot_id"]
    assert membership["run_id"] == evidence["run_id"]

    content = repo.semantic_store.search_representation(representation_id).content
    assert "Source: Source a" in content
    assert "Title: Profile a" in content
    assert "Evidence: 証拠本文。" in content
    assert evidence["run_id"] not in content


def test_relation_text_is_integrated_into_object_overall_not_a_separate_kind(repo):
    evidence = _evidence(repo)
    subject = repo.object_store.create_object("人物A", _class_id(repo))
    target = repo.object_store.create_object("人物B", _class_id(repo))
    version_id = repo.version_store.begin_candidate(subject, None, version_id="version-rel")
    relation_type_id = repo.object_store.register_relation_type("mentor_of_i01", "Mentor of")
    with repo.db:
        repo.db.execute(
            "INSERT INTO object_relations VALUES(?,?,?,?,?,?)",
            (
                "relation-i01",
                version_id,
                subject,
                relation_type_id,
                target,
                "2026-10-13T00:00:00Z",
            ),
        )
    repo.source_store.link_evidence(
        version_id,
        EvidenceTargetKind.RELATION,
        "relation-i01",
        evidence["evidence_id"],
    )
    repo.version_store.accept_candidate(version_id)

    built = SearchRepresentationBuilder(repo).build_object_overall(version_id)
    assert "Relations:" in built.content
    assert "人物A Mentor of 人物B" in built.content
    assert {kind.value for kind in SearchRepresentationKind} == {
        "object_overall",
        "facet",
        "statement",
        "evidence",
    }


def test_builder_rejects_candidate_version_and_derived_failure_does_not_rollback(repo):
    evidence = _evidence(repo)
    object_id = repo.object_store.create_object("架空太郎", _class_id(repo))
    candidate = repo.version_store.begin_candidate(object_id, None, version_id="candidate-a")
    builder = SearchRepresentationBuilder(repo)
    with pytest.raises(ValueError, match="accepted"):
        builder.build_object_overall(candidate)

    version = _accepted_version(
        repo,
        object_id,
        evidence["evidence_id"],
        version_id="accepted-a",
        base_version_id=None,
    )
    state = next(
        item
        for item in repo.version_store.derived_states(object_id)
        if item.kind == "search_representation"
    )
    assert repo.version_store.mark_derived_state(
        object_id,
        "search_representation",
        state.revision,
        DerivedState.FAILED,
        error="simulated builder failure",
    )
    assert repo.version_store.current_version_id(object_id) == version["version_id"]
    assert repo.version_store.version_by_id(version["version_id"]).state.value == "accepted"
