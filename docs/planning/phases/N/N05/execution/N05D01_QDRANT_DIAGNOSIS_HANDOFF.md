# N05D-01 — Reference Workstation Qdrant Diagnosis Handoff

更新日: 2026-10-22

- Parent: `N-05 [P0] — Performance`
- Task: `N05D-01 — Qdrant storage/path diagnosis`
- Status: **Local comparative execution pending**
- Evaluation: `docs/evaluation/N05D01_QDRANT_STORAGE_PATH_DIAGNOSIS.md`

## 1. Do not run the formal performance benchmark

このTaskはN-05 p95計測ではない。

旧formal run:

```text
20261022T130413+0900
```

は保存し、上書きしない。

Gateやworkloadも変更しない。

## 2. Repository preflight

```powershell
cd C:\codex\SourceGroundedObjectKnowledgeBase
git pull --ff-only origin main
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse origin/main

python -m pytest -q tests/test_n05d01_qdrant_storage_diagnosis.py
python -m pytest -q tests/test_n05_performance_evaluator.py tests/test_n05_performance_workflow.py
python -m ruff check benchmark/tools/n05d01_qdrant_storage_diagnosis.py tests/test_n05d01_qdrant_storage_diagnosis.py
git diff --check
```

意図しないtracked差分がある場合は診断を開始しない。

## 3. Existing Qdrant evidence

診断runnerを実行する前に、localhost:6333をlistenしているprocessを記録する。

```powershell
$connection = Get-NetTCPConnection -State Listen -LocalPort 6333 | Select-Object -First 1
$process = Get-CimInstance Win32_Process -Filter "ProcessId=$($connection.OwningProcess)"
$process | Select-Object ProcessId,Name,ExecutablePath,CommandLine | Format-List
```

可能な範囲で次を確認する。

```text
Qdrant version
qdrant.exe path
start command
config path
storage_path
snapshots_path
temp_path
storage directory existence
write permission
volume/free space
```

既存Qdrant processを停止・再起動してはいけない。

## 4. Execute comparative diagnostic

```powershell
powershell -ExecutionPolicy Bypass -File benchmark/tools/n05d01_run_qdrant_diagnosis.ps1
```

runnerは:

1. 既存localhost:6333/6334をprobeする。
2. 同じnative qdrant.exeを6433/6434で隔離起動する。
3. 隔離serverではrun固有absolute storage/snapshot/temp pathを使う。
4. direct client / adapter、payload indexなし/ありを比較する。
5. indexed direct pathを複数回繰り返す。
6. 既存serverは停止しない。
7. isolated serverだけ終了する。

## 5. Evidence

`.local/n05d01/<run_id>/`を保存する。

最低限:

```text
run-meta.json
current-server.json
current-server.log
isolated-server.json
isolated-server.log
isolated-qdrant.stdout.log
isolated-qdrant.stderr.log
summary.json
```

failed diagnostic collectionは調査のため自動削除されない。

## 6. Interpretation

### Existing FAIL / Isolated PASS

強く疑う:

```text
QDRANT_ENVIRONMENT_DEFECT
BENCHMARK_RUNNER_DEFECT
```

既存serverのstorage path/config/lifecycleを比較する。

### Direct plain PASS / Direct indexed FAIL

SGOKB adapterより前で再現している。

```text
SGOKB_ADAPTER_DEFECTをprimary causeから外す
```

server logの正確なOS error code/pathを確認する。

Windows native Qdrant 1.19.1/1.19.2でpayload-index loadとfilesystem renameが競合するupstream issue #10806は重要な比較対象だが、error signatureが一致するまではBACKEND_PRODUCT_DEFECTと断定しない。

### Direct indexed PASS / Adapter indexed FAIL

```text
SGOKB_ADAPTER_DEFECT
```

adapterのcollection configuration / payload schema / lifecycleを縮退する。

### Existing + Isolatedともindexed FAIL

同じexact error signatureなら:

```text
BACKEND_PRODUCT_DEFECT
```

またはReference Workstation固有security/filesystem interactionを疑う。

必要ならWindows Process Monitorでisolated storage directoryをfilterし、`qdrant.exe`以外がGridstore/payload-index fileをopenしていないか確認する。

特にMicrosoft Defender / MsSense等のfile filterとの相互作用を確認する。

### All PASS

original N-05 failureはminimal loadでは再現していない。

point count / create-delete cadence / payload-index count / optimizer activityを一度に一要因ずつ増やす。

formal benchmarkを直接再実行してはいけない。

## 7. Completion

N05D-01 Completeには:

- root cause class確定
- evidence保存
- 必要な最小修復
- minimal real-Qdrant smoke反復PASS
- regression PASS

が必要。

完了後は:

```text
N05D-02 — Long-input Harrier memory diagnosis
```

へ進む。N05D-01とN05D-02は独立だが、N05D-04 formal rerunは両方Complete後のみ行う。
