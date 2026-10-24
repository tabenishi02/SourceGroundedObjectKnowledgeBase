# SGOKB Operational Safety / Backup / Recovery

Updated: 2026-10-25

- Status: **Current / Accepted operational design**
- Phase: `Phase O — Documentation / Release / Git cleanup`
- Task: `O-02 [P0] 現行設計書を更新する`
- Requirements authority: `docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md`
- Formal recovery evidence: `docs/evaluation/N07_R01_COMPOSITE_BACKUP_RESTORE_REACCEPTANCE.md`

## 1. Purpose

本書は、SGOKBの現行運用におけるOffline、Backup、Restore、Retention、Security、External Egress、Failure Recovery、Benchmark条件を1つの運用設計として整理する。

本書は要件を新規追加するものではない。Phase Bで定義した非機能要件、Phase MのCLI、安全境界、Phase Nのformal acceptance結果を現在形へ統合する。

---

## 2. Operational invariants

SGOKB運用では次を優先順位付き不変条件とする。

```text
Data integrity / provenance
  > recoverability
  > explicit state / human decision boundary
  > availability / graceful degradation
  > performance
  > convenience / automation rate
```

禁止事項:

- performanceやavailabilityのためにaccepted Versionをin-place書換えする。
- Raw / Evidence / ProvenanceをVector IndexやMarkdownで置換する。
- local provider failureからcloud providerへsilent fallbackする。
- validation済みという理由だけでResultをautomatic importする。
- `review_required` / `blocked` Packageを無確認でexternal exportする。
- backup未検証のままrestore可能とみなす。
- historical / current search generationをsilentに混在させる。

---

## 3. Data criticality

| Class | Examples | Operational treatment |
|---|---|---|
| Canonical / authoritative | SQLite Object / Version / Registry / Source / Snapshot / Evidence Link, Raw Artifact | backup / restore対象 |
| Provenance-bearing retained | Evidence, Normalized Run, accepted original Result, audit metadata | referenced中は保全 |
| Rebuildable derived | Search Representation, Embedding, Qdrant Index, rendered Markdown | rebuild可能 |
| Transient / exchange | Package staging, temporary files, cache | cleanup可能 |

Canonical SQLiteだけでは完全なSGOKB backupにならない。Raw Artifactとaccepted Result provenance等、SQLite外のcanonical dependencyもComposite generationへ含める。

---

## 4. Offline / graceful degradation

### 4.1 Offlineで維持するcore read path

保存済みdataについてInternetなしでも次を成立させる。

- Object ID / name / alias lookup。
- current accepted Knowledge表示。
- Relation traversal。
- Source / Evidence参照。
- Lexical Search。
- local rendering。
- local MCP read。
- local Vector runtimeが既に利用可能な場合のSemantic / Similarity。

Application起動をChatGPT、Google Drive、external Embedding API等のavailabilityへ依存させない。

### 4.2 Derived subsystem failure matrix

| Failure | Canonical read | Lexical | Semantic / Similarity | Required action |
|---|---|---|---|---|
| Qdrant unavailable | continue | continue | unavailable / degraded | explicit warning; rebuild/restart |
| Embedding provider unavailable | continue | continue | new query/vector work unavailable | no cloud fallback |
| MCP server stopped | CLI continues | continue | CLI/runtime次第 | restart MCP only |
| External AI unavailable | continue | continue | continue | Packageをlocal保持 |
| Google Drive / exchange unavailable | continue | continue | continue | export/result transferを延期 |
| Render failure | continue | continue | continue | derived render retry |
| stale derived generation | continue | continue | fail/degrade according to mode | rebuild/cutover |

Semantic-only operationは必要runtimeがない場合にexplicit failureとする。Hybridはcontract上許可される場合のみLexicalへdegradeし、`degraded_channels`等で状態を明示する。

---

## 5. External data egress / security

### 5.1 Default posture

SGOKB Coreはlocal-onlyをdefaultとし、設定・明示操作なしにlocal dataを外部Serviceへ送信しない。

### 5.2 Package export boundary

External AIへ渡すPackageは、build / stage後にpreflightを通す。

```text
allow
review_required
blocked
```

- `allow`: policy上export可能。ただしexport command自体は明示操作。
- `review_required`: 人間が内容・destination・warningを確認し、明示acknowledgementした場合のみexport。
- `blocked`: 標準workflowではexportしない。

Data minimizationを適用し、対象Objectに必要なEvidence / metadataだけをPackageへ含める。Source store全体や無関係Objectを標準Packageへ含めない。

### 5.3 Secrets

標準Packageへ次を含めない。

- browser cookie。
- session token。
- OAuth token。
- API key。
- password。
- private key。
- OS credential material。

credentialをGit管理configへ平文保存しない。logにもsecretやfull Raw / full Package / full Resultを標準dumpしない。

### 5.4 Untrusted external result

外部AIから返るJSON / Markdown / URL / pathはuntrusted inputとして扱う。

