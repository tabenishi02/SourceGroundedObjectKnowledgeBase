# N05D-01C — Qdrant Storage Isolation Remediation

更新日: 2026-10-22

- Parent: `N05D-01 — Qdrant storage/path diagnosis`
- Status: **Complete - revised storage gate and post-switch runtime PASS**
- Current N05D-01 status: **Complete**
- Current `main` before this task: `2ea954c9c9ab0dcefd77720bf3dee606c5c87d25`

## 1. Purpose

ProcMon観測では、既存Qdrant storage配下のpayload-index fileを`Code.exe`が`ShareMode: None`でopenしている時間帯と、Qdrantの`SetRenameInformationFile -> ACCESS DENIED`が重なる事象を確認した。

この観測はcleanup renameについての具体的なexternal-reader contention candidateであり、元のpayload-index作成時OS error 5の原因確定ではない。

N05D-01Cでは、Qdrant runtime storageをVS Code workspaceから物理的に分離し、Windows path長も短くした構成でreal-Qdrant indexed stress testを実行する。

formal N-05 performance sampleは実行しない。

## 2. Adopted remediation

### 2.1 Short collection namespace

N05診断で導入した短いcollection namespaceを維持する。

```text
n05 + SHA-256(run_id:sample_id) first 12 hex
```

目標prefix長は15文字。

これはOS error 3 / excessive native path lengthのmitigationであり、OS error 5単独の修復とは扱わない。

### 2.2 External short Qdrant storage root

Reference Workstationのtarget runtime rootを次とする。

```text
C:\Qdrant\SGOKB
```

最低限のruntime path:

```text
C:\Qdrant\SGOKB\storage
C:\Qdrant\SGOKB\snapshots
C:\Qdrant\SGOKB\temp
C:\Qdrant\SGOKB\qdrant.yaml
```

`C:\Qdrant\SGOKB`は、Qdrant用runtimeであることとSGOKB専用領域であることをpath名から識別でき、かつWindows native pathを十分短く維持できる命名として採用する。

要件:

- repository / VS Code workspace外であること。
- local NTFS上のabsolute pathであること。
- Qdrant専用runtime directoryとして扱うこと。
- Qdrant executable自体は既存locationを使用してよい。
- existing storageを即削除しないこと。

旧storage:

```text
C:\codex\SourceGroundedObjectKnowledgeBase\.local\n04p06\qdrant\storage
```

は診断証跡として、remediation acceptance完了まで保持する。

### 2.3 VS Code watcher exclusion

workspace内に残る旧Qdrant/diagnostic runtimeについては、workspace設定でfile watcherから除外する。

最低候補:

```text
**/.local/n04p06/qdrant/**
**/.local/n05d01/**
**/.local/q/**
```

既存`.vscode/settings.json`がある場合はpreserve/mergeする。

`files.watcherExclude`は補助策であり、external storage isolationの代替としない。

### 2.4 Security policy

今回のremediationでは次を行わない。

- Microsoft Defender停止
- Defender / EDR exclusion追加
- MsSense停止
- Firewall緩和
- Qdrant processの恒久的な管理者実行

security設定を変更せず成立することをAcceptance条件とする。

## 3. Migration safety

既存Qdrant server PID/config/storageを最初に記録する。

移行時は:

1. current process / config / collectionsを記録する。
2. existing serverをcontrolled stopする。
3. 旧storageを削除・移動しない。
4. `C:\Qdrant\SGOKB`を新規runtime rootとして作成する。
5. `C:\Qdrant\SGOKB\qdrant.yaml`をabsolute pathで作成する。
6. 新storageでQdrantを起動する。
7. server version / ports / storage pathを確認する。

既存canonical SQLite DBは変更しない。

必要なderived Vector Indexはrebuildable artifactとして新storageへ再生成してよいが、旧Qdrant storageから直接copyして新環境へ持ち込まない。既存storage stateを原因候補から除外するため、新storageはclean startする。

## 4. Diagnostic acceptance

### 4.1 Minimal indexed smoke

新external storage上で最低限:

```text
collection create
payload indexes create
point upload
filtered query
collection delete
```

をdirect qdrant-clientとSGOKB adapterの両方でPASSさせる。

### 4.2 Stress cycle

formal performanceとは分離してindexed lifecycleを複数回繰り返す。

Target:

```text
>= 50 complete indexed cycles
```

各cycle:

```text
create -> all payload indexes -> upload -> query -> delete
```

Failure replacementは禁止する。

Acceptance:

```text
OS error 3 = 0
OS error 5 = 0
client terminal failure = 0
```

### 4.3 ProcMon observation

stress cycle中にProcMon captureを行う。

確認:

- `C:\Qdrant\SGOKB\storage`配下を`Code.exe`がopenしていないこと。
- Unrecovered collection rename failure、delete API failure、successful-delete source survivors、terminal cleanup error、surfaced client/server OS error 3/5がすべて0件であること。
- Recovered primary `ACCESS DENIED`はdiagnostic counterとして保持する。`SHARING VIOLATION`も記録する。
- 異常な`PATH NOT FOUND`が診断failureとして出ていないこと。

