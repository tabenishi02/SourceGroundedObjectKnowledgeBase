from __future__ import annotations

import pytest
from test_hybrid_search import _accepted, _class, _engine

from sgokb.domain import EmbeddingSpaceSpec, ObjectSearchFilters
from sgokb.repository import Repository


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "search-validity-range-identity.sqlite")
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


@pytest.mark.parametrize(
    "valid_at",
    (
        "1900-01-01..1901-01-01",
        "2100-01-01..2200-01-01",
        "..1950-12-31",
        "2050-01-01..",
    ),
)
def test_range_keeps_statementless_accepted_version_identity_visible(repo, space, valid_at):
    object_id = repo.object_store.create_object(
        "Statementless Range Hero",
        _class(repo, "character"),
    )
    version_id, records = _accepted(
        repo,
        object_id,
        "statementless-range-v1",
        statements=[],
    )
    assert records == []

    engine, _ = _engine(repo, space)
    response = engine.search(
        "Statementless Range Hero",
        mode="lexical",
        filters=ObjectSearchFilters(knowledge_valid_at=valid_at),
    )

    matching = [result for result in response.results if result.object_id == object_id]
    assert matching
    assert matching[0].version_id == version_id


def test_statement_specific_filter_still_rejects_statementless_version(repo, space):
    object_id = repo.object_store.create_object(
        "Statementless Facet Hero",
        _class(repo, "character"),
    )
    _accepted(
        repo,
        object_id,
        "statementless-facet-v1",
        statements=[],
    )
    engine, _ = _engine(repo, space)

    response = engine.search(
        "Statementless Facet Hero",
        mode="lexical",
        filters=ObjectSearchFilters(
            knowledge_valid_at="2020-01-01..2030-01-01",
            facet="personality",
        ),
    )
    assert all(result.object_id != object_id for result in response.results)
