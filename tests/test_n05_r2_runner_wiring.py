"""R2-09 normal maintenance, empty bootstrap and cold/warm boundary contracts."""

from __future__ import annotations

import importlib.util
import sys

import pytest
from qdrant_client import QdrantClient
from test_n05_performance_workflow import ROOT, WORK, UnitProvider, target

from sgokb.application_generation import (
    LEGACY_GENERATION_ID,
    KnowledgeSearchGenerationApplication,
    KnowledgeSearchGenerationError,
)
from sgokb.application_maintenance import DerivedSearchMaintenanceApplication
from sgokb.repository import Repository
from sgokb.retrieval.embedding import frozen_harrier_space
from sgokb.retrieval.hybrid_search_r2 import HybridObjectSearch
from sgokb.retrieval.vector_index import QdrantVectorIndexAdapter


def vector():
    return QdrantVectorIndexAdapter(
        client=QdrantClient(":memory:"),
        wait_for_index=False,
    )


def application(repo, index):
    return KnowledgeSearchGenerationApplication(
        repo,
        embedding_space=UnitProvider().space,
        vector_index=index,
    )


def test_empty_bootstrap_has_no_provider_and_zero_points(tmp_path, monkeypatch):
    repo = Repository(tmp_path / "empty.sqlite")
    index = vector()
    try:

        def forbidden(*args, **kwargs):
            pytest.fail("bootstrap constructed or invoked an embedding provider")

        monkeypatch.setattr(UnitProvider, "embed_documents", forbidden)
        app = application(repo, index)
        switched = app.bootstrap_empty_r2()
        generation = app._generation_row(switched.to_generation_id)
        binding = repo.one("SELECT * FROM knowledge_search_generation_vector_indexes")
        assert generation["contract_key"] == "n05d04r2-hierarchical-v2"
        assert generation["membership_digest"] == app.membership_digest(generation["id"])
        assert binding["point_count"] == 0
        assert index._client.get_collection(binding["namespace_key"]).points_count == 0
        assert not app._accepted_versions()
        assert repo.one("SELECT count(*) n FROM search_representation_embeddings")["n"] == 0
        assert (
            repo.one("SELECT count(*) n FROM knowledge_search_representation_memberships")["n"] == 0
        )
        with pytest.raises(KnowledgeSearchGenerationError, match="empty inactive"):
            app.bootstrap_empty_r2()
    finally:
        index._client.close()
        repo.close()


@pytest.mark.parametrize("mode", ["none", "v1", "r2", "unsupported", "wrong-version"])
def test_default_maintenance_honors_generation_contract(tmp_path, mode):
    repo = Repository(tmp_path / "contract.sqlite")
    index = vector()
    try:
        app = application(repo, index)
        if mode != "none":
            switch = app.bootstrap_empty_r2()
            generation_id = switch.to_generation_id
            if mode in {"v1", "unsupported", "wrong-version"}:
                key = (
                    "phase-i-search-v1"
                    if mode == "v1"
                    else (
                        "unsupported-contract"
                        if mode == "unsupported"
                        else "n05d04r2-hierarchical-v2"
                    )
                )
                with repo.db:
                    repo.db.execute(
                        "UPDATE knowledge_search_generations SET contract_key=?,contract_version=? "
                        "WHERE id=?",
                        (key, 1 if mode == "v1" else 99, generation_id),
                    )
        oid = repo.object_store.create_object(
            "Unit Object",
            repo.object_store.class_by_key("character").class_id,
        )
        vid = repo.version_store.begin_candidate(oid, None)
        repo.version_store.accept_candidate(vid)
        maintenance = DerivedSearchMaintenanceApplication(repo)
        if mode in {"unsupported", "wrong-version"}:
            with pytest.raises(RuntimeError, match="Unsupported"):
                maintenance.sync_search_representation(oid)
            assert repo.one("SELECT count(*) n FROM search_representations")["n"] == 0
            return
        maintenance.sync_search_representation(oid)
        kinds = {row["kind"] for row in repo.rows("SELECT kind FROM search_representations")}
        assert kinds == {"object_overview" if mode == "r2" else "object_overall"}
    finally:
        index._client.close()
        repo.close()