- arbitrary path accessを許可しない。
- path traversalを拒否する。
- stringをcommand / SQLとして実行しない。
- Package membership / Result identity / schema / provenanceを検証する。

---

## 6. Backup model

### 6.1 SQLite-only backup vs Composite backup

M-01以前からのSQLite-only commandは互換surfaceとして残る。

```text
sgokb --db <db> system backup create
sgokb --db <db> system backup status
sgokb --db <db> system restore plan <backup>
sgokb --db <db> system restore apply <backup> [--acknowledge-overwrite]
```

ただし、Raw / original Result等のDB外dependencyを持つ現行SGOKBの**完全canonical backup**にはComposite backupを使用する。

```text
sgokb --db <source.sqlite> system backup composite create \
  --incoming-root <incoming> \
  --output <generation>

sgokb system backup composite verify <generation>

sgokb system restore composite plan <generation> \
  --db-target <db> \
  --raw-root <raw> \
  --incoming-root <incoming>

sgokb system restore composite apply <generation> \
  --db-target <db> \
  --raw-root <raw> \
  --incoming-root <incoming> \
  [--acknowledge-overwrite]
```

### 6.2 Composite generation contents

完全backup generationは少なくとも次を閉包する。

- canonical SQLite snapshot。
- snapshotから参照されるRaw Artifact bytes。
- accepted Versionに必要なoriginal Result artifact / receipt-import identity。
- relocation / recovery metadata。
- manifest / checksums / inventory。

Rebuildable derived dataはcanonical RTOから除外可能。

- Search Representation。
- Embedding cache。
- Qdrant Vector Index。
- rendered Markdown。

### 6.3 Consistency point

SQLite Online Backup相当の安全なsnapshotを先に取得し、dependency inventoryはそのsnapshotを基準に閉包する。変化し続けるlive DBを見ながらfile store inventoryを作らない。

Manifestはgeneration contents確定後に作成し、verificationを通してから完成generationとして公開する。

### 6.4 Verification

Backupは「作成commandが成功した」だけではvalidとみなさない。

Verifyで少なくとも次を確認する。

- manifest/schema。
- declared files / unexpected files。
- byte count / checksum。
- SQLite integrity / FK。
- Raw / Result dependency closure。
- unsafe path / traversal / symlink / staging generation拒否。

verificationはpackaged DB / artifactを変更してはならない。

---

## 7. Restore safety

### 7.1 Plan before apply

Restoreは`plan`と`apply`を分離する。既存targetへ上書きする場合は`--acknowledge-overwrite`を必須とする。

### 7.2 Alternate-root recovery

Composite restoreは元のabsolute pathへ依存せず、別DB / Raw / incoming rootへ復旧できることをcurrent product contractとする。

### 7.3 Fail closed

次を拒否する。

- incomplete/staging generation。
- missing / corrupt Raw。
- missing / corrupt Result。
- manifest traversal。
- overlapping restore targets。
- active SQLite sidecar等を含むunsafe target。
- non-empty targetへのunacknowledged overwrite。

### 7.4 Publication order

staging copy / validationを完了してからcanonical targetを公開する。partial copy、ENOSPC、publication failure等で既存DBや既存metadataを破壊しない。

---

## 8. RPO / RTO

初期operational target:

```text
RPO <= 24 hours
RTO <= 4 hours (14400 s)
```

RTOはcanonical DB + Raw / Provenanceを最低限利用可能にし、Object read / Lexical retrievalが復旧するまでを対象とする。全Embedding / Vector Index再構築完了はcanonical RTOへ含めない。

N07-R01 formal Reference Workstation proofでは小規模完全fixtureについて次を確認した。

- Composite create + verification: 0.107322000 s。
- Product restore: 0.072726100 s。
- canonical RTO through Raw reprocessing / Result audit / SQLite-FK / Object-Lexical availability: 0.129272400 s。
- complete backup age: 24 h target内。

これはrequired small fixtureの受入証拠であり、production-scale recovery時間への外挿ではない。

---

## 9. Retention

Initial retention target:

```text
daily generation  >= 7
weekly generation >= 4
```

重要:

- Phase Nで「daily-equivalent complete generation capability」は検証済み。
- 24時間schedulerを実際に連続稼働した証明ではない。
- automatic scheduler / rotation / long-term retention policyはPhase O以降の運用整備領域として残る。

通常cleanupで自動削除しないもの:

- current / historical Knowledge Versionが参照するEvidence。
- そのNormalized Run / Snapshot / Raw Artifact。
- accepted Versionのoriginal Result provenance。
- stable Registry / Identity history。

容量削減はまずrebuildable derived generation、cache、obsolete stagingを対象とする。

Hard deleteは日常操作とせず、dependency impact、preview/dry-run、strong warning、auditを持つ管理操作とする。ArchiveとDeleteを区別する。

---

## 10. Derived search rebuild after recovery

Canonical restore完了後、必要に応じてderived stateを別工程で再構築する。

