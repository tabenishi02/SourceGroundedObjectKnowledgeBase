from sgokb.application_read import KnowledgeReadApplication
from sgokb.domain import ObjectSearchFilters, ObjectSearchMode
from sgokb.repository import Repository
from sgokb.retrieval import HybridObjectSearch


def test_application_search_preserves_core_ranking_and_filter_semantics(tmp_path):
    repo = Repository(tmp_path / "j01-semantics.sqlite")
    try:
        character_class = repo.object_store.class_by_key("character").class_id
        work_class = repo.object_store.class_by_key("work").class_id
        character = repo.object_store.create_object(
            "Shared Name",
            character_class,
            aliases=("Shared Alias",),
        )
        work = repo.object_store.create_object("Shared Name Work", work_class)
        for object_id, version_id in (
            (character, "version:character:v1"),
            (work, "version:work:v1"),
        ):
            candidate = repo.version_store.begin_candidate(object_id, None, version_id=version_id)
            repo.version_store.accept_candidate(candidate)

        filters = ObjectSearchFilters(primary_class="character")
        direct = HybridObjectSearch(repo).search(
            "Shared Name",
            filters=filters,
            limit=10,
            mode=ObjectSearchMode.LEXICAL,
        )
        through_application = KnowledgeReadApplication(repo).search_objects(
            "Shared Name",
            filters=filters,
            limit=10,
            mode=ObjectSearchMode.LEXICAL,
        )

        assert through_application == direct
        assert [item.object_id for item in through_application.results] == [character]
    finally:
        repo.close()
