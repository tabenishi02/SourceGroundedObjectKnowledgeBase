import importlib
import json
from pathlib import Path

import pytest

from sgokb.cli import main, parser
from sgokb.repository import Repository


def _stdout_json(capsys):
    output = capsys.readouterr()
    return json.loads(output.out), output


def test_object_centered_cli_add_show_and_json_contract(tmp_path, capsys):
    db = tmp_path / "cli.sqlite"
    code = main(
        [
            "--db",
            str(db),
            "object",
            "add",
            "--name",
            "Alice",
            "--primary-class",
            "character",
            "--alias",
            "A",
        ]
    )
    assert code == 0
    payload, _ = _stdout_json(capsys)
    assert payload["schema_version"] == "sgokb.cli/1.0"
    assert payload["ok"] is True
    assert payload["command"] == "object.add"
    object_id = payload["data"]["object_id"]

    code = main(["--db", str(db), "object", "show", "--name", "A"])
    assert code == 0
    payload, _ = _stdout_json(capsys)
    assert payload["data"]["object_id"] == object_id
    assert payload["data"]["name"] == "Alice"


def test_exact_name_selector_rejects_ambiguity(tmp_path, capsys):
    db = tmp_path / "ambiguous.sqlite"
    for _ in range(2):
        assert (
            main(
                [
                    "--db",
                    str(db),
                    "object",
                    "add",
                    "--name",
                    "Same",
                    "--primary-class",
                    "character",
                ]
            )
            == 0
        )
        capsys.readouterr()

    code = main(["--db", str(db), "object", "show", "--name", "Same"])
    assert code == 3
    captured = capsys.readouterr()
    payload = json.loads(captured.err)
    assert payload["ok"] is False
    assert payload["error"]["code"] == "object_selector_error"


def test_new_domain_parser_has_no_legacy_flat_commands():
    with pytest.raises(SystemExit) as exc:
        parser().parse_args(["import", "sample"])
    assert exc.value.code == 2

    with pytest.raises(SystemExit) as exc:
        parser().parse_args(["object", "relate"])
    assert exc.value.code == 2

    args = parser().parse_args(["package", "build", "--object", "object-1"])
    assert args.domain == "package"
    assert args.action == "build"


def test_system_integrity_and_migration_17(tmp_path, capsys):
    db = tmp_path / "integrity.sqlite"
    code = main(["--db", str(db), "system", "integrity"])
    assert code == 0
    payload, _ = _stdout_json(capsys)
    assert payload["data"]["ok"] is True
    assert payload["data"]["schema_migrations"][-1] == 17

    repo = Repository(db)
    try:
        assert repo.one(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name='registry_proposal_reviews'"
        )
    finally:
        repo.close()


def test_registry_and_source_read_commands_use_new_namespace(tmp_path, capsys):
    db = tmp_path / "read.sqlite"
    assert main(["--db", str(db), "registry", "class", "list"]) == 0
    payload, _ = _stdout_json(capsys)
    assert any(item["key"] == "character" for item in payload["data"])

    assert main(["--db", str(db), "source", "status"]) == 0
    payload, _ = _stdout_json(capsys)
    assert payload["command"] == "source.status"


def test_mcp_stdio_command_does_not_append_cli_json(tmp_path, capsys, monkeypatch):
    module = importlib.import_module("sgokb.cli.main")
    called = []

    def fake_mcp_dispatch(repository, args):
        called.append((repository, args.action))

    monkeypatch.setattr(module, "_mcp_dispatch", fake_mcp_dispatch)
    code = module.main(["--db", str(tmp_path / "mcp.sqlite"), "mcp", "serve"])
    captured = capsys.readouterr()

    assert code == 0
    assert called and called[0][1] == "serve"
    assert captured.out == ""
    assert captured.err == ""


def test_sgokb_package_entrypoint_removed():
    pyproject = (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    assert 'sgokb = "sgokb.cli:main"' in pyproject
    assert "sgokb-package" not in pyproject