routine lookup missesはfailureと混同しない。

raw PML/CSVは`.local`等のGit管理外に保持する。

## 5. Existing runtime switch

4のAcceptanceがPASSした場合のみ、Reference Workstationで通常利用するQdrant configを新external storageへ切り替える。

切替後:

```text
Qdrant server metadata PASS
Derived Search minimal real-runtime smoke PASS
system integrity PASS
```

を確認する。

旧workspace内Qdrant storageは直ちに削除せず、rollback/evidence用に保持する。

## 6. Verdict semantics

### PASS candidate

次をすべて満たした場合、N05D-01 remediationは成功候補とする。

- short namespace維持。
- external short storage root `C:\Qdrant\SGOKB`使用。
- direct indexed smoke PASS。
- adapter indexed smoke PASS。
- >=50 stress cyclesでsurfaced client/server OS error 3/5 = 0。
- ProcMonでexternal storageへのCode.exe openが確認されない。
- Unrecovered collection rename failure / delete API failure / surviving collection / terminal cleanup error / surfaced OS error 3/5 = 0。
- security設定変更なし。
- regression suite PASS。

この結果は「元障害の唯一原因がVS Codeだった」とは証明しない。

分類はevidenceに応じて`QDRANT_ENVIRONMENT_DEFECT`または`OTHER_IDENTIFIED_CAUSE`として確定する。

### FAIL / BLOCKED

external storageでsurfaced / unrecovered OS error 5が再現した場合:

- N05D-01をBLOCKEDのまま維持する。
- WSL2/Linux filesystem Qdrantを次のremediation candidateとする。
- Defender/EDR停止でGateを通さない。

## 7. Regression

code/config/document変更後:

```text
focused N05D-01 tests PASS
full pytest 0 failed
Ruff PASS
git diff --check PASS
```

## 8. Completion boundary

N05D-01Cはenvironment remediationとdiagnostic acceptanceまでを扱う。

N05D-02 Long-input Harrier memory diagnosisやN05 formal performance rerunへ自動的に進まない。

N05D-01をCompleteにできるのは、root-cause classificationとsafe remediationのexit conditionを満たした場合のみ。


## Historical N05D-01C external-storage result (original gate; superseded below) — 2026-10-22

**N05D-01C = BLOCKED; N05D-01 = BLOCKED / Not Complete. No production cutover.**

- Run: `20261022T191928+0900`; execution HEAD:
  `a2e2a48fdc04ec730fc14b655dc00e0a4fd1a4a1` (clean main at start).
- Existing native Qdrant: 1.19.2, build `016542aa`; qdrant-client: 1.19.1.
  Executable `.local/qdrant-1.19.2/qdrant.exe`; existing PID 45700, HTTP 6333 /
  gRPC 6334, config `.local/n04p06/qdrant.yaml`, unchanged.
- Old storage `.local/n04p06/qdrant/storage` and snapshots were not moved,
  deleted, or copied. Existing collections were unchanged (31 before/after).
- Clean external root: `C:\Qdrant\SGOKB`. Storage, snapshots and temp are
  absolute paths in `qdrant.yaml` and `qdrant-diagnostic.yaml`, outside the
  workspace. External diagnostic PID 18756 used HTTP 6433 / gRPC 6434 with:
  `qdrant.exe --config-path C:\Qdrant\SGOKB\qdrant-diagnostic.yaml`.
  Qdrant was started without elevation. The root was absent before preparation;
  no old storage state was copied. All path write probes passed.
- The three required `files.watcherExclude` entries were verified. They supplement
  external storage isolation; no security setting or exclusion was changed.

### Smoke, stress and native-operation evidence

| Check | Observed result |
|---|---|
| Direct plain / indexed smoke | PASS / PASS |
| Adapter plain / indexed smoke | PASS / PASS |
| Complete indexed lifecycle cycles | 50/50 (25 direct + 25 adapter) |
| Terminal API failure / failed cleanup response | 0 / 0 |
| Client/server exception OS error 3 / 5 | 0 / 0 |
| ProcMon qdrant.exe ACCESS DENIED | **50 — mandatory gate failed** |
| ProcMon qdrant.exe SHARING VIOLATION | 0 |
| Code.exe external-storage successful opens / all accesses | 0 / 0 |
| Entire stress interval covered by trace | PASS |
| Post-switch Derived Search smoke | NOT RUN — cutover gate failed |
| Existing evaluation DB system integrity | PASS (not a post-switch result) |

Short namespaces were `n05` + first 12 hex SHA-256(run_id:sample_id), unchanged.
Every cycle used all configured payload indexes, upload, filtered query and
collection deletion. No failed cycle was replaced or hidden. No formal N-05
performance sample or N05D-02 experiment was executed.

ProcMon 4.12 was user-authorized for elevation; the server and probes stayed
non-admin. The raw capture retained all processes; the analyzed scope was the
exact external root. It spans `19:33:12.9521605` to `19:40:12.7519241` JST and
fully covers stress `19:33:14.727329` to `19:38:56.432627` JST. Scoped events:
1,722,290 (qdrant.exe 1,615,587; MsMpEng.exe 68,519; System 38,184; Code.exe 0).

