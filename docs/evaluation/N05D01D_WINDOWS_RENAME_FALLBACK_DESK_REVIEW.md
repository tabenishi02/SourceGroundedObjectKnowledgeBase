# N05D-01D — Windows rename fallback desk review

更新日: 2026-10-22

- Parent: `N05D-01 — Qdrant storage/path diagnosis`
- Status: **Complete - 50/50 recovered; revised gate and post-switch acceptance PASS**
- Source run: `20261022T191928+0900`
- Source HEAD: `fd8746445f855ac0f6adfa905b9f3d9504b8316d`

## 1. Question

N05D-01Cでは、external storage `C:\Qdrant\SGOKB` 上のindexed lifecycle stressが50/50 API PASSした一方、ProcMonでは各collection cleanup時に `qdrant.exe SetRenameInformationFile -> ACCESS DENIED` を50件観測した。

この50件が未回復のQdrant defectなのか、Windows/Rust rename fallbackの途中経過なのかをdesk reviewする。

## 2. Qdrant 1.19.2 delete semantics

Qdrant v1.19.2の `safe_delete_in_tmp()` は、対象directoryをtemporary `.deleted` directoryへ `fs::rename(path, &to_delete)?` でrenameする。

Collection delete pathでも `safe_delete_in_tmp(&collection_path, &safe_delete_path)?` として呼び出されるため、この `fs::rename` が最終的にErrならdelete APIはその場でerrorへ伝播する。

その後の `to_delete.close()` はbackgroundで行われるが、collection rootから `.deleted` への最初のrename自体はAPI成功前に同期的に完了する必要がある。

したがって、N05D-01Cの50/50 delete API PASSは、50 cycleすべてで `fs::rename` が最終的にはOkを返したことを強く示す。

## 3. Rust Windows rename semantics

現行Rust標準ライブラリのWindows `std::fs::rename` は、まず `MoveFileExW(..., MOVEFILE_REPLACE_EXISTING)` を試す。

このprimary renameが `ERROR_ACCESS_DENIED` で失敗した場合、sourceをDELETE accessで開き、`SetFileInformationByHandle(FileRenameInfoEx)` と `FILE_RENAME_FLAG_REPLACE_IF_EXISTS | FILE_RENAME_FLAG_POSIX_SEMANTICS` を使用するfallback renameを試す。

fallbackが成功すれば `std::fs::rename` はOkを返す。fallbackまで失敗した場合のみ元のACCESS_DENIEDをErrとして返す。

この実装は、Windowsのtraditional rename semanticsがopen file/handle条件でACCESS_DENIEDになり得る問題を緩和するためのものである。

## 4. Interpretation of N05D-01C 50 ACCESS DENIED events

N05D-01Cでは:

- collection delete API: 50/50 PASS
- terminal API failure: 0
- surfaced client/server OS error 5: 0
- each cycleでcollection cleanup root renameにProcMon ACCESS DENIED: 1件
- Code.exe external storage access: 0

という組み合わせだった。

Qdrant v1.19.2の同期error propagationとRust Windows rename fallbackを合わせると、最有力説明は次である。

```text
Qdrant safe_delete_in_tmp
  -> Rust std::fs::rename
     -> MoveFileExW primary attempt
        -> ACCESS DENIED
     -> FileRenameInfoEx + POSIX semantics fallback
        -> SUCCESS
  -> Qdrant delete API PASS
```

50 cycleすべてで1件ずつACCESS DENIEDが観測され、APIは50/50 PASSしたという規則性は、random external-reader contentionだけよりもこのfallback sequenceと強く整合する。

## 5. Gate implication

現行N05D-01C acceptanceの

```text
ProcMon qdrant.exe ACCESS DENIED = 0
```

は、Windows/Rust内部で回復済みのprimary rename attemptまでfailure扱いするため、system correctness Gateとして過剰である可能性が高い。

Gateを変更する前にReference Workstation raw PML/CSVで、各ACCESS DENIED eventが同じcollection cleanupについて後続のsuccessful renameへ対応することを確認する。

確認後の候補Gate:

```text
unrecovered collection rename failure = 0
delete API failure = 0
surviving collection directory after successful delete = 0
Qdrant server error caused by cleanup rename = 0
surfaced OS error 3/5 = 0
```

ProcMonのrecoverable primary ACCESS DENIED件数はdiagnostic observationとして記録するが、それ単独をFAIL条件にはしない。

## 6. Original N-05 failureとの関係