@pytest.mark.parametrize(
    "profile,workload",
    [
        (
            "standard",
            dict(
                source_count=10,
                candidate_evidence_count=500,
                package_evidence_count=120,
                knowledge_statement_count=300,
            ),
        ),
        (
            "large",
            dict(
                source_count=40,
                candidate_evidence_count=2000,
                package_evidence_count=350,
                knowledge_statement_count=1200,
            ),
        ),
    ],
)
def test_fresh_first_version_r2_incremental_and_audit(tmp_path, profile, workload, monkeypatch):
    fixture, sample = tmp_path / "fixture", tmp_path / "sample"
    WORK.prepare_fixture(fixture, profile, workload)
    seed_hash = WORK.sha(fixture / "starting.sqlite")
    index = vector()
    close_client = index._client.close
    monkeypatch.setattr(index._client, "close", lambda: None)
    events = []
    original_measure = WORK.SegmentClock.measure

    def measure(self, name, operation):
        events.append((name, "start"))
        try:
            return original_measure(self, name, operation)
        finally:
            events.append((name, "end"))

    monkeypatch.setattr(WORK.SegmentClock, "measure", measure)

    class Provider(UnitProvider):
        def __init__(self):
            assert events[-1] == ("derived_incremental_sync", "start")
            events.append(("provider", "construct"))
            super().__init__()

        def embed_documents(self, texts):
            assert ("derived_incremental_sync", "end") not in events
            return super().embed_documents(texts)

        def embed_queries(self, texts):
            return [[1.0, 0.0, 0.0] for _ in texts]

    def forbid_rebuild(*args, **kwargs):
        pytest.fail("incremental workflow invoked a full generation/Vector rebuild")

    monkeypatch.setattr(KnowledgeSearchGenerationApplication, "build_r2_candidate", forbid_rebuild)
    monkeypatch.setattr(QdrantVectorIndexAdapter, "rebuild", forbid_rebuild)
    result = WORK.run_sample(
        fixture,
        sample,
        profile,
        Provider,
        lambda space: index,
        bootstrap_space=UnitProvider().space,
    )
    assert result["status"] == "PASS", (
        WORK.read(sample / "execution-error.json") if result["status"] != "PASS" else result
    )
    assert WORK.sha(fixture / "starting.sqlite") == seed_hash
    assert result["actual_workload"] == workload
    repo = Repository(sample / "sgokb.sqlite")
    try:
        app = application(repo, index)
        active = repo.one("SELECT active_generation_id FROM knowledge_search_active_generation")[
            "active_generation_id"
        ]
        generation = app._generation_row(active)
        binding = repo.one("SELECT * FROM knowledge_search_generation_vector_indexes")
        rows = app._generation_membership_rows(active)
        assert {row["target_kind"] for row in rows} == {"object_overview", "facet", "statement"}
        assert len(rows) == workload["knowledge_statement_count"] + 4
        assert generation["source_catalog_digest"] == app.source_catalog_digest()
        assert (
            generation["membership_digest"]
            == binding["membership_digest"]
            == app.membership_digest(active)
        )
        assert binding["point_count"] == len(rows)
        client = index._client
        points, _ = client.scroll(binding["namespace_key"], limit=2000, with_payload=True)
        assert len(points) == len(rows)
        assert {p.payload["generation_id"] for p in points} == {active}
        assert {p.payload["__sgokb_space_id"] for p in points} == {UnitProvider().space.space_id}
        assert all(row["target_kind"] != "object_overall" for row in rows)
        provider = UnitProvider()
        provider.embed_queries = lambda texts: [[1.0, 0.0, 0.0] for _ in texts]
        from sgokb.retrieval.generation import route_generation_vector_index

        found = HybridObjectSearch(
            repo,
            embedding_provider=provider,
            vector_index=route_generation_vector_index(repo, index),
        ).search("N05 Subject", mode="semantic")
        assert found.results[0].object_id == f"object-n05-{profile}"
        assert not found.degraded_channels
        assert repo.one("PRAGMA integrity_check")["integrity_check"] == "ok"
        assert not repo.rows("PRAGMA foreign_key_check")
        setup = WORK.read(sample / "empty-r2-bootstrap.json")
        assert setup["counts"]["version_count"] == 0
        assert setup["counts"]["membership_count"] == 0
        assert setup["counts"]["embedding_count"] == 0
        assert setup["provider_constructed_during_bootstrap"] is False
    finally:
        close_client()
        repo.close()


def test_warm_provider_is_reused_without_factory_call(tmp_path):
    fixture = tmp_path / "fixture"
    WORK.prepare_fixture(fixture, "unit", target())

    def forbidden():
        pytest.fail("warm sample constructed a second provider")

    warm = UnitProvider()
    result = WORK.run_sample(
        fixture,
        tmp_path / "warm",
        "warm",
        forbidden,
        lambda space: vector(),
        warm_provider=warm,
        bootstrap_space=warm.space,
    )
    assert result["status"] == "PASS"


