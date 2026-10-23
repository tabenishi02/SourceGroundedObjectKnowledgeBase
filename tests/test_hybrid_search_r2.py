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
from sgokb.retrieval.hybrid_search_r2 import KnowledgeVectorIndexBuilder as FixtureVectorBuilder


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
    version_id = repo.version_store.begin_candidate(
        object_id, repo.version_store.current_version_id(object_id), version_id=version_id
    )
    evidence_id = _evidence(repo, version_id)
    for index, item in enumerate(statements):
        facet_key = item.get("facet")
        facet_id = None
        if facet_key is not None:
            facet_id = repo.semantic_store.facet_by_key(facet_key).facet_id
            repo.semantic_store.set_version_facet(version_id, facet_id, FacetStatus.CONTENT)
        temporal_scope_id = None
        if item.get("temporal"):
            temporal_scope_id = repo.semantic_store.create_temporal_scope(
                version_id, **item["temporal"]
            )
        statement_id = repo.semantic_store.add_statement(
            version_id,
            f"s-{index}",
            item["text"],
            item.get("derivation", DerivationKind.DIRECT_STATEMENT),
            facet_id=facet_id,
            temporal_scope_id=temporal_scope_id,
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
    assert {point.metadata["generation_id"] for point in index.points.values()} == {generation_id}
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


@pytest.mark.parametrize("mode", ["lexical", "semantic", "hybrid"])
def test_r2_excludes_unlinked_knowledge_even_with_foreign_vector_points(repo, space, mode):
    active = repo.object_store.create_object("Active", _class(repo, "character"))
    _accepted_r2(
        repo, active, "active-isolation", [{"facet": "values", "text": "isolation-sentinel"}]
    )
    generation_id = _activate_r2_generation(repo)
    late = repo.object_store.create_object("Unlinked", _class(repo, "character"))
    _accepted_r2(
        repo, late, "unlinked-isolation", [{"facet": "values", "text": "isolation-sentinel"}]
    )
    engine, index = _engine(repo, space, generation_id)
    foreign = [
        VectorIndexPoint(
            point_id=p.point_id,
            vector=p.vector,
            metadata={**p.metadata, "generation_id": "foreign-generation"},
        )
        # Deliberately construct foreign points outside the active maintenance scope.
        for p in FixtureVectorBuilder(repo, index).points(space)
        if p.metadata["object_id"] == late
    ]
    assert foreign
    index.upsert(space, foreign)
    response = engine.search("isolation-sentinel", mode=mode)
    assert {r.object_id for r in response.results} == {active}
    assert all(
        m.representation_kind != "object_overall" for r in response.results for m in r.matches
    )


@pytest.mark.parametrize("generation", ["pre-cutover", "v1", "r2"])
def test_object_channel_identity_is_explicit_for_each_generation(repo, space, generation):
    object_id = repo.object_store.create_object("Identity", _class(repo, "character"))
    _accepted_r2(repo, object_id, "identity-v1", [{"text": "identity-sentinel"}])
    generation_id = None
    if generation == "r2":
        generation_id = _activate_r2_generation(repo)
    elif generation == "v1":
        generation_id = "search-generation:phase-i-v1"
        with repo.db:
            repo.db.execute(
                "UPDATE knowledge_search_generations SET state='ready',source_catalog_digest=?,"
                "membership_digest=?,ready_at=? WHERE id=?",
                ("a" * 64, "b" * 64, "2026-10-23T00:00:00Z", generation_id),
            )
            repo.db.execute(
                "INSERT INTO knowledge_search_generation_memberships "
                "SELECT ?,id,created_at FROM knowledge_search_representation_memberships "
                "WHERE target_kind IN ('object_overall','facet','statement')",
                (generation_id,),
            )
            repo.db.execute(
                "INSERT INTO knowledge_search_active_generation VALUES('knowledge',?,1,?)",
                (generation_id, "2026-10-23T00:00:00Z"),
            )
    engine, _ = _engine(repo, space, generation_id)
    response = engine.search("identity-sentinel", mode="semantic")
    kind = "object_overview" if generation == "r2" else "object_overall"
    channel = "semantic_object_overview" if generation == "r2" else "semantic_object_overall"
    object_matches = [
        m for r in response.results for m in r.matches if m.representation_kind == kind
    ]
    assert object_matches and all(m.channel.value == channel for m in object_matches)
    excluded = "object_overall" if generation == "r2" else "object_overview"
    assert all(m.representation_kind != excluded for r in response.results for m in r.matches)


def test_r2_missing_facet_has_no_overview_or_other_facet_rescue(repo, space):
    object_id = repo.object_store.create_object("No Rescue", _class(repo, "character"))
    _accepted_r2(
        repo,
        object_id,
        "no-rescue-v1",
        [
            {"text": "rescue-sentinel"},
            {"facet": "personality", "text": "rescue-sentinel"},
        ],
    )
    generation_id = _activate_r2_generation(repo)
    engine, _ = _engine(repo, space, generation_id)
    for mode in ("lexical", "semantic", "hybrid"):
        assert (
            engine.search(
                "rescue-sentinel", mode=mode, filters=ObjectSearchFilters(facet="values")
            ).results
            == ()
        )


@pytest.mark.parametrize("filter_kind", ["temporal_scope", "valid_at", "derivation"])
def test_r2_temporal_and_derivation_filters_are_statement_only(repo, space, filter_kind):
    object_id = repo.object_store.create_object("Filtered", _class(repo, "character"))
    _accepted_r2(
        repo,
        object_id,
        "filtered-v1",
        [
            {"text": "filter-sentinel overview"},
            {
                "facet": "personality",
                "text": "filter-sentinel dated",
                "temporal": {"valid_from": "2026-01-01", "valid_to": "2026-12-31"},
            },
            {
                "facet": "personality",
                "text": "filter-sentinel interpreted",
                "derivation": DerivationKind.INTERPRETATION,
            },
        ],
    )
    generation_id = _activate_r2_generation(repo)
    engine, _ = _engine(repo, space, generation_id)
    dated = repo.one("SELECT id,temporal_scope_id FROM knowledge_statements WHERE local_key='s-1'")
    if filter_kind == "temporal_scope":
        filters = ObjectSearchFilters(temporal_scope_id=dated["temporal_scope_id"])
        expected = {dated["id"]}
    elif filter_kind == "valid_at":
        filters = ObjectSearchFilters(knowledge_valid_at="2025-06-01")
        expected = {
            r["id"]
            for r in repo.rows(
                "SELECT id FROM knowledge_statements WHERE temporal_scope_id IS NULL"
            )
        }
    else:
        filters = ObjectSearchFilters(derivation_kind="interpretation")
        expected = {
            r["id"]
            for r in repo.rows(
                "SELECT id FROM knowledge_statements WHERE derivation_kind='interpretation'"
            )
        }
    for mode in ("lexical", "semantic"):
        response = engine.search("filter-sentinel", mode=mode, filters=filters)
        matches = [m for r in response.results for m in r.matches]
        assert matches and {m.statement_id for m in matches} == expected
        assert all(m.representation_kind == "statement" for m in matches)


def test_r2_current_historical_isolation_and_one_result_per_object(repo, space):
    object_id = repo.object_store.create_object("History", _class(repo, "character"))
    _accepted_r2(repo, object_id, "history-old", [{"facet": "values", "text": "history-sentinel"}])
    _accepted_r2(
        repo, object_id, "history-current", [{"facet": "values", "text": "history-sentinel"}]
    )
    generation_id = _activate_r2_generation(repo)
    engine, _ = _engine(repo, space, generation_id)
    for mode in ("lexical", "semantic", "hybrid"):
        current = engine.search("history-sentinel", mode=mode)
        assert len(current.results) == 1 and current.results[0].version_id == "history-current"
        historical = engine.search(
            "history-sentinel", mode=mode, filters=ObjectSearchFilters(version_id="history-old")
        )
        assert len(historical.results) == 1 and historical.results[0].version_id == "history-old"
        assert all(m.version_id == "history-old" for m in historical.results[0].matches)


def test_r2_exact_identity_priority_and_rrf_are_preserved(repo, space):
    ids = []
    for name, aliases in [("Needle", []), ("Alias Holder", ["Needle"]), ("Other", [])]:
        object_id = repo.object_store.create_object(
            name, _class(repo, "character"), aliases=aliases
        )
        _accepted_r2(
            repo,
            object_id,
            "priority-" + str(len(ids)),
            [
                {"text": "Needle overview"},
                {"facet": "personality", "text": "Needle detail"},
            ],
        )
        ids.append(object_id)
    generation_id = _activate_r2_generation(repo)
    engine, _ = _engine(repo, space, generation_id)
    response = engine.search("Needle", mode="hybrid")
    assert [r.object_id for r in response.results] == ids
    assert [r.exact_identity for r in response.results] == ["name", "alias", None]
    assert len(set(r.object_id for r in response.results)) == 3
    semantic = engine.search(
        "Needle", mode="semantic", filters=ObjectSearchFilters(version_id="priority-0")
    )
    assert len(semantic.results) == 1 and semantic.results[0].object_id == ids[0]
    # Three public semantic match families now produce one outer Semantic vote.
    assert semantic.results[0].fused_score == pytest.approx(1 / 61)
    assert {m.channel for m in semantic.results[0].matches} == {
        ObjectSearchChannel.SEMANTIC_OBJECT_OVERVIEW,
        ObjectSearchChannel.SEMANTIC_FACET,
        ObjectSearchChannel.SEMANTIC_STATEMENT,
    }


@pytest.mark.parametrize(
    "channel,cap",
    [
        (ObjectSearchChannel.SEMANTIC_OBJECT_OVERVIEW, 1),
        (ObjectSearchChannel.SEMANTIC_FACET, 2),
        (ObjectSearchChannel.SEMANTIC_STATEMENT, 3),
        (ObjectSearchChannel.KNOWLEDGE_LEXICAL, 3),
    ],
)
def test_r2_channel_growth_is_bounded_at_frozen_caps(channel, cap):
    from sgokb.retrieval.hybrid_search import _CHANNEL_CONTRIBUTION_CAPS, RRF_K

    assert RRF_K == 60 and _CHANNEL_CONTRIBUTION_CAPS[channel] == cap

    def row(object_id, rank):
        match = ObjectSearchMatch(
            channel=channel,
            version_id="v",
            representation_id=str(rank),
            membership_id=str(rank),
            representation_kind="statement",
            facet="values",
            statement_id=str(rank),
            snippet="detail",
            score=1,
            score_type="test",
            source_rank=rank,
        )
        return ((object_id, "v"), match)

    base = [row("a", x) for x in (1, 4, 7)[:cap]] + [row("b", x) for x in (2, 3, 5)[:cap]]
    before, _ = HybridObjectSearch._aggregate_channel(base, channel)
    after, _ = HybridObjectSearch._aggregate_channel(
        base + [row("a", x) for x in range(8, 80)], channel
    )
    assert before == after


def test_r2_hybrid_degrades_runtime_failure_but_semantic_raises(repo, space):
    object_id = repo.object_store.create_object("Degrade", _class(repo, "character"))
    _accepted_r2(repo, object_id, "degrade-v1", [{"facet": "values", "text": "degrade-sentinel"}])
    generation_id = _activate_r2_generation(repo)
    engine, index = _engine(repo, space, generation_id)

    def unavailable(*args, **kwargs):
        raise RuntimeError("offline backend unavailable")

    index.search = unavailable
    hybrid = engine.search("degrade-sentinel", mode="hybrid")
    assert hybrid.results and hybrid.degraded_channels == ("semantic:RuntimeError",)
    with pytest.raises(RuntimeError, match="offline backend unavailable"):
        engine.search("degrade-sentinel", mode="semantic")


def test_r2_qdrant_adapter_scopes_active_family(repo, space):
    qdrant = pytest.importorskip("qdrant_client")
    from sgokb.retrieval.vector_index import QdrantVectorIndexAdapter

    object_id = repo.object_store.create_object("Qdrant R2", _class(repo, "character"))
    _accepted_r2(repo, object_id, "qdrant-r2", [{"facet": "values", "text": "qdrant-r2-sentinel"}])
    generation_id = _activate_r2_generation(repo)
    adapter = QdrantVectorIndexAdapter(
        client=qdrant.QdrantClient(location=":memory:"), wait_for_index=False
    )
    try:
        engine, _ = _engine(repo, space, generation_id, index=adapter)
        response = engine.search("qdrant-r2-sentinel", mode="semantic")
        assert {r.object_id for r in response.results} == {object_id}
        assert all(
            m.representation_kind != "object_overall" for r in response.results for m in r.matches
        )
        assert ObjectSearchChannel.SEMANTIC_OBJECT_OVERVIEW in response.results[0].channels
    finally:
        adapter.client.close() if hasattr(adapter, "client") else adapter._client.close()


def test_mcp_search_reaches_r2_wrapper_through_real_read_application(repo, space):
    from sgokb.application_read import KnowledgeReadApplication
    from sgokb.mcp import MCPReadAdapter

    active = repo.object_store.create_object("MCP Active", _class(repo, "character"))
    _accepted_r2(
        repo, active, "mcp-active", [{"facet": "values", "text": "mcp-generation-sentinel"}]
    )
    generation_id = _activate_r2_generation(repo)
    late = repo.object_store.create_object("MCP Late", _class(repo, "character"))
    _accepted_r2(repo, late, "mcp-late", [{"facet": "values", "text": "mcp-generation-sentinel"}])
    _, index = _engine(repo, space, generation_id)
    application = KnowledgeReadApplication(
        repo, embedding_provider=FakeEmbeddingProvider(space), vector_index=index
    )
    response = MCPReadAdapter(application).call_tool(
        "search_objects", {"query": "mcp-generation-sentinel", "mode": "semantic"}
    )
    results = response["data"]["results"]
    assert {r["object_id"] for r in results} == {active}
    assert "semantic_object_overview" in results[0]["channels"]
    assert "semantic_object_overall" not in results[0]["channels"]
    assert all(m["representation_kind"] != "object_overall" for r in results for m in r["matches"])