```text
restored canonical SQLite
  ↓
Search Representation rebuild
  ↓
Embedding generation
  ↓
Qdrant generation rebuild
  ↓
semantic / similarity acceptance check
```

Current R2 family:

```text
object_overview
facet
statement
```

active `object_overall` leakageを許可しない。

N07-R01では同じrestored fixtureをnormal generation-aware maintenanceへ通し、Harrier frozen revisionでderived rebuild、generation membership/vector audit、Semantic read、RenderまでPASSした。このderived rebuild時間はcanonical RTOと分離して記録する。

---

## 11. Failure / recovery categories

Operational handlingを次へ分類する。

### Input / Result failure

- invalid JSON / schema。
- stale base Version。
- missing Evidence membership。
- partial / duplicated Result。

→ canonical import前にfail/review。既存accepted Versionを維持する。

### Derived retrieval failure

- Embedding failure。
- Qdrant unavailable/corrupt。
- stale generation。

→ canonical Knowledgeを維持し、Lexical継続 / Semantic unavailableまたはdegradedを明示。必要ならrebuild。

### Storage / process failure

- process kill。
- disk full。
- partial file。

→ temp/staging + atomic publication、transaction、preflightでpartial artifactをcompleted扱いしない。

### Provenance failure

- missing Raw。
- checksum mismatch。
- broken Evidence chain。

→ affected scopeをbroken/degradedとして隔離。新Knowledge generationへsilent利用しない。

### External dependency failure

- Internet unavailable。
- ChatGPT unavailable。
- exchange destination unavailable。
- MCP server stopped。

→ local canonical workflowを維持し、external stepのみ延期/明示failure。

---

## 12. Benchmark / acceptance conditions

### 12.1 Reference Workstation

Phase N primary Reference Workstation:

```text
OS:     Windows 11
CPU:    Intel Core i5-13600KF
RAM:    128 GB
GPU:    NVIDIA GeForce RTX 4090 24 GB
Storage: local filesystem; actual volume/free space recorded per run
```

Benchmark結果はhardware、software、Git source、storage、model revision、runtime identityを付けて解釈する。

### 12.2 N-05 performance gates

Current formal performance gates:

```text
Standard warm p95 <= 600 s
Large warm p95    <= 1200 s
```

Human / external timeはlocal automatic processing gateへ含めない。

除外例:

- Source探索 / network capture待ち。
- Package manual review。
- ChatGPT generation待ち。
- result transfer待ち。
- review-required human decision。

normal automatic retryは計測へ含める。cold / warm条件は分離記録する。

### 12.3 Retrieval benchmark identity

Current accepted semantic baseline:

```text
representation contract: n05d04r2-hierarchical-v2
active object family:    object_overview / facet / statement
embedding model:         microsoft/harrier-oss-v1-0.6b
revision:                f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
output dimension:        1024
vector backend:          Qdrant
```

Model / revision / representation builder / dimensionが変わる場合、同一Embedding Spaceとして無条件比較しない。

### 12.4 Formal evidence boundaries

Phase N acceptance結果を再利用するときは、元runのfixture / scale / hardware boundaryを保持する。

- small recovery fixtureのRTOをproduction-scale RTOとして宣伝しない。
- N-03 small ecological fixtureをpopulation-wide quality proofとしない。
- optional reranker未採用をfailureとしない。
- historical failed runを削除・PASSへ書換えしない。

---

## 13. Operator checks

日常的なminimum checks:

```powershell
sgokb --db <db> system status
sgokb --db <db> system integrity
sgokb --db <db> system index status
sgokb --db <db> system backup status
```

1 Object処理は`docs/operations/OBJECT_STANDARD_WORKFLOW.md`を使用する。

Backup/restore testではproduction targetを直接上書きせず、可能な限りalternate rootへrestoreしてintegrity / Raw / Result / Object read / Lexical readを確認する。

---

## 14. Current accepted limitations / deferred operations

Phase N PASSを否定しない既知の運用上の残件:

- retention scheduler / rotationのproduction automation。
- off-device backup destinationの具体運用。
- production-scale RTO measurement。
- optional reranker adoption。
- derived full rebuildのproduction-scale throughput planning。

これらを「既存のcanonical backup / restore capabilityがない」と読み替えない。Composite generation / verification / alternate-root restoreはcurrent product capabilityとしてformal acceptance済みである。

---

## 15. Authority map

- Non-functional requirements: `docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md`
- Workflow boundary: `docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md`
- CLI / system operation contract: `docs/decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md`
- Standard Object workflow: `docs/operations/OBJECT_STANDARD_WORKFLOW.md`
- Original N-07 failure evidence: `docs/evaluation/N07_FAILURE_RECOVERY.md`
- Composite recovery re-acceptance: `docs/evaluation/N07_R01_COMPOSITE_BACKUP_RESTORE_REACCEPTANCE.md`
- Phase N final closure: `docs/evaluation/PHASE_N_CLOSURE_AUDIT.md`
- Current integrated architecture: `docs/design/SGOKB_CURRENT_ARCHITECTURE.md`
