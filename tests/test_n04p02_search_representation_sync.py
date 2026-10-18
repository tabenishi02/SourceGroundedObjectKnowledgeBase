import hashlib

import pytest

from sgokb.application_maintenance import (
    DerivedMaintenanceError,
    DerivedMaintenanceSupersededError,
    DerivedSearchMaintenanceApplication,
)
from sgokb.application_read import KnowledgeReadApplication
from sgokb.domain import (
    DerivationKind,
    DerivedState,
    EvidenceExtractionMode,
    EvidenceTargetKind,
    FacetStatus,
)
from sgokb.repository import Repository
from sgokb.retrieval import SearchRepresentationBuilder


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "n04p02-search-representation.sqlite")
    yield value
    value.close()


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
    source = repo.source_store.create_source("Alpha source")
    locator = repo.source_store.add_locator(source, "url", "https://example.test/alpha")
    snapshot = repo.source_store.create_snapshot(
        source, "2026-10-16T00:00:00Z", "test_fixture", observed_locator_id=locator
    )
    raw = statement_text.encode("utf-8")
    artifact = repo.source_store.add_raw_artifact(
        snapshot, "document", "fixture/alpha.txt", hashlib.sha256(raw).hexdigest(), len(raw)
    )
    run = repo.source_store.create_normalization_run(snapshot, "fixture", "1", [artifact])
    evidence = repo.source_store.add_evidence(run, statement_text, EvidenceExtractionMode.VERBATIM)
    repo.source_store.link_evidence(
        version_id, EvidenceTargetKind.STATEMENT, statement_id, evidence
    )
    repo.version_store.accept_candidate(version_id)
    return version_id, statement_id


def _derived_state(repo, object_id, kind):
    return next(item for item in repo.version_store.derived_states(object_id) if item.kind == kind)


