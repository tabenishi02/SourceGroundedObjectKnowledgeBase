import hashlib
import importlib
import json
import math

import pytest

from sgokb.application_maintenance import (
    DerivedMaintenanceError,
    DerivedMaintenanceRuntimeUnavailableError,
    DerivedMaintenanceSupersededError,
    DerivedSearchMaintenanceApplication,
)
from sgokb.application_read import KnowledgeReadApplication
from sgokb.domain import (
    DerivationKind,
    DerivedState,
    EmbeddingSpaceSpec,
    EvidenceExtractionMode,
    EvidenceTargetKind,
    FacetStatus,
    VectorIndexMetadata,
    VectorSearchHit,
)
from sgokb.repository import Repository
from sgokb.retrieval import (
    HybridObjectSearch,
    KnowledgeVectorIndexBuilder,
    KnowledgeVectorMaintenanceBuilder,
    ObjectSimilaritySearch,
)


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "n04p04-vector-index-sync.sqlite")
    yield value
    value.close()


def _space():
    return EmbeddingSpaceSpec(
        provider_key="fake-local",
        provider_version="1",
        model="fake-model",
        model_revision="space-a",
        dimension=3,
        native_dimension=3,
        preprocessing_key="sgokb-search-representation",
        preprocessing_version="2",
        query_instruction="",
        document_instruction="",
        normalize_embeddings=True,
        max_sequence_length=1024,
        overflow_policy="reject",
        output_dtype="float32",
        provider_configuration="{}",
    )


class FakeEmbeddingProvider:
    def __init__(self, space=None):
        self._space = space or _space()
        self.document_calls = []
        self.query_calls = []

    @property
    def space(self):
        return self._space

    def embed_documents(self, texts):
        self.document_calls.append(tuple(texts))
        return [[1.0, 0.0, 0.0] for _ in texts]

    def embed_queries(self, texts):
        self.query_calls.append(tuple(texts))
        return [[1.0, 0.0, 0.0] for _ in texts]


class FakeVectorIndex:
    backend_key = "fake-exact"

    def __init__(self, *, fail_upsert=False, fail_rebuild=False, on_write=None):
        self.points = {}
        self.fail_upsert = fail_upsert
        self.fail_rebuild = fail_rebuild
        self.on_write = on_write
        self.upsert_calls = 0
        self.rebuild_calls = 0

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
        for condition in filters.ranges:
            value = point.metadata.get(condition.field)
            if value is None:
                return False
            if condition.gt is not None and not value > condition.gt:
                return False
            if condition.gte is not None and not value >= condition.gte:
                return False
            if condition.lt is not None and not value < condition.lt:
                return False
            if condition.lte is not None and not value <= condition.lte:
                return False
        return True

    def upsert(self, space, points):
        self.upsert_calls += 1
        if self.on_write is not None:
            self.on_write()
        if self.fail_upsert:
            raise RuntimeError("simulated vector upsert failure")
        for point in points:
            if len(point.vector) != space.dimension:
                raise ValueError("dimension")
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
        self.rebuild_calls += 1
        if self.on_write is not None:
            self.on_write()
        if self.fail_rebuild:
            raise RuntimeError("simulated vector rebuild failure")
        self.points = {point.point_id: point for point in points}
        return self.metadata(space)

    def metadata(self, space):
        return VectorIndexMetadata(
            backend_key=self.backend_key,
            backend_version="1",
            space_id=space.space_id,
            dimension=space.dimension,
            distance="cosine",
            points_count=len(self.points),
            indexed_points_count=len(self.points),
            approximate=False,
            status="ready",
        )

    def drop(self, space):
        self.points.clear()


def _character_class(repo):
    return repo.object_store.class_by_key("character").class_id


