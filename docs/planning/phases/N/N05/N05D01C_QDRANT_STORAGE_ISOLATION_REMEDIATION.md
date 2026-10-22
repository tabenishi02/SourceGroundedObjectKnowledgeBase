# N05D-01C — Qdrant Storage Isolation Remediation

更新日: 2026-10-22

- Parent: `N05D-01 — Qdrant storage/path diagnosis`
- Status: **Ready for Reference Workstation execution**
- Current N05D-01 status: **BLOCKED / Not Complete**
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

Reference Workstationのtarget runtime pathを次へ移す。

```text
C:\q\sgokb\storage
C:\q\sgokb\snapshots
C:\q\sgokb\temp
```

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
4. 新storage rootを新規作成する。
5. 新configをabsolute pathで作成する。
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

- external storage root配下を`Code.exe`がopenしていないこと。
- qdrant.exeの`ACCESS DENIED` / `SHARING VIOLATION`が0件であること。
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
- external short storage root使用。
- direct indexed smoke PASS。
- adapter indexed smoke PASS。
- >=50 stress cyclesでOS error 3/5 = 0。
- ProcMonでexternal storageへのCode.exe openが確認されない。
- Qdrant ACCESS DENIED / SHARING VIOLATION = 0。
- security設定変更なし。
- regression suite PASS。

この結果は「元障害の唯一原因がVS Codeだった」とは証明しない。

分類はevidenceに応じて`QDRANT_ENVIRONMENT_DEFECT`または`OTHER_IDENTIFIED_CAUSE`として確定する。

### FAIL / BLOCKED

external storageでもOS error 5が再現した場合:

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