このdesk reviewはN05D-01C cleanup renameの50件を説明するものであり、formal N-05のpayload-index preparation中にsurfaceしたOS error 3/5を直接説明したものではない。

Qdrant upstream issue #10806では、Windows上でpayload-index/segment fileへのexternal/security reader accessとrenameが競合し、Qdrant-levelで最終的なPermissionDeniedがsurfaceする事象が報告されている。

したがって次の2状態を区別する必要がある。

```text
A. primary Windows rename ACCESS DENIED -> Rust fallback SUCCESS
   = recovered internal event

B. primary rename ACCESS DENIED -> fallback/retry pathも失敗 -> Qdrant error
   = actual runtime defect
```

N05D-01CはAを50 cycleで観測した可能性が高い。Formal N-05の元障害はBまたはpath-length related OS error 3であった可能性が残る。

## 7. Required local validation

Reference Workstationでrun `20261022T191928+0900` のraw ProcMon evidenceを再解析し、50件それぞれについて次を相関する。

1. ACCESS DENIED eventのtimestamp/source/destination。
2. 同一source/destinationまたは同一collectionに対する直後のrename SUCCESS。
3. ACCESS DENIED直後のDELETE-access CreateFile等、Rust fallbackと整合するevent sequence。
4. delete API response timestamp/status。
5. collection source directory消滅と `.deleted` target lifecycle。
6. Qdrant server logにterminal delete errorがないこと。
7. 可能ならPML stackで `MoveFileExW` / `SetFileInformationByHandle` の区別。

50/50がrecoverable fallback sequenceと確認できれば、N05D-01C Gateをevidence-basedに修正し、external storage runtime cutover/post-switch Derived Search smokeへ進む候補とする。

確認できないeventがある場合はBLOCKEDを維持する。

## 8. Historical desk-review verdict (superseded by local verification)

- **N05D-01 = BLOCKED / Not Complete** を維持する。
- WSL2移行はまだ実施しない。
- 先にN05D-01D local rename-outcome correlationを行う。
- Security設定は変更しない。
- N05D-02 / formal N-05 rerunは開始しない。


## 9. Reference Workstation exact correlation — 2026-10-22

Execution HEAD: `c1c8e5cdbaec786668f52fa9d2db95c461be3b6b`.
The original run `20261022T191928+0900` was analyzed without another stress run
or rewriting PML/CSV/cycle/log evidence. The reproducible tool is
`benchmark/tools/n05d01_correlate_rename_fallback.py`.

- Primary ACCESS DENIED: 50; RECOVERED_FALLBACK: **50**; UNRECOVERED_FAILURE: **0**; AMBIGUOUS: **0**.
- Unique diagnostic-cycle/delete API PASS binding: **50/50**.
- Matching source/destination file identity: **50/50**; surviving source directories: **0**.
- Terminal Qdrant cleanup errors: **0**; Code.exe external-storage accesses: **0**.
- Fallback delta: min **0.9498 ms**, median **1.77175 ms**, max **40.226 ms** (initial 100 ms search window).

Representative PID 18756 sequence for collection `n05a4b0a543c9cf`:

```text
19:33:23.7577958 SetRenameInformationFile ACCESS DENIED
19:33:23.7590883 CreateFile SUCCESS (source, DELETE access)
19:33:23.7595815 SetRenameInformationEx SUCCESS (same source/destination, POSIX + REPLACE)
19:33:23.7611887 CloseFile SUCCESS (destination .deleted/ShuBVt)
```

Both paths have file identity `0x27f00000003df98`; source and destination are
now absent. Each of the other 49 events has the same independently checked
sequence and successful cycle/API binding. Time proximity alone is insufficient;
negative tests reject wrong PID/path/flags, missing reopen/close, unknown
filesystem state, terminal errors and duplicate cycle matches.

