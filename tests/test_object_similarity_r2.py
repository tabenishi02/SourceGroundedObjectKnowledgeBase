import importlib
import json
import math

import pytest

from sgokb.application_read import KnowledgeReadApplication
from sgokb.domain import (
    DerivationKind,
    EmbeddingSpaceSpec,
    EvidenceExtractionMode,
    EvidenceTargetKind,
    FacetStatus,
    VectorIndexMetadata,
    VectorSearchFilter,
    VectorSearchHit,
)
from sgokb.mcp import MCPReadAdapter
from sgokb.repository import Repository
from sgokb.retrieval import (
    KnowledgeVectorIndexBuilder,
    ObjectSimilaritySearch,
    SearchRepresentationBuilder,
)


class FakeVectorIndex:
    backend_key = "fake-exact"

    def __init__(self):
        self.points = {}
        self.search_filters = []
        self.search_limits = []

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
        self.search_filters.append(filters)
        self.search_limits.append(limit)
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
    value = Repository(tmp_path / "object-similarity-r2.sqlite")
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
    source_id = repo.source_store.create_source(f"R2 Similarity Source {suffix}")
    locator_id = repo.source_store.add_locator(
        source_id,
        "url",
        f"https://example.test/r2-similarity/{suffix}",
        preferred=True,
    )
    snapshot_id = repo.source_store.create_snapshot(
        source_id,
        "2026-10-23T00:00:00Z",
        "test",
        observed_locator_id=locator_id,
        title=f"R2 Similarity {suffix}",
    )
    artifact_id = repo.source_store.add_raw_artifact(
        snapshot_id,
        "html",
        f"memory://r2-similarity/{suffix}",
        "a" * 64,
        10,
    )
    run_id = repo.source_store.create_normalization_run(snapshot_id, "fixture", "1", [artifact_id])
    return repo.source_store.add_evidence(
        run_id,
        f"Evidence for {suffix}",
        EvidenceExtractionMode.NORMALIZED,
        language="ja",
    )


