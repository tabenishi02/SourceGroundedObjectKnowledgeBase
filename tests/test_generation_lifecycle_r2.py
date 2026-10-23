import math

import pytest

from sgokb.application_generation import (
    LEGACY_GENERATION_ID,
    KnowledgeSearchGenerationApplication,
    KnowledgeSearchGenerationError,
)
from sgokb.domain import EmbeddingSpaceSpec, VectorIndexMetadata, VectorSearchHit
from sgokb.repository import Repository
from sgokb.retrieval import KnowledgeVectorMaintenanceBuilder, SearchRepresentationBuilder


class FakeProvider:
    def __init__(self, space):
        self.space = space
        self.document_calls = 0

    @staticmethod
    def _vector(text):
        total = sum(text.encode("utf-8")) or 1
        return [
            1.0,
            float((total % 7) + 1) / 10.0,
            float((total % 11) + 1) / 10.0,
        ]

    def embed_documents(self, texts):
        self.document_calls += len(texts)
        return [self._vector(text) for text in texts]

    def embed_queries(self, texts):
        return [self._vector(text) for text in texts]


class _NamespaceIndex:
    def __init__(self, backend, namespace):
        self.backend = backend
        self.namespace = namespace

    @property
    def backend_key(self):
        return self.backend.backend_key

    @property
    def points(self):
        return self.backend.namespaces.setdefault(self.namespace, {})

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
        hits = []
        for point in self.points.values():
            if not self._matches(point, filters):
                continue
            point_length = math.sqrt(sum(value * value for value in point.vector))
            score = sum(left * right for left, right in zip(query_vector, point.vector)) / (
                query_length * point_length
            )
            hits.append((point.point_id, score, point.metadata))
        hits.sort(key=lambda item: (-item[1], item[0]))
        return tuple(
            VectorSearchHit(
                point_id=point_id,
                score=score,
                rank=rank,
                metadata=metadata,
            )
            for rank, (point_id, score, metadata) in enumerate(hits[:limit], start=1)
        )

    def delete(self, space, point_ids):
        count = 0
        for point_id in point_ids:
            count += int(self.points.pop(point_id, None) is not None)
        return count

    def rebuild(self, space, points):
        self.backend.namespaces[self.namespace] = {point.point_id: point for point in points}
        return self.metadata(space)

    def metadata(self, space):
        count = len(self.points)
        return VectorIndexMetadata(
            backend_key=self.backend_key,
            backend_version="1",
            space_id=space.space_id,
            dimension=space.dimension,
            distance="cosine",
            points_count=count,
            indexed_points_count=count,
            approximate=False,
            status="ready",
        )

    def drop(self, space):
        self.backend.namespaces.pop(self.namespace, None)


class FakeNamespaceVectorIndex:
    backend_key = "fake-generation"

    def __init__(self):
        self.namespaces = {}

    def namespace_key(self, space):
        return f"legacy-{space.space_id}"

    def bind_namespace(self, namespace_key):
        return _NamespaceIndex(self, namespace_key)


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "generation-r2.sqlite")
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


def _accepted_empty(repo, name, version_id):
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
    return object_id, candidate


def _link_legacy_memberships(repo):
    now = "2026-10-23T00:00:00Z"
    repo.db.execute(
        """INSERT OR IGNORE INTO knowledge_search_generation_memberships(
               generation_id,membership_id,created_at
           )
           SELECT ?,m.id,?
           FROM knowledge_search_representation_memberships m
           JOIN object_version_lifecycle l ON l.version_id=m.version_id
           WHERE l.state='accepted'
             AND m.target_kind IN ('object_overall','facet','statement')
           ORDER BY m.id""",
        (LEGACY_GENERATION_ID, now),
    )
    repo.db.commit()


def _embed_generation(repo, provider, generation_id):
    rows = repo.db.execute(
        """SELECT DISTINCT m.representation_id,r.content
           FROM knowledge_search_generation_memberships gm
           JOIN knowledge_search_representation_memberships m ON m.id=gm.membership_id
           JOIN search_representations r ON r.id=m.representation_id
           WHERE gm.generation_id=?
           ORDER BY m.representation_id""",
        (generation_id,),
    ).fetchall()
    vectors = provider.embed_documents([row["content"] for row in rows])
    for row, vector in zip(rows, vectors):
        repo.embedding_store.save_representation_embedding(
            provider.space,
            row["representation_id"],
            vector,
        )


