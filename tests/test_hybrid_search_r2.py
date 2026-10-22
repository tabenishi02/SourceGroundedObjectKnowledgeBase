import math

import pytest

from sgokb.domain import (
    DerivationKind,
    EmbeddingSpaceSpec,
    EvidenceExtractionMode,
    EvidenceTargetKind,
    FacetStatus,
    ObjectSearchChannel,
    ObjectSearchFilters,
    VectorIndexMetadata,
    VectorIndexPoint,
    VectorSearchFilter,
    VectorSearchHit,
)
from sgokb.repository import Repository
from sgokb.retrieval import (
    HybridObjectSearch,
    KnowledgeVectorIndexBuilder,
    SearchRepresentationBuilder,
)


class FakeEmbeddingProvider:
    def __init__(self, space, mapping=None):
        self._space = space
        self.mapping = mapping or {}

    @property
    def space(self):
        return self._space

    def embed_queries(self, texts):
        return [list(self.mapping.get(text, (1.0, 0.0, 0.0))) for text in texts]


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


class GenerationBlindFakeVectorIndex(FakeVectorIndex):
    """Simulate a backend bug that ignores the generation hard filter."""

    def search(self, space, query_vector, *, limit, filters=None):
        if filters is not None:
            filters = VectorSearchFilter(
                matches=tuple(item for item in filters.matches if item.field != "generation_id"),
                excludes=filters.excludes,
                ranges=filters.ranges,
            )
        return super().search(space, query_vector, limit=limit, filters=filters)


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "hybrid-search-r2.sqlite")
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
    source_id = repo.source_store.create_source(f"R2 Source {suffix}")
    locator_id = repo.source_store.add_locator(
        source_id, "url", f"https://example.test/r2/{suffix}", preferred=True
    )
    snapshot_id = repo.source_store.create_snapshot(
        source_id,
        "2026-10-23T00:00:00Z",
        "test",
        observed_locator_id=locator_id,
        title=f"R2 {suffix}",
    )
    artifact_id = repo.source_store.add_raw_artifact(
        snapshot_id, "html", f"memory://r2/{suffix}", "a" * 64, 10
    )
    run_id = repo.source_store.create_normalization_run(snapshot_id, "fixture", "1", [artifact_id])
    return repo.source_store.add_evidence(
        run_id, f"Evidence for {suffix}", EvidenceExtractionMode.NORMALIZED, language="ja"
    )


def _accepted_r2(repo, object_id, version_id, statements):
    version_id = repo.version_store.begin_candidate(object_id, None, version_id=version_id)
    evidence_id = _evidence(repo, version_id)
    for index, item in enumerate(statements):
        facet_key = item.get("facet")
        facet_id = None
        if facet_key is not None:
            facet_id = repo.semantic_store.facet_by_key(facet_key).facet_id
            repo.semantic_store.set_version_facet(version_id, facet_id, FacetStatus.CONTENT)
        statement_id = repo.semantic_store.add_statement(
            version_id,
            f"s-{index}",
            item["text"],
            item.get("derivation", DerivationKind.DIRECT_STATEMENT),
            facet_id=facet_id,
        )
        repo.source_store.link_evidence(
            version_id, EvidenceTargetKind.STATEMENT, statement_id, evidence_id
        )
    repo.version_store.accept_candidate(version_id)
    builder = SearchRepresentationBuilder(repo)
    builder.materialize_version(version_id)
    builder.materialize_version_r2(version_id)
    return version_id


def _activate_r2_generation(repo, generation_id="test-r2-generation"):
    now = "2026-10-23T00:00:00Z"
    repo.db.execute(
        """INSERT INTO knowledge_search_generations(
             id,contract_key,contract_version,state,source_catalog_digest,
             membership_digest,created_at,ready_at
           ) VALUES(?,?,?,?,?,?,?,?)""",
        (
            generation_id,
            "n05d04r2-hierarchical-v2",
            2,
            "ready",
            "a" * 64,
            "b" * 64,
            now,
            now,
        ),
    )
    rows = repo.db.execute(
        """SELECT id FROM knowledge_search_representation_memberships
           WHERE target_kind IN ('object_overview','facet','statement') ORDER BY id"""
    ).fetchall()
    for row in rows:
        repo.db.execute(
            """INSERT INTO knowledge_search_generation_memberships(
                 generation_id,membership_id,created_at
               ) VALUES(?,?,?)""",
            (generation_id, row["id"], now),
        )
    repo.db.execute(
        """INSERT INTO knowledge_search_active_generation(
             scope,active_generation_id,activation_revision,activated_at
           ) VALUES('knowledge',?,?,?)""",
        (generation_id, 1, now),
    )
    return generation_id


