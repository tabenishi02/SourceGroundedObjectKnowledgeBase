import pytest

from sgokb.domain import EmbeddingSpaceSpec
from sgokb.domain.vector_index import (
    VectorIndexPoint,
    VectorMatch,
    VectorRange,
    VectorSearchFilter,
)
from sgokb.retrieval.vector_index import (
    DEFAULT_QDRANT_EF_CONSTRUCT,
    DEFAULT_QDRANT_HNSW_M,
    DEFAULT_QDRANT_SEARCH_EF,
    DEFAULT_VECTOR_INDEX_BACKEND,
    QdrantVectorIndexAdapter,
)

qdrant_client = pytest.importorskip("qdrant_client")


def test_i07_default_backend_profile_uses_100k_tuned_qdrant_hnsw():
    assert DEFAULT_VECTOR_INDEX_BACKEND == "qdrant"
    assert DEFAULT_QDRANT_HNSW_M == 16
    assert DEFAULT_QDRANT_EF_CONSTRUCT == 128
    assert DEFAULT_QDRANT_SEARCH_EF == 768


def _space(**overrides):
    values = {
        "provider_key": "test",
        "provider_version": "1",
        "model": "test-model",
        "model_revision": "rev-a",
        "dimension": 3,
        "native_dimension": 3,
        "preprocessing_key": "test",
        "preprocessing_version": "1",
        "normalize_embeddings": True,
        "max_sequence_length": 128,
        "overflow_policy": "reject",
        "output_dtype": "float32",
        "provider_configuration": "{}",
    }
    values.update(overrides)
    return EmbeddingSpaceSpec(**values)


def _adapter():
    client = qdrant_client.QdrantClient(location=":memory:")
    return QdrantVectorIndexAdapter(
        client=client,
        wait_for_index=False,
        filter_schema={
            "kind": "keyword",
            "primary_class": "keyword",
            "is_current": "bool",
            "priority": "integer",
        },
    )


def _points():
    return [
        VectorIndexPoint(
            point_id="statement:not-a-uuid:1",
            vector=(1.0, 0.0, 0.0),
            metadata={
                "kind": "statement",
                "primary_class": "character",
                "is_current": True,
                "priority": 10,
            },
        ),
        VectorIndexPoint(
            point_id="statement:not-a-uuid:2",
            vector=(0.9, 0.1, 0.0),
            metadata={
                "kind": "statement",
                "primary_class": "work",
                "is_current": True,
                "priority": 5,
            },
        ),
        VectorIndexPoint(
            point_id="historical:3",
            vector=(0.99, 0.01, 0.0),
            metadata={
                "kind": "statement",
                "primary_class": "character",
                "is_current": False,
                "priority": 1,
            },
        ),
    ]


def test_vector_point_rejects_reserved_metadata_and_dimension_mismatch():
    with pytest.raises(ValueError, match="reserved"):
        VectorIndexPoint("p", (1.0,), {"__sgokb_private": "x"})

    adapter = _adapter()
    with pytest.raises(ValueError, match="dimension"):
        adapter.rebuild(_space(), [VectorIndexPoint("bad", (1.0, 0.0), {})])


def test_qdrant_adapter_rebuild_search_filter_delete_and_metadata():
    adapter = _adapter()
    space = _space()
    metadata = adapter.rebuild(space, _points())

    assert metadata.backend_key == "qdrant"
    assert metadata.space_id == space.space_id
    assert metadata.points_count == 3
    assert metadata.dimension == 3
    assert metadata.distance == "cosine"

    hits = adapter.search(space, (1.0, 0.0, 0.0), limit=3)
    assert hits[0].point_id == "statement:not-a-uuid:1"
    assert hits[0].score >= hits[1].score

    filtered = adapter.search(
        space,
        (1.0, 0.0, 0.0),
        limit=3,
        filters=VectorSearchFilter(
            matches=(
                VectorMatch("primary_class", ("character",)),
                VectorMatch("is_current", (True,)),
            ),
            ranges=(VectorRange("priority", gte=5),),
        ),
    )
    assert [hit.point_id for hit in filtered] == ["statement:not-a-uuid:1"]

    assert adapter.delete(space, ["statement:not-a-uuid:1"]) == 1
    hits_after_delete = adapter.search(space, (1.0, 0.0, 0.0), limit=3)
    assert "statement:not-a-uuid:1" not in {hit.point_id for hit in hits_after_delete}


def test_qdrant_adapter_keeps_embedding_spaces_physically_isolated():
    adapter = _adapter()
    first = _space(model_revision="first")
    second = _space(model_revision="second")
    adapter.rebuild(first, _points()[:1])
    adapter.rebuild(second, _points()[1:])

    assert adapter.metadata(first).points_count == 1
    assert adapter.metadata(second).points_count == 2
    assert adapter.search(first, (1.0, 0.0, 0.0), limit=3)[0].point_id == "statement:not-a-uuid:1"
    assert adapter.search(second, (1.0, 0.0, 0.0), limit=3)[0].point_id != "statement:not-a-uuid:1"

    adapter.drop(first)
    with pytest.raises(RuntimeError, match="unavailable"):
        adapter.metadata(first)
    assert adapter.metadata(second).points_count == 2


def test_qdrant_adapter_rejects_invalid_query_limit_and_dimension():
    adapter = _adapter()
    space = _space()
    adapter.rebuild(space, _points())
    with pytest.raises(ValueError, match="limit"):
        adapter.search(space, (1.0, 0.0, 0.0), limit=0)
    with pytest.raises(ValueError, match="dimension"):
        adapter.search(space, (1.0, 0.0), limit=1)
