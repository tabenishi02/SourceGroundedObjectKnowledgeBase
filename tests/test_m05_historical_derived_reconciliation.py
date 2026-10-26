"""M-05 regression coverage for accepted historical derived reconciliation."""

import pytest
from test_n04p04_vector_index_sync import (
    FakeEmbeddingProvider,
    FakeVectorIndex,
    _accepted_version,
    _character_class,
)

from sgokb.application_maintenance import DerivedSearchMaintenanceApplication
from sgokb.application_read import KnowledgeReadApplication
from sgokb.domain import ObjectSearchFilters
from sgokb.repository import Repository


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "m05-historical-derived-reconciliation.sqlite")
    yield value
    value.close()


def _membership_ids(repo, version_id):
    return tuple(
        row["id"]
        for row in repo.semantic_store.knowledge_search_memberships(version_id=version_id)
    )


def test_ready_current_sync_backfills_unsynced_accepted_history_and_is_idempotent(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    version1_id = _accepted_version(
        repo,
        object_id,
        "alpha-v1",
        statement_text="Legacy cedar marker for the first accepted version.",
    )

    # Reproduce the acceptance-test gap: V1 is promoted but never derived-synced.
    assert _membership_ids(repo, version1_id) == ()

    version2_id = _accepted_version(
        repo,
        object_id,
        "alpha-v2",
        base_version_id=version1_id,
        statement_text="Current birch marker for the second accepted version.",
    )
    service = DerivedSearchMaintenanceApplication(repo)

    first = service.sync_search_representation(object_id)

    v1_memberships = _membership_ids(repo, version1_id)
    v2_memberships = _membership_ids(repo, version2_id)
    assert first.version_id == version2_id
    assert first.changed is True
    assert v1_memberships
    assert v2_memberships

    # Explicit historical search must address V1 rather than leaking current V2.
    reader = KnowledgeReadApplication(repo)
    historical = reader.search_objects(
        "cedar",
        filters=ObjectSearchFilters(version_id=version1_id),
        mode="lexical",
    )
    assert historical.results
    assert historical.results[0].object_id == object_id
    assert historical.results[0].version_id == version1_id

    current = reader.search_objects("birch", mode="lexical")
    assert current.results
    assert current.results[0].version_id == version2_id
    historical_current_term = reader.search_objects(
        "birch",
        filters=ObjectSearchFilters(version_id=version1_id),
        mode="lexical",
    )
    assert not historical_current_term.results

    # Candidate Versions are outside the accepted-history reconciliation set.
    candidate_id = repo.version_store.begin_candidate(
        object_id,
        version2_id,
        version_id="alpha-v3-candidate",
    )
    second = service.sync_search_representation(object_id)
    assert second.changed is False
    assert _membership_ids(repo, candidate_id) == ()
    assert _membership_ids(repo, version1_id) == v1_memberships
    assert _membership_ids(repo, version2_id) == v2_memberships


def test_semantic_sync_embeds_and_indexes_all_backfilled_accepted_memberships(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    version1_id = _accepted_version(
        repo,
        object_id,
        "alpha-v1",
        statement_text="Legacy cedar marker for the first accepted version.",
    )
    version2_id = _accepted_version(
        repo,
        object_id,
        "alpha-v2",
        base_version_id=version1_id,
        statement_text="Current birch marker for the second accepted version.",
    )

    provider = FakeEmbeddingProvider()
    vector = FakeVectorIndex()
    service = DerivedSearchMaintenanceApplication(
        repo,
        embedding_provider=provider,
        vector_index=vector,
        embedding_space=provider.space,
    )

    service.sync_search_representation(object_id)
    accepted_memberships = tuple(
        row
        for row in repo.semantic_store.knowledge_search_memberships(object_id=object_id)
        if row["version_id"] in {version1_id, version2_id}
    )
    representation_ids = tuple(
        dict.fromkeys(row["representation_id"] for row in accepted_memberships)
    )

    embedding = service.sync_embedding(object_id)
    embedded_ids = {
        row["representation_id"]
        for row in repo.embedding_store.embedding_rows(
            provider.space.space_id,
            representation_ids,
        )
    }
    assert embedding.representation_count == len(representation_ids)
    assert embedded_ids == set(representation_ids)

    vector_result = service.sync_vector_index(object_id)
    assert vector_result.point_count == len(accepted_memberships)
    assert len(vector.points) == len(accepted_memberships)
    assert {point.metadata["version_id"] for point in vector.points.values()} == {
        version1_id,
        version2_id,
    }
    assert all(
        point.metadata["is_current"] is (point.metadata["version_id"] == version2_id)
        for point in vector.points.values()
    )
