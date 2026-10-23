"""Causal R2 Semantic fusion regression; no model/runtime or gold changes."""

from dataclasses import replace

import pytest
from test_hybrid_search_r2 import (
    _activate_r2_generation,
    _class,
    _engine,
    _evidence,
)
from test_hybrid_search_r2 import repo as repo
from test_hybrid_search_r2 import space as space

from sgokb.domain import DerivationKind, EvidenceTargetKind, FacetStatus, ObjectSearchChannel
from sgokb.retrieval import HybridObjectSearch, SearchRepresentationBuilder
from sgokb.retrieval.hybrid_search import HybridObjectSearch as PhaseISearch
from sgokb.retrieval.hybrid_search import _Candidate
from sgokb.retrieval.hybrid_search_r2 import (
    _GENERATION_CONTEXT,
    _ResolvedKnowledgeGeneration,
)

OVERVIEW = ObjectSearchChannel.SEMANTIC_OBJECT_OVERVIEW
FACET = ObjectSearchChannel.SEMANTIC_FACET
STATEMENT = ObjectSearchChannel.SEMANTIC_STATEMENT


def _candidate(oid, overview, facet, statement):
    return _Candidate(
        oid,
        oid,
        "character",
        "v:" + oid,
        channel_ranks={OVERVIEW: overview, FACET: facet, STATEMENT: statement},
    )


def test_r2_restores_detail_consensus_and_gives_one_semantic_outer_vote(repo):
    candidates = {
        c.key: c
        for c in [
            _candidate("aoi", 1, 4, 2),
            _candidate("ash", 2, 2, 3),
            _candidate("mika", 8, 1, 1),
        ]
    }
    engine = HybridObjectSearch(repo)
    legacy = PhaseISearch._fusion_scores(engine, candidates)
    assert sorted(legacy, key=legacy.get, reverse=True)[0][0] == "aoi"
    token = _GENERATION_CONTEXT.set(
        _ResolvedKnowledgeGeneration("r2", "n05d04r2-hierarchical-v2", 2)
    )
    try:
        semantic = engine._fusion_scores(candidates)
        assert sorted(semantic, key=semantic.get, reverse=True)[0][0] == "mika"
        assert semantic[("mika", "v:mika")] == pytest.approx(1 / 61)
        # Adding a lexical vote leaves the internal Semantic ranking intact.
        candidates[("ash", "v:ash")].channel_ranks[ObjectSearchChannel.REGISTRY_LEXICAL] = 1
        hybrid = engine._fusion_scores(candidates)
        assert hybrid[("ash", "v:ash")] == pytest.approx(1 / 61 + 1 / 62)
        assert hybrid[("mika", "v:mika")] == semantic[("mika", "v:mika")]
    finally:
        _GENERATION_CONTEXT.reset(token)


@pytest.mark.parametrize("generation_id", [None, "v1"])
def test_v1_fusion_is_unchanged(repo, generation_id):
    candidate = _candidate("one", 1, 1, 1)
    candidate.channel_ranks[ObjectSearchChannel.SEMANTIC_OBJECT_OVERALL] = (
        candidate.channel_ranks.pop(OVERVIEW)
    )
    engine = HybridObjectSearch(repo)
    token = _GENERATION_CONTEXT.set(
        _ResolvedKnowledgeGeneration(generation_id, "phase-i-search-v1", 1)
    )
    try:
        assert engine._fusion_scores({candidate.key: candidate})[candidate.key] == pytest.approx(
            3 / 61
        )
    finally:
        _GENERATION_CONTEXT.reset(token)


@pytest.mark.parametrize("kind", ["attribute", "relation", "summary"])
def test_overview_owned_information_is_searchable_without_content_facet_duplication(
    repo, space, kind
):
    phrase = "Distinctive coral restoration expertise"
    object_id = repo.object_store.create_object("Subject", _class(repo, "character"))
    version = repo.version_store.begin_candidate(object_id, None)
    evidence = _evidence(repo, kind)
    facet = repo.semantic_store.facet_by_key("personality").facet_id
    repo.semantic_store.set_version_facet(version, facet, FacetStatus.CONTENT)
    statement = repo.semantic_store.add_statement(
        version, "detail", "Enjoys quiet walks.", DerivationKind.DIRECT_STATEMENT, facet_id=facet
    )
    repo.source_store.link_evidence(version, EvidenceTargetKind.STATEMENT, statement, evidence)
    if kind == "attribute":
        repo.semantic_store.register_attribute_definition("specialty", "Specialty", "text")
        identity = repo.semantic_store.add_attribute(version, "specialty", phrase)
        target_kind = EvidenceTargetKind.ATTRIBUTE
    elif kind == "relation":
        related = repo.object_store.create_object(phrase, _class(repo, "character"))
        relation_type = repo.object_store.register_relation_type("mentored_at", "Mentored at")
        identity = "relation:overview-probe"
        with repo.db:
            repo.db.execute(
                "INSERT INTO object_relations VALUES(?,?,?,?,?,?)",
                (identity, version, object_id, relation_type, related, "2026-10-24T00:00:00Z"),
            )
        target_kind = EvidenceTargetKind.RELATION
    else:
        identity = repo.semantic_store.add_statement(
            version, "summary", phrase, DerivationKind.SYNTHESIS
        )
        target_kind = EvidenceTargetKind.STATEMENT
    repo.source_store.link_evidence(version, target_kind, identity, evidence)
    repo.version_store.accept_candidate(version)
    builder = SearchRepresentationBuilder(repo)
    builder.materialize_version_r2(version)
    assert phrase in builder.build_object_overview(version).content
    assert all(
        phrase not in row["text"]
        for row in repo.rows("SELECT text FROM knowledge_statements WHERE facet_id IS NOT NULL")
    )
    generation = _activate_r2_generation(repo)
    engine, index = _engine(repo, space, generation)
    # Only the overview receives query similarity: prove its independent path,
    # while retaining real Facet/Statement candidates and their public channels.
    for pid, point in list(index.points.items()):
        vector = (1.0, 0.0, 0.0) if point.metadata["kind"] == "object_overview" else (0.0, 1.0, 0.0)
        index.points[pid] = replace(point, vector=vector)
    result = engine.search(phrase, mode="semantic")
    assert len(result.results) == 1
    assert result.results[0].object_id == object_id
    assert result.results[0].fused_score == pytest.approx(1 / 61)
    overview = next(m for m in result.results[0].matches if m.channel == OVERVIEW)
    assert phrase in overview.snippet and overview.score == pytest.approx(1.0)
