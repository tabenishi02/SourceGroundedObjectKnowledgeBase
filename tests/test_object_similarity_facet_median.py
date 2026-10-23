"""Candidate E scoring, canonical anchor and reproducible median explanation contracts."""

import math
from dataclasses import asdict

import pytest
from test_object_similarity_r2 import (
    _accepted_r2,
    _activate_generation,
    _class,
    _finder,
)
from test_object_similarity_r2 import repo as repo
from test_object_similarity_r2 import space as space


def _pair(repo, source_statements=None):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    target = repo.object_store.create_object("Target", _class(repo, "character"))
    _accepted_r2(
        repo,
        source,
        "source-v1",
        source_statements or [{"facet": "values", "text": "source"}],
    )
    _accepted_r2(repo, target, "target-v1", [{"facet": "values", "text": "target"}])
    return source, target, _activate_generation(repo)


def _summary(result):
    return result.evidence[0].facet_median


def test_median_uses_both_facets_instead_of_max(repo, space):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    target = repo.object_store.create_object("Target", _class(repo, "character"))
    for oid, version in [(source, "source-v1"), (target, "target-v1")]:
        _accepted_r2(
            repo,
            oid,
            version,
            [{"facet": f, "text": f"{f}-detail"} for f in ["personality", "values"]],
        )
    generation = _activate_generation(repo)

    def vectors(row):
        if row["object_id"] == source:
            return (1.0, 0.0, 0.0)
        value = (
            0.8
            if row["target_kind"] == "object_overview"
            else (0.9 if row["facet"] == "personality" else 0.1)
        )
        return (value, math.sqrt(1 - value * value), 0.0)

    finder, _ = _finder(repo, space, generation, vectors)
    result = finder.find_similar_objects(source).results[0]
    explanation = _summary(result)
    assert explanation.eligible_shared_facet_count == 2
    assert explanation.detail_median == pytest.approx(0.5)
    assert set(explanation.median_support_facets) == {"personality", "values"}
    assert result.score == pytest.approx(0.65)
    assert sum(e.contribution for e in result.evidence) == pytest.approx(result.score)
    payload = asdict(result)
    assert payload["evidence"][0]["facet_median"]["eligible_shared_facet_count"] == 2
    assert result.score_type == "hierarchical_similarity"


def test_weak_selected_query_is_retained_without_score_eviction(repo, space, monkeypatch):
    values = [0.9, 0.8, 0.1, 0.5]
    source, target, generation = _pair(
        repo, [{"facet": "values", "text": f"query-{i}"} for i in range(4)]
    )

    def vectors(row):
        if row["object_id"] == target:
            return (1.0, 0.0, 0.0)
        value = (
            values[int(row["statement_text"].split("-")[-1])]
            if (row["target_kind"] == "statement")
            else 0.8
        )
        return (value, math.sqrt(1 - value * value), 0.0)

    finder, index = _finder(repo, space, generation, vectors)
    original = index.search

    def omit_last_query(spec, query, **kwargs):
        return () if query[0] == 0.5 else original(spec, query, **kwargs)

    monkeypatch.setattr(index, "search", omit_last_query)
    before = finder.find_similar_objects(source).results[0]
    monkeypatch.setattr(index, "search", original)
    after = finder.find_similar_objects(source).results[0]
    assert _summary(before).clusters[0].statement_mean == pytest.approx(0.6)
    assert _summary(after).clusters[0].statement_mean == pytest.approx(0.575)
    assert _summary(after).clusters[0].statement_observation_count == 4
    assert after.score < before.score


def test_all_twelve_observations_are_explained(repo, space):
    source, target, generation = _pair(
        repo, [{"facet": "values", "text": f"query-{i}"} for i in range(12)]
    )
    finder, _ = _finder(repo, space, generation, lambda row: (1.0, 0.0, 0.0))
    result = finder.find_similar_objects(source).results[0]
    assert _summary(result).clusters[0].statement_observation_count == 12
    assert len([e for e in result.evidence if e.component == "statement"]) == 12
    assert len(result.evidence) == 14
    assert sum(e.contribution for e in result.evidence) == pytest.approx(result.score)


@pytest.mark.parametrize("anchor_present", [True, False])
def test_statement_discovery_requires_canonical_anchor(repo, space, monkeypatch, anchor_present):
    source, target, generation = _pair(repo)
    finder, index = _finder(repo, space, generation, lambda row: (1.0, 0.0, 0.0))
    if not anchor_present:
        with repo.db:
            repo.db.execute(
                """DELETE FROM knowledge_search_generation_memberships
                   WHERE generation_id=? AND membership_id IN (
                       SELECT id FROM knowledge_search_representation_memberships
                       WHERE object_id=? AND target_kind='facet')""",
                (generation, target),
            )
    original = index.search

    def statement_only(*args, **kwargs):
        kinds = next(m.values for m in kwargs["filters"].matches if m.field == "kind")
        return original(*args, **kwargs) if kinds == ("statement",) else ()

    monkeypatch.setattr(index, "search", statement_only)
    result = finder.find_similar_objects(source).results[0]
    assert result.object_id == target
    assert _summary(result).eligible_shared_facet_count == int(anchor_present)
    assert result.score == pytest.approx(0.5 if anchor_present else 0.0)
    if anchor_present:
        assert any(e.component == "facet" for e in result.evidence)
    else:
        assert all(e.contribution == 0 for e in result.evidence)
        assert not any(e.component == "facet" for e in result.evidence)


def test_duplicate_points_and_order_do_not_change_result(repo, space, monkeypatch):
    source, target, generation = _pair(repo)
    finder, index = _finder(repo, space, generation, lambda row: (1.0, 0.0, 0.0))
    before = finder.find_similar_objects(source)
    original = index.search

    def duplicates(*args, **kwargs):
        found = original(*args, **kwargs)
        return tuple(reversed(found)) + found

    monkeypatch.setattr(index, "search", duplicates)
    assert finder.find_similar_objects(source) == before


def test_statement_source_facets_outside_eight_ann_queries_are_resolved(repo, space):
    keys = [r["key"] for r in repo.rows("SELECT key FROM facet_definitions ORDER BY key LIMIT 10")]
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    target = repo.object_store.create_object("Target", _class(repo, "character"))
    for oid, version in [(source, "source-v1"), (target, "target-v1")]:
        _accepted_r2(repo, oid, version, [{"facet": f, "text": f"detail {f}"} for f in keys])
    generation = _activate_generation(repo)
    finder, index = _finder(repo, space, generation, lambda row: (1.0, 0.0, 0.0))
    result = finder.find_similar_objects(source).results[0]
    assert _summary(result).eligible_shared_facet_count == 10
    assert len(index.search_limits) == 19  # 1 overview + 8 Facets + 10 Statements
    assert result.score == pytest.approx(1.0)