def _accepted_r2(repo, object_id, version_id, statements, *, base=None):
    version_id = repo.version_store.begin_candidate(object_id, base, version_id=version_id)
    evidence_id = _evidence(repo, version_id)
    seen_facets = set()
    for index, item in enumerate(statements):
        facet_key = item.get("facet")
        facet_id = None
        if facet_key is not None:
            facet_id = repo.semantic_store.facet_by_key(facet_key).facet_id
            if facet_id not in seen_facets:
                repo.semantic_store.set_version_facet(version_id, facet_id, FacetStatus.CONTENT)
                seen_facets.add(facet_id)
        statement_id = repo.semantic_store.add_statement(
            version_id,
            f"s-{index:03d}",
            item["text"],
            DerivationKind.DIRECT_STATEMENT,
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


def _activate_generation(repo, generation_id="test-r2-similarity-generation", *, r2=True):
    now = "2026-10-23T00:00:00Z"
    repo.db.execute(
        """INSERT INTO knowledge_search_generations(
             id,contract_key,contract_version,state,source_catalog_digest,
             membership_digest,created_at,ready_at
           ) VALUES(?,?,?,?,?,?,?,?)""",
        (
            generation_id,
            "n05d04r2-hierarchical-v2" if r2 else "phase-i-search-v1",
            2 if r2 else 1,
            "ready",
            "a" * 64,
            "b" * 64,
            now,
            now,
        ),
    )
    rows = repo.db.execute(
        """SELECT id FROM knowledge_search_representation_memberships
           WHERE target_kind IN (?,'facet','statement') ORDER BY id""",
        ("object_overview" if r2 else "object_overall",),
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


def _membership_rows(repo):
    return [
        dict(row)
        for row in repo.db.execute(
            """SELECT m.object_id,m.version_id,m.target_kind,m.representation_id,
                      m.statement_id,f.key AS facet,s.text AS statement_text
               FROM knowledge_search_representation_memberships m
               LEFT JOIN facet_definitions f ON f.id=m.facet_id
               LEFT JOIN knowledge_statements s ON s.id=m.statement_id
               ORDER BY m.id"""
        ).fetchall()
    ]


def _save_embeddings(repo, space, vector_for):
    saved = set()
    for row in _membership_rows(repo):
        representation_id = row["representation_id"]
        if representation_id in saved:
            continue
        vector = vector_for(row)
        repo.embedding_store.save_representation_embedding(space, representation_id, list(vector))
        saved.add(representation_id)


def _finder(repo, space, generation_id, vector_for, index=None):
    _save_embeddings(repo, space, vector_for)
    index = index or FakeVectorIndex()
    KnowledgeVectorIndexBuilder(repo, index, generation_id=generation_id).rebuild(space)
    return ObjectSimilaritySearch(repo, space=space, vector_index=index), index


def _vector_map(mapping, default=(0.0, 0.0, 1.0)):
    def resolve(row):
        keys = [
            (
                row["object_id"],
                row["version_id"],
                row["target_kind"],
                row["facet"],
                row["statement_text"],
            ),
            (
                row["object_id"],
                row["target_kind"],
                row["facet"],
                row["statement_text"],
            ),
            (row["object_id"], row["target_kind"], row["facet"]),
            (row["object_id"], row["target_kind"]),
        ]
        for key in keys:
            if key in mapping:
                return mapping[key]
        return default

    return resolve


def test_r2_overall_uses_detail_facet_when_overviews_are_indistinguishable(repo, space):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    near = repo.object_store.create_object("Near", _class(repo, "character"))
    far = repo.object_store.create_object("Far", _class(repo, "character"))
    _accepted_r2(repo, source, "source-v1", [{"facet": "personality", "text": "kind"}])
    _accepted_r2(repo, near, "near-v1", [{"facet": "personality", "text": "kindish"}])
    _accepted_r2(repo, far, "far-v1", [{"facet": "personality", "text": "cold"}])
    generation = _activate_generation(repo)
    finder, _ = _finder(
        repo,
        space,
        generation,
        _vector_map(
            {
                (source, "object_overview"): (1.0, 0.0, 0.0),
                (near, "object_overview"): (1.0, 0.0, 0.0),
                (far, "object_overview"): (1.0, 0.0, 0.0),
                (source, "facet", "personality"): (0.0, 1.0, 0.0),
                (near, "facet", "personality"): (0.0, 1.0, 0.0),
                (far, "facet", "personality"): (0.0, 0.0, 1.0),
            }
        ),
    )

    response = finder.find_similar_objects(source)
    assert response.results[0].object_id == near
    assert response.results[0].score_type == "hierarchical_similarity"
    assert any(item.component == "facet" for item in response.results[0].evidence)
    assert all(
        item.representation_kind != "object_overall" for item in response.results[0].evidence
    )


def test_r2_statement_evidence_can_break_overview_and_facet_tie(repo, space):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    near = repo.object_store.create_object("Near", _class(repo, "character"))
    far = repo.object_store.create_object("Far", _class(repo, "character"))
    for object_id, version, text in (
        (source, "source-v1", "protect friends"),
        (near, "near-v1", "protect companions"),
        (far, "far-v1", "prefer solitude"),
    ):
        _accepted_r2(repo, object_id, version, [{"facet": "values", "text": text}])
    generation = _activate_generation(repo)
    finder, _ = _finder(
        repo,
        space,
        generation,
        _vector_map(
            {
                (source, "object_overview"): (1.0, 0.0, 0.0),
                (near, "object_overview"): (1.0, 0.0, 0.0),
                (far, "object_overview"): (1.0, 0.0, 0.0),
                (source, "facet", "values"): (0.0, 1.0, 0.0),
                (near, "facet", "values"): (0.0, 1.0, 0.0),
                (far, "facet", "values"): (0.0, 1.0, 0.0),
                (source, "statement", "values", "protect friends"): (1.0, 1.0, 0.0),
                (near, "statement", "values", "protect companions"): (1.0, 1.0, 0.0),
                (far, "statement", "values", "prefer solitude"): (0.0, 0.0, 1.0),
            }
        ),
    )

    response = finder.find_similar_objects(source)
    assert response.results[0].object_id == near
    statement_evidence = [
        item for item in response.results[0].evidence if item.component == "statement"
    ]
    assert statement_evidence
    assert statement_evidence[0].score_type == "cosine_similarity"
    assert statement_evidence[0].contribution > 0


def test_many_irrelevant_candidate_statements_do_not_create_count_boost(repo, space):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    near = repo.object_store.create_object("Near", _class(repo, "character"))
    large = repo.object_store.create_object("Large", _class(repo, "character"))
    _accepted_r2(repo, source, "source-v1", [{"facet": "values", "text": "target"}])
    _accepted_r2(repo, near, "near-v1", [{"facet": "values", "text": "relevant"}])
    _accepted_r2(
        repo,
        large,
        "large-v1",
        [{"facet": "values", "text": f"irrelevant-{index}"} for index in range(40)],
    )
    generation = _activate_generation(repo)

    def vectors(row):
        if row["target_kind"] in {"object_overview", "facet"}:
            return (1.0, 0.0, 0.0)
        if row["object_id"] == source:
            return (0.0, 1.0, 0.0)
        if row["object_id"] == near:
            return (0.0, 1.0, 0.0)
        return (0.8, 0.6, 0.0)

    finder, _ = _finder(repo, space, generation, vectors)
    response = finder.find_similar_objects(source)
    assert response.results[0].object_id == near
    for result in response.results:
        assert len([item for item in result.evidence if item.component == "statement"]) <= 3


def test_r2_same_facet_boundary_prevents_cross_facet_statement_match(repo, space):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    good = repo.object_store.create_object("Good", _class(repo, "character"))
    wrong = repo.object_store.create_object("Wrong", _class(repo, "character"))
    _accepted_r2(repo, source, "source-v1", [{"facet": "personality", "text": "shared"}])
    _accepted_r2(repo, good, "good-v1", [{"facet": "personality", "text": "shared-good"}])
    _accepted_r2(repo, wrong, "wrong-v1", [{"facet": "values", "text": "shared-wrong"}])
    generation = _activate_generation(repo)
    finder, _ = _finder(
        repo,
        space,
        generation,
        _vector_map(
            {
                (source, "statement", "personality", "shared"): (0.0, 1.0, 0.0),
                (good, "statement", "personality", "shared-good"): (0.0, 1.0, 0.0),
                (wrong, "statement", "values", "shared-wrong"): (0.0, 1.0, 0.0),
            }
        ),
    )
    response = finder.find_similar_objects(source)
    wrong_result = next(result for result in response.results if result.object_id == wrong)
    assert all(
        not (item.component == "statement" and item.facet == "values")
        for item in wrong_result.evidence
    )


def test_source_is_excluded_in_vector_filter_before_candidate_limit(repo, space):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    target = repo.object_store.create_object("Target", _class(repo, "character"))
    _accepted_r2(repo, source, "source-v1", [])
    _accepted_r2(repo, target, "target-v1", [])
    generation = _activate_generation(repo)
    finder, index = _finder(repo, space, generation, lambda row: (1.0, 0.0, 0.0))
    response = finder.find_similar_objects(source)
    assert response.results[0].object_id == target
    assert index.search_filters
    for filters in index.search_filters:
        assert any(item.field == "object_id" and source in item.values for item in filters.excludes)


def test_same_class_default_and_cross_class_override(repo, space):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    character = repo.object_store.create_object("Character", _class(repo, "character"))
    work = repo.object_store.create_object("Work", _class(repo, "work"))
    for object_id, version in (
        (source, "source-v1"),
        (character, "character-v1"),
        (work, "work-v1"),
    ):
        _accepted_r2(repo, object_id, version, [])
    generation = _activate_generation(repo)
    finder, _ = _finder(
        repo,
        space,
        generation,
        _vector_map(
            {
                (source, "object_overview"): (1.0, 0.0, 0.0),
                (character, "object_overview"): (0.8, 0.2, 0.0),
                (work, "object_overview"): (1.0, 0.0, 0.0),
            }
        ),
    )
    same_class = finder.find_similar_objects(source)
    assert [item.object_id for item in same_class.results] == [character]
    cross_class = finder.find_similar_objects(source, cross_class=True)
    assert cross_class.results[0].object_id == work


def test_historical_source_uses_historical_vectors_but_candidates_are_current(repo, space):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    left = repo.object_store.create_object("Left", _class(repo, "character"))
    right = repo.object_store.create_object("Right", _class(repo, "character"))
    first = _accepted_r2(repo, source, "source-v1", [{"text": "Historical summary"}])
    _accepted_r2(repo, source, "source-v2", [{"text": "Current summary"}], base=first)
    overview_ids = {
        row["representation_id"]
        for row in _membership_rows(repo)
        if row["object_id"] == source and row["target_kind"] == "object_overview"
    }
    assert len(overview_ids) == 2
    old_left = _accepted_r2(repo, left, "left-v0", [{"text": "Obsolete candidate"}])
    _accepted_r2(repo, left, "left-v1", [], base=old_left)
    _accepted_r2(repo, right, "right-v1", [])
    generation = _activate_generation(repo)
    finder, _ = _finder(
        repo,
        space,
        generation,
        _vector_map(
            {
                (source, "source-v1", "object_overview", None, None): (1.0, 0.0, 0.0),
                (source, "source-v2", "object_overview", None, None): (0.0, 1.0, 0.0),
                (left, "object_overview"): (1.0, 0.0, 0.0),
                (right, "object_overview"): (0.0, 1.0, 0.0),
            }
        ),
    )
    historical = finder.find_similar_objects(source, source_version_id="source-v1")
    current = finder.find_similar_objects(source)
    assert historical.source_version_id == "source-v1"
    assert historical.results[0].object_id == left
    assert historical.results[0].version_id == "left-v1"
    assert all(result.version_id != "left-v0" for result in historical.results)
    assert current.source_version_id == "source-v2"
    assert current.results[0].object_id == right


def test_active_generation_isolation_and_object_overall_exclusion(repo, space):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    target = repo.object_store.create_object("Target", _class(repo, "character"))
    _accepted_r2(repo, source, "source-v1", [{"facet": "values", "text": "source"}])
    _accepted_r2(repo, target, "target-v1", [{"facet": "values", "text": "target"}])
    generation = _activate_generation(repo)
    finder, index = _finder(repo, space, generation, lambda row: (1.0, 0.0, 0.0))
    assert {point.metadata["generation_id"] for point in index.points.values()} == {generation}
    assert "object_overall" not in {point.metadata["kind"] for point in index.points.values()}
    response = finder.find_similar_objects(source)
    assert response.generation_id == generation
    assert all(
        item.representation_kind in {"object_overview", "facet", "statement"}
        for result in response.results
        for item in result.evidence
    )


def test_generation_payload_mismatch_is_integrity_error(repo, space):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    target = repo.object_store.create_object("Target", _class(repo, "character"))
    _accepted_r2(repo, source, "source-v1", [])
    _accepted_r2(repo, target, "target-v1", [])
    generation = _activate_generation(repo)
    index = GenerationBlindFakeVectorIndex()
    finder, index = _finder(repo, space, generation, lambda row: (1.0, 0.0, 0.0), index=index)
    target_point = next(
        point
        for point in index.points.values()
        if point.metadata["object_id"] == target and point.metadata["kind"] == "object_overview"
    )
    index.points[target_point.point_id] = type(target_point)(
        point_id=target_point.point_id,
        vector=target_point.vector,
        metadata={**target_point.metadata, "generation_id": "wrong-generation"},
    )
    with pytest.raises(RuntimeError, match="generation payload mismatch"):
        finder.find_similar_objects(source)


def test_generation_is_resolved_once_per_similarity_operation(repo, space):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    target = repo.object_store.create_object("Target", _class(repo, "character"))
    _accepted_r2(repo, source, "source-v1", [{"facet": "values", "text": "source"}])
    _accepted_r2(repo, target, "target-v1", [{"facet": "values", "text": "target"}])
    generation = _activate_generation(repo)
    finder, index = _finder(repo, space, generation, lambda row: (1.0, 0.0, 0.0))

    class CountingFinder(ObjectSimilaritySearch):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.resolve_count = 0

        def _resolve_generation(self):
            self.resolve_count += 1
            return super()._resolve_generation()

    counting = CountingFinder(repo, space=space, vector_index=index)
    counting.find_similar_objects(source)
    assert counting.resolve_count == 1


def test_source_query_count_and_result_evidence_are_bounded(repo, space):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    target = repo.object_store.create_object("Target", _class(repo, "character"))
    facet_keys = [
        row["key"]
        for row in repo.db.execute(
            "SELECT key FROM facet_definitions ORDER BY key LIMIT 10"
        ).fetchall()
    ]
    assert len(facet_keys) == 10
    statements = [
        {"facet": key, "text": f"source-{key}-{index}"} for key in facet_keys for index in range(3)
    ]
    _accepted_r2(repo, source, "source-v1", statements)
    _accepted_r2(
        repo, target, "target-v1", [{"facet": key, "text": f"target-{key}"} for key in facet_keys]
    )
    generation = _activate_generation(repo)
    finder, index = _finder(repo, space, generation, lambda row: (1.0, 0.0, 0.0))
    response = finder.find_similar_objects(source)
    assert len(index.search_filters) == 1 + 8 + 12
    assert index.search_limits == [128] + [24] * 8 + [12] * 12
    assert sum(index.search_limits) == 464
    assert len(response.results[0].evidence) <= 1 + 2 + 3
    assert 0.0 <= response.results[0].score <= 1.0


def test_active_r2_facet_similarity_remains_same_facet_raw_cosine(repo, space):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    near = repo.object_store.create_object("Near", _class(repo, "character"))
    wrong = repo.object_store.create_object("Wrong", _class(repo, "character"))
    _accepted_r2(repo, source, "source-v1", [{"facet": "personality", "text": "source"}])
    _accepted_r2(repo, near, "near-v1", [{"facet": "personality", "text": "near"}])
    _accepted_r2(repo, wrong, "wrong-v1", [{"facet": "values", "text": "wrong"}])
    generation = _activate_generation(repo)
    finder, _ = _finder(
        repo,
        space,
        generation,
        _vector_map(
            {
                (source, "facet", "personality"): (0.0, 1.0, 0.0),
                (near, "facet", "personality"): (0.0, 1.0, 0.0),
                (wrong, "facet", "values"): (0.0, 1.0, 0.0),
            }
        ),
    )
    response = finder.find_similar_objects(source, facet="personality")
    assert response.results[0].object_id == near
    assert response.results[0].score_type == "cosine_similarity"
    assert response.results[0].matched_facet == "personality"
    assert wrong not in {item.object_id for item in response.results}
    with pytest.raises(ValueError, match="no content Facet"):
        finder.find_similar_objects(source, facet="values")


def test_qdrant_r2_hierarchical_similarity_smoke(repo, space):
    qdrant_client = pytest.importorskip("qdrant_client")
    from sgokb.retrieval.vector_index import QdrantVectorIndexAdapter

    source = repo.object_store.create_object("Source", _class(repo, "character"))
    target = repo.object_store.create_object("Target", _class(repo, "character"))
    _accepted_r2(repo, source, "source-v1", [{"facet": "values", "text": "source"}])
    _accepted_r2(repo, target, "target-v1", [{"facet": "values", "text": "target"}])
    generation = _activate_generation(repo)
    _save_embeddings(repo, space, lambda row: (1.0, 0.0, 0.0))
    adapter = QdrantVectorIndexAdapter(
        client=qdrant_client.QdrantClient(location=":memory:"),
        wait_for_index=False,
    )
    KnowledgeVectorIndexBuilder(repo, adapter, generation_id=generation).rebuild(space)
    finder = ObjectSimilaritySearch(repo, space=space, vector_index=adapter)
    response = finder.find_similar_objects(source)
    assert response.results[0].object_id == target
    assert response.results[0].score_type == "hierarchical_similarity"


@pytest.mark.parametrize("facet", [None, "personality"])
def test_active_v1_generation_keeps_overall_and_facet_cosine_contract(repo, space, facet):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    target = repo.object_store.create_object("Target", _class(repo, "character"))
    _accepted_r2(repo, source, "source-v1", [{"facet": "personality", "text": "source"}])
    _accepted_r2(repo, target, "target-v1", [{"facet": "personality", "text": "target"}])
    generation = _activate_generation(repo, "test-active-v1", r2=False)
    finder, index = _finder(repo, space, generation, lambda row: (1.0, 0.0, 0.0))
    response = finder.find_similar_objects(source, facet=facet)
    assert response.generation_id == generation
    result = response.results[0]
    assert result.object_id == target
    assert result.score_type == "cosine_similarity"
    assert result.score == pytest.approx(1.0)
    assert result.matched_facet == facet
    assert result.evidence == ()
    kind = "object_overall" if facet is None else "facet"
    assert index.points[result.membership_id].metadata["kind"] == kind
    assert "object_overview" not in {p.metadata["kind"] for p in index.points.values()}


@pytest.mark.parametrize("facet", [None, "personality"])
def test_r2_application_cli_mcp_keep_base_fields_and_additive_evidence(
    repo, space, monkeypatch, capsys, tmp_path, facet
):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    target = repo.object_store.create_object("Target", _class(repo, "character"))
    _accepted_r2(repo, source, "source-v1", [{"facet": "personality", "text": "source"}])
    _accepted_r2(repo, target, "target-v1", [{"facet": "personality", "text": "target"}])
    generation = _activate_generation(repo)
    _, index = _finder(repo, space, generation, lambda row: (1.0, 0.0, 0.0))
    app = KnowledgeReadApplication(repo, embedding_space=space, vector_index=index)
    expected = app.find_similar_objects(source, facet=facet)
    mcp = MCPReadAdapter(app).call_tool(
        "find_similar_objects", {"object_id": source, "facet": facet}
    )
    cli = importlib.import_module("sgokb.cli.main")
    monkeypatch.setattr(cli, "build_read_application", lambda *args, **kwargs: app)
    args = ["--db", str(tmp_path / "object-similarity-r2.sqlite"), "similar", "--object", source]
    if facet is not None:
        args.extend(["--facet", facet])
    assert cli.main(args) == 0
    cli_data = json.loads(capsys.readouterr().out)["data"]
    for data in (mcp["data"], cli_data):
        assert data["source_object_id"] == source
        assert data["source_version_id"] == "source-v1"
        assert data["source_representation_id"] == expected.source_representation_id
        assert data["source_membership_id"] == expected.source_membership_id
        assert data["generation_id"] == generation
        assert data["facet"] == facet
        result = data["results"][0]
        assert result["object_id"] == target
        assert result["representation_id"] == expected.results[0].representation_id
        assert result["membership_id"] == expected.results[0].membership_id
        assert result["score_type"] == (
            "hierarchical_similarity" if facet is None else "cosine_similarity"
        )
        assert bool(result["evidence"]) == (facet is None)


def test_candidate_object_cap_applies_even_when_caller_requests_more(repo, space):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    _accepted_r2(repo, source, "source-v1", [])
    for i in range(130):
        target = repo.object_store.create_object(f"Target {i}", _class(repo, "character"))
        _accepted_r2(repo, target, f"target-{i}-v1", [])
    generation = _activate_generation(repo)
    finder, index = _finder(repo, space, generation, lambda row: (1.0, 0.0, 0.0))
    response = finder.find_similar_objects(source, limit=1000)
    assert len(response.results) == 128
    assert len({item.object_id for item in response.results}) == 128
    assert index.search_limits == [128]
    assert source not in {item.object_id for item in response.results}


def test_correct_payload_cannot_bypass_sqlite_generation_membership(repo, space):
    source = repo.object_store.create_object("Source", _class(repo, "character"))
    target = repo.object_store.create_object("Target", _class(repo, "character"))
    _accepted_r2(repo, source, "source-v1", [])
    _accepted_r2(repo, target, "target-v1", [])
    generation = _activate_generation(repo)
    finder, index = _finder(repo, space, generation, lambda row: (1.0, 0.0, 0.0))
    target_point = next(p for p in index.points.values() if p.metadata["object_id"] == target)
    assert target_point.metadata["generation_id"] == generation
    repo.db.execute(
        "DELETE FROM knowledge_search_generation_memberships "
        "WHERE generation_id=? AND membership_id=?",
        (generation, target_point.point_id),
    )
    with pytest.raises(RuntimeError, match="outside active generation"):
        finder.find_similar_objects(source)