def _accepted_version(
    repo,
    object_id,
    version_id,
    *,
    base_version_id=None,
    statement_text="Chooses self sacrifice to protect companions.",
):
    version_id = repo.version_store.begin_candidate(
        object_id,
        base_version_id,
        version_id=version_id,
    )
    personality = repo.semantic_store.facet_by_key("personality").facet_id
    repo.semantic_store.set_version_facet(version_id, personality, FacetStatus.CONTENT)
    statement_id = repo.semantic_store.add_statement(
        version_id,
        "personality-1",
        statement_text,
        DerivationKind.DIRECT_STATEMENT,
        facet_id=personality,
        language="en",
    )
    source = repo.source_store.create_source(f"Source {version_id}")
    locator = repo.source_store.add_locator(
        source,
        "url",
        f"https://example.test/{version_id}",
    )
    snapshot = repo.source_store.create_snapshot(
        source,
        "2026-10-16T00:00:00Z",
        "test_fixture",
        observed_locator_id=locator,
    )
    raw = statement_text.encode("utf-8")
    artifact = repo.source_store.add_raw_artifact(
        snapshot,
        "document",
        f"fixture/{version_id}.txt",
        hashlib.sha256(raw).hexdigest(),
        len(raw),
    )
    run = repo.source_store.create_normalization_run(snapshot, "fixture", "1", [artifact])
    evidence = repo.source_store.add_evidence(
        run,
        statement_text,
        EvidenceExtractionMode.VERBATIM,
    )
    repo.source_store.link_evidence(
        version_id,
        EvidenceTargetKind.STATEMENT,
        statement_id,
        evidence,
    )
    repo.version_store.accept_candidate(version_id)
    return version_id


def _derived_state(repo, object_id, kind):
    return next(item for item in repo.version_store.derived_states(object_id) if item.kind == kind)


def _prepare_embedding_ready(repo, object_id, provider):
    service = DerivedSearchMaintenanceApplication(repo, embedding_provider=provider)
    service.sync_search_representation(object_id)
    result = service.sync_embedding(object_id)
    assert result.state == "ready"
    return result


def _vector_service(repo, provider, vector_index):
    return DerivedSearchMaintenanceApplication(
        repo,
        embedding_provider=provider,
        vector_index=vector_index,
        embedding_space=provider.space,
    )


