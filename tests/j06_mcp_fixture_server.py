"""Real Repository/Application stdio fixture used by J-06 MCP acceptance tests."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from sgokb.application_read import KnowledgeReadApplication
from sgokb.domain import EmbeddingSpaceSpec
from sgokb.mcp import MCPReadAdapter
from sgokb.mcp.server import create_read_server, run_stdio_server
from sgokb.repository import Repository
from sgokb.retrieval import (
    ExactVectorIndexAdapter,
    KnowledgeVectorIndexBuilder,
    SearchRepresentationBuilder,
)


class AcceptanceEmbeddingProvider:
    """Deterministic query embedder for the local semantic acceptance fixture."""

    def __init__(self, space: EmbeddingSpaceSpec):
        self._space = space

    @property
    def space(self) -> EmbeddingSpaceSpec:
        return self._space

    def embed_queries(self, texts):
        mapping = {
            "calm character": [1.0, 0.0, 0.0],
        }
        return [list(mapping.get(text, [1.0, 0.0, 0.0])) for text in texts]


def _space() -> EmbeddingSpaceSpec:
    return EmbeddingSpaceSpec(
        provider_key="j06-acceptance",
        provider_version="1",
        model="j06-deterministic",
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


def _accept(repo: Repository, object_id: str, version_id: str) -> None:
    candidate = repo.version_store.begin_candidate(object_id, None, version_id=version_id)
    repo.version_store.accept_candidate(candidate)
    SearchRepresentationBuilder(repo).materialize_version(candidate)


def _build_application(db_path: Path) -> tuple[Repository, KnowledgeReadApplication]:
    repo = Repository(db_path)
    character_class = repo.object_store.class_by_key("character").class_id
    repo.object_store.create_object("Alpha", character_class, object_id="object:alpha")
    repo.object_store.create_object("Beta", character_class, object_id="object:beta")
    _accept(repo, "object:alpha", "version:alpha:v1")
    _accept(repo, "object:beta", "version:beta:v1")

    space = _space()
    vectors = {
        "object:alpha": [1.0, 0.0, 0.0],
        "object:beta": [0.9, 0.1, 0.0],
    }
    for membership in repo.semantic_store.knowledge_search_memberships():
        repo.embedding_store.save_representation_embedding(
            space,
            membership["representation_id"],
            vectors[membership["object_id"]],
        )

    index = ExactVectorIndexAdapter()
    KnowledgeVectorIndexBuilder(repo, index).rebuild(space)
    app = KnowledgeReadApplication(
        repo,
        embedding_provider=AcceptanceEmbeddingProvider(space),
        embedding_space=space,
        vector_index=index,
    )
    return repo, app


async def main() -> None:
    with tempfile.TemporaryDirectory(prefix="sgokb-j06-") as directory:
        repo, application = _build_application(Path(directory) / "acceptance.sqlite")
        try:
            adapter = MCPReadAdapter(application)
            await run_stdio_server(create_read_server(adapter))
        finally:
            repo.close()


if __name__ == "__main__":
    asyncio.run(main())
