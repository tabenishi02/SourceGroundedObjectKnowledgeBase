import hashlib

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
)
from sgokb.repository import Repository


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "n04p03-embedding-sync.sqlite")
    yield value
    value.close()


def _space(revision="space-a"):
    return EmbeddingSpaceSpec(
        provider_key="fake-local",
        provider_version="1",
        model="fake-model",
        model_revision=revision,
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
    def __init__(self, space=None, *, fail=False, on_embed=None):
        self._space = space or _space()
        self.fail = fail
        self.on_embed = on_embed
        self.calls = []

    @property
    def space(self):
        return self._space

    def embed_documents(self, texts):
        self.calls.append(tuple(texts))
        if self.on_embed is not None:
            self.on_embed()
        if self.fail:
            raise RuntimeError("simulated local embedding failure")
        return [[1.0, 0.0, 0.0] for _ in texts]

    def embed_queries(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]


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


def _prepare_search_ready(repo, object_id):
    service = DerivedSearchMaintenanceApplication(repo)
    result = service.sync_search_representation(object_id)
    assert result.state == "ready"
    return result


def test_embedding_sync_generates_only_missing_current_representations_and_marks_ready(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    version_id = _accepted_version(repo, object_id, "alpha-v1")
    search = _prepare_search_ready(repo, object_id)
    provider = FakeEmbeddingProvider()
    service = DerivedSearchMaintenanceApplication(repo, embedding_provider=provider)

    result = service.sync_embedding(object_id)

    assert result.object_id == object_id
    assert result.version_id == version_id
    assert result.representation_count == search.unique_representation_count == 3
    assert result.created_embedding_count == 3
    assert result.reused_embedding_count == 0
    assert result.changed is True
    assert result.state == "ready"
    assert len(provider.calls) == 1
    assert len(provider.calls[0]) == 3
    assert len(repo.embedding_store.embedding_rows(provider.space.space_id)) == 3
    assert _derived_state(repo, object_id, "embedding").status is DerivedState.READY
    assert _derived_state(repo, object_id, "vector_index").status is DerivedState.PENDING


def test_embedding_sync_without_provider_leaves_pending_unattempted(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    _accepted_version(repo, object_id, "alpha-v1")
    _prepare_search_ready(repo, object_id)
    before = _derived_state(repo, object_id, "embedding")

    with pytest.raises(DerivedMaintenanceRuntimeUnavailableError, match="explicitly injected"):
        DerivedSearchMaintenanceApplication(repo).sync_embedding(object_id)

    after = _derived_state(repo, object_id, "embedding")
    assert after == before
    assert repo.one("SELECT count(*) AS n FROM search_embedding_spaces")["n"] == 0


def test_embedding_sync_requires_ready_search_representation_without_calling_provider(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    _accepted_version(repo, object_id, "alpha-v1")
    provider = FakeEmbeddingProvider()

    with pytest.raises(DerivedMaintenanceError, match="search_representation to be ready"):
        DerivedSearchMaintenanceApplication(repo, embedding_provider=provider).sync_embedding(
            object_id
        )

    assert provider.calls == []
    assert _derived_state(repo, object_id, "embedding").status is DerivedState.PENDING


def test_ready_rerun_reuses_embeddings_without_provider_recall(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    _accepted_version(repo, object_id, "alpha-v1")
    _prepare_search_ready(repo, object_id)
    provider = FakeEmbeddingProvider()
    service = DerivedSearchMaintenanceApplication(repo, embedding_provider=provider)

    first = service.sync_embedding(object_id)
    second = service.sync_embedding(object_id)

    assert first.created_embedding_count == 3
    assert second.created_embedding_count == 0
    assert second.reused_embedding_count == 3
    assert second.changed is False
    assert len(provider.calls) == 1


def test_new_version_reuses_existing_representation_embeddings_without_provider_recall(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    first_version = _accepted_version(repo, object_id, "alpha-v1")
    _prepare_search_ready(repo, object_id)
    provider = FakeEmbeddingProvider()
    service = DerivedSearchMaintenanceApplication(repo, embedding_provider=provider)
    first = service.sync_embedding(object_id)
    assert first.created_embedding_count == 3
    assert len(provider.calls) == 1

    second_version = _accepted_version(
        repo,
        object_id,
        "alpha-v2",
        base_version_id=first_version,
    )
    _prepare_search_ready(repo, object_id)
    second = service.sync_embedding(object_id)

    assert second.version_id == second_version
    assert second.created_embedding_count == 0
    assert second.reused_embedding_count == 3
    assert len(provider.calls) == 1
    assert _derived_state(repo, object_id, "embedding").revision == 2
    assert _derived_state(repo, object_id, "embedding").status is DerivedState.READY


def test_provider_failure_marks_embedding_failed_and_preserves_canonical_knowledge(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    version_id = _accepted_version(repo, object_id, "alpha-v1")
    _prepare_search_ready(repo, object_id)
    before = KnowledgeReadApplication(repo).get_object(object_id)
    provider = FakeEmbeddingProvider(fail=True)

    with pytest.raises(DerivedMaintenanceError, match="simulated local embedding failure"):
        DerivedSearchMaintenanceApplication(repo, embedding_provider=provider).sync_embedding(
            object_id
        )

    state = _derived_state(repo, object_id, "embedding")
    assert state.status is DerivedState.FAILED
    assert "simulated local embedding failure" in state.last_error
    assert repo.version_store.current_version_id(object_id) == version_id
    assert repo.version_store.version_by_id(version_id).state.value == "accepted"
    assert KnowledgeReadApplication(repo).get_object(object_id) == before
    assert _derived_state(repo, object_id, "vector_index").status is DerivedState.PENDING


def test_different_embedding_spaces_do_not_overwrite_each_other(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    _accepted_version(repo, object_id, "alpha-v1")
    _prepare_search_ready(repo, object_id)
    left_provider = FakeEmbeddingProvider(_space("left"))
    right_provider = FakeEmbeddingProvider(_space("right"))

    left = DerivedSearchMaintenanceApplication(
        repo, embedding_provider=left_provider
    ).sync_embedding(object_id)
    right = DerivedSearchMaintenanceApplication(
        repo, embedding_provider=right_provider
    ).sync_embedding(object_id)

    assert left.space_id != right.space_id
    assert left.created_embedding_count == 3
    assert right.created_embedding_count == 3
    assert len(repo.embedding_store.embedding_rows(left.space_id)) == 3
    assert len(repo.embedding_store.embedding_rows(right.space_id)) == 3
    assert repo.one("SELECT count(*) AS n FROM search_embedding_spaces")["n"] == 2


@pytest.mark.parametrize("fail_after_superseding", [False, True])
def test_superseded_embedding_attempt_cannot_mark_new_revision_ready_or_failed(
    repo, fail_after_superseding
):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    first_version = _accepted_version(repo, object_id, "alpha-v1")
    _prepare_search_ready(repo, object_id)

    def supersede():
        _accepted_version(
            repo,
            object_id,
            "alpha-v2",
            base_version_id=first_version,
            statement_text="A newer accepted description.",
        )

    provider = FakeEmbeddingProvider(fail=fail_after_superseding, on_embed=supersede)
    service = DerivedSearchMaintenanceApplication(repo, embedding_provider=provider)

    with pytest.raises(DerivedMaintenanceSupersededError, match="superseded|dependency changed"):
        service.sync_embedding(object_id)

    state = _derived_state(repo, object_id, "embedding")
    assert state.target_version_id == "alpha-v2"
    assert state.revision == 2
    assert state.status is DerivedState.PENDING
    assert state.last_error is None
    assert repo.version_store.current_version_id(object_id) == "alpha-v2"
