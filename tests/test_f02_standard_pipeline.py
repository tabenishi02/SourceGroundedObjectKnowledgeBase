import json

import pytest

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
        assert repo.one("SELECT name FROM sqlite_master WHERE name='snapshots'") is None
        assert repo.one("SELECT name FROM sqlite_master WHERE name='fragments'") is None
        assert repo.one("SELECT name FROM sqlite_master WHERE name='ai_runs'") is None
    finally:
        repo.close()

    assert main(["--db", str(db), "process", "--snapshot", snapshot_id]) == 0
    processed = json.loads(capsys.readouterr().out)[0]
    assert processed["evidence"] > 0
    evidence_id = processed["evidence_ids"][0]
    assert main(["--db", str(db), "provenance", "evidence", evidence_id]) == 0
    provenance = json.loads(capsys.readouterr().out)
    assert provenance["snapshot"]["snapshot_id"] == snapshot_id
    assert provenance["evidence"]["evidence_id"] == evidence_id

    repo = Repository(db)
    try:
        assert _count(repo, "evidence_records") == processed["evidence"]
        assert repo.one("SELECT name FROM sqlite_master WHERE name='evidence'") is None
        assert repo.one("SELECT name FROM sqlite_master WHERE name='fragments'") is None
        assert repo.one("SELECT name FROM sqlite_master WHERE name='ai_runs'") is None
        assert repo.one("SELECT name FROM sqlite_master WHERE name='structured_documents'") is None
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


@pytest.mark.parametrize(
    "argv",
    [
        ["legacy-fragment"],
        ["fragment"],
        ["legacy-generate"],
        ["generate"],
        ["legacy-benchmark"],
        ["benchmark"],
        ["benchmark-score"],
        ["coverage"],
        ["entity"],
        ["embed"],
        ["search"],
        ["context"],
        ["import", "capture.zip", "--legacy"],
        ["process", "--legacy"],
        ["status", "--legacy"],
        ["snapshots", "--legacy"],
        ["provenance", "fragment", "id"],
        ["provenance", "document", "id"],
        ["--prompt-dir", "prompts", "status"],
    ],
)
def test_retired_cli_surface_is_rejected(argv):
    with pytest.raises(SystemExit) as error:
        parser().parse_args(argv)
    assert error.value.code == 2
