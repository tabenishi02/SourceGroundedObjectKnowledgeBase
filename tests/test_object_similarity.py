import math

import pytest

from sgokb.domain import (
    DerivationKind,
    EmbeddingSpaceSpec,
    EvidenceExtractionMode,
    EvidenceTargetKind,
    FacetStatus,
    VectorIndexMetadata,
    VectorSearchHit,
)
from sgokb.repository import Repository
from sgokb.retrieval import (
    KnowledgeVectorIndexBuilder,
    ObjectSimilaritySearch,
    SearchRepresentationBuilder,
)


class FakeVectorIndex:
    backend_key = "fake-exact"

    def __init__(self):
        self.points = {}

    @staticmethod
    def _matches(point, filters):
        if filters is None:
            return True
        for condition in filters.matches:
            value = point.metadata.get(condition.field)
            if isinstance(value, tuple):
                if not any(expected in value for expected in condition.values):
                    return False
            elif value not in condition.values:
                return False
        for condition in filters.excludes:
            value = point.metadata.get(condition.field)
            if isinstance(value, tuple):
                if any(expected in value for expected in condition.values):
                    return False
            elif value in condition.values:
                return False
        return True

    def upsert(self, space, points):
        for point in points:
            self.points[point.point_id] = point
        return len(points)

    def search(self, space, query_vector, *, limit, filters=None):
        query_length = math.sqrt(sum(value * value for value in query_vector))
        scored = []
        for point in self.points.values():
            if not self._matches(point, filters):
                continue
            vector_length = math.sqrt(sum(value * value for value in point.vector))
            score = sum(a * b for a, b in zip(query_vector, point.vector)) / (
                query_length * vector_length
            )
            scored.append((point.point_id, score, point.metadata))
        scored.sort(key=lambda item: (-item[1], item[0]))
        return tuple(
            VectorSearchHit(point_id=pid, score=score, rank=rank, metadata=metadata)
            for rank, (pid, score, metadata) in enumerate(scored[:limit], start=1)
        )

    def delete(self, space, point_ids):
        count = 0
        for point_id in point_ids:
            count += int(self.points.pop(point_id, None) is not None)
        return count

    def rebuild(self, space, points):
        self.points = {point.point_id: point for point in points}
        return VectorIndexMetadata(
            backend_key=self.backend_key,
            backend_version="1",
            space_id=space.space_id,
            dimension=space.dimension,
            distance="cosine",
            points_count=len(points),
            indexed_points_count=len(points),
            approximate=False,
            status="ready",
        )

    def metadata(self, space):
        return self.rebuild(space, list(self.points.values()))

    def drop(self, space):
        self.points.clear()


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "object-similarity.sqlite")
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


def _class(repo, key):
    return repo.object_store.class_by_key(key).class_id


def _evidence(repo, suffix):
    source_id = repo.source_store.create_source(f"Similarity Source {suffix}")
    locator_id = repo.source_store.add_locator(
        source_id, "url", f"https://example.test/similarity/{suffix}", preferred=True
    )
    snapshot_id = repo.source_store.create_snapshot(
        source_id,
        "2026-10-14T00:00:00Z",
        "test",
        observed_locator_id=locator_id,
        title=f"Similarity {suffix}",
    )
    artifact_id = repo.source_store.add_raw_artifact(
        snapshot_id, "html", f"memory://similarity/{suffix}", "a" * 64, 10
    )
    run_id = repo.source_store.create_normalization_run(snapshot_id, "fixture", "1", [artifact_id])
    return repo.source_store.add_evidence(
        run_id, f"Evidence for {suffix}", EvidenceExtractionMode.NORMALIZED, language="ja"
    )


def _accepted(repo, object_id, version_id, *, base=None, statements=None):
    version_id = repo.version_store.begin_candidate(object_id, base, version_id=version_id)
    evidence_id = _evidence(repo, version_id)
    for index, item in enumerate(statements or []):
        facet_id = None
        if item.get("facet") is not None:
            facet_id = repo.semantic_store.facet_by_key(item["facet"]).facet_id
            repo.semantic_store.set_version_facet(version_id, facet_id, FacetStatus.CONTENT)
        statement_id = repo.semantic_store.add_statement(
            version_id,
            f"s-{index}",
            item["text"],
            DerivationKind.DIRECT_STATEMENT,
            facet_id=facet_id,
        )
        repo.source_store.link_evidence(
            version_id, EvidenceTargetKind.STATEMENT, statement_id, evidence_id
        )
    repo.version_store.accept_candidate(version_id)
    SearchRepresentationBuilder(repo).materialize_version(version_id)
    return version_id


