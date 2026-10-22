# N05D-01 — Qdrant storage/path diagnosis

更新日: 2026-10-22

- Parent: `N-05 [P0] — Performance`
- Task: `N05D-01 — Qdrant storage/path diagnosis`
- Status: **BLOCKED — local comparison completed; short-path access-denied failure remains**
- Formal N-05 run: `20261022T130413+0900`
- Formal run HEAD: `a7147f9842f94e96944bc7f67b4c3986970462b0`
- N-05 formal verdict: **BLOCKED / performance target not judgeable**

## 1. Diagnostic question

Standard profileの23 sampleすべてを停止させたQdrant storage/gridstore path errorが、次のどこに属するかを確定する。

```text
QDRANT_ENVIRONMENT_DEFECT
SGOKB_ADAPTER_DEFECT
BENCHMARK_RUNNER_DEFECT
BACKEND_PRODUCT_DEFECT
OTHER_IDENTIFIED_CAUSE
```

N05D-01の診断値はN-05 formal performance sampleへ混ぜない。

## 2. Known local evidence before N05D-01

N-04P-06ではReference Workstation上で次のruntimeが成立していた。

```text
OS: Windows 11
Qdrant server: 1.19.2 native qdrant.exe
qdrant-client: 1.19.1
HTTP: localhost:6333
gRPC: localhost:6334
storage: .local/n04p06/qdrant/
vector points: 24
```

このsmall real-data acceptanceではEmbedding / Vector sync、semantic search、SimilarityがPASSした。

一方、N-05 formal runではStandard profile 23/23 sampleがDerived Search sync中のQdrant collection / payload-index preparationで停止した。観測errorはgridstoreの保存先pathが見つからない旨を示した。

したがって現時点では、Qdrant自体が常に起動不能なのではなく、**N-05負荷・server lifecycle・payload-index storage pathの組み合わせで発生するdefect**を優先して疑う。

## 3. SGOKB adapter desk review

`QdrantVectorIndexAdapter._ensure_collection()`は次の順で処理する。

```text
create_collection
→ configured payload indexesをcreate_payload_index(wait=True)で作成
→ upsert時にpoint upload
```

この順序はQdrantの一般的な推奨である「既知のpayload fieldはupload前にindex作成」と矛盾しない。

N05D-01では同じpayload schemaを、SGOKB adapterを通さないdirect qdrant-clientでも作成する。direct pathでも同じerrorが再現すれば、SGOKB adapterをprimary triggerから外せる。

## 4. External research

2026-10-22時点でQdrant upstreamにはWindows / payload-index / filesystem interactionに関する重要な既知事象がある。

### Qdrant issue #10806

Open / `bug` / `parked`のissueで、native `qdrant.exe` 1.19.1 / 1.19.2をWindows 11上で利用し、複数payload indexを持つloadでfilesystem operationが失敗する再現報告がある。

報告者側の追加調査では、Microsoft Defender for Endpoint (`MsSense.exe`) がsegment/index fileを読み取るタイミングとQdrant側renameが競合し、`Access is denied (os error 5)`が発生したとされる。

このupstream issueは今回の「gridstore path not found」と**完全一致するerrorではない**。したがって現時点ではroot causeと断定しない。ただし、

```text
Windows 11
native qdrant.exe 1.19.2
payload indexes
Gridstore / filesystem operations
```

という条件が強く重なるため、重要なupstream candidateとして扱う。

### Qdrant filesystem guidance

Qdrantはpersistent storageについてfilesystem semanticsを重要視しており、Windows上のDocker/WSL bind mount等について互換性注意を明示している。

今回のReference Workstationはnative `qdrant.exe` + local storageであり、Docker bind mount問題と同一ではない。ただしstorage path / filesystem / file-filter interactionを診断対象に含める根拠になる。

## 5. Diagnostic harness

追加した資産:

```text
benchmark/tools/n05d01_qdrant_storage_diagnosis.py
benchmark/tools/n05d01_run_qdrant_diagnosis.ps1
tests/test_n05d01_qdrant_storage_diagnosis.py
```

