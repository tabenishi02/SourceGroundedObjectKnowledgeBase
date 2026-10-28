from __future__ import annotations

import pytest
from test_hybrid_search import _accepted, _class, _engine

from sgokb.domain import EmbeddingSpaceSpec, ObjectSearchFilters
from sgokb.repository import Repository


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "search-validity-range.sqlite")
    yield value
    value.close()


@pytest.fixture
def space():
    return EmbeddingSpaceSpec(
        provider_key="fake",
        provider_version="1",
        model="fake-model",
        model_revision="rev-1",
        dimension=3,
        native_dimension=3,
        preprocessing_key="sgokb-search-representation",
        preprocessing_version="2",
        normalize_embeddings=True,
        max_sequence_length=1024,
        overflow_policy="reject",
        output_dtype="float32",
        provider_configuration="{}",
    )


def _statement_ids(response):
    return {
        match.statement_id
        for result in response.results
        for match in result.matches
        if match.statement_id is not None
    }


def test_knowledge_validity_range_uses_temporal_overlap_and_keeps_timeless(repo, space):
    object_id = repo.object_store.create_object("Range Alpha", _class(repo, "character"))
    _, records = _accepted(
        repo,
        object_id,
        "range-v1",
        statements=[
            {
                "facet": "personality",
                "text": "期間対象の2026年状態",
                "temporal": {"valid_from": "2026-01-01", "valid_to": "2026-12-31"},
            },
            {
                "facet": "personality",
                "text": "期間対象の2028年状態",
                "temporal": {"valid_from": "2028-01-01", "valid_to": "2028-12-31"},
            },
            {
                "facet": "personality",
                "text": "期間対象の恒常状態",
            },
        ],
    )
    dated_2026, dated_2028, timeless = records
    engine, _ = _engine(repo, space)

    overlap = engine.search(
        "期間対象",
        mode="semantic",
        filters=ObjectSearchFilters(knowledge_valid_at="2026-06-01..2027-06-01"),
    )
    ids = _statement_ids(overlap)
    assert dated_2026["statement_id"] in ids
    assert dated_2028["statement_id"] not in ids
    assert timeless["statement_id"] in ids

    open_from = engine.search(
        "期間対象",
        mode="semantic",
        filters=ObjectSearchFilters(knowledge_valid_at="2027-01-01.."),
    )
    ids = _statement_ids(open_from)
    assert dated_2026["statement_id"] not in ids
    assert dated_2028["statement_id"] in ids
    assert timeless["statement_id"] in ids

    open_to = engine.search(
        "期間対象",
        mode="semantic",
        filters=ObjectSearchFilters(knowledge_valid_at="..2026-06-30"),
    )
    ids = _statement_ids(open_to)
    assert dated_2026["statement_id"] in ids
    assert dated_2028["statement_id"] not in ids
    assert timeless["statement_id"] in ids

    with pytest.raises(ValueError, match="From must not be after To"):
        engine.search(
            "期間対象",
            mode="semantic",
            filters=ObjectSearchFilters(knowledge_valid_at="2028-01-01..2026-01-01"),
        )
