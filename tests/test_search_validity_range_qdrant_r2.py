# ruff: noqa: I001 - sibling test helpers are imported as support utilities.

from __future__ import annotations

import pytest
from test_generation_lifecycle_qdrant_r2 import (
    FakeProvider,
    _link_legacy,
    _save_legacy_embeddings,
    _space,
)
from test_hybrid_search import _accepted, _class

from sgokb.application_generation import (
    LEGACY_GENERATION_ID,
    KnowledgeSearchGenerationApplication,
)
from sgokb.domain import ObjectSearchFilters
from sgokb.repository import Repository
from sgokb.retrieval import (
    HybridObjectSearch,
    KnowledgeVectorMaintenanceBuilder,
    QdrantVectorIndexAdapter,
    route_generation_vector_index,
)


def test_r2_qdrant_semantic_range_search_handles_timeless_statement(tmp_path):
    qdrant_client = pytest.importorskip("qdrant_client")
    repo = Repository(tmp_path / "range-qdrant-r2.sqlite")
    client = qdrant_client.QdrantClient(location=":memory:")
    try:
        object_id = repo.object_store.create_object(
            "Qdrant Range Hero",
            _class(repo, "character"),
        )
        version_id, records = _accepted(
            repo,
            object_id,
            "qdrant-range-v1",
            statements=[
                {
                    "facet": "personality",
                    "text": "Qdrant range timeless statement",
                }
            ],
        )
        assert records
        _link_legacy(repo)

        space = _space()
        provider = FakeProvider(space)
        _save_legacy_embeddings(repo, provider)
        vector = QdrantVectorIndexAdapter(client=client, wait_for_index=False)
        KnowledgeVectorMaintenanceBuilder(
            repo,
            vector,
            generation_id=LEGACY_GENERATION_ID,
        ).rebuild(space)

        generation = KnowledgeSearchGenerationApplication(
            repo,
            embedding_provider=provider,
            vector_index=vector,
        )
        generation.bootstrap_legacy()
        candidate = generation.build_r2_candidate()
        generation.cutover(candidate.generation_id)

        engine = HybridObjectSearch(
            repo,
            embedding_provider=provider,
            vector_index=route_generation_vector_index(repo, vector),
        )
        response = engine.search(
            "Qdrant range timeless statement",
            mode="semantic",
            filters=ObjectSearchFilters(
                knowledge_valid_at="2100-01-01..2200-01-01"
            ),
        )

        assert response.degraded_channels == ()
        matching = [result for result in response.results if result.object_id == object_id]
        assert matching
        assert matching[0].version_id == version_id
        assert any(
            match.statement_id == records[0]["statement_id"]
            for match in matching[0].matches
        )
    finally:
        client.close()
        repo.close()
