"""Offline public Derived Search CLI contracts."""

import importlib
import json
from unittest.mock import Mock

import pytest
from test_n04p04_vector_index_sync import (
    FakeEmbeddingProvider,
    FakeVectorIndex,
    _accepted_version,
    _character_class,
)

from sgokb.application_derived import DerivedSearchOperatorApplication
from sgokb.application_maintenance import DerivedMaintenanceRuntimeUnavailableError
from sgokb.application_read import KnowledgeReadApplication
from sgokb.domain import DerivedState
from sgokb.repository import Repository

cli = importlib.import_module("sgokb.cli.main")


@pytest.fixture
def setup(tmp_path, monkeypatch):
    path = tmp_path / "derived.sqlite"
    repo = Repository(path)
    runtime = Mock(side_effect=AssertionError("unexpected semantic composition"))
    monkeypatch.setattr(cli, "semantic_runtime", runtime)
    yield repo, path, runtime
    repo.close()


def accepted(repo, name="Alpha"):
    oid = repo.object_store.create_object(name, _character_class(repo))
    _accepted_version(repo, oid, f"{oid}-v1")
    return oid


def invoke(path, capsys, *args):
    code = cli.main(["--db", str(path), "system", *args])
    output = capsys.readouterr()
    return code, json.loads(output.out if output.out else output.err)


def snapshot(repo):
    return tuple(repo.db.iterdump())


def states(repo, oid):
    return {s.kind: s.status.value for s in repo.version_store.derived_states(oid)}


@pytest.mark.parametrize("action", ["status", "sync"])
def test_parser(action):
    args = cli.parser().parse_args(
        ["system", "derived", action, "--object", "abc", "--semantic-runtime"]
    )
    assert (args.action, args.subaction, args.object_id, args.semantic_runtime) == (
        "derived",
        action,
        "abc",
        True,
    )


def test_runtime_free_status_is_read_only_and_reports_states(setup, capsys):
    repo, path, runtime = setup
    oid = accepted(repo)
    assert invoke(path, capsys, "derived", "sync", "--object", oid)[0] == 0
    state = next(s for s in repo.version_store.derived_states(oid) if s.kind == "embedding")
    repo.version_store.mark_derived_state(
        oid, "embedding", state.revision, DerivedState.FAILED, error="test diagnostic"
    )
    before = snapshot(repo)
    code, output = invoke(path, capsys, "derived", "status", "--object", oid)
    assert code == 0 and output["ok"]
    data = output["data"]
    obj = data["objects"][0]
    assert (obj["object_id"], obj["name"], obj["current_version_id"]) == (oid, "Alpha", f"{oid}-v1")
    assert obj["search_representations"] == {
        "membership_count": 3,
        "unique_representation_count": 3,
    }
    embedding = next(s for s in obj["derived_states"] if s["kind"] == "embedding")
    assert embedding == {
        "kind": "embedding",
        "target_version_id": state.target_version_id,
        "status": "failed",
        "revision": state.revision,
        "last_error": "test diagnostic",
        "updated_at": embedding["updated_at"],
    }
    assert embedding["updated_at"]
    assert data["runtime"]["semantic_configured"] is False
    assert snapshot(repo) == before
    runtime.assert_not_called()


def test_runtime_free_sync_only_materializes_search_and_filters_targets(setup, capsys):
    repo, path, runtime = setup
    oid = accepted(repo)
    repo.object_store.create_object("No Version", _character_class(repo))
    before = KnowledgeReadApplication(repo).get_object(oid)
    code, output = invoke(path, capsys, "derived", "sync")
    assert code == 0 and output["ok"]
    assert output["data"]["object_count"] == 1
    assert [s["kind"] for s in output["data"]["objects"][0]["stages"]] == ["search_representation"]
    assert states(repo, oid) == {
        "search_representation": "ready",
        "embedding": "pending",
        "vector_index": "pending",
        "rendering": "pending",
    }
    assert KnowledgeReadApplication(repo).get_object(oid) == before
    runtime.assert_not_called()


def test_semantic_sync_is_ordered_idempotent_and_status_read_only(setup, monkeypatch, capsys):
    repo, path, _ = setup
    oid = accepted(repo)
    provider, vector = FakeEmbeddingProvider(), FakeVectorIndex()
    runtime = Mock(return_value=(provider, vector))
    monkeypatch.setattr(cli, "semantic_runtime", runtime)
    args = ("derived", "sync", "--object", oid, "--semantic-runtime")
    assert invoke(path, capsys, *args)[0] == 0
    assert runtime.call_count == 1
    document_calls = len(provider.document_calls)
    points = dict(vector.points)
    canonical = KnowledgeReadApplication(repo).get_object(oid)
    before_states = [
        (s.kind, s.target_version_id, s.status, s.revision, s.last_error)
        for s in repo.version_store.derived_states(oid)
    ]
    code, output = invoke(path, capsys, *args)
    assert code == 0 and output["data"]["partial"] is False
    stages = output["data"]["objects"][0]["stages"]
    assert [(s["kind"], s["status"]) for s in stages] == [
        ("search_representation", "ready"),
        ("embedding", "ready"),
        ("vector_index", "ready"),
    ]
    assert all(s["result"]["changed"] is False for s in stages)
    assert len(provider.document_calls) == document_calls
    assert vector.points == points
    assert [
        (s.kind, s.target_version_id, s.status, s.revision, s.last_error)
        for s in repo.version_store.derived_states(oid)
    ] == before_states
    assert KnowledgeReadApplication(repo).get_object(oid) == canonical
    before = snapshot(repo)
    code, output = invoke(path, capsys, "derived", "status", "--semantic-runtime")
    assert code == 0
    data = output["data"]
    space = data["runtime"]["embedding_space"]
    assert space == {
        key: getattr(provider.space, key)
        for key in ("space_id", "provider_key", "model", "model_revision", "dimension")
    }
    assert data["runtime"]["vector_backend"]["available"] is True
    assert data["objects"][0]["embedding"] == {
        "space_id": provider.space.space_id,
        "representation_count": 3,
        "embedding_count": 3,
        "missing_embedding_count": 0,
    }
    assert snapshot(repo) == before