def _save_embeddings(repo, space, vectors):
    rows = repo.rows(
        """SELECT m.object_id,m.version_id,m.target_kind,m.representation_id,f.key AS facet
           FROM knowledge_search_representation_memberships m
           LEFT JOIN facet_definitions f ON f.id=m.facet_id
           ORDER BY m.id"""
    )
    for row in rows:
        key = (row["object_id"], row["version_id"], row["target_kind"], row["facet"])
        vector = vectors.get(key)
        if vector is None:
            vector = vectors.get((row["object_id"], row["target_kind"], row["facet"]))
        if vector is None:
            vector = (0.0, 0.0, 1.0)
        repo.embedding_store.save_representation_embedding(
            space, row["representation_id"], list(vector)
        )


def _finder(repo, space, vectors):
    _save_embeddings(repo, space, vectors)
    index = FakeVectorIndex()
    KnowledgeVectorIndexBuilder(repo, index).rebuild(space)
    return ObjectSimilaritySearch(repo, space=space, vector_index=index), index


def _fixture_objects(repo):
    source = repo.object_store.create_object("Source Character", _class(repo, "character"))
    near = repo.object_store.create_object("Near Character", _class(repo, "character"))
    far = repo.object_store.create_object("Far Character", _class(repo, "character"))
    work = repo.object_store.create_object("Near Work", _class(repo, "work"))
    _accepted(
        repo,
        source,
        "source-v1",
        statements=[
            {"facet": "personality", "text": "仲間を優先する"},
            {"facet": "values", "text": "信頼を重視する"},
        ],
    )
    _accepted(
        repo,
        near,
        "near-v1",
        statements=[
            {"facet": "personality", "text": "友人を守る"},
            {"facet": "values", "text": "信頼関係を重んじる"},
        ],
    )
    _accepted(
        repo,
        far,
        "far-v1",
        statements=[{"facet": "values", "text": "独立を重視する"}],
    )
    _accepted(repo, work, "work-v1", statements=[{"facet": "themes", "text": "友情"}])
    return source, near, far, work


def test_overall_similarity_defaults_to_same_primary_class_and_excludes_source(repo, space):
    source, near, far, work = _fixture_objects(repo)
    finder, _ = _finder(
        repo,
        space,
        {
            (source, "object_overall", None): (1.0, 0.0, 0.0),
            (near, "object_overall", None): (0.95, 0.05, 0.0),
            (far, "object_overall", None): (0.2, 0.8, 0.0),
            (work, "object_overall", None): (0.999, 0.001, 0.0),
        },
    )

    response = finder.find_similar_objects(source, limit=2)
    assert [result.object_id for result in response.results] == [near, far]
    assert response.results[0].score > response.results[1].score
    assert response.results[0].score_type == "cosine_similarity"
    assert response.results[0].matched_facet is None
    assert response.results[0].version_id == "near-v1"
    assert work not in {result.object_id for result in response.results}
    assert source not in {result.object_id for result in response.results}


def test_cross_class_is_explicit_and_can_return_other_primary_classes(repo, space):
    source, near, _, work = _fixture_objects(repo)
    finder, _ = _finder(
        repo,
        space,
        {
            (source, "object_overall", None): (1.0, 0.0, 0.0),
            (near, "object_overall", None): (0.8, 0.2, 0.0),
            (work, "object_overall", None): (0.999, 0.001, 0.0),
        },
    )

    response = finder.find_similar_objects(source, cross_class=True, limit=10)
    assert response.cross_class is True
    assert response.results[0].object_id == work
    assert response.results[0].primary_class == "work"


def test_facet_similarity_compares_only_same_facet_and_missing_candidates_are_absent(repo, space):
    source, near, far, _ = _fixture_objects(repo)
    finder, _ = _finder(
        repo,
        space,
        {
            (source, "facet", "personality"): (0.0, 1.0, 0.0),
            (near, "facet", "personality"): (0.1, 0.99, 0.0),
            (far, "object_overall", None): (0.0, 1.0, 0.0),
        },
    )

    response = finder.find_similar_objects(source, facet="personality", limit=10)
    assert response.facet == "personality"
    assert [result.object_id for result in response.results] == [near]
    assert response.results[0].matched_facet == "personality"
    assert far not in {result.object_id for result in response.results}


def test_missing_source_facet_is_error_and_never_falls_back_to_overall(repo, space):
    source, near, _, _ = _fixture_objects(repo)
    finder, _ = _finder(
        repo,
        space,
        {
            (source, "object_overall", None): (1.0, 0.0, 0.0),
            (near, "object_overall", None): (0.99, 0.01, 0.0),
        },
    )

    with pytest.raises(ValueError, match="no content Facet: themes"):
        finder.find_similar_objects(source, facet="themes")
    with pytest.raises(ValueError, match="Unknown Facet"):
        finder.find_similar_objects(source, facet="not_a_facet")


