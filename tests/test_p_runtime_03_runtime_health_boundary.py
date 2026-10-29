from __future__ import annotations

import json

import httpx

from sgokb.application_operator import SHARED_OPERATION_IDS, OperatorSession
from sgokb.application_system import SystemOperatorApplication
from sgokb.cli import main
from sgokb.operation_contracts import OperationRequest
from sgokb.repository import Repository
from sgokb.runtime import RuntimeConfig, RuntimeFactory
from sgokb.runtime_health import RUNTIME_HEALTH_SCHEMA


def _mock_qdrant_client(monkeypatch, *, ready_status: int = 200):
    from sgokb import runtime_health

    real_client = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/readyz":
            return httpx.Response(ready_status, text="all shards are ready")
        if request.url.path == "/":
            return httpx.Response(200, json={"version": "1.20.0"})
        if request.url.path == "/collections":
            return httpx.Response(200, json={"result": {"collections": []}})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        runtime_health.httpx,
        "Client",
        lambda **kwargs: real_client(transport=transport, **kwargs),
    )


def test_system_status_exposes_shared_runtime_health_without_loading_model(tmp_path, monkeypatch):
    _mock_qdrant_client(monkeypatch)
    calls = []

    def semantic_builder():
        calls.append("built")
        raise AssertionError("runtime health must not construct the embedding model")

    db = tmp_path / "health.sqlite"
    repository = Repository(db)
    factory = RuntimeFactory(
        RuntimeConfig(qdrant_url="http://qdrant.test"),
        semantic_builder=semantic_builder,
    )
    try:
        payload = SystemOperatorApplication(
            repository,
            db,
            runtime_factory=factory,
        ).status()
    finally:
        repository.close()

    health = payload["runtime_health"]
    assert health["schema_version"] == RUNTIME_HEALTH_SCHEMA
    assert health["lifecycle"] == {
        "qdrant_owner": "external",
        "observe": True,
        "start": False,
        "stop": False,
        "restart": False,
    }
    assert health["components"]["sqlite"]["status"] == "healthy"
    assert health["components"]["qdrant"]["status"] == "healthy"
    assert health["components"]["qdrant"]["details"]["version"] == "1.20.0"
    assert health["components"]["generation"]["status"] == "not_configured"
    assert health["components"]["derived"]["status"] == "healthy"
    assert health["components"]["embedding"]["details"]["loaded"] is False
    assert calls == []


def test_qdrant_readiness_failure_is_component_error_not_operation_failure(tmp_path, monkeypatch):
    _mock_qdrant_client(monkeypatch, ready_status=503)
    db = tmp_path / "degraded.sqlite"
    repository = Repository(db)
    try:
        health = SystemOperatorApplication(
            repository,
            db,
            runtime_factory=RuntimeFactory(RuntimeConfig(qdrant_url="http://qdrant.test")),
        ).runtime_status()
    finally:
        repository.close()

    qdrant = health["components"]["qdrant"]
    assert health["overall_status"] == "degraded"
    assert qdrant["status"] == "unavailable"
    assert qdrant["issue"]["category"] == "runtime"
    assert qdrant["issue"]["code"] == "qdrant_readiness_failed"
    assert qdrant["details"]["ready"] is False


def test_operator_and_cli_expose_same_runtime_health_contract(tmp_path, capsys):
    db = tmp_path / "shared.sqlite"
    assert "system.status" in SHARED_OPERATION_IDS

    outcome = OperatorSession(db).execute(OperationRequest("system.status", {}))
    operator_health = outcome.data["runtime_health"]
    assert operator_health["schema_version"] == RUNTIME_HEALTH_SCHEMA
    assert operator_health["lifecycle"]["qdrant_owner"] == "external"
    assert operator_health["lifecycle"]["start"] is False

    assert main(["--db", str(db), "system", "status"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    cli_health = cli_payload["data"]["runtime_health"]
    assert cli_health["schema_version"] == operator_health["schema_version"]
    assert cli_health["lifecycle"] == operator_health["lifecycle"]
