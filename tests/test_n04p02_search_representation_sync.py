import pytest

from sgokb.application_maintenance import (
    DerivedMaintenanceError,
    DerivedMaintenanceSupersededError,
    DerivedSearchMaintenanceApplication,
)
from sgokb.application_read import KnowledgeReadApplication
from sgokb.domain import DerivationKind, DerivedState, FacetStatus
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
    repo.version_store.accept_candidate(version_id)
    return version_id, statement_id


def _derived_state(repo, object_id, kind):
    return next(item for item in repo.version_store.derived_states(object_id) if item.kind == kind)


def test_sync_materializes_current_version_marks_ready_and_enables_lexical_search(repo):
    object_id = repo.object_store.create_object("Alpha Hero", _character_class(repo))
    version_id, statement_id = _accepted_version(repo, object_id, "alpha-v1")
    reader = KnowledgeReadApplication(repo)

    before = reader.search_objects("sacrifice", mode="lexical")
    assert before.results == ()
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


def test_superseded_revision_cannot_mark_new_current_version_ready(repo):
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
            return stored

    service = DerivedSearchMaintenanceApplication(
        repo,
        search_representation_builder=SupersedingBuilder(),
    )
    with pytest.raises(DerivedMaintenanceSupersededError, match="superseded"):
        service.sync_search_representation(object_id)

    state = _derived_state(repo, object_id, "search_representation")
    assert state.target_version_id == "alpha-v2"
    assert state.revision == 2
    assert state.status is DerivedState.PENDING
    assert repo.version_store.current_version_id(object_id) == "alpha-v2"
