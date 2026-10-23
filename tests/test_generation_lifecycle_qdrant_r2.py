import pytest

from sgokb.application_generation import (
    LEGACY_GENERATION_ID,
    KnowledgeSearchGenerationApplication,
)
from sgokb.domain import EmbeddingSpaceSpec
from sgokb.repository import Repository
from sgokb.retrieval import (
    KnowledgeVectorMaintenanceBuilder,
    QdrantVectorIndexAdapter,
    SearchRepresentationBuilder,
)


class FakeProvider:
    def __init__(self, space):
        self.space = space

    @staticmethod
    def _vector(text):
        total = sum(text.encode("utf-8")) or 1
        return [
            1.0,
            float((total % 7) + 1) / 10.0,
            float((total % 11) + 1) / 10.0,
        ]

    def embed_documents(self, texts):
        return [self._vector(text) for text in texts]

    def embed_queries(self, texts):
        return [self._vector(text) for text in texts]


def _space():
    return EmbeddingSpaceSpec(
        provider_key="fake-qdrant",
        provider_version="1",
        model="fake-qdrant-model",
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


def _accepted(repo, name, version_id):
    object_id = repo.object_store.create_object(
        name,
        repo.object_store.class_by_key("character").class_id,
    )
    candidate = repo.version_store.begin_candidate(
        object_id,
        None,
        version_id=version_id,
    )
    repo.version_store.accept_candidate(candidate)
    SearchRepresentationBuilder(repo).materialize_version(candidate)
    return object_id


def _link_legacy(repo):
    repo.db.execute(
        """INSERT OR IGNORE INTO knowledge_search_generation_memberships(
               generation_id,membership_id,created_at
           )
           SELECT ?,m.id,'2026-10-23T00:00:00Z'
           FROM knowledge_search_representation_memberships m
           JOIN object_version_lifecycle l ON l.version_id=m.version_id
           WHERE l.state='accepted'
             AND m.target_kind IN ('object_overall','facet','statement')""",
        (LEGACY_GENERATION_ID,),
    )
    repo.db.commit()


def _save_legacy_embeddings(repo, provider):
    rows = repo.db.execute(
        """SELECT DISTINCT m.representation_id,r.content
           FROM knowledge_search_generation_memberships gm
           JOIN knowledge_search_representation_memberships m ON m.id=gm.membership_id
           JOIN search_representations r ON r.id=m.representation_id
           WHERE gm.generation_id=?
           ORDER BY m.representation_id""",
        (LEGACY_GENERATION_ID,),
    ).fetchall()
    for row, vector in zip(
        rows,
        provider.embed_documents([row["content"] for row in rows]),
    ):
        repo.embedding_store.save_representation_embedding(
            provider.space,
            row["representation_id"],
            vector,
        )


def test_qdrant_generation_cutover_rollback_and_recutover(tmp_path):
    qdrant_client = pytest.importorskip("qdrant_client")
    repo = Repository(tmp_path / "generation-qdrant.sqlite")
    try:
        _accepted(repo, "Alpha", "version:alpha:v1")
        _accepted(repo, "Beta", "version:beta:v1")
        _link_legacy(repo)

        space = _space()
        provider = FakeProvider(space)
        _save_legacy_embeddings(repo, provider)

        vector = QdrantVectorIndexAdapter(
            client=qdrant_client.QdrantClient(location=":memory:"),
            wait_for_index=False,
        )
        KnowledgeVectorMaintenanceBuilder(
            repo,
            vector,
            generation_id=LEGACY_GENERATION_ID,
        ).rebuild(space)

        app = KnowledgeSearchGenerationApplication(
            repo,
            embedding_provider=provider,
            vector_index=vector,
        )
        app.bootstrap_legacy()
        candidate = app.build_r2_candidate()

        assert candidate.namespace_key != vector._collection(space)
        assert candidate.point_count == candidate.membership_count

        app.cutover(candidate.generation_id)
        assert app.status()["active_generation"]["active_generation_id"] == candidate.generation_id

        app.rollback()
        assert app.status()["active_generation"]["active_generation_id"] == LEGACY_GENERATION_ID

        app.cutover(candidate.generation_id)
        assert app.status()["active_generation"]["active_generation_id"] == candidate.generation_id

        kinds = {
            row["target_kind"]
            for row in repo.db.execute(
                """SELECT m.target_kind
                   FROM knowledge_search_generation_memberships gm
                   JOIN knowledge_search_representation_memberships m
                     ON m.id=gm.membership_id
                   WHERE gm.generation_id=?""",
                (candidate.generation_id,),
            )
        }
        assert "object_overall" not in kinds
        assert "object_overview" in kinds
    finally:
        repo.close()


@pytest.mark.parametrize("fault", ["backend_id", "payload", "membership"])
def test_qdrant_namespace_identity_audit_rejects_corruption(tmp_path, fault):
    import uuid

    qdrant_client = pytest.importorskip("qdrant_client")
    from qdrant_client import models

    from sgokb.application_generation import KnowledgeSearchGenerationError

    repo = Repository(tmp_path / "negative-qdrant.sqlite")
    client = qdrant_client.QdrantClient(location=":memory:")
    try:
        _accepted(repo, "Alpha", "alpha-v1")
        _link_legacy(repo)
        space = _space()
        provider = FakeProvider(space)
        _save_legacy_embeddings(repo, provider)
        base = QdrantVectorIndexAdapter(client=client, wait_for_index=False)
        KnowledgeVectorMaintenanceBuilder(repo, base, generation_id=LEGACY_GENERATION_ID).rebuild(
            space
        )
        app = KnowledgeSearchGenerationApplication(
            repo, embedding_provider=provider, vector_index=base
        )
        app.bootstrap_legacy()
        candidate = app.build_r2_candidate()
        points, _ = client.scroll(candidate.namespace_key, with_vectors=True)
        point = points[0]
        if fault == "backend_id":
            client.delete(candidate.namespace_key, models.PointIdsList(points=[point.id]))
            client.upsert(
                candidate.namespace_key,
                [
                    models.PointStruct(
                        id=str(uuid.uuid4()), vector=point.vector, payload=point.payload
                    )
                ],
            )
        else:
            field = "generation_id" if fault == "payload" else "__sgokb_point_id"
            client.set_payload(candidate.namespace_key, {field: "foreign"}, points=[point.id])
        with pytest.raises(KnowledgeSearchGenerationError, match="identity audit"):
            app.cutover(candidate.generation_id)
        assert app.status()["active_generation"]["active_generation_id"] == LEGACY_GENERATION_ID
    finally:
        client.close()
        repo.close()