Python diagnosticは同一Qdrant serverに対して次を順に実行する。

```text
A. direct qdrant-client / payload indexesなし
B. direct qdrant-client / SGOKBと同じpayload indexesあり
C. SGOKB QdrantVectorIndexAdapter / indexesなし
D. SGOKB QdrantVectorIndexAdapter / indexesあり
E. direct indexed pathの連続create/upload/query/delete
```

成功したdiagnostic collectionは削除する。失敗したcollectionはserver-side inspectionのため残す。

canonical SQLite DBは開かない。

## 6. Existing server vs isolated server

PowerShell runnerは2条件を比較する。

### Existing server

```text
localhost:6333 / 6334
```

現在N-05が利用しているserverに対してminimal probeを行い、process path / command lineと既知storage candidateの存在・writeabilityを保存する。

### Isolated server

同じnative `qdrant.exe`を別port:

```text
HTTP 6433
gRPC 6434
```

で起動し、run固有のabsolute pathを明示する。

```text
.local/n05d01/<run_id>/isolated-qdrant/storage
.local/n05d01/<run_id>/isolated-qdrant/snapshots
.local/n05d01/<run_id>/isolated-qdrant/temp
```

既存Qdrant processは停止・変更しない。

これにより、

```text
existing serverだけFAIL / isolated PASS
  → stale storage path / server lifecycle / local configurationを強く疑う

existing + isolatedのdirect indexed pathが同じFAIL
  → Windows/Qdrant backendまたはfilesystem/security-filter interactionを強く疑う

direct indexed PASS / adapter indexed FAIL
  → SGOKB_ADAPTER_DEFECT

全てPASS
  → original failure条件を追加で縮退再現する
```

という切り分けが可能になる。

## 7. Current hypotheses

| Hypothesis | Current assessment | Reason |
|---|---|---|
| Existing Qdrant storage root / lifecycle defect | **High priority** | N-04P-06のtemporary evaluation storageを継続利用していたため、実path・process/configの再確認が必要 |
| Native Windows Qdrant/Gridstore/filesystem interaction | **Credible upstream candidate** | Qdrant 1.19.1/1.19.2 + Windows + payload indexの既知issueが存在 |
| SGOKB adapter defect | **Unproven / lower confidence** | adapter operation order自体は通常形。direct comparison未実行 |
| N-05 benchmark runner defect | **Possible** | sample-specific collection lifecycleと既存server lifecycleの相互作用をまだ分離できていない |

## 8. Local execution requirement

Root-cause classificationをCompleteにするにはReference Workstationで次を実行する必要がある。

```powershell
powershell -ExecutionPolicy Bypass -File benchmark/tools/n05d01_run_qdrant_diagnosis.ps1
```

raw evidence:

```text
.local/n05d01/<run_id>/run-meta.json
.local/n05d01/<run_id>/current-server.json
.local/n05d01/<run_id>/current-server.log
.local/n05d01/<run_id>/isolated-server.json
.local/n05d01/<run_id>/isolated-server.log
.local/n05d01/<run_id>/isolated-qdrant.stdout.log
.local/n05d01/<run_id>/isolated-qdrant.stderr.log
.local/n05d01/<run_id>/summary.json
```

必要ならProcess Monitor / Defender/EDR evidenceを追加する。

## 9. Exit condition

N05D-01をCompleteにできるのは、local comparative runとserver/storage evidenceから次のいずれかを確定し、修復後のminimal real-Qdrant smokeを繰り返しPASSさせた場合だけである。

```text
QDRANT_ENVIRONMENT_DEFECT
SGOKB_ADAPTER_DEFECT
BENCHMARK_RUNNER_DEFECT
BACKEND_PRODUCT_DEFECT
OTHER_IDENTIFIED_CAUSE
```

比較実行前にはReference Workstation command executionが利用できず未完了だった。以下の実機結果で更新する。**N05D-01は引き続きCompleteではない**。


