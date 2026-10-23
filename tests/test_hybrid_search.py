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
    ObjectSearchMatch,
    SearchRepresentationKind,
    VectorIndexMetadata,
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

    def __init__(self, *, fail_search=False):
        self.points = {}
        self.fail_search = fail_search

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
        if self.fail_search:
            raise RuntimeError("simulated vector backend outage")
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


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "hybrid-search.sqlite")
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
    source_id = repo.source_store.create_source(f"Hybrid Source {suffix}")
    locator_id = repo.source_store.add_locator(
        source_id, "url", f"https://example.test/hybrid/{suffix}", preferred=True
    )
    snapshot_id = repo.source_store.create_snapshot(
        source_id,
        "2026-10-13T00:00:00Z",
        "test",
        observed_locator_id=locator_id,
        title=f"Hybrid {suffix}",
    )
    artifact_id = repo.source_store.add_raw_artifact(
        snapshot_id, "html", f"memory://hybrid/{suffix}", "a" * 64, 10
    )
    run_id = repo.source_store.create_normalization_run(snapshot_id, "fixture", "1", [artifact_id])
    return repo.source_store.add_evidence(
        run_id, f"Evidence for {suffix}", EvidenceExtractionMode.NORMALIZED, language="ja"
    )


def _accepted(
    repo,
    object_id,
    version_id,
    *,
    base=None,
    statements=None,
):
    version_id = repo.version_store.begin_candidate(object_id, base, version_id=version_id)
    evidence_id = _evidence(repo, version_id)
    records = []
    for index, item in enumerate(statements or []):
        facet_key = item.get("facet")
        facet_id = None
        if facet_key is not None:
            facet_id = repo.semantic_store.facet_by_key(facet_key).facet_id
            repo.semantic_store.set_version_facet(version_id, facet_id, FacetStatus.CONTENT)
        scope_id = None
        if item.get("temporal"):
            scope_id = repo.semantic_store.create_temporal_scope(
                version_id,
                **item["temporal"],
            )
        statement_id = repo.semantic_store.add_statement(
            version_id,
            f"s-{index}",
            item["text"],
            item.get("derivation", DerivationKind.DIRECT_STATEMENT),
            facet_id=facet_id,
            temporal_scope_id=scope_id,
        )
        repo.source_store.link_evidence(
            version_id, EvidenceTargetKind.STATEMENT, statement_id, evidence_id
        )
        records.append(
            {
                "statement_id": statement_id,
                "facet_id": facet_id,
                "facet": facet_key,
                "temporal_scope_id": scope_id,
            }
        )
    repo.version_store.accept_candidate(version_id)
    SearchRepresentationBuilder(repo).materialize_version(version_id)
    return version_id, records


def _save_embeddings(repo, space, vectors_by_object=None):
    vectors_by_object = vectors_by_object or {}
    memberships = repo.semantic_store.knowledge_search_memberships()
    for membership in memberships:
        vector = vectors_by_object.get(membership["object_id"], (1.0, 0.0, 0.0))
        repo.embedding_store.save_representation_embedding(
            space,
            membership["representation_id"],
            list(vector),
        )


def _engine(repo, space, vectors_by_object=None, query_mapping=None, fail_search=False):
    _save_embeddings(repo, space, vectors_by_object)
    index = FakeVectorIndex(fail_search=fail_search)
    KnowledgeVectorIndexBuilder(repo, index).rebuild(space)
    provider = FakeEmbeddingProvider(space, query_mapping)
    return HybridObjectSearch(repo, embedding_provider=provider, vector_index=index), index


def test_migration_016_fts_tracks_search_representations(repo):
    representation_id = repo.semantic_store.get_or_create_search_representation(
        SearchRepresentationKind.STATEMENT,
        "test-builder",
        "1",
        "仲間を守るため自己犠牲を選ぶ",
    )
    row = repo.one(
        "SELECT representation_id,content FROM search_representation_fts WHERE representation_id=?",
        (representation_id,),
    )
    assert row["content"] == "仲間を守るため自己犠牲を選ぶ"
    assert repo.one("SELECT max(version) AS n FROM schema_migrations")["n"] == 18


def test_vector_builder_uses_membership_points_for_reused_representation(repo, space):
    object_id = repo.object_store.create_object("Alpha", _class(repo, "character"))
    first, _ = _accepted(
        repo,
        object_id,
        "version-1",
        statements=[{"facet": "personality", "text": "仲間を優先する"}],
    )
    second, _ = _accepted(
        repo,
        object_id,
        "version-2",
        base=first,
        statements=[{"facet": "personality", "text": "仲間を優先する"}],
    )
    _save_embeddings(repo, space)
    index = FakeVectorIndex()
    points = KnowledgeVectorIndexBuilder(repo, index).points(space)
    statement_points = [point for point in points if point.metadata["kind"] == "statement"]
    assert len(statement_points) == 2
    assert (
        statement_points[0].metadata["representation_id"]
        == statement_points[1].metadata["representation_id"]
    )
    assert statement_points[0].point_id != statement_points[1].point_id
    assert {point.metadata["is_current"] for point in statement_points} == {False, True}
    assert {point.metadata["version_id"] for point in statement_points} == {first, second}


