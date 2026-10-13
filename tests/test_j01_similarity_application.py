from sgokb.application_read import KnowledgeReadApplication
from sgokb.domain import EmbeddingSpaceSpec
from sgokb.repository import Repository
from sgokb.retrieval import (
    ExactVectorIndexAdapter,
    KnowledgeVectorIndexBuilder,
    SearchRepresentationBuilder,
)


def _class_id(repo):
    return repo.object_store.class_by_key("character").class_id


def _accepted(repo, object_id, version_id, base=None):
    value = repo.version_store.begin_candidate(object_id, base, version_id=version_id)
    repo.version_store.accept_candidate(value)
    SearchRepresentationBuilder(repo).materialize_version(value)
    return value


def _space():
    return EmbeddingSpaceSpec(
        provider_key="j01-test",
        provider_version="1",
        model="j01-test-model",
        model_revision="1",
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


def test_similarity_is_available_through_application_boundary(tmp_path):
    repo = Repository(tmp_path / "j01-similarity.sqlite")
    try:
        left = repo.object_store.create_object("Left Character", _class_id(repo))
        right = repo.object_store.create_object("Right Character", _class_id(repo))
        _accepted(repo, left, "version:left:v1")
        _accepted(repo, right, "version:right:v1")

        space = _space()
        vectors = {
            left: [1.0, 0.0, 0.0],
            right: [0.9, 0.1, 0.0],
        }
        for membership in repo.semantic_store.knowledge_search_memberships():
            repo.embedding_store.save_representation_embedding(
                space,
                membership["representation_id"],
                vectors[membership["object_id"]],
            )

        index = ExactVectorIndexAdapter()
        KnowledgeVectorIndexBuilder(repo, index).rebuild(space)
        app = KnowledgeReadApplication(repo, embedding_space=space, vector_index=index)

        response = app.find_similar_objects(left, limit=5)

        assert response.source_object_id == left
        assert response.source_version_id == "version:left:v1"
        assert response.results[0].object_id == right
        assert response.results[0].version_id == "version:right:v1"
    finally:
        repo.close()