The event sequence matches the [Rust Windows rename implementation](https://github.com/rust-lang/rust/blob/main/library/std/src/sys/fs/windows.rs)
and [Qdrant v1.19.2 safe_delete_in_tmp](https://github.com/qdrant/qdrant/blob/v1.19.2/lib/common/common/src/fs/safe_delete.rs).
Binary compiler revision and native stacks were not decoded, so exact call-stack
attribution remains unverified; operation/API/filesystem evidence is sufficient
to classify these 50 cleanup outcomes with high confidence.

Gate correction is authorized by this implementation/evidence agreement; it
does not waive surfaced OS error 5 or claim the original payload-index failure
was recovered. External storage passes the revised pre-cutover gate.
Controlled cutover and post-switch checks subsequently passed; see final outcome below.


## N05D-01D final local outcome - 2026-10-22

**N05D-01D = Complete; N05D-01C = Complete; N05D-01 = Complete.**

- Correlation source run: `20261022T191928+0900`; cutover/regression run:
  `20261022T221858+0900`. Execution HEAD: `c1c8e5cdbaec786668f52fa9d2db95c461be3b6b`.
- All 50 primary denials are **RECOVERED_FALLBACK**; unrecovered 0, ambiguous 0.
  Same PID, exact source/destination, DELETE reopen, POSIX rename success,
  matching file identity and destination close were correlated to each cycle.
  Delete API PASS 50/50; surviving source directories 0; terminal cleanup errors 0.
  Delta min/median/max: **0.9498 / 1.77175 / 40.226 ms**.
- Revised storage gate: PASS. Recovered internal ACCESS DENIED remains 50 as a
  diagnostic counter. Unrecovered rename, delete API failure, surviving source,
  terminal cleanup error and surfaced OS error 3/5 are all 0.
  ProcMon SHARING VIOLATION 0; Code.exe external-storage accesses/opens 0.
- Old Qdrant PID 45700/config/31 collections were recorded before graceful
  CTRL_C stop. Diagnostic PID 18756 was also stopped gracefully after recording
  its empty collection state. Private-console checks excluded unrelated processes.
  No force stop or security change was used.
- Old `.local/n04p06/qdrant/storage` remains untouched for rollback/evidence;
  no old storage state was copied. New runtime root: `C:\Qdrant\SGOKB`, config
  `C:\Qdrant\SGOKB\qdrant.yaml`, absolute storage/snapshots/temp paths.
- New native Qdrant **1.19.2**, build `016542aa5deb6c66380bb137badf73d54f742bde`,
  PID **54084**, HTTP 6333 / gRPC 6334, non-admin. Command:
  `.local/qdrant-1.19.2/qdrant.exe --config-path C:\Qdrant\SGOKB\qdrant.yaml --disable-telemetry`.
  qdrant-client **1.19.1**. HTTP connectivity/readiness PASS.
- Approved `system index rebuild` on the N-03 evaluation DB rebuilt **24 points**
  (1024 dimensions, Qdrant green, configured payload indexes). No new Embedding
  generation or manual SQL/readiness edits were needed. Small collections may
  report indexed_points_count 0 below the vector indexing threshold.
- Real `search --mode semantic --semantic-runtime --require-full-runtime
  --primary-class character` returned Saber rank 1, semantic channels present,
  no degraded channels. This also verifies the filtered Vector query path.
- `system integrity` PASS. Evaluation and production canonical semantic
  fingerprints match before/after. Production DB was not used for CLI writes.
  New server logs contain no terminal cleanup / surfaced OS error 3/5 match.
- Focused N05D-01/D tests: **17 passed**. Full pytest: **541 passed, 0 failed,
  2 warnings** (local-Qdrant index/search-parameter notices), 174.35 seconds.
  Repository Ruff and `git diff --check`: **PASS**.
- Local-only readiness helper initially parsed the plain-text `/readyz` response
  as JSON. Corrected response handling resumed against the already-ready server;
  the failed helper log/attempt remains retained. No SGOKB production code changed.

Classification: **QDRANT_ENVIRONMENT_DEFECT**; remediation subtype:
workspace-resident Windows native storage / path-length sensitivity /
external-reader contention candidate. Remediation effectiveness and recovered
cleanup classification have high confidence. The unique cause of the original
surfaced payload-index OS error 5, exact binary Rust compiler revision and native
stack attribution remain unproven. Recovered internal cleanup ACCESS DENIED is
not the original surfaced/unrecovered OS error 5. VS Code is not established as
its sole cause; Defender/EDR causation is not asserted.

Evidence is retained locally under both run roots, including all original
PML/CSV, per-cycle API results, correlation JSON, old/new runtime metadata,
canonical fingerprints, commands, smoke and regression logs. Raw evidence is
not a Git asset. No security policy/service/exclusion/firewall changes, WSL2
migration, N05D-02 execution or formal N-05 rerun were performed.

Next task: **N05D-02 - Long-input Harrier memory diagnosis (not started)**.
N-05 remains **BLOCKED / Not Complete** until its independent blockers and formal
rerun requirements are satisfied.