## 10. Reference Workstation execution — 2026-10-22

**N05D-01 = BLOCKED / not Complete. N-05 remains BLOCKED / not Complete.**

- Latest comparative run: `20261022T161445+0900`.
- Execution HEAD: `47d87ae13f621db8f6c6140209749d03d460a26c`, plus the local
  diagnostic/path/explicit-empty-schema fixes described below.
- Native Qdrant 1.19.2, build `016542aa`; qdrant-client 1.19.1.
- Executable: `.local/qdrant-1.19.2/qdrant.exe`.
- Existing server PID 45700 was not stopped or reconfigured; command:
  `qdrant.exe --config-path .local/n04p06/qdrant.yaml --disable-telemetry`.
- Existing storage: `.local/n04p06/qdrant/storage`; snapshots:
  `.local/n04p06/qdrant/snapshots`; no explicit temp override in that config.
- Isolated storage: `.local/q/f2677073`; snapshots: `.local/q/f2677073-snap`;
  temp: `.local/q/f2677073-tmp`. These were passed as absolute paths, using
  HTTP 6433 / gRPC 6434. Only the isolated server was stopped after diagnosis.
- Existing storage write probes passed, with approximately 26.35 GB free.
  Raw reports record process/config/path existence and exact disk measurements.

| Server | Direct plain | Direct indexed | Adapter plain | Adapter indexed | Repeated direct indexed |
|---|---|---|---|---|---|
| Existing, original diagnostic names | PASS | FAIL: OS error 5 | PASS | FAIL: OS error 3 | 5/5 PASS |
| Isolated, short storage/name | PASS | PASS | PASS | PASS | 5/5 PASS |

### Established observations and unresolved cause

The initial raw automatic classification is not sufficient for a causal verdict:
its direct and adapter probes use different-length collection names. Classifier
rules and historical results have not been altered to force another outcome.

On the same existing server, additional indexed controls showed:

- Short direct collection names: 3/3 PASS.
- Short adapter prefixes matching the proposed compact N-05 format: **2/3 PASS**.
  The first failed with OS error 5; it is retained and not replaced by a success.
- Deliberately long direct name: FAIL with OS error 3, independently of SGOKB adapter.
- Earlier run `20261022T154733+0900` had short direct/adapter 3/3 PASS each,
  but the later failure disproves a claim that shortening alone fully repairs the runtime.
- Original adapter error:
  `Service internal error: failed to open mutable map index on gridstore: 指定されたパスが見つかりません。 (os error 3)`.
- Additional short-path error:
  `Service internal error: Failed to save structure on disk with error: アクセスが拒否されました。 (os error 5)`.
  The direct indexed probe failed after `object_status` index creation; the
  short adapter failed during index creation. Full Python exceptions are retained.
- Failed long-name trees contain stored paths of 266 characters. Short-path OS
  error 5 occurred with longest observed stored paths around 240/248 characters.
  These observations establish length sensitivity but do not prove a unique
  Win32 limit, Qdrant product defect, or file-filter cause for both signatures.
- `LongPathsEnabled=1` was already present. No registry change was made.

**Final root-cause classification is unresolved.** Evidence prioritizes native
Windows Qdrant/storage/filesystem interactions, with existing-server environment
or lifecycle as an additional factor. SGOKB is not required to reproduce either
error signature. Do not declare `BACKEND_PRODUCT_DEFECT`, Defender interference,
or a complete adapter/runner repair without file-operation evidence.

### Verified fixes and bounded changes

- Corrected Python Ruff formatting without changing the diagnostic classifier.
- Fixed `filter_schema={}` being replaced by default indexes; `None` still uses
  the complete default schema. This ancillary adapter defect invalidated the
  first no-index comparison; it does not explain indexed direct failures.
- Added a regression covering explicit-empty versus default schema behavior.
- Proposed N-05 namespace is `n05` plus 12 hex SHA-256 characters of
  `run_id:sample_id`: 15 characters, deterministic and distinct across all 46
  planned samples. Namespace existence checks use the complete planned set.
  This is a partial path mitigation, not a proven repair for OS error 5.
