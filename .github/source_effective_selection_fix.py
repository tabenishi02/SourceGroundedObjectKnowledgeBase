from pathlib import Path


def replace_once(path, old, new):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected 1 replacement, found {count}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


main = "src/sgokb/cli/main.py"
replace_once(
    main,
    '''    source_actions.add_parser("status")
    source_actions.add_parser("snapshots")

    obj = domains.add_parser("object", help="Object Registry and accepted Knowledge reads")
''',
    '''    source_actions.add_parser("status")
    source_actions.add_parser("snapshots")
    select_snapshot = source_actions.add_parser("select-snapshot")
    select_snapshot.add_argument("--source", required=True)
    select_snapshot.add_argument("--snapshot", required=True)
    select_snapshot.add_argument("--reason", required=True)
    select_run = source_actions.add_parser("select-run")
    select_run.add_argument("--snapshot", required=True)
    select_run.add_argument("--run", required=True)
    select_run.add_argument("--reason", required=True)

    obj = domains.add_parser("object", help="Object Registry and accepted Knowledge reads")
''',
)
replace_once(
    main,
    '''        return result, False

    if args.action == "import":
''',
    '''        return result, False
    if args.action == "select-snapshot":
        selection_id = repository.source_store.select_effective_snapshot(
            args.source,
            args.snapshot,
            reason=args.reason,
        )
        effective = repository.source_store.effective_snapshot(args.source)
        return {
            "selection_id": selection_id,
            "source_id": args.source,
            "snapshot_id": args.snapshot,
            "effective": bool(effective and effective.snapshot_id == args.snapshot),
        }, False
    if args.action == "select-run":
        snapshot = repository.source_store.snapshot_by_id(args.snapshot)
        selection_id = repository.source_store.select_effective_run(
            args.snapshot,
            args.run,
            reason=args.reason,
        )
        effective = repository.source_store.effective_run(args.snapshot)
        return {
            "selection_id": selection_id,
            "source_id": snapshot.source_id,
            "snapshot_id": args.snapshot,
            "run_id": args.run,
            "effective": bool(effective and effective["id"] == args.run),
        }, False

    if args.action == "import":
''',
)

Path("tests/test_source_effective_selection_cli.py").write_text(
    '''import json

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
''',
    encoding="utf-8",
)

replace_once(
    "docs/decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md",
    '''sgokb source import <path>
sgokb source process [--snapshot <id>]
sgokb source status
sgokb source snapshots
```

旧`extract` aliasは廃止する。
''',
    '''sgokb source import <path>
sgokb source process [--snapshot <id>]
sgokb source status
sgokb source snapshots
sgokb source select-snapshot --source <source-id> --snapshot <snapshot-id> --reason <text>
sgokb source select-run --snapshot <snapshot-id> --run <run-id> --reason <text>
```

旧`extract` aliasは廃止する。

後続Snapshot / Normalization Runは新しいという理由だけで自動effective化しない。operatorが内容を確認した後、`select-snapshot` / `select-run`を明示実行してappend-only selection eventを記録する。両commandはcanonical stateを変更する`WRITE`操作であり、`--reason`を必須とする。
''',
)

replace_once(
    "docs/design/SOURCE_INGESTION_PIPELINE.md",
    '''- manual selection eventで切替可能とする。

Selection eventには`origin_kind / reason / created_at`を保持し、旧Snapshot / Run / Evidenceは削除しない。
''',
    '''- manual selection eventで切替可能とする。

operator-facing public CLIでは、確認済み世代の切替を次で行う。

```text
sgokb source select-snapshot --source <source-id> --snapshot <snapshot-id> --reason <text>
sgokb source select-run --snapshot <snapshot-id> --run <run-id> --reason <text>
```

これらはRepositoryのmanual selection contractを利用し、SQLite直接操作を要求しない。`latest == effective`へ戻す自動昇格ではなく、operatorの明示判断をselection eventとして記録する。

Selection eventには`origin_kind / reason / created_at`を保持し、旧Snapshot / Run / Evidenceは削除しない。
''',
)