def test_hybrid_exact_alias_outranks_semantic_and_returns_one_row_per_object(repo, space):
    alpha = repo.object_store.create_object(
        "Alpha Hero", _class(repo, "character"), aliases=["アルファ"]
    )
    beta = repo.object_store.create_object("Beta Rival", _class(repo, "character"))
    _accepted(
        repo,
        alpha,
        "alpha-v1",
        statements=[{"facet": "personality", "text": "仲間を守るため自己犠牲を選ぶ"}],
    )
    _accepted(
        repo,
        beta,
        "beta-v1",
        statements=[{"facet": "personality", "text": "競争心が強く単独行動を好む"}],
    )
    engine, _ = _engine(
        repo,
        space,
        {alpha: (1.0, 0.0, 0.0), beta: (0.0, 1.0, 0.0)},
        {"アルファ": (0.0, 1.0, 0.0)},
    )
    response = engine.search("アルファ", limit=10)
    assert response.results[0].object_id == alpha
    assert response.results[0].exact_identity == "alias"
    assert ObjectSearchChannel.EXACT_ALIAS in response.results[0].channels
    assert len({result.object_id for result in response.results}) == len(response.results)


def test_facet_and_version_filters_apply_before_semantic_candidate_generation(repo, space):
    object_id = repo.object_store.create_object("Alpha", _class(repo, "character"))
    first, _ = _accepted(
        repo,
        object_id,
        "alpha-v1",
        statements=[
            {"facet": "personality", "text": "古い性格"},
            {"facet": "values", "text": "古い価値観"},
        ],
    )
    second, _ = _accepted(
        repo,
        object_id,
        "alpha-v2",
        base=first,
        statements=[
            {"facet": "personality", "text": "新しい性格"},
            {"facet": "values", "text": "新しい価値観"},
        ],
    )
    engine, _ = _engine(repo, space)
    current = engine.search(
        "性格",
        mode="semantic",
        filters=ObjectSearchFilters(facet="personality"),
    )
    assert current.results
    assert {result.version_id for result in current.results} == {second}
    assert set(current.results[0].matched_facets) == {"personality"}
    assert all(match.facet == "personality" for match in current.results[0].matches)

    historical = engine.search(
        "性格",
        mode="semantic",
        filters=ObjectSearchFilters(facet="personality", version_id=first),
    )
    assert historical.results[0].version_id == first
    assert all(match.version_id == first for match in historical.results[0].matches)


def test_temporal_valid_at_and_temporal_scope_are_hard_filters(repo, space):
    object_id = repo.object_store.create_object("Temporal Alpha", _class(repo, "character"))
    _, records = _accepted(
        repo,
        object_id,
        "temporal-v1",
        statements=[
            {
                "facet": "personality",
                "text": "2026年だけ慎重に振る舞う",
                "temporal": {"valid_from": "2026-01-01", "valid_to": "2026-12-31"},
            },
            {"facet": "personality", "text": "普段は仲間を優先する"},
        ],
    )
    dated = records[0]
    timeless = records[1]
    engine, _ = _engine(repo, space)

    before = engine.search(
        "慎重",
        mode="semantic",
        filters=ObjectSearchFilters(knowledge_valid_at="2025-06-01"),
    )
    ids = {match.statement_id for result in before.results for match in result.matches}
    assert dated["statement_id"] not in ids
    assert timeless["statement_id"] in ids

    exact_scope = engine.search(
        "慎重",
        mode="semantic",
        filters=ObjectSearchFilters(temporal_scope_id=dated["temporal_scope_id"]),
    )
    ids = {match.statement_id for result in exact_scope.results for match in result.matches}
    assert ids == {dated["statement_id"]}