def _save_embeddings(repo, space):
    for membership in repo.semantic_store.knowledge_search_memberships():
        repo.embedding_store.save_representation_embedding(
            space,
            membership["representation_id"],
            [1.0, 0.0, 0.0],
        )


def _engine(repo, space, generation_id, index=None):
    _save_embeddings(repo, space)
    index = index or FakeVectorIndex()
    KnowledgeVectorIndexBuilder(
        repo,
        index,
        generation_id=generation_id,
    ).rebuild(space)
    return HybridObjectSearch(
        repo,
        embedding_provider=FakeEmbeddingProvider(space),
        vector_index=index,
    ), index


def test_r2_channel_value_and_active_semantic_family_exclude_object_overall(repo, space):
    object_id = repo.object_store.create_object("Alpha Hero", _class(repo, "character"))
    _accepted_r2(
        repo,
        object_id,
        "alpha-v1",
        [
            {"text": "仲間を守る人物"},
            {"facet": "personality", "text": "慎重だが勇敢"},
        ],
    )
    generation_id = _activate_r2_generation(repo)
    engine, index = _engine(repo, space, generation_id)

    assert ObjectSearchChannel.SEMANTIC_OBJECT.value == "semantic_object_overview"
    assert {point.metadata["generation_id"] for point in index.points.values()} == {
        generation_id
    }
    assert "object_overall" not in {point.metadata["kind"] for point in index.points.values()}

    response = engine.search("仲間", mode="semantic")
    assert response.results[0].object_id == object_id
    matches = response.results[0].matches
    assert any(match.representation_kind == "object_overview" for match in matches)
    assert all(match.representation_kind != "object_overall" for match in matches)
    assert ObjectSearchChannel.SEMANTIC_OBJECT in response.results[0].channels


def test_r2_knowledge_lexical_uses_only_active_generation_memberships(repo, space):
    first = repo.object_store.create_object("First", _class(repo, "character"))
    _accepted_r2(
        repo,
        first,
        "first-v1",
        [{"facet": "personality", "text": "active-generation-only"}],
    )
    generation_id = _activate_r2_generation(repo)

    late = repo.object_store.create_object("Late", _class(repo, "character"))
    _accepted_r2(
        repo,
        late,
        "late-v1",
        [{"facet": "personality", "text": "late-unlinked-sentinel"}],
    )
    engine, _ = _engine(repo, space, generation_id)

    response = engine.search("late-unlinked-sentinel", mode="lexical")
    assert all(result.object_id != late for result in response.results)


def test_r2_facet_scope_has_no_overview_or_other_facet_fallback(repo, space):
    object_id = repo.object_store.create_object("Scoped", _class(repo, "character"))
    _accepted_r2(
        repo,
        object_id,
        "scoped-v1",
        [
            {"text": "overview sentinel"},
            {"facet": "personality", "text": "personality sentinel"},
            {"facet": "values", "text": "values sentinel"},
        ],
    )
    generation_id = _activate_r2_generation(repo)
    engine, _ = _engine(repo, space, generation_id)

    response = engine.search(
        "sentinel",
        mode="semantic",
        filters=ObjectSearchFilters(facet="values"),
    )
    assert response.results
    for result in response.results:
        assert result.matched_facets == ("values",)
        assert all(match.representation_kind in {"facet", "statement"} for match in result.matches)
        assert all(match.facet == "values" for match in result.matches)


def test_r2_search_resolves_generation_once_per_request(repo, space):
    object_id = repo.object_store.create_object("Resolve Once", _class(repo, "character"))
    _accepted_r2(
        repo,
        object_id,
        "resolve-v1",
        [{"facet": "personality", "text": "resolve-once-sentinel"}],
    )
    generation_id = _activate_r2_generation(repo)
    engine, _ = _engine(repo, space, generation_id)

    original = engine._resolve_generation
    calls = 0

    def wrapped():
        nonlocal calls
        calls += 1
        return original()

    engine._resolve_generation = wrapped
    engine.search("resolve-once-sentinel", mode="hybrid")
    assert calls == 1


def test_r2_vector_generation_payload_mismatch_is_integrity_error(repo, space):
    object_id = repo.object_store.create_object("Mismatch", _class(repo, "character"))
    _accepted_r2(
        repo,
        object_id,
        "mismatch-v1",
        [{"facet": "personality", "text": "mismatch sentinel"}],
    )
    generation_id = _activate_r2_generation(repo)
    index = GenerationBlindFakeVectorIndex()
    engine, index = _engine(repo, space, generation_id, index=index)
    index.points = {
        point_id: VectorIndexPoint(
            point_id=point.point_id,
            vector=point.vector,
            metadata={**point.metadata, "generation_id": "wrong-generation"},
        )
        for point_id, point in index.points.items()
    }

    with pytest.raises(RuntimeError, match="generation payload mismatch"):
        engine.search("mismatch sentinel", mode="semantic")