replace_once(
    "docs/operations/OBJECT_STANDARD_WORKFLOW.md",
    '''sgokb --db $Db source process --snapshot $SnapshotId
if ($LASTEXITCODE -ne 0) { throw "source process failed" }
```

### Source↔Object association
''',
    '''$ProcessResult = sgokb --db $Db source process --snapshot $SnapshotId | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "source process failed" }
$RunId = $ProcessResult.data[0].run
```

最初のusable Snapshot / successful Runは`automatic_initial`としてeffectiveになる。既にeffective世代が存在するSourceへ後続Captureを追加した場合は、自動で置換しない。operatorが後続CaptureとNormalization結果を確認し、採用する場合だけ次を明示実行する。

```powershell
sgokb --db $Db source select-snapshot `
  --source $SourceId --snapshot $SnapshotId `
  --reason "operator reviewed follow-up capture"
sgokb --db $Db source select-run `
  --snapshot $SnapshotId --run $RunId `
  --reason "operator reviewed normalization"
```

この選択はappend-only selection eventであり、旧Snapshot / Run / Evidenceを削除しない。

### Source↔Object association
''',
)

procedure = "docs/operations/SGOKB_HAPPY_PATH_ACCEPTANCE_TEST_PROCEDURES.md"
replace_once(
    procedure,
    '''$ImportA1V2 = sgokb --db $Db source import $CaptureA1V2 | ConvertFrom-Json
$SourceA1V2Id   = $ImportA1V2.data[0].source
$SnapshotA1V2Id = $ImportA1V2.data[0].snapshot
sgokb --db $Db source process --snapshot $SnapshotA1V2Id
```
''',
    '''$ImportA1V2 = sgokb --db $Db source import $CaptureA1V2 | ConvertFrom-Json
$SourceA1V2Id   = $ImportA1V2.data[0].source
$SnapshotA1V2Id = $ImportA1V2.data[0].snapshot
$ProcessA1V2 = sgokb --db $Db source process --snapshot $SnapshotA1V2Id | ConvertFrom-Json
$RunA1V2Id = $ProcessA1V2.data[0].run
```
''',
)
replace_once(
    procedure,
    '''sgokb --db $Db association set `
  --object $ObjectAId --source $SourceA1V2Id --status confirmed
sgokb --db $Db evidence candidates --object $ObjectAId
sgokb --db $Db evidence select --object $ObjectAId
```

**PASS**: 2回目のanalysis cycle向けにnew Evidenceが利用可能である。
''',
    '''sgokb --db $Db association set `
  --object $ObjectAId --source $SourceA1V2Id --status confirmed

sgokb --db $Db source select-snapshot `
  --source $SourceA1V2Id --snapshot $SnapshotA1V2Id `
  --reason "happy-path follow-up snapshot reviewed"
sgokb --db $Db source select-run `
  --snapshot $SnapshotA1V2Id --run $RunA1V2Id `
  --reason "happy-path follow-up normalization reviewed"

sgokb --db $Db evidence candidates --object $ObjectAId
sgokb --db $Db evidence select --object $ObjectAId
```

後続Snapshot / Runは新しさだけでは自動effective化しないため、上記のexplicit operator selectionを正常系の必須工程とする。

**PASS**: effective generationがC-08の後続Snapshot / Runへ切り替わり、そのEvidenceが2回目のanalysis cycleで利用可能である。
''',
)

replace_once(
    "docs/operations/SGOKB_HAPPY_PATH_ACCEPTANCE_TEST_PLAN.md",
    '''| J-02 | Add new Evidence | Import/process later OBJ-A source/snapshot | New Evidence exists |
''',
    '''| J-02 | Add new Evidence | Import/process later OBJ-A snapshot, explicitly select the reviewed Snapshot/Run as effective, then retrieve Evidence | New Evidence from the selected follow-up generation exists |
''',
)