def test_sync_materializes_current_version_marks_ready_and_enables_lexical_search(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    version_id, statement_id = _accepted_version(repo, object_id, "alpha-v1")
    reader = KnowledgeReadApplication(repo)

    before = reader.search_objects("sacrifice", mode="lexical")
    assert not before.results
    state = _derived_state(repo, object_id, "search_representation")
    assert state.status is DerivedState.PENDING
    assert state.target_version_id == version_id

    result = DerivedSearchMaintenanceApplication(repo).sync_search_representation(object_id)

    assert result.object_id == object_id
    assert result.version_id == version_id
    assert result.changed is True
    assert result.state == "ready"
    assert result.representation_count == 3
    memberships = repo.semantic_store.knowledge_search_memberships(
        object_id=object_id,
        version_id=version_id,
    )
    assert {row["target_kind"] for row in memberships} == {
        "object_overall",
        "facet",
        "statement",
    }
    assert any(row["statement_id"] == statement_id for row in memberships)

    state = _derived_state(repo, object_id, "search_representation")
    assert state.status is DerivedState.READY
    assert state.last_error is None
    assert _derived_state(repo, object_id, "embedding").status is DerivedState.PENDING
    assert _derived_state(repo, object_id, "vector_index").status is DerivedState.PENDING

    after = reader.search_objects("sacrifice", mode="lexical")
    assert after.results
    assert after.results[0].object_id == object_id
    assert after.results[0].version_id == version_id


def test_sync_is_idempotent_after_ready_without_duplicate_memberships(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    version_id, _ = _accepted_version(repo, object_id, "alpha-v1")
    service = DerivedSearchMaintenanceApplication(repo)

    first = service.sync_search_representation(object_id)
    first_memberships = repo.semantic_store.knowledge_search_memberships(
        object_id=object_id,
        version_id=version_id,
    )
    second = service.sync_search_representation(object_id)
    second_memberships = repo.semantic_store.knowledge_search_memberships(
        object_id=object_id,
        version_id=version_id,
    )

    assert first.changed is True
    assert second.changed is False
    assert second.representation_count == first.representation_count
    assert [row["id"] for row in second_memberships] == [row["id"] for row in first_memberships]


def test_builder_failure_marks_only_derived_state_failed_and_keeps_accepted_knowledge(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    version_id, _ = _accepted_version(repo, object_id, "alpha-v1")

    before = KnowledgeReadApplication(repo).get_object(object_id)

    class FailingBuilder:
        def materialize_version(self, target_version_id):
            assert target_version_id == version_id
            raise RuntimeError("simulated representation failure")

    service = DerivedSearchMaintenanceApplication(
        repo,
        search_representation_builder=FailingBuilder(),
    )
    with pytest.raises(DerivedMaintenanceError, match="simulated representation failure"):
        service.sync_search_representation(object_id)

    state = _derived_state(repo, object_id, "search_representation")
    assert state.status is DerivedState.FAILED
    assert "simulated representation failure" in state.last_error
    assert repo.version_store.current_version_id(object_id) == version_id
    assert repo.version_store.version_by_id(version_id).state.value == "accepted"
    assert KnowledgeReadApplication(repo).get_object(object_id) == before


@pytest.mark.parametrize("fail_after_superseding", [False, True])
def test_superseded_revision_cannot_mark_new_current_version_ready_or_failed(
    repo, fail_after_superseding
):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    first_version_id, _ = _accepted_version(repo, object_id, "alpha-v1")
    real_builder = SearchRepresentationBuilder(repo)

    class SupersedingBuilder:
        def materialize_version(self, target_version_id):
            assert target_version_id == first_version_id
            stored = real_builder.materialize_version(target_version_id)
            _accepted_version(
                repo,
                object_id,
                "alpha-v2",
                base_version_id=first_version_id,
                statement_text="A newer accepted description.",
            )
            if fail_after_superseding:
                raise RuntimeError("older attempt failed after supersession")
            return stored

    service = DerivedSearchMaintenanceApplication(
        repo,
        search_representation_builder=SupersedingBuilder(),
    )
    with pytest.raises(DerivedMaintenanceSupersededError, match="superseded"):
        service.sync_search_representation(object_id)

    state = _derived_state(repo, object_id, "search_representation")
    assert state.last_error is None
    assert state.target_version_id == "alpha-v2"
    assert state.revision == 2
    assert state.status is DerivedState.PENDING
    assert repo.version_store.current_version_id(object_id) == "alpha-v2"


def test_new_current_version_reuses_content_and_preserves_historical_memberships(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    first_version_id, _ = _accepted_version(repo, object_id, "alpha-v1")
    service = DerivedSearchMaintenanceApplication(repo)
    service.sync_search_representation(object_id)
    first_memberships = repo.semantic_store.knowledge_search_memberships(
        object_id=object_id,
        version_id=first_version_id,
    )
    first_representation_ids = {row["representation_id"] for row in first_memberships}

    second_version_id, _ = _accepted_version(
        repo,
        object_id,
        "alpha-v2",
        base_version_id=first_version_id,
    )
    pending = _derived_state(repo, object_id, "search_representation")
    assert pending.target_version_id == second_version_id
    assert pending.revision == 2
    assert pending.status is DerivedState.PENDING

    service.sync_search_representation(object_id)
    second_memberships = repo.semantic_store.knowledge_search_memberships(
        object_id=object_id,
        version_id=second_version_id,
    )
    second_representation_ids = {row["representation_id"] for row in second_memberships}

    assert first_representation_ids == second_representation_ids
    historical = repo.semantic_store.knowledge_search_memberships(version_id=first_version_id)
    current = repo.semantic_store.knowledge_search_memberships(
        object_id=object_id,
        current_only=True,
    )
    assert historical
    assert {row["version_id"] for row in historical} == {first_version_id}
    assert current
    assert {row["version_id"] for row in current} == {second_version_id}

    response = KnowledgeReadApplication(repo).search_objects("sacrifice", mode="lexical")
    assert response.results
    assert response.results[0].version_id == second_version_id