- Diagnostic runner uses short run-specific absolute storage, explicit IPv4
  Python readiness, hidden isolated process/working directory, early status,
  and explicit config-directory creation. No payload index was removed from
  the default production configuration and no fake backend was substituted.
- The first interrupted diagnostic `20261022T141823+0900` and subsequent
  `20261022T154733+0900` / `20261022T160438+0900` failures remain available.
  The latter lacked a config directory; its regression success did not mean
  comparative diagnosis success. The premature completion helper stopped at
  its safety assertion; no commit/push or Complete update occurred.

### Regression and next diagnostic boundary

- Focused diagnostic/vector/workflow tests: **16 PASS**.
- Full pytest: **524 PASS, 0 failed, 2 existing local-Qdrant warnings**.
- Repository-wide Ruff and `git diff --check`: **PASS**.
- Failed diagnostic collections, original N-05 run and all diagnostic logs remain.
- Canonical SQLite DBs are not opened by the diagnostic tool. No formal N-05
  performance sample or Harrier memory experiment was executed.
- Defender service, antivirus and real-time protection are enabled. No matching
  Defender event was returned by the bounded time-window query. This does not
  exclude file-filter interaction. `fltmc filters` returned access denied
  (`0x80070005`); Procmon/Handle were not available on PATH. No security product
  was stopped, disabled, or given an exclusion.
- Next diagnostic candidate: authorized Process Monitor/file-handle tracing of
  the exact failed open/rename/save operation on controlled isolated storage,
  correlated with Qdrant logs. Preserve failures; do not retry until PASS or
  change the classification rules, indexes, Gate, model, or production server.
- **N05D-01 stays current. N05D-02 is not started.** Commit/push is withheld
  because the requested diagnostic completion/repair condition is not met.

Raw evidence: `.local/n05d01/20261022T161445+0900/`; launcher/regression logs:
`.local/n05d01-control/20261022T161445+0900/`. These are not Git artifacts.


## 11. ProcMon observation progress — 2026-10-22

**N05D-01 remains BLOCKED / Not Complete.** This is an observation/progress
commit, explicitly authorized even while the runtime defect remains unresolved.

- ProcMon run: `20261022T172340+0900`; execution HEAD:
  `47d87ae13f621db8f6c6140209749d03d460a26c` plus the preserved diagnostic changes.
- Before execution, all nine existing modified files were retained and backed
  up as `.local/n05d01/20261022T172340+0900/pre-procmon-working-tree.patch`.
- Microsoft official portable ProcMon 4.12 was downloaded from
  `https://download.sysinternals.com/files/ProcessMonitor.zip`; Authenticode
  signature was Valid, publisher Microsoft Corporation. Executable SHA-256:
  `28495E642B2A465474A4EDC58380EAF8B7EE580F3FBCB4141061DEADAFE9B885`.
- User approved elevation of ProcMon only. Existing qdrant.exe (PID 45700),
  server configuration, client probes, Defender/EDR and security policy were
  not elevated or changed. No exclusion or firewall change was made.
- Existing server: native Qdrant 1.19.2;
  `.local/qdrant-1.19.2/qdrant.exe --config-path .local/n04p06/qdrant.yaml --disable-telemetry`.
  Actual target storage: `.local/n04p06/qdrant/storage`.
- Capture started at `2026-10-22T17:29:26.299832+09:00`, bounded to 120 seconds.
  GUI path-filter automation was unavailable; CLI capture retained all processes
  in local raw PML, then analysis scoped every process to the exact storage-root
  boundary. Raw machine-wide PML/CSV never enters Git or cloud inference.
- PML was saved as `procmon/procmon.pml`; CSV as `procmon/procmon-raw.csv`.
  The first analysis opened the export too early and received PermissionError.
  That log is retained; completed CSV was reanalyzed into `procmon/analysis-04/`.
  The second total-comparison analysis was stopped and replaced by path/time indexing.
  No raw evidence was overwritten. This export-lock error is not the Qdrant
  storage OS error 5 under investigation.