def _prepared(repo, space):
    _accepted_empty(repo, "Alpha", "version:alpha:v1")
    _accepted_empty(repo, "Beta", "version:beta:v1")
    _link_legacy_memberships(repo)

    provider = FakeProvider(space)
    _embed_generation(repo, provider, LEGACY_GENERATION_ID)

    backend = FakeNamespaceVectorIndex()
    legacy = backend.bind_namespace(backend.namespace_key(space))
    KnowledgeVectorMaintenanceBuilder(
        repo,
        legacy,
        generation_id=LEGACY_GENERATION_ID,
    ).rebuild(space)

    app = KnowledgeSearchGenerationApplication(
        repo,
        embedding_provider=provider,
        vector_index=backend,
    )
    return app, provider, backend


def test_bootstrap_candidate_cutover_rollback_and_recutover(repo, space):
    app, provider, backend = _prepared(repo, space)

    bootstrap = app.bootstrap_legacy()
    assert bootstrap.to_generation_id == LEGACY_GENERATION_ID
    assert bootstrap.switch_kind == "bootstrap"

    candidate = app.build_r2_candidate()
    assert candidate.state == "ready"
    assert candidate.contract_key == "n05d04r2-hierarchical-v2"
    assert candidate.created_embedding_count == 2
    assert candidate.reused_embedding_count == 0
    assert candidate.namespace_key != backend.namespace_key(space)

    status = app.status()
    assert status["active_generation"]["active_generation_id"] == LEGACY_GENERATION_ID

    kinds = {
        row["target_kind"]
        for row in repo.db.execute(
            """SELECT m.target_kind
               FROM knowledge_search_generation_memberships gm
               JOIN knowledge_search_representation_memberships m ON m.id=gm.membership_id
               WHERE gm.generation_id=?""",
            (candidate.generation_id,),
        )
    }
    assert kinds == {"object_overview"}

    cutover = app.cutover(candidate.generation_id)
    assert cutover.from_generation_id == LEGACY_GENERATION_ID
    assert cutover.to_generation_id == candidate.generation_id

    rollback = app.rollback()
    assert rollback.from_generation_id == candidate.generation_id
    assert rollback.to_generation_id == LEGACY_GENERATION_ID

    recutover = app.cutover(candidate.generation_id)
    assert recutover.from_generation_id == LEGACY_GENERATION_ID
    assert recutover.to_generation_id == candidate.generation_id

    switch_kinds = [
        row["switch_kind"]
        for row in repo.db.execute(
            "SELECT switch_kind FROM knowledge_search_generation_switches ORDER BY switched_at,id"
        )
    ]
    assert switch_kinds == ["bootstrap", "cutover", "rollback", "cutover"]
    assert provider.document_calls >= 4


def test_candidate_build_failure_preserves_active_generation(repo, space, monkeypatch):
    app, _, _ = _prepared(repo, space)
    app.bootstrap_legacy()

    def fail(_generation_id):
        raise RuntimeError("fixture embedding failure")

    monkeypatch.setattr(app, "_complete_embeddings", fail)
    with pytest.raises(KnowledgeSearchGenerationError, match="candidate generation build failed"):
        app.build_r2_candidate()

    active = repo.db.execute(
        "SELECT active_generation_id FROM knowledge_search_active_generation"
    ).fetchone()
    assert active["active_generation_id"] == LEGACY_GENERATION_ID
    failed = repo.db.execute(
        """SELECT state,last_error FROM knowledge_search_generations
           WHERE contract_key='n05d04r2-hierarchical-v2'
           ORDER BY created_at DESC LIMIT 1"""
    ).fetchone()
    assert failed["state"] == "failed"
    assert "fixture embedding failure" in failed["last_error"]


def test_ready_candidate_does_not_auto_cutover(repo, space):
    app, _, _ = _prepared(repo, space)
    app.bootstrap_legacy()
    candidate = app.build_r2_candidate()

    active = repo.db.execute(
        "SELECT active_generation_id FROM knowledge_search_active_generation"
    ).fetchone()
    assert active["active_generation_id"] == LEGACY_GENERATION_ID
    row = repo.db.execute(
        "SELECT state FROM knowledge_search_generations WHERE id=?",
        (candidate.generation_id,),
    ).fetchone()
    assert row["state"] == "ready"


def test_stale_legacy_generation_is_not_rollback_eligible(repo, space):
    app, _, _ = _prepared(repo, space)
    app.bootstrap_legacy()
    candidate = app.build_r2_candidate()
    app.cutover(candidate.generation_id)

    repo.db.execute("UPDATE objects SET status='archived' WHERE name='Beta'")
    repo.db.commit()

    with pytest.raises(KnowledgeSearchGenerationError, match="catalog digest is stale"):
        app.rollback()

    active = repo.db.execute(
        "SELECT active_generation_id FROM knowledge_search_active_generation"
    ).fetchone()
    assert active["active_generation_id"] == candidate.generation_id