@pytest.mark.parametrize("unreachable", [False, True])
def test_semantic_status_missing_embeddings_and_backend_diagnostic(
    setup, monkeypatch, capsys, unreachable
):
    repo, path, _ = setup
    oid = accepted(repo)
    invoke(path, capsys, "derived", "sync")
    provider, vector = FakeEmbeddingProvider(), FakeVectorIndex()
    if unreachable:
        vector.metadata = Mock(side_effect=RuntimeError("collection unavailable"))
    monkeypatch.setattr(cli, "semantic_runtime", lambda: (provider, vector))
    before = snapshot(repo)
    code, output = invoke(path, capsys, "derived", "status", "--semantic-runtime")
    assert code == 0
    data = output["data"]
    assert data["objects"][0]["object_id"] == oid
    assert data["objects"][0]["embedding"]["missing_embedding_count"] == 3
    backend = data["runtime"]["vector_backend"]
    assert backend["backend_key"] == vector.backend_key
    assert backend["available"] is (not unreachable)
    if unreachable:
        assert backend["metadata"] is None
        assert "collection unavailable" in backend["error"]
    assert snapshot(repo) == before
    assert not provider.document_calls


def test_partial_batch_continues_after_vector_failure(setup, monkeypatch, capsys):
    repo, path, _ = setup
    oids = sorted([accepted(repo, "Alpha"), accepted(repo, "Beta")])
    provider, vector = FakeEmbeddingProvider(), FakeVectorIndex()
    original = vector.upsert
    attempts = []

    def upsert(space, points):
        attempts.append(points)
        if len(attempts) == 1:
            raise RuntimeError("first object unavailable")
        return original(space, points)

    vector.upsert = upsert
    monkeypatch.setattr(cli, "semantic_runtime", lambda: (provider, vector))
    knowledge = [KnowledgeReadApplication(repo).get_object(oid) for oid in oids]
    code, output = invoke(path, capsys, "derived", "sync", "--semantic-runtime")
    assert code == 8 and output["ok"]
    data = output["data"]
    assert (data["object_count"], data["completed_object_count"], data["partial"]) == (2, 1, True)
    assert [o["object_id"] for o in data["objects"]] == oids
    assert data["objects"][0]["stages"][-1]["status"] == "failed"
    assert "first object unavailable" in data["objects"][0]["stages"][-1]["error"]
    assert data["objects"][1]["complete"] is True
    assert states(repo, oids[0])["vector_index"] == "failed"
    assert states(repo, oids[1])["vector_index"] == "ready"
    assert [KnowledgeReadApplication(repo).get_object(oid) for oid in oids] == knowledge


@pytest.mark.parametrize("action", ["status", "sync"])
@pytest.mark.parametrize(
    "error",
    [
        RuntimeError("local runtime unavailable"),
        DerivedMaintenanceRuntimeUnavailableError("explicit runtime unavailable"),
    ],
)
def test_composition_failure_exits_runtime_without_changes(
    setup, monkeypatch, capsys, action, error
):
    repo, path, _ = setup
    accepted(repo)
    monkeypatch.setattr(cli, "semantic_runtime", Mock(side_effect=error))
    before = snapshot(repo)
    code, output = invoke(path, capsys, "derived", action, "--semantic-runtime")
    assert code == 5 and not output["ok"]
    assert snapshot(repo) == before


@pytest.mark.parametrize("action", ["status", "sync"])
@pytest.mark.parametrize("unknown", [False, True])
def test_selector_error_contract(setup, capsys, action, unknown):
    repo, path, runtime = setup
    oid = "missing" if unknown else repo.object_store.create_object("Empty", _character_class(repo))
    before = snapshot(repo)
    code, output = invoke(path, capsys, "derived", action, "--object", oid)
    assert code == (3 if unknown else 4) and not output["ok"]
    assert snapshot(repo) == before
    runtime.assert_not_called()


def test_index_rebuild_remains_vector_only_and_lifecycle_neutral(setup, monkeypatch, capsys):
    repo, path, _ = setup
    oid = accepted(repo)
    provider, vector = FakeEmbeddingProvider(), FakeVectorIndex()
    app = DerivedSearchOperatorApplication(repo, embedding_provider=provider, vector_index=vector)
    assert app.sync(oid, semantic=True).partial is False
    state = next(s for s in repo.version_store.derived_states(oid) if s.kind == "vector_index")
    repo.version_store.mark_derived_state(oid, "vector_index", state.revision, DerivedState.PENDING)
    before = snapshot(repo)
    calls = len(provider.document_calls)
    monkeypatch.setattr(cli, "semantic_runtime", lambda: (provider, vector))
    assert invoke(path, capsys, "index", "status")[0] == 0
    code, output = invoke(path, capsys, "index", "rebuild")
    assert code == 0 and output["data"]["points_count"] == 3
    assert snapshot(repo) == before
    assert states(repo, oid)["vector_index"] == "pending"
    assert len(provider.document_calls) == calls