All 50 ACCESS DENIED events were `SetRenameInformationFile` during collection
cleanup into `storage/.deleted`. Example:

```text
2026-10-22 19:33:23.7577958 +09:00
qdrant.exe PID 18756
SetRenameInformationFile -> ACCESS DENIED
source: C:\Qdrant\SGOKB\storage\collections\n05a4b0a543c9cf
destination: C:\Qdrant\SGOKB\storage\.deleted\ShuBVt
ReplaceIfExists: True
```

The native ACCESS DENIED result represents denied file operations even though
client/server exception-string counters for `os error 5` are zero. Those zero
exception counters must not be interpreted as absence of native OS error 5.
PATH NOT FOUND (17,100) and NAME NOT FOUND (63,527) were retained as observations;
lookup misses were not automatically labeled abnormal failures. The explicit
zero-ACCESS-DENIED gate was applied without weakening it for successful API calls.

### Decision, confidence and remaining scope

**Root-cause classification remains UNRESOLVED.** External workspace isolation
was verified with high confidence (zero observed Code.exe storage accesses), but
it did not satisfy the native-operation acceptance gate. Therefore no claim of
successful environment remediation or `QDRANT_ENVIRONMENT_DEFECT` closure is made.

This run demonstrates that Code.exe access is not necessary for these cleanup
rename denials. It does not establish the cause of the original payload-index
creation OS error 5, nor a unique backend/security-filter mechanism. MsMpEng.exe
presence alone is not evidence of Defender causation; stack/filter attribution
is unproven. No Defender/EDR service, exclusion, firewall, or system policy was
changed. No Qdrant administrator fallback was used.

Old PID 45700 / config / 6333/6334 were retained. No Vector artifacts were rebuilt
and no Derived Search readiness flags were changed manually. The existing N-03
evaluation DB passed the normal `system integrity` CLI; production canonical DBs
were not modified by this diagnostic.

Next remediation candidate is **WSL2/Linux-filesystem Qdrant in a separately
authorized task**. Do not execute N05D-02 or formal N-05 rerun from this result.

### Regression and retained artifacts

- Focused N05D-01 tests: **10 PASS / 0 failed**.
- Full pytest: **529 PASS / 0 failed**.
- Repository Ruff: **PASS**.
- `git diff --check`: **PASS**.
- Evidence: `.local/n05d01/20261022T191928+0900/`, including pre-state,
  minimal smoke, all 50 cycle results, gate/review JSON, raw split PML, raw and
  filtered CSV, Qdrant logs and evaluation integrity output. These are not Git assets.
- Wrapper pipe inheritance and PowerShell security-module auto-import failures
  occurred before stress; their logs and source snapshots are retained. Explicit
  bundled-module import validated ProcMon's signature; no security policy changed.
- Old N-05 and N05D-01 evidence remain intact. Completion status stays BLOCKED.


## N05D-01D gate correction — 2026-10-22

All 50 primary ACCESS DENIED events are **RECOVERED_FALLBACK**, with no
unrecovered or ambiguous event. This is not inference from API success alone:
each PID/source/destination pair has a DELETE-access reopen, successful
SetRenameInformationEx with REPLACE_IF_EXISTS + POSIX_SEMANTICS, destination
close, matching file identity, successful cycle delete and absent source.
No terminal cleanup error was found. The original raw gate/evidence is retained.

The zero-primary-ACCESS-DENIED rule incorrectly rejected successful Windows
rename fallback. The active gate now requires zero unrecovered collection rename
failures, delete API failures, surviving source collections after successful delete,
terminal cleanup errors, and surfaced client/server OS error 3/5. Recovered
ACCESS DENIED remains a diagnostic counter (50); Code.exe storage opens = 0.
The existing 50-cycle external-storage result passes this revised gate.

Local evidence: `.local/n05d01/20261022T191928+0900/n05d01d/`.
Controlled cutover and post-switch Derived Search acceptance passed (details below).
The original surfaced payload-index preparation error is not equated with these recovered cleanup events.


## Final remediation acceptance

N05D-01C and N05D-01 are **Complete** after N05D-01D verified all 50 recovered
rename sequences and corrected the gate. The historical BLOCKED result above
is retained as the outcome under the original zero-primary-denial rule.

Cutover/regression run `20261022T221858+0900`: old storage retained, new
`C:\Qdrant\SGOKB` runtime on 6333/6334, 24 Vector points rebuilt through the
approved CLI, real filtered semantic search and system integrity PASS.
Canonical semantic state unchanged; focused 17 passed, full 541 passed (2 warnings),
Ruff/diff PASS. No security setting changed. Remediation effectiveness is high
confidence; the original payload-index OS error 5 has no proven unique cause.

See [final local evidence and limitations](../../../../evaluation/N05D01_QDRANT_STORAGE_PATH_DIAGNOSIS.md#n05d-01d-final-local-outcome---2026-10-22).
N05D-02 is next but not started. N-05 formal benchmark remains BLOCKED.