def test_interrupted_build_recovery_marks_only_non_active_builds_failed(repo, space):
    app, _, _ = _prepared(repo, space)
    app.bootstrap_legacy()
    now = "2026-10-23T00:01:00Z"
    repo.db.execute(
        """INSERT INTO knowledge_search_generations(
               id,contract_key,contract_version,state,created_at
           ) VALUES(?,?,?,?,?)""",
        ("generation:interrupted", "n05d04r2-hierarchical-v2", 2, "building", now),
    )
    repo.db.commit()

    assert app.recover_interrupted_builds() == 1
    row = repo.db.execute(
        "SELECT state,last_error FROM knowledge_search_generations WHERE id=?",
        ("generation:interrupted",),
    ).fetchone()
    assert row["state"] == "failed"
    assert "interrupted build recovery" in row["last_error"]


def test_cutover_rejects_not_ready_generation_without_pointer_change(repo, space):
    app, _, _ = _prepared(repo, space)
    app.bootstrap_legacy()
    now = "2026-10-23T00:02:00Z"
    repo.db.execute(
        """INSERT INTO knowledge_search_generations(
               id,contract_key,contract_version,state,created_at
           ) VALUES(?,?,?,?,?)""",
        ("generation:not-ready", "n05d04r2-hierarchical-v2", 2, "building", now),
    )
    repo.db.commit()

    with pytest.raises(KnowledgeSearchGenerationError, match="not ready"):
        app.cutover("generation:not-ready")

    active = repo.db.execute(
        "SELECT active_generation_id FROM knowledge_search_active_generation"
    ).fetchone()
    assert active["active_generation_id"] == LEGACY_GENERATION_ID


@pytest.mark.parametrize("start_r2", [False, True])
@pytest.mark.parametrize("operation", ["hybrid", "overall", "facet"])
def test_concurrent_cutover_pins_one_operation_generation(
    repo, space, monkeypatch, start_r2, operation
):
    from test_object_similarity_r2 import _accepted_r2

    from sgokb.application_read import KnowledgeReadApplication

    for i in range(2):
        oid = repo.object_store.create_object(
            f"Character {i}", repo.object_store.class_by_key("character").class_id
        )
        _accepted_r2(repo, oid, f"v{i}", [{"facet": "values", "text": f"Value {i}"}])
    _link_legacy_memberships(repo)
    provider = FakeProvider(space)
    _embed_generation(repo, provider, LEGACY_GENERATION_ID)
    backend = FakeNamespaceVectorIndex()
    KnowledgeVectorMaintenanceBuilder(
        repo,
        backend.bind_namespace(backend.namespace_key(space)),
        generation_id=LEGACY_GENERATION_ID,
    ).rebuild(space)
    app = KnowledgeSearchGenerationApplication(
        repo, embedding_provider=provider, vector_index=backend
    )
    app.bootstrap_legacy()
    candidate = app.build_r2_candidate()
    if start_r2:
        app.cutover(candidate.generation_id)
    original = _NamespaceIndex.search
    seen = []

    def switch_after_first(index, *args, **kwargs):
        result = original(index, *args, **kwargs)
        seen.append(index.namespace)
        if len(seen) == 1:
            if start_r2:
                app.rollback(smoke=False)
            else:
                app.cutover(candidate.generation_id, smoke=False)
        return result

    monkeypatch.setattr(_NamespaceIndex, "search", switch_after_first)
    read = KnowledgeReadApplication(
        repo, embedding_provider=provider, embedding_space=space, vector_index=backend
    )
    source = repo.one("SELECT id FROM objects ORDER BY id")["id"]
    if operation == "hybrid":
        result = read.search_objects("Character", mode="semantic")
        assert result.results
        assert len(seen) >= 2
    else:
        result = read.find_similar_objects(source, facet="values" if operation == "facet" else None)
        assert result.results
        assert result.generation_id == (
            candidate.generation_id if start_r2 else LEGACY_GENERATION_ID
        )
    assert set(seen) == {candidate.namespace_key if start_r2 else backend.namespace_key(space)}


