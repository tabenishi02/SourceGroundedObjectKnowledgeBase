from __future__ import annotations

import httpx

from sgokb.application_system import SystemOperatorApplication
from sgokb.gui.runtime_dashboard import build_runtime_dashboard
from sgokb.repository import Repository
from sgokb.runtime import RuntimeConfig, RuntimeFactory


def _install_qdrant_transport(monkeypatch, state: dict[str, int]) -> None:
    from sgokb import runtime_health

    real_client = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/readyz":
            status = state["ready_status"]
            return httpx.Response(status, text="all shards are ready" if status == 200 else "not ready")
        if request.url.path == "/":
            return httpx.Response(200, json={"version": "1.19.2"})
        if request.url.path == "/collections":
            return httpx.Response(200, json={"result": {"collections": []}})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        runtime_health.httpx,
        "Client",
        lambda **kwargs: real_client(transport=transport, **kwargs),
    )


def _system_app(repository: Repository, db_path, *, qdrant_url: str = "http://qdrant.test"):
    return SystemOperatorApplication(
        repository,
        db_path,
        runtime_factory=RuntimeFactory(RuntimeConfig(qdrant_url=qdrant_url)),
    )


def test_qdrant_unavailable_blocks_semantic_search_without_canonical_writes(
    tmp_path,
    monkeypatch,
):
    state = {"ready_status": 503}
    _install_qdrant_transport(monkeypatch, state)
    db = tmp_path / "runtime-failure.sqlite"
    repository = Repository(db)
    try:
        app = _system_app(repository, db)
        before_changes = repository.db.total_changes
        before_integrity = app.integrity()

        health = app.runtime_status()
        dashboard = build_runtime_dashboard(health)

        after_integrity = app.integrity()
        after_changes = repository.db.total_changes
    finally:
        repository.close()

    qdrant = health["components"]["qdrant"]
    assert qdrant["status"] == "unavailable"
    assert qdrant["details"]["ready"] is False
    assert qdrant["issue"]["code"] == "qdrant_readiness_failed"
    assert dashboard.readiness.status == "blocked"
    assert any("Qdrant" in blocker for blocker in dashboard.readiness.blockers)
    assert before_integrity["ok"] is True
    assert after_integrity["ok"] is True
    assert before_integrity == after_integrity
    assert before_changes == after_changes


def test_port_open_wrong_service_is_not_treated_as_qdrant_ready(tmp_path, monkeypatch):
    state = {"ready_status": 404}
    _install_qdrant_transport(monkeypatch, state)
    db = tmp_path / "port-conflict.sqlite"
    repository = Repository(db)
    try:
        health = _system_app(repository, db).runtime_status()
    finally:
        repository.close()

    qdrant = health["components"]["qdrant"]
    assert qdrant["status"] == "unavailable"
    assert qdrant["details"]["ready"] is False
    assert qdrant["issue"]["code"] == "qdrant_readiness_failed"
    assert "HTTP 404" in qdrant["issue"]["message"]


def test_runtime_projection_recovers_after_qdrant_readiness_returns(tmp_path, monkeypatch):
    state = {"ready_status": 503}
    _install_qdrant_transport(monkeypatch, state)
    db = tmp_path / "runtime-recovery.sqlite"
    repository = Repository(db)
    try:
        app = _system_app(repository, db)
        failed = app.runtime_status()
        failed_dashboard = build_runtime_dashboard(failed)

        state["ready_status"] = 200
        recovered = app.runtime_status()
        recovered_dashboard = build_runtime_dashboard(recovered)
        integrity = app.integrity()
    finally:
        repository.close()

    assert failed["components"]["qdrant"]["status"] == "unavailable"
    assert failed_dashboard.readiness.status == "blocked"
    assert recovered["components"]["qdrant"]["status"] == "healthy"
    assert recovered["components"]["qdrant"]["details"]["ready"] is True
    assert recovered_dashboard.readiness.status in {"ready", "degraded"}
    assert integrity["ok"] is True


def test_runtime_failure_projection_preserves_external_lifecycle_boundary(
    tmp_path,
    monkeypatch,
):
    state = {"ready_status": 503}
    _install_qdrant_transport(monkeypatch, state)
    db = tmp_path / "lifecycle.sqlite"
    repository = Repository(db)
    try:
        health = _system_app(repository, db).runtime_status()
        dashboard = build_runtime_dashboard(health)
    finally:
        repository.close()

    assert health["lifecycle"] == {
        "qdrant_owner": "external",
        "observe": True,
        "start": False,
        "stop": False,
        "restart": False,
    }
    assert "external" in dashboard.lifecycle_note
    assert "start/stop/restart=false" in dashboard.lifecycle_note