- Indexed short-namespace probes: **10/10 PASS**.
  Client-side OS error 5 occurrences: **0**.
  No failing formal sample was replaced; these are diagnosis-only probes.
- Storage-scoped events: **734643**.
  Qdrant result counts (routine lookup misses included): `{'NAME NOT FOUND': 11759, 'SUCCESS': 275033, 'NO MORE FILES': 3199, 'BUFFER OVERFLOW': 3753, 'FILE LOCKED WITH WRITERS': 3764, 'PATH NOT FOUND': 3196, 'IS DIRECTORY': 176, 'NOT REPARSE POINT': 352, 'FAST IO DISALLOWED': 176, 'INVALID PARAMETER': 176, 'NAME COLLISION': 9, 'ACCESS DENIED': 9, 'USER MAPPED FILE': 1, 'FILE LOCK CONFLICT': 1}`.
  ACCESS DENIED / SHARING VIOLATION events: **9**.
- Exact raw timestamps, operations, full paths, result/detail, and same-path or
  directory-tree correlation candidates are retained in the filtered CSV and
  failure-summary JSON. The analyzer retains all processes, handles midnight,
  and explicitly does not infer causation from temporal/path correlation.
- Concrete file-operation evidence: Qdrant PID 45700 recorded **9**
  `SetRenameInformationFile -> ACCESS DENIED` events while moving deleted
  diagnostic collections into `storage/.deleted`. These are cleanup renames;
  the client indexed probes and their cleanup responses were PASS.
- At `17:30:30.8199279 +09:00`, collection
  `p08d8bb03a_1d0348863f50a231efa114b4` could not be renamed. At
  `17:30:30.8196435`, `Code.exe` PID 49388 successfully opened its descendant
  `0/segments/4875879a-aa68-4d01-bb60-63e0d43d072b/payload_index/00dnhangnlrk7dbgirs6adci-valid_to-map/gaps.dat`
  with **ShareMode: None**; its CloseFile was at `17:30:30.8201801`.
  The open preceded the denied rename by **0.2844 ms**, and close followed it
  by **0.2522 ms**. Exact full paths/details are retained in
  `procmon/handle-overlap-candidates.json`. The open-handle interval is inferred
  conservatively from CSV CreateFile/CloseFile; CSV has no unique handle identity.
- This establishes a concrete **VS Code open/share-mode overlap candidate for
  a cleanup rename**, beyond time proximity alone. It does not establish the
  cause of the earlier index-creation OS error 5. No security-product cause
  is proven. Code.exe, MsMpEng.exe and System all appear in storage-scoped trace;
  mere presence is not attribution. PML stack/filter-driver inspection is pending.
- The storage-filtered trace spans `17:29:30.8455337` through
  `17:31:26.1627887`; the last probe ended after capture. Do not claim full
  coverage of all ten probe durations.
- **Root cause classification/confidence: unresolved; no proven cause for the original index-creation
  defect, stack/filter-driver attribution, or safe full
  remediation.** Even if raw failures exist, their attribution needs manual
  review against probe windows and PML stacks. Routine NAME NOT FOUND alone
  does not establish the original access-denied defect.
- Remaining action: inspect storage-scoped ACCESS DENIED/SHARING VIOLATION
  events and stacks if present; if absent, capture a bounded short-namespace
  indexed recurrence of client OS error 5 with file-level/handle evidence.
  Do not disable security, retry until PASS, or change the formal Gate.
- New diagnostic analyzer streams the CSV to avoid loading unrelated machine
  events into memory; tests protect scope, cross-process retention, midnight
  correlation, and non-promotion of temporal correlation to causal proof.
- Focused tests: **10 PASS**; full pytest: **529 PASS**, 0 failed.
  Repository Ruff and diff check: **PASS**.
- This progress commit does not change N05D-01 completion status. N05D-02 and
  N-05 formal rerun remain unstarted.