def test_active_incremental_sync_refreshes_digests_count_and_only_r2_family(repo, space):
    from sgokb.application_derived import DerivedSearchOperatorApplication

    app, provider, backend = _prepared(repo, space)
    app.bootstrap_legacy()
    candidate = app.build_r2_candidate()
    app.cutover(candidate.generation_id)
    legacy = app._generation_row(LEGACY_GENERATION_ID)
    oid = repo.object_store.create_object(
        "New Object", repo.object_store.class_by_key("character").class_id
    )
    version = repo.version_store.begin_candidate(oid, None, version_id="new-version")
    repo.version_store.accept_candidate(version)
    operator = DerivedSearchOperatorApplication(
        repo, embedding_provider=provider, vector_index=backend
    )
    result = operator.sync(oid, semantic=True)
    assert result.completed_object_count == 1
    assert result.partial is False
    kinds = {
        r["target_kind"]
        for r in repo.semantic_store.knowledge_search_memberships(version_id=version)
    }
    assert kinds == {"object_overview"}
    row = app._generation_row(candidate.generation_id)
    assert row["source_catalog_digest"] == app.source_catalog_digest()
    assert row["source_catalog_digest"] != candidate.source_catalog_digest
    assert row["membership_digest"] == app.membership_digest(candidate.generation_id)
    assert row["membership_digest"] != candidate.membership_digest
    binding = repo.one(
        "SELECT * FROM knowledge_search_generation_vector_indexes WHERE generation_id=?",
        (candidate.generation_id,),
    )
    assert binding["membership_digest"] == row["membership_digest"]
    assert binding["point_count"] == candidate.point_count + 1
    app._verify_switch_target(candidate.generation_id)
    assert app._generation_row(LEGACY_GENERATION_ID) == legacy
    with pytest.raises(KnowledgeSearchGenerationError, match="catalog digest is stale"):
        app.rollback()


@pytest.mark.parametrize("fault", ["digest", "count", "point_id", "payload"])
def test_invalid_ready_candidate_fails_closed(repo, space, fault):
    from dataclasses import replace

    app, _, backend = _prepared(repo, space)
    app.bootstrap_legacy()
    candidate = app.build_r2_candidate()
    if fault == "digest":
        repo.db.execute(
            "UPDATE knowledge_search_generations SET membership_digest=? WHERE id=?",
            ("0" * 64, candidate.generation_id),
        )
    elif fault == "count":
        repo.db.execute(
            "UPDATE knowledge_search_generation_vector_indexes SET point_count=999 "
            "WHERE generation_id=?",
            (candidate.generation_id,),
        )
    else:
        points = backend.namespaces[candidate.namespace_key]
        point_id = next(iter(points))
        if fault == "point_id":
            points["foreign-membership"] = points.pop(point_id)
        else:
            points[point_id] = replace(
                points[point_id],
                metadata={**points[point_id].metadata, "generation_id": "foreign-generation"},
            )
    repo.db.commit()
    with pytest.raises(KnowledgeSearchGenerationError):
        app.cutover(candidate.generation_id)
    assert app.status()["active_generation"]["active_generation_id"] == LEGACY_GENERATION_ID


@pytest.mark.parametrize("rollback", [False, True])
def test_smoke_failure_recovers_previous_pointer_and_audit(repo, space, monkeypatch, rollback):
    app, _, _ = _prepared(repo, space)
    app.bootstrap_legacy()
    candidate = app.build_r2_candidate()
    if rollback:
        app.cutover(candidate.generation_id)
    prior = app.status()["active_generation"]["active_generation_id"]

    def fail():
        raise RuntimeError("smoke failure fixture")

    monkeypatch.setattr(app, "_smoke_active_generation", fail)
    with pytest.raises(KnowledgeSearchGenerationError, match="previous generation was restored"):
        if rollback:
            app.rollback()
        else:
            app.cutover(candidate.generation_id)
    assert app.status()["active_generation"]["active_generation_id"] == prior
    assert (
        repo.one(
            "SELECT count(*) AS n FROM knowledge_search_generation_switches "
            "WHERE switch_kind='recovery'"
        )["n"]
        == 1
    )


def test_bootstrap_rejects_equal_count_wrong_point_identity(repo, space):
    app, _, backend = _prepared(repo, space)
    points = backend.namespaces[backend.namespace_key(space)]
    points["foreign"] = points.pop(next(iter(points)))
    with pytest.raises(KnowledgeSearchGenerationError, match="membership identity"):
        app.bootstrap_legacy()
    assert app.status()["active_generation"] is None


def test_catalog_change_during_candidate_build_fails_closed(repo, space, monkeypatch):
    app, _, _ = _prepared(repo, space)
    app.bootstrap_legacy()
    original = app._complete_embeddings

    def change(generation_id):
        result = original(generation_id)
        repo.db.execute("UPDATE objects SET status='archived' WHERE name='Beta'")
        repo.db.commit()
        return result

    monkeypatch.setattr(app, "_complete_embeddings", change)
    with pytest.raises(KnowledgeSearchGenerationError, match="catalog changed"):
        app.build_r2_candidate()
    assert app.status()["active_generation"]["active_generation_id"] == LEGACY_GENERATION_ID


