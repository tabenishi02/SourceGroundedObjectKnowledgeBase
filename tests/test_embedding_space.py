import sqlite3
from pathlib import Path

import pytest

from sgokb.domain import EmbeddingSpaceSpec, SearchRepresentationKind
from sgokb.repository import Repository
from sgokb.retrieval import (
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_EMBEDDING_MAX_SEQUENCE_LENGTH,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_REVISION,
    exact_cosine_scores,
)


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "embedding-space.sqlite")
    yield value
    value.close()


def _spec(**overrides):
    values = {
        "provider_key": "sentence-transformers",
        "provider_version": "5.7.0",
        "model": "Qwen/Qwen3-Embedding-0.6B",
        "model_revision": "revision-a",
        "dimension": 4,
        "native_dimension": 4,
        "preprocessing_key": "sgokb-search-representation",
        "preprocessing_version": "1",
        "query_instruction": "Retrieve relevant object knowledge.",
        "document_instruction": "",
        "normalize_embeddings": True,
        "max_sequence_length": 32768,
        "overflow_policy": "reject",
        "output_dtype": "float32",
        "provider_configuration": '{"dtype":"bfloat16","truncate_dim":null}',
    }
    values.update(overrides)
    return EmbeddingSpaceSpec(**values)


def test_embedding_space_identity_covers_model_provider_preprocessing_and_instruction():
    base = _spec()
    assert base.space_id == base.configuration_hash
    assert len(base.space_id) == 64
    assert base.provider_configuration == '{"dtype":"bfloat16","truncate_dim":null}'

    variants = [
        _spec(provider_key="fastembed"),
        _spec(model_revision="revision-b"),
        _spec(dimension=2, native_dimension=4),
        _spec(preprocessing_version="2"),
        _spec(query_instruction="Different retrieval task."),
        _spec(normalize_embeddings=False),
        _spec(overflow_policy="truncate"),
    ]
    assert len({base.space_id, *(item.space_id for item in variants)}) == len(variants) + 1


def test_embedding_space_rejects_invalid_dimension_and_configuration():
    with pytest.raises(ValueError, match="cannot exceed"):
        _spec(dimension=8, native_dimension=4)
    with pytest.raises(ValueError, match="provider_configuration"):
        _spec(provider_configuration="not json")


def test_embedding_repository_persists_space_and_float32_vector(repo):
    spec = _spec()
    representation_id = repo.semantic_store.get_or_create_search_representation(
        SearchRepresentationKind.STATEMENT,
        "sgokb-canonical-search",
        "1",
        "Object: Example\nStatement: 仲間を優先する。",
    )
    vector = [1.0, 0.0, 0.5, -0.25]

    assert repo.embedding_store.save_representation_embedding(spec, representation_id, vector)
    assert not repo.embedding_store.save_representation_embedding(spec, representation_id, vector)
    stored = repo.embedding_store.representation_embedding(spec.space_id, representation_id)
    assert stored == pytest.approx(vector)
    record = repo.embedding_store.space_by_id(spec.space_id)
    assert record.spec == spec

    row = repo.one(
        "SELECT length(vector) AS bytes FROM search_representation_embeddings "
        "WHERE space_id=? AND representation_id=?",
        (spec.space_id, representation_id),
    )
    assert row["bytes"] == 4 * spec.dimension


def test_embedding_repository_rejects_dimension_and_hash_mismatch(repo):
    spec = _spec()
    representation_id = repo.semantic_store.get_or_create_search_representation(
        SearchRepresentationKind.STATEMENT, "builder", "1", "stable text"
    )
    with pytest.raises(ValueError, match="dimension"):
        repo.embedding_store.save_representation_embedding(spec, representation_id, [1.0, 2.0])

    repo.embedding_store.ensure_space(spec)
    with pytest.raises(sqlite3.IntegrityError, match="content hash"):
        with repo.db:
            repo.db.execute(
                """INSERT INTO search_representation_embeddings
                   (space_id,representation_id,content_hash,vector,created_at)
                   VALUES(?,?,?,?,?)""",
                (spec.space_id, representation_id, "0" * 64, b"0" * 16, "2026-10-13T00:00:00Z"),
            )


def test_embedding_rows_are_space_isolated(repo):
    representation_id = repo.semantic_store.get_or_create_search_representation(
        SearchRepresentationKind.STATEMENT, "builder", "1", "same representation"
    )
    left = _spec(model_revision="left")
    right = _spec(model_revision="right")
    repo.embedding_store.save_representation_embedding(left, representation_id, [1, 0, 0, 0])
    repo.embedding_store.save_representation_embedding(right, representation_id, [0, 1, 0, 0])

    assert repo.embedding_store.representation_embedding(left.space_id, representation_id) == [
        1.0,
        0.0,
        0.0,
        0.0,
    ]
    assert repo.embedding_store.representation_embedding(right.space_id, representation_id) == [
        0.0,
        1.0,
        0.0,
        0.0,
    ]


