import pytest

from sgokb.domain import (
    DerivationKind,
    EvidenceExtractionMode,
    EvidenceTargetKind,
    FacetStatus,
)
from sgokb.repository import Repository
from sgokb.retrieval import SearchRepresentationBuilder


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "object-overview-r2.sqlite")
    yield value
    value.close()


def _evidence(repo):
    source_id = repo.source_store.create_source("R2 Source")
    locator_id = repo.source_store.add_locator(
        source_id, "url", "https://example.test/r2-overview", preferred=True
    )
    snapshot_id = repo.source_store.create_snapshot(
        source_id,
        "2026-10-23T00:00:00Z",
        "test",
        observed_locator_id=locator_id,
        title="R2 Overview Source",
    )
    artifact_id = repo.source_store.add_raw_artifact(
        snapshot_id,
        "html",
        "memory://r2-overview",
        "a" * 64,
        10,
    )
    run_id = repo.source_store.create_normalization_run(
        snapshot_id,
        "fixture",
        "1",
        [artifact_id],
    )
    return repo.source_store.add_evidence(
        run_id,
        "R2 overview grounding evidence.",
        EvidenceExtractionMode.NORMALIZED,
        language="en",
    )


def test_object_overview_retains_attributes_relations_and_summary_without_facet_body(repo):
    evidence_id = _evidence(repo)
    character = repo.object_store.class_by_key("character").class_id
    subject = repo.object_store.create_object(
        "R2 Subject",
        character,
        aliases=["zeta", "Alpha"],
    )
    related = repo.object_store.create_object("R2 Related", character)
    version_id = repo.version_store.begin_candidate(
        subject,
        None,
        version_id="version-r2-field-coverage",
    )

    personality = repo.semantic_store.facet_by_key("personality").facet_id
    repo.semantic_store.set_version_facet(version_id, personality, FacetStatus.CONTENT)
    facet_statement = repo.semantic_store.add_statement(
        version_id,
        "personality-private-body",
        "FACET-DETAIL-MUST-STAY-OUT-OF-OVERVIEW",
        DerivationKind.DIRECT_STATEMENT,
        facet_id=personality,
        language="en",
    )
    repo.source_store.link_evidence(
        version_id,
        EvidenceTargetKind.STATEMENT,
        facet_statement,
        evidence_id,
    )
    summary = repo.semantic_store.add_statement(
        version_id,
        "summary",
        "Compact canonical summary.",
        DerivationKind.SYNTHESIS,
        language="en",
    )
    repo.source_store.link_evidence(
        version_id,
        EvidenceTargetKind.STATEMENT,
        summary,
        evidence_id,
    )

    repo.semantic_store.register_attribute_definition(
        "rank_r2",
        "Rank",
        "text",
        description="R2 test attribute",
    )
    attribute_id = repo.semantic_store.add_attribute(
        version_id,
        "rank_r2",
        "Captain",
    )
    repo.source_store.link_evidence(
        version_id,
        EvidenceTargetKind.ATTRIBUTE,
        attribute_id,
        evidence_id,
    )

    relation_type_id = repo.object_store.register_relation_type(
        "mentor_of_r2",
        "Mentor of",
    )
    relation_id = "relation-r2-field-coverage"
    with repo.db:
        repo.db.execute(
            "INSERT INTO object_relations VALUES(?,?,?,?,?,?)",
            (
                relation_id,
                version_id,
                subject,
                relation_type_id,
                related,
                "2026-10-23T00:00:00Z",
            ),
        )
    repo.source_store.link_evidence(
        version_id,
        EvidenceTargetKind.RELATION,
        relation_id,
        evidence_id,
    )

    repo.version_store.accept_candidate(version_id)
    overview = SearchRepresentationBuilder(repo).build_object_overview(version_id)

    assert "Aliases: Alpha, zeta" in overview.content
    assert "Summary:" in overview.content
    assert "Compact canonical summary." in overview.content
    assert "Facets:" in overview.content
    assert "personality (Personality)" in overview.content
    assert "Attributes:" in overview.content
    assert "rank_r2 (Rank): Captain" in overview.content
    assert "Relations:" in overview.content
    assert "R2 Subject mentor_of_r2 (Mentor of) R2 Related" in overview.content

    assert "FACET-DETAIL-MUST-STAY-OUT-OF-OVERVIEW" not in overview.content
    assert facet_statement not in overview.content
    assert attribute_id not in overview.content
    assert relation_id not in overview.content
    assert evidence_id not in overview.content