def test_vector_sync_requires_explicit_runtime_and_leaves_pending(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    _accepted_version(repo, object_id, "alpha-v1")
    provider = FakeEmbeddingProvider()
    _prepare_embedding_ready(repo, object_id, provider)
    before = _derived_state(repo, object_id, "vector_index")

    with pytest.raises(DerivedMaintenanceRuntimeUnavailableError, match="Vector backend"):
        DerivedSearchMaintenanceApplication(
            repo,
            embedding_provider=provider,
        ).sync_vector_index(object_id)

    assert _derived_state(repo, object_id, "vector_index") == before


def test_vector_sync_requires_embedding_ready_without_writing_backend(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    _accepted_version(repo, object_id, "alpha-v1")
    provider = FakeEmbeddingProvider()
    DerivedSearchMaintenanceApplication(repo).sync_search_representation(object_id)
    index = FakeVectorIndex()

    with pytest.raises(DerivedMaintenanceError, match="embedding to be ready"):
        _vector_service(repo, provider, index).sync_vector_index(object_id)

    assert index.upsert_calls == 0
    assert _derived_state(repo, object_id, "vector_index").status is DerivedState.PENDING


def test_vector_sync_upserts_membership_points_and_marks_ready(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    version_id = _accepted_version(repo, object_id, "alpha-v1")
    provider = FakeEmbeddingProvider()
    _prepare_embedding_ready(repo, object_id, provider)
    index = FakeVectorIndex()

    result = _vector_service(repo, provider, index).sync_vector_index(object_id)

    assert result.version_id == version_id
    assert result.point_count == 3
    assert result.written_point_count == 3
    assert result.state == "ready"
    assert len(index.points) == 3
    assert all(point.metadata["object_id"] == object_id for point in index.points.values())
    assert all(point.metadata["is_current"] is True for point in index.points.values())
    assert _derived_state(repo, object_id, "vector_index").status is DerivedState.READY


def test_new_version_refreshes_historical_is_current_metadata(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    first_version = _accepted_version(repo, object_id, "alpha-v1")
    provider = FakeEmbeddingProvider()
    _prepare_embedding_ready(repo, object_id, provider)
    index = FakeVectorIndex()
    service = _vector_service(repo, provider, index)
    service.sync_vector_index(object_id)

    second_version = _accepted_version(
        repo,
        object_id,
        "alpha-v2",
        base_version_id=first_version,
    )
    _prepare_embedding_ready(repo, object_id, provider)
    result = service.sync_vector_index(object_id)

    assert result.version_id == second_version
    assert result.point_count == 6
    assert len(index.points) == 6
    first_points = [
        point for point in index.points.values() if point.metadata["version_id"] == first_version
    ]
    second_points = [
        point for point in index.points.values() if point.metadata["version_id"] == second_version
    ]
    assert len(first_points) == 3
    assert len(second_points) == 3
    assert all(point.metadata["is_current"] is False for point in first_points)
    assert all(point.metadata["is_current"] is True for point in second_points)
    assert {point.metadata["representation_id"] for point in first_points} == {
        point.metadata["representation_id"] for point in second_points
    }


def test_missing_historical_embedding_is_explicit_failure(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    first_version = _accepted_version(
        repo,
        object_id,
        "alpha-v1",
        statement_text="Old unique description.",
    )
    provider = FakeEmbeddingProvider()
    _prepare_embedding_ready(repo, object_id, provider)

    second_version = _accepted_version(
        repo,
        object_id,
        "alpha-v2",
        base_version_id=first_version,
        statement_text="New unique description.",
    )
    _prepare_embedding_ready(repo, object_id, provider)
    old_memberships = repo.semantic_store.knowledge_search_memberships(version_id=first_version)
    current_ids = {
        row["representation_id"]
        for row in repo.semantic_store.knowledge_search_memberships(version_id=second_version)
    }
    old_unique = next(
        row["representation_id"]
        for row in old_memberships
        if row["representation_id"] not in current_ids
    )
    with repo.db:
        repo.db.execute(
            "DELETE FROM search_representation_embeddings WHERE space_id=? AND representation_id=?",
            (provider.space.space_id, old_unique),
        )

    with pytest.raises(DerivedMaintenanceError, match="missing=1"):
        _vector_service(repo, provider, FakeVectorIndex()).sync_vector_index(object_id)

    state = _derived_state(repo, object_id, "vector_index")
    assert state.status is DerivedState.FAILED
    assert "missing=1" in state.last_error


def test_vector_backend_failure_marks_failed_and_preserves_canonical_knowledge(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    version_id = _accepted_version(repo, object_id, "alpha-v1")
    provider = FakeEmbeddingProvider()
    _prepare_embedding_ready(repo, object_id, provider)
    before = KnowledgeReadApplication(repo).get_object(object_id)

    with pytest.raises(DerivedMaintenanceError, match="simulated vector upsert failure"):
        _vector_service(
            repo,
            provider,
            FakeVectorIndex(fail_upsert=True),
        ).sync_vector_index(object_id)

    state = _derived_state(repo, object_id, "vector_index")
    assert state.status is DerivedState.FAILED
    assert "simulated vector upsert failure" in state.last_error
    assert repo.version_store.current_version_id(object_id) == version_id
    assert KnowledgeReadApplication(repo).get_object(object_id) == before


@pytest.mark.parametrize("fail_after_superseding", [False, True])
def test_superseded_vector_attempt_cannot_mark_new_revision_ready_or_failed(
    repo,
    fail_after_superseding,
):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    first_version = _accepted_version(repo, object_id, "alpha-v1")
    provider = FakeEmbeddingProvider()
    _prepare_embedding_ready(repo, object_id, provider)

    def supersede():
        _accepted_version(
            repo,
            object_id,
            "alpha-v2",
            base_version_id=first_version,
            statement_text="A newer accepted description.",
        )

    index = FakeVectorIndex(
        fail_upsert=fail_after_superseding,
        on_write=supersede,
    )
    with pytest.raises(DerivedMaintenanceSupersededError, match="superseded|dependency changed"):
        _vector_service(repo, provider, index).sync_vector_index(object_id)

    state = _derived_state(repo, object_id, "vector_index")
    assert state.target_version_id == "alpha-v2"
    assert state.revision == 2
    assert state.status is DerivedState.PENDING
    assert state.last_error is None


def test_full_rebuild_recovers_backend_and_enables_semantic_and_similarity(repo):
    alpha = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    beta = repo.object_store.create_object("Beta Hero", _character_class(repo))
    _accepted_version(repo, alpha, "alpha-v1")
    _accepted_version(repo, beta, "beta-v1", statement_text="Protects friends in battle.")
    provider = FakeEmbeddingProvider()
    _prepare_embedding_ready(repo, alpha, provider)
    _prepare_embedding_ready(repo, beta, provider)
    index = FakeVectorIndex()
    unprepared = repo.object_store.create_object("Unprepared Hero", _character_class(repo))
    _accepted_version(repo, unprepared, "unprepared-v1")

    result = _vector_service(repo, provider, index).rebuild_vector_index()

    assert result.point_count == 6
    assert result.ready_object_count == 2
    assert _derived_state(repo, unprepared, "vector_index").status is DerivedState.PENDING
    assert result.state == "ready"
    assert len(index.points) == 6
    assert _derived_state(repo, alpha, "vector_index").status is DerivedState.READY
    assert _derived_state(repo, beta, "vector_index").status is DerivedState.READY

    semantic = HybridObjectSearch(
        repo,
        embedding_provider=provider,
        vector_index=index,
    ).search("protect companions", mode="semantic")
    assert {item.object_id for item in semantic.results} == {alpha, beta}

    similar = ObjectSimilaritySearch(
        repo,
        space=provider.space,
        vector_index=index,
    ).find_similar_objects(alpha)
    assert similar.results
    assert similar.results[0].object_id == beta


def test_full_rebuild_missing_embedding_fails_without_ready_promotion(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    _accepted_version(repo, object_id, "alpha-v1")
    provider = FakeEmbeddingProvider()
    DerivedSearchMaintenanceApplication(repo).sync_search_representation(object_id)
    repo.embedding_store.ensure_space(provider.space)
    before = _derived_state(repo, object_id, "vector_index")

    with pytest.raises(DerivedMaintenanceError, match="missing=3"):
        _vector_service(repo, provider, FakeVectorIndex()).rebuild_vector_index()

    assert _derived_state(repo, object_id, "vector_index") == before


def test_exported_builder_and_cli_rebuild_do_not_change_derived_lifecycle(
    repo, tmp_path, capsys, monkeypatch
):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    _accepted_version(repo, object_id, "alpha-v1")
    provider = FakeEmbeddingProvider()
    _prepare_embedding_ready(repo, object_id, provider)
    before = repo.version_store.derived_states(object_id)
    calls_before = list(provider.document_calls)
    assert _derived_state(repo, object_id, "vector_index").status is DerivedState.PENDING
    assert KnowledgeVectorIndexBuilder is KnowledgeVectorMaintenanceBuilder

    direct_index = FakeVectorIndex()
    metadata = KnowledgeVectorIndexBuilder(repo, direct_index).rebuild(provider.space)
    assert metadata.points_count == 3
    assert len(direct_index.points) == 3
    assert repo.version_store.derived_states(object_id) == before

    cli_module = importlib.import_module("sgokb.cli.main")
    cli_index = FakeVectorIndex()
    monkeypatch.setattr(cli_module, "semantic_runtime", lambda: (provider, cli_index))
    assert (
        cli_module.main(
            [
                "--db",
                str(tmp_path / "n04p04-vector-index-sync.sqlite"),
                "system",
                "index",
                "rebuild",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["data"]["points_count"] == 3
    assert len(cli_index.points) == 3
    assert repo.version_store.derived_states(object_id) == before
    assert provider.document_calls == calls_before


@pytest.mark.parametrize("change", ["new_object", "new_version"])
def test_full_rebuild_rejects_catalog_changes_without_ready_promotion(repo, change):
    alpha = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    version = _accepted_version(repo, alpha, "alpha-v1")
    provider = FakeEmbeddingProvider()
    _prepare_embedding_ready(repo, alpha, provider)
    targets = [alpha]

    def supersede():
        if change == "new_object":
            beta = repo.object_store.create_object("Beta Hero", _character_class(repo))
            targets.append(beta)
            _accepted_version(repo, beta, "beta-v1")
        else:
            _accepted_version(repo, alpha, "alpha-v2", base_version_id=version)

    index = FakeVectorIndex(on_write=supersede)
    with pytest.raises(DerivedMaintenanceSupersededError, match="catalog changed"):
        _vector_service(repo, provider, index).rebuild_vector_index()
    for object_id in targets:
        state = _derived_state(repo, object_id, "vector_index")
        assert state.status is DerivedState.PENDING
        assert state.last_error is None
    assert repo.version_store.version_by_id(version).state.value == "accepted"


def test_full_rebuild_backend_failure_preserves_all_objects_and_states(repo):
    alpha = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    beta = repo.object_store.create_object("Beta Hero", _character_class(repo))
    provider = FakeEmbeddingProvider()
    for object_id, version in ((alpha, "alpha-v1"), (beta, "beta-v1")):
        _accepted_version(repo, object_id, version)
        _prepare_embedding_ready(repo, object_id, provider)
    reader = KnowledgeReadApplication(repo)
    before_knowledge = {oid: reader.get_object(oid) for oid in (alpha, beta)}
    before_states = {oid: repo.version_store.derived_states(oid) for oid in (alpha, beta)}
    calls_before = list(provider.document_calls)

    with pytest.raises(DerivedMaintenanceError, match="simulated vector rebuild failure"):
        _vector_service(repo, provider, FakeVectorIndex(fail_rebuild=True)).rebuild_vector_index()
    assert {oid: reader.get_object(oid) for oid in (alpha, beta)} == before_knowledge
    assert {oid: repo.version_store.derived_states(oid) for oid in (alpha, beta)} == before_states
    assert provider.document_calls == calls_before