def test_exact_cosine_baseline_is_backend_independent():
    scores = exact_cosine_scores([1.0, 0.0], [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    assert scores[0] == pytest.approx(1.0)
    assert scores[1] == pytest.approx(0.0)
    assert scores[2] == pytest.approx(2**-0.5)


def test_i02_default_profile_is_frozen_to_harrier_06b():
    assert DEFAULT_EMBEDDING_MODEL == "microsoft/harrier-oss-v1-0.6b"
    assert DEFAULT_EMBEDDING_REVISION == "f9b9dc8d367d443f2479d27aa5d8d2850c0774ee"
    assert DEFAULT_EMBEDDING_DIMENSION == 1024
    assert DEFAULT_EMBEDDING_MAX_SEQUENCE_LENGTH == 32768


def test_migration_015_upgrades_i01_schema_without_losing_representations(tmp_path):
    path = tmp_path / "pre-i02.sqlite"
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY)")
    migrations = Path("src/sgokb/migrations")
    for file in sorted(migrations.glob("*.sql")):
        version = int(file.name.split("_", 1)[0])
        if version > 14:
            continue
        db.executescript(file.read_text(encoding="utf-8"))
        db.execute("INSERT INTO schema_migrations VALUES(?)", (version,))
    db.execute(
        """INSERT INTO search_representations
           (id,kind,builder_key,builder_version,content,content_hash,created_at)
           VALUES(?,?,?,?,?,?,?)""",
        (
            "representation-before-i02",
            "statement",
            "sgokb-canonical-search",
            "1",
            "stable representation",
            "0" * 64,
            "2026-10-13T00:00:00Z",
        ),
    )
    db.commit()
    db.close()

    upgraded = Repository(path)
    try:
        assert upgraded.one("SELECT max(version) AS n FROM schema_migrations")["n"] == 18
        assert (
            upgraded.one(
                "SELECT content FROM search_representations WHERE id='representation-before-i02'"
            )["content"]
            == "stable representation"
        )
        assert upgraded.one("SELECT count(*) AS n FROM search_embedding_spaces")["n"] == 0
        assert upgraded.one("SELECT count(*) AS n FROM search_representation_embeddings")["n"] == 0
        assert upgraded.one("PRAGMA integrity_check")["integrity_check"] == "ok"
        assert not upgraded.rows("PRAGMA foreign_key_check")
    finally:
        upgraded.close()


def test_sentence_transformer_loads_all_components_from_pinned_offline_cache(monkeypatch):
    import sys
    from types import SimpleNamespace

    from sgokb.retrieval.embedding import SentenceTransformerEmbeddingProvider

    calls = []
    transformer = SimpleNamespace(
        get_embedding_dimension=lambda: 1024,
        auto_model=SimpleNamespace(config=SimpleNamespace(_commit_hash=DEFAULT_EMBEDDING_REVISION)),
    )

    class Encoder:
        max_seq_length = 32768

        def __init__(self, model, **kwargs):
            calls.append((model, kwargs))

        def __getitem__(self, index):
            assert index == 0
            return transformer

    monkeypatch.setattr(
        "sgokb.retrieval.embedding.metadata", SimpleNamespace(version=lambda name: "6.1.0")
    )
    monkeypatch.setitem(
        sys.modules, "torch", SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False))
    )
    monkeypatch.setitem(
        sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=Encoder)
    )
    provider = SentenceTransformerEmbeddingProvider(
        DEFAULT_EMBEDDING_MODEL,
        revision=DEFAULT_EMBEDDING_REVISION,
        local_files_only=True,
        cache_folder="offline-cache",
    )
    model, kwargs = calls[0]
    assert model == DEFAULT_EMBEDDING_MODEL
    assert kwargs["revision"] == DEFAULT_EMBEDDING_REVISION
    assert kwargs["local_files_only"] is True
    assert kwargs["cache_folder"] == "offline-cache"
    assert kwargs["model_kwargs"]["revision"] == DEFAULT_EMBEDDING_REVISION
    assert kwargs["model_kwargs"]["local_files_only"] is True
    assert provider.space.model_revision == DEFAULT_EMBEDDING_REVISION
    assert provider.space.dimension == 1024