def test_only_current_target_version_is_returned_and_target_version_is_explained(repo, space):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    target = repo.object_store.create_object("Target", _class(repo, "character"))
    _accepted(repo, source, "source-v1", statements=[])
    first = _accepted(repo, target, "target-v1", statements=[])
    _accepted(repo, target, "target-v2", base=first, statements=[])
    finder, _ = _finder(
        repo,
        space,
        {
            (source, "source-v1", "object_overall", None): (1.0, 0.0, 0.0),
            (target, "target-v1", "object_overall", None): (1.0, 0.0, 0.0),
            (target, "target-v2", "object_overall", None): (0.7, 0.3, 0.0),
        },
    )

    response = finder.find_similar_objects(source)
    assert len(response.results) == 1
    assert response.results[0].object_id == target
    assert response.results[0].version_id == "target-v2"


def test_explicit_historical_source_version_uses_that_versions_embedding(repo, space):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    left = repo.object_store.create_object("Left", _class(repo, "character"))
    right = repo.object_store.create_object("Right", _class(repo, "character"))
    first = _accepted(
        repo,
        source,
        "source-v1",
        statements=[{"facet": "personality", "text": "左側の性格"}],
    )
    _accepted(
        repo,
        source,
        "source-v2",
        base=first,
        statements=[{"facet": "personality", "text": "右側の性格"}],
    )
    _accepted(repo, left, "left-v1", statements=[])
    _accepted(repo, right, "right-v1", statements=[])
    finder, _ = _finder(
        repo,
        space,
        {
            (source, "source-v1", "object_overall", None): (1.0, 0.0, 0.0),
            (source, "source-v2", "object_overall", None): (0.0, 1.0, 0.0),
            (left, "object_overall", None): (0.99, 0.01, 0.0),
            (right, "object_overall", None): (0.01, 0.99, 0.0),
        },
    )

    historical = finder.find_similar_objects(source, source_version_id="source-v1")
    current = finder.find_similar_objects(source)
    assert historical.source_version_id == "source-v1"
    assert historical.results[0].object_id == left
    assert current.source_version_id == "source-v2"
    assert current.results[0].object_id == right


def test_missing_source_embedding_fails_explicitly(repo, space):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    _accepted(repo, source, "source-v1", statements=[])
    index = FakeVectorIndex()
    finder = ObjectSimilaritySearch(repo, space=space, vector_index=index)

    with pytest.raises(RuntimeError, match="no embedding"):
        finder.find_similar_objects(source)


def test_invalid_limit_and_source_version_are_rejected(repo, space):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    _accepted(repo, source, "source-v1", statements=[])
    finder, _ = _finder(repo, space, {(source, "object_overall", None): (1.0, 0.0, 0.0)})

    with pytest.raises(ValueError, match="between 1 and 1000"):
        finder.find_similar_objects(source, limit=1001)
    with pytest.raises(ValueError, match="accepted Version"):
        finder.find_similar_objects(source, source_version_id="missing-version")


def test_qdrant_adapter_supports_overall_and_facet_similarity(repo, space):
    qdrant_client = pytest.importorskip("qdrant_client")
    from sgokb.retrieval.vector_index import QdrantVectorIndexAdapter

    source = repo.object_store.create_object("Qdrant Source", _class(repo, "character"))
    target = repo.object_store.create_object("Qdrant Target", _class(repo, "character"))
    _accepted(
        repo,
        source,
        "qdrant-source-v1",
        statements=[{"facet": "personality", "text": "仲間を優先する"}],
    )
    _accepted(
        repo,
        target,
        "qdrant-target-v1",
        statements=[{"facet": "personality", "text": "友人を守る"}],
    )
    _save_embeddings(
        repo,
        space,
        {
            (source, "object_overall", None): (1.0, 0.0, 0.0),
            (target, "object_overall", None): (0.99, 0.01, 0.0),
            (source, "facet", "personality"): (0.0, 1.0, 0.0),
            (target, "facet", "personality"): (0.01, 0.99, 0.0),
        },
    )
    adapter = QdrantVectorIndexAdapter(
        client=qdrant_client.QdrantClient(location=":memory:"),
        wait_for_index=False,
    )
    KnowledgeVectorIndexBuilder(repo, adapter).rebuild(space)
    finder = ObjectSimilaritySearch(repo, space=space, vector_index=adapter)

    overall = finder.find_similar_objects(source)
    facet = finder.find_similar_objects(source, facet="personality")
    assert overall.results[0].object_id == target
    assert overall.results[0].matched_facet is None
    assert facet.results[0].object_id == target
    assert facet.results[0].matched_facet == "personality"

