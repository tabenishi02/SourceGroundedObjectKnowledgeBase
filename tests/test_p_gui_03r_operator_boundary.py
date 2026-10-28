from __future__ import annotations

import importlib
import json

import pytest

from sgokb.application_operator import (
    PUBLIC_OPERATION_IDS,
    SHARED_OPERATION_IDS,
    TRANSPORT_OPERATION_IDS,
    OperatorSession,
)
from sgokb.cli import main
from sgokb.operation_contracts import (
    CATEGORY_NOT_FOUND,
    OperationFailure,
    OperationRequest,
)


def test_public_operator_inventory_has_67_operations_and_mcp_is_transport_only():
    assert len(PUBLIC_OPERATION_IDS) == 67
    assert TRANSPORT_OPERATION_IDS == {"mcp.serve"}
    assert len(SHARED_OPERATION_IDS) == 66
    assert SHARED_OPERATION_IDS | TRANSPORT_OPERATION_IDS == PUBLIC_OPERATION_IDS


def test_operator_session_can_execute_object_write_and_read_without_cli(tmp_path):
    db = tmp_path / "operator.sqlite"
    session = OperatorSession(db)

    created = session.execute(
        OperationRequest(
            "object.add",
            {
                "name": "Operator Object",
                "primary_class": "character",
                "alias": ["Operator Alias"],
            },
        )
    )
    object_id = created.data["object_id"]

    shown = session.execute(
        OperationRequest("object.show", {"object_id": object_id, "name": None})
    )
    assert shown.data["object_id"] == object_id
    assert shown.data["name"] == "Operator Object"

    by_alias = session.execute(
        OperationRequest("object.show", {"object_id": None, "name": "Operator Alias"})
    )
    assert by_alias.data["object_id"] == object_id


def test_operator_session_normalizes_selector_error_without_cli_exit_codes(tmp_path):
    session = OperatorSession(tmp_path / "missing.sqlite")
    with pytest.raises(OperationFailure) as exc:
        session.execute(
            OperationRequest("object.show", {"object_id": None, "name": "Missing"})
        )
    assert exc.value.category == CATEGORY_NOT_FOUND
    assert exc.value.code == "object_selector_error"


def test_cli_adapter_keeps_sgokb_cli_envelope_on_shared_operator_path(tmp_path, capsys):
    db = tmp_path / "cli.sqlite"
    assert (
        main(
            [
                "--db",
                str(db),
                "object",
                "add",
                "--name",
                "Shared Boundary",
                "--primary-class",
                "character",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == "sgokb.cli/1.0"
    assert payload["command"] == "object.add"
    assert payload["ok"] is True

    assert main(["--db", str(db), "object", "show", "--name", "Shared Boundary"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "object.show"
    assert payload["data"]["name"] == "Shared Boundary"


def test_cli_runtime_factory_honors_historical_main_module_hooks(monkeypatch):
    cli_main = importlib.import_module("sgokb.cli.main")
    cli_runtime = importlib.import_module("sgokb.cli.runtime")

    pair = (object(), object())
    read_app = object()
    calls = []

    monkeypatch.setattr(cli_main, "semantic_runtime", lambda: pair)

    def fake_build_read_application(repository, *, with_semantic=False):
        calls.append((repository, with_semantic))
        return read_app

    monkeypatch.setattr(cli_main, "build_read_application", fake_build_read_application)
    factory = cli_runtime.runtime_factory()

    assert factory.semantic_runtime() is pair
    repository = object()
    assert factory.build_read_application(repository, with_semantic=True) is read_app
    assert calls == [(repository, True)]


def test_mcp_serve_is_rejected_by_synchronous_operator_session(tmp_path):
    session = OperatorSession(tmp_path / "mcp.sqlite")
    with pytest.raises(OperationFailure) as exc:
        session.execute(OperationRequest("mcp.serve", {}))
    assert exc.value.code == "invalid_input"
