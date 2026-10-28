from __future__ import annotations

import pytest
from test_hybrid_search import _accepted, _class, _engine
from test_hybrid_search_r2 import (
    _accepted_r2,
    _activate_r2_generation,
    _engine as _r2_engine,
)

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

    overlap_filter = ObjectSearchFilters(knowledge_valid_at="2026-06-01..2027-06-01")
    overlap = engine.search("期間対象", mode="semantic", filters=overlap_filter)
    ids = _statement_ids(overlap)
    assert dated_2026["statement_id"] in ids
    assert dated_2028["statement_id"] not in ids
    assert timeless["statement_id"] in ids

    lexical_overlap = engine.search("期間対象", mode="lexical", filters=overlap_filter)
    ids = _statement_ids(lexical_overlap)
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


@pytest.mark.parametrize(
    "valid_at",
    (
        "1900-01-01..1901-01-01",
        "2100-01-01..2200-01-01",
        "..1950-12-31",
        "2050-01-01..",
    ),
)
def test_range_registry_identity_uses_current_canonical_version_when_generation_lags(
    repo,
    space,
    valid_at,
):
    object_id = repo.object_store.create_object(
        "Lagged Range Hero",
        _class(repo, "character"),
    )
    _accepted_r2(
        repo,
        object_id,
        "lagged-range-v1",
        [{"facet": "personality", "text": "old active generation knowledge"}],
    )
    generation_id = _activate_r2_generation(repo)

    current_version_id = _accepted_r2(
        repo,
        object_id,
        "lagged-range-v2",
        [{"facet": "personality", "text": "new current canonical knowledge"}],
    )
    engine, _ = _r2_engine(repo, space, generation_id)
    filters = ObjectSearchFilters(knowledge_valid_at=valid_at)

    identity = engine.search("Lagged Range Hero", mode="lexical", filters=filters)
    matching = [result for result in identity.results if result.object_id == object_id]
    assert matching
    assert matching[0].version_id == current_version_id

    # Preserve the R2 isolation contract for derived Knowledge channels: the new
    # Version is canonical/current but is not silently injected into the older
    # active generation's lexical Knowledge membership.
    content = engine.search("new current canonical knowledge", mode="lexical", filters=filters)
    assert all(result.object_id != object_id for result in content.results)