def test_class_filters_and_unknown_filter_validation(repo, space):
    character = repo.object_store.create_object("Character A", _class(repo, "character"))
    repo.object_store.add_additional_class(character, _class(repo, "fictional_entity"))
    work = repo.object_store.create_object("Work A", _class(repo, "work"))
    _accepted(
        repo,
        character,
        "character-v1",
        statements=[{"facet": "personality", "text": "勇敢"}],
    )
    _accepted(repo, work, "work-v1", statements=[{"facet": "themes", "text": "勇気"}])
    engine, _ = _engine(repo, space)

    primary = engine.search(
        "勇敢",
        mode="semantic",
        filters=ObjectSearchFilters(primary_class="character"),
    )
    assert {result.object_id for result in primary.results} == {character}
    ancestor = engine.search(
        "勇敢",
        mode="semantic",
        filters=ObjectSearchFilters(ancestor_class="agent"),
    )
    assert {result.object_id for result in ancestor.results} == {character}
    additional = engine.search(
        "勇敢",
        mode="semantic",
        filters=ObjectSearchFilters(additional_class="fictional_entity"),
    )
    assert {result.object_id for result in additional.results} == {character}
    with pytest.raises(ValueError, match="Unknown Class"):
        engine.search("勇敢", filters=ObjectSearchFilters(primary_class="does_not_exist"))
    with pytest.raises(ValueError, match="Unknown Facet"):
        engine.search("勇敢", filters=ObjectSearchFilters(facet="does_not_exist"))


def test_short_japanese_lexical_fallback_and_explicit_semantic_degradation(repo, space):
    object_id = repo.object_store.create_object("Short Query", _class(repo, "character"))
    _accepted(
        repo,
        object_id,
        "short-v1",
        statements=[{"facet": "values", "text": "愛を最優先する"}],
    )
    provider = FakeEmbeddingProvider(space)
    broken_index = FakeVectorIndex(fail_search=True)
    engine = HybridObjectSearch(repo, embedding_provider=provider, vector_index=broken_index)

    lexical = engine.search("愛", mode="lexical")
    assert lexical.results[0].object_id == object_id
    hybrid = engine.search("愛", mode="hybrid")
    assert hybrid.results[0].object_id == object_id
    assert hybrid.degraded_channels == ("semantic:RuntimeError",)
    with pytest.raises(RuntimeError, match="outage"):
        engine.search("愛", mode="semantic")


def test_statement_channel_contribution_is_capped_at_three():
    def match(rank, membership):
        return ObjectSearchMatch(
            channel=ObjectSearchChannel.SEMANTIC_STATEMENT,
            version_id="v",
            representation_id=membership,
            membership_id=membership,
            representation_kind="statement",
            facet="personality",
            statement_id=membership,
            snippet=membership,
            score=1.0,
            score_type="cosine_similarity",
            source_rank=rank,
        )

    base = [
        (("a", "v"), match(1, "a1")),
        (("a", "v"), match(4, "a2")),
        (("a", "v"), match(7, "a3")),
        (("b", "v"), match(2, "b1")),
        (("b", "v"), match(3, "b2")),
        (("b", "v"), match(5, "b3")),
    ]
    ranks_before, _ = HybridObjectSearch._aggregate_channel(
        base, ObjectSearchChannel.SEMANTIC_STATEMENT
    )
    extra = base + [(("a", "v"), match(rank, f"a{rank}")) for rank in range(8, 40)]
    ranks_after, _ = HybridObjectSearch._aggregate_channel(
        extra, ObjectSearchChannel.SEMANTIC_STATEMENT
    )
    assert ranks_before == ranks_after


def test_qdrant_adapter_integrates_with_membership_index_and_hybrid_search(repo, space):
    qdrant_client = pytest.importorskip("qdrant_client")
    from sgokb.retrieval.vector_index import QdrantVectorIndexAdapter

    object_id = repo.object_store.create_object("Qdrant Alpha", _class(repo, "character"))
    repo.object_store.add_additional_class(object_id, _class(repo, "fictional_entity"))
    _accepted(
        repo,
        object_id,
        "qdrant-v1",
        statements=[{"facet": "personality", "text": "仲間を守るため自己犠牲を選ぶ"}],
    )
    _save_embeddings(repo, space, {object_id: (1.0, 0.0, 0.0)})
    adapter = QdrantVectorIndexAdapter(
        client=qdrant_client.QdrantClient(location=":memory:"),
        wait_for_index=False,
    )
    metadata = KnowledgeVectorIndexBuilder(repo, adapter).rebuild(space)
    assert metadata.points_count == len(repo.semantic_store.knowledge_search_memberships())

    engine = HybridObjectSearch(
        repo,
        embedding_provider=FakeEmbeddingProvider(space, {"自己犠牲": (1.0, 0.0, 0.0)}),
        vector_index=adapter,
    )
    response = engine.search(
        "自己犠牲",
        mode="semantic",
        filters=ObjectSearchFilters(
            facet="personality",
            primary_class="character",
            additional_class="fictional_entity",
            ancestor_class="agent",
        ),
    )
    assert response.results[0].object_id == object_id
    assert response.results[0].matched_facets == ("personality",)
    assert all(match.version_id == "qdrant-v1" for match in response.results[0].matches)
