import json

from sgokb.cli import main
from sgokb.repository import Repository


def _payload(capsys):
    captured = capsys.readouterr()
    return json.loads(captured.out)


def test_source_effective_selection_is_exposed_through_cli(tmp_path, capsys):
    db = tmp_path / "source-selection.sqlite"
    repository = Repository(db)
    try:
        store = repository.source_store
        source_id = store.create_source("History")
        first_snapshot = store.create_snapshot(
            source_id,
            "2026-01-01T00:00:00Z",
            "web_capture",
            completeness="complete",
        )
        second_snapshot = store.create_snapshot(
            source_id,
            "2026-01-02T00:00:00Z",
            "web_capture",
            completeness="complete",
        )
        store.select_effective_snapshot(
            source_id,
            first_snapshot,
            origin_kind="automatic_initial",
            reason="first_usable_snapshot",
        )
        artifact_id = store.add_raw_artifact(
            second_snapshot,
            "rendered_dom",
            "memory://second",
            "0" * 64,
            1,
            logical_path="dom/main.html",
            media_type="text/html",
        )
        second_run = store.create_normalization_run(
            second_snapshot,
            "fixture",
            "1",
            [artifact_id],
            status="complete",
        )
    finally:
        repository.close()

    code = main(
        [
            "--db",
            str(db),
            "source",
            "select-snapshot",
            "--source",
            source_id,
            "--snapshot",
            second_snapshot,
            "--reason",
            "operator reviewed follow-up capture",
        ]
    )
    assert code == 0
    snapshot_payload = _payload(capsys)
    assert snapshot_payload["command"] == "source.select-snapshot"
    assert snapshot_payload["data"]["source_id"] == source_id
    assert snapshot_payload["data"]["snapshot_id"] == second_snapshot
    assert snapshot_payload["data"]["effective"] is True

    code = main(
        [
            "--db",
            str(db),
            "source",
            "select-run",
            "--snapshot",
            second_snapshot,
            "--run",
            second_run,
            "--reason",
            "operator reviewed normalization",
        ]
    )
    assert code == 0
    run_payload = _payload(capsys)
    assert run_payload["command"] == "source.select-run"
    assert run_payload["data"]["source_id"] == source_id
    assert run_payload["data"]["snapshot_id"] == second_snapshot
    assert run_payload["data"]["run_id"] == second_run
    assert run_payload["data"]["effective"] is True

    repository = Repository(db)
    try:
        assert repository.source_store.effective_snapshot(source_id).snapshot_id == second_snapshot
        assert repository.source_store.effective_run(second_snapshot)["id"] == second_run
    finally:
        repository.close()