def test_child_embeddings_are_reused_and_only_overviews_created(repo, space):
    from test_object_similarity_r2 import _accepted_r2

    for i in range(2):
        oid = repo.object_store.create_object(
            f"Child {i}", repo.object_store.class_by_key("character").class_id
        )
        _accepted_r2(repo, oid, f"child-{i}", [{"facet": "values", "text": f"Value {i}"}])
    _link_legacy_memberships(repo)
    provider = FakeProvider(space)
    _embed_generation(repo, provider, LEGACY_GENERATION_ID)
    backend = FakeNamespaceVectorIndex()
    KnowledgeVectorMaintenanceBuilder(
        repo,
        backend.bind_namespace(backend.namespace_key(space)),
        generation_id=LEGACY_GENERATION_ID,
    ).rebuild(space)
    app = KnowledgeSearchGenerationApplication(
        repo, embedding_provider=provider, vector_index=backend
    )
    app.bootstrap_legacy()
    calls = provider.document_calls
    candidate = app.build_r2_candidate()
    assert candidate.reused_embedding_count == 4
    assert candidate.created_embedding_count == 2
    assert provider.document_calls - calls == 2


def test_batch_incremental_sync_publishes_only_after_all_objects_synced(repo, space):
    from sgokb.application_derived import DerivedSearchOperatorApplication

    app, provider, backend = _prepared(repo, space)
    app.bootstrap_legacy()
    candidate = app.build_r2_candidate()
    app.cutover(candidate.generation_id)
    for i in range(2):
        oid = repo.object_store.create_object(
            f"New {i}", repo.object_store.class_by_key("character").class_id
        )
        version = repo.version_store.begin_candidate(oid, None)
        repo.version_store.accept_candidate(version)
    operator = DerivedSearchOperatorApplication(
        repo, embedding_provider=provider, vector_index=backend
    )
    result = operator.sync(semantic=True)
    assert result.completed_object_count == 4
    app._verify_switch_target(candidate.generation_id)


def test_incremental_audit_failure_does_not_publish_new_digest(repo, space, monkeypatch):
    from sgokb.application_derived import DerivedSearchOperatorApplication

    app, provider, backend = _prepared(repo, space)
    app.bootstrap_legacy()
    candidate = app.build_r2_candidate()
    app.cutover(candidate.generation_id)
    oid = repo.object_store.create_object(
        "New", repo.object_store.class_by_key("character").class_id
    )
    version = repo.version_store.begin_candidate(oid, None)
    repo.version_store.accept_candidate(version)
    operator = DerivedSearchOperatorApplication(
        repo, embedding_provider=provider, vector_index=backend
    )

    def fail(*args, **kwargs):
        raise KnowledgeSearchGenerationError("audit failure fixture")

    monkeypatch.setattr(operator._generation, "_audit_namespace", fail)
    with pytest.raises(KnowledgeSearchGenerationError, match="audit failure fixture"):
        operator.sync(oid, semantic=True)
    assert (
        app._generation_row(candidate.generation_id)["membership_digest"]
        == candidate.membership_digest
    )
    assert (
        app._generation_row(candidate.generation_id)["source_catalog_digest"]
        == candidate.source_catalog_digest
    )


def test_cli_index_rebuild_routes_to_active_r2_and_preserves_v1(
    repo, space, monkeypatch, capsys, tmp_path
):
    import importlib

    from sgokb.application_derived import DerivedSearchOperatorApplication

    app, provider, backend = _prepared(repo, space)
    app.bootstrap_legacy()
    candidate = app.build_r2_candidate()
    app.cutover(candidate.generation_id)
    legacy = dict(backend.namespaces[backend.namespace_key(space)])
    cli = importlib.import_module("sgokb.cli.main")
    monkeypatch.setattr(cli, "semantic_runtime", lambda: (provider, backend))
    assert (
        cli.main(["--db", str(tmp_path / "generation-r2.sqlite"), "system", "index", "rebuild"])
        == 0
    )
    assert backend.namespaces[backend.namespace_key(space)] == legacy
    assert set(backend.namespaces[candidate.namespace_key]) == {
        row["membership_id"] for row in app._generation_membership_rows(candidate.generation_id)
    }
    status = DerivedSearchOperatorApplication(
        repo, embedding_provider=provider, vector_index=backend
    ).status()
    assert all(obj["search_representations"]["membership_count"] == 1 for obj in status["objects"])
    capsys.readouterr()
