import json

from sgokb.cli import main, parser
from sgokb.repository import Repository


def _count(repo, table):
    return repo.one(f"SELECT count(*) AS n FROM {table}")["n"]


def test_standard_cli_import_and_process_stop_at_canonical_evidence(tmp_path, make_bundle, capsys):
    db = tmp_path / "standard.sqlite"
    path = make_bundle()

    assert main(["--db", str(db), "import", str(path)]) == 0
    imported = json.loads(capsys.readouterr().out)[0]
    snapshot_id = imported["snapshot"]

    repo = Repository(db)
    try:
        assert _count(repo, "source_records") == 1
        assert _count(repo, "source_snapshots") == 1
        assert _count(repo, "snapshots") == 0
        assert _count(repo, "fragments") == 0
        assert _count(repo, "ai_runs") == 0
    finally:
        repo.close()

    assert main(["--db", str(db), "process", "--snapshot", snapshot_id]) == 0
    processed = json.loads(capsys.readouterr().out)[0]
    assert processed["evidence"] > 0

    repo = Repository(db)
    try:
        assert _count(repo, "evidence_records") == processed["evidence"]
        assert _count(repo, "evidence") == 0
        assert _count(repo, "fragments") == 0
        assert _count(repo, "ai_runs") == 0
        assert _count(repo, "structured_documents") == 0
    finally:
        repo.close()

    assert main(["--db", str(db), "status"]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["sources"] == 1
    assert status["snapshots"] == 1
    assert status["evidence"] == processed["evidence"]
    assert "fragments" not in status

    assert main(["--db", str(db), "snapshots"]) == 0
    snapshots = json.loads(capsys.readouterr().out)
    assert snapshots[0]["id"] == snapshot_id
    assert snapshots[0]["effective"] is True


def test_legacy_cli_import_and_process_remain_available(tmp_path, make_bundle, capsys):
    db = tmp_path / "legacy.sqlite"
    path = make_bundle()

    assert main(["--db", str(db), "import", str(path), "--legacy"]) == 0
    imported = json.loads(capsys.readouterr().out)[0]
    assert main(["--db", str(db), "process", "--snapshot", imported["snapshot"], "--legacy"]) == 0
    json.loads(capsys.readouterr().out)

    repo = Repository(db)
    try:
        assert _count(repo, "snapshots") == 1
        assert _count(repo, "evidence") > 0
        assert _count(repo, "source_snapshots") == 0
        assert _count(repo, "evidence_records") == 0
    finally:
        repo.close()


def test_fragment_and_final_commands_are_explicitly_legacy_with_compatibility_aliases():
    root = parser()
    canonical = root.parse_args(["legacy-fragment", "--snapshot", "snapshot", "--entity", "entity"])
    compatibility = root.parse_args(["fragment", "--snapshot", "snapshot", "--entity", "entity"])
    final = root.parse_args(["legacy-generate", "--entity", "entity"])
    benchmark = root.parse_args(["legacy-benchmark", "manifest.json"])

    assert canonical.command == "legacy-fragment"
    assert compatibility.command == "fragment"
    assert final.command == "legacy-generate"
    assert benchmark.command == "legacy-benchmark"