def test_frozen_space_declaration_does_not_import_torch_or_construct_model(monkeypatch):
    # Metadata reads only; actual provider equality is also checked in the local diagnostic.
    before = set(sys.modules)
    space = frozen_harrier_space()
    assert set(sys.modules) - before == set()
    assert space.model == "microsoft/harrier-oss-v1-0.6b"
    assert space.model_revision == "f9b9dc8d367d443f2479d27aa5d8d2850c0774ee"
    assert space.dimension == 1024
    assert space.overflow_policy == "reject"
    assert space.max_sequence_length == 32768
    assert space.normalize_embeddings
    assert '"dtype":"bfloat16"' in space.provider_configuration


def test_runner_still_has_fixed_cold_warm_sequence(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "benchmark/tools"))
    spec = importlib.util.spec_from_file_location(
        "runner_r2_test", ROOT / "benchmark/tools/n05_run_performance.py"
    )
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    assert runner.sample_prefix("run", "sample") != runner.sample_prefix("run", "other")
    assert runner.TARGETS["large"]["knowledge_statement_count"] == 1200
    assert LEGACY_GENERATION_ID not in runner.sample_prefix("run", "sample")


def test_declared_space_matches_provider_identity_without_model_load(monkeypatch):
    from types import SimpleNamespace

    from sgokb.retrieval.embedding import default_sentence_transformer_provider

    class Encoder:
        def __init__(self, model, **kwargs):
            self.max_seq_length = 32768
            self.transformer = SimpleNamespace(
                get_embedding_dimension=lambda: 1024,
                auto_model=SimpleNamespace(
                    config=SimpleNamespace(
                        _commit_hash="f9b9dc8d367d443f2479d27aa5d8d2850c0774ee",
                    )
                ),
            )

        def __getitem__(self, index):
            return self.transformer

    monkeypatch.setitem(
        sys.modules,
        "torch",
        SimpleNamespace(
            cuda=SimpleNamespace(is_available=lambda: True),
            bfloat16="bfloat16",
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        SimpleNamespace(
            SentenceTransformer=Encoder,
        ),
    )
    assert (
        frozen_harrier_space()
        == default_sentence_transformer_provider(
            local_files_only=True,
        ).space
    )


def test_bootstrap_rejects_accepted_catalog_without_changing_pointer(tmp_path):
    repo = Repository(tmp_path / "nonempty.sqlite")
    index = vector()
    try:
        oid = repo.object_store.create_object(
            "Accepted",
            repo.object_store.class_by_key("character").class_id,
        )
        vid = repo.version_store.begin_candidate(oid, None)
        repo.version_store.accept_candidate(vid)
        with pytest.raises(KnowledgeSearchGenerationError, match="empty inactive"):
            application(repo, index).bootstrap_empty_r2()
        assert not repo.rows("SELECT * FROM knowledge_search_active_generation")
        assert index._client.get_collections().collections == []
    finally:
        index._client.close()
        repo.close()


def test_declared_space_mismatch_fails_before_embedding(tmp_path):
    fixture = tmp_path / "fixture"
    WORK.prepare_fixture(fixture, "unit", target())
    provider = UnitProvider()
    from dataclasses import replace

    wrong = replace(provider.space, model_revision="different")
    result = WORK.run_sample(
        fixture,
        tmp_path / "mismatch",
        "mismatch",
        UnitProvider,
        lambda space: vector(),
        bootstrap_space=wrong,
    )
    assert result["status"] == "FAIL"
    error = WORK.read(tmp_path / "mismatch/execution-error.json")
    assert "differs from bootstrap" in error["traceback"]
    repo = Repository(tmp_path / "mismatch/sgokb.sqlite")
    try:
        assert repo.one("SELECT count(*) n FROM search_representation_embeddings")["n"] == 0
    finally:
        repo.close()


def test_incremental_audit_failure_is_not_success(tmp_path, monkeypatch):
    fixture = tmp_path / "fixture"
    WORK.prepare_fixture(fixture, "unit", target())

    def failed_audit(*args, **kwargs):
        raise KnowledgeSearchGenerationError("Injected live namespace audit failure")

    monkeypatch.setattr(
        KnowledgeSearchGenerationApplication, "refresh_active_generation", failed_audit
    )
    sample = tmp_path / "audit-failure"
    result = WORK.run_sample(
        fixture,
        sample,
        "failed-audit",
        UnitProvider,
        lambda space: vector(),
        bootstrap_space=UnitProvider().space,
    )
    assert result["status"] == "FAIL"
    assert "render" not in result["segments"]
    repo = Repository(sample / "sgokb.sqlite")
    try:
        assert (
            repo.one("SELECT point_count FROM knowledge_search_generation_vector_indexes")[
                "point_count"
            ]
            == 0
        )
        assert (
            repo.one("SELECT status FROM object_derived_states WHERE kind='vector_index'")["status"]
            == "failed"
        )
    finally:
        repo.close()
