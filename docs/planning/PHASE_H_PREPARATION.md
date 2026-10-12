# Source Grounded Object Knowledge Base — Phase H Preparation

更新日: 2026-10-13

- Status: In Progress
- Completed phase: Phase G — Google Drive / ChatGPT交換ワークフロー
- Next phase: Phase H — Result Validation / Import / Rendering
- Completed tasks: `H-01 [P0] Result JSON Validator`, `H-02 [P0] Object Version Import`
- Next task: `H-03 [P1] Markdown Rendererを実装する`
- Working branch: `integration/knowledge-base-redesign`

---

## 1. Phase G completion audit

Phase Gのtask master、G-01〜G-05成果物、Exchange実装を再監査した。

| Task | Status | Authority / implementation |
|---|---|---|
| G-01 Object Evidence Package format | Complete | `docs/design/OBJECT_EVIDENCE_PACKAGE_FORMAT.md` |
| G-02 `manifest.json` schema | Complete | `docs/design/OBJECT_EVIDENCE_PACKAGE_MANIFEST_SCHEMA.md`, `exchange/package_manifest.py`, JSON Schema |
| G-03 ChatGPT `instructions.md` | Complete | `docs/design/OBJECT_ANALYSIS_INSTRUCTIONS.md`, `exchange/instructions.py`, `prompts/object_analysis.md` |
| G-04 local staging / external export | Complete | `docs/design/PACKAGE_STAGING_DRIVE_EXPORT.md`, `exchange/package_transfer.py`, `package_cli.py` |
| G-05 Result receipt | Complete | `docs/design/RESULT_RECEIPT_WORKFLOW.md`, `exchange/result_receipt.py`, Migration 011 |

個別Taskはすべて成果物を持つ。ただしPhase完了条件を再確認した結果、G-01〜G-05の間に暗黙の接続gapが1件あった。

### Closure gap — canonical DBからPackage workspaceを作るBuilder

G-04は既存Package build directoryをstagingする実装だったため、canonical Object / Evidenceから実際のPackage directoryを生成する処理が未接続だった。

Phase G完了条件:

> APIを利用せず、ユーザーがChatGPTとの手動工程を介して1 Objectを往復できる。

を満たすには、手動でPackage fileを組み立てることを要求してはならない。

Phase G closureで次を追加した。

- `src/sgokb/exchange/package_builder.py`
  - canonical Object / Class / Facet / EvidenceからPackage workspaceを生成する。
  - F-03 `ObjectEvidenceRetriever` + F-04 `EvidencePackageSelector`を再利用する。
  - generative LLMを呼ばない。
  - `instructions.md` / Result Schema / Evidence payload / manifestを生成する。
  - update Packageでは`current_object.json`を生成する。
  - current VersionのEvidence groundingをsystem-protected carry-forwardとして自動追加する。
- `src/sgokb/storage/package_repository.py`
  - Package build専用read model。
  - current accepted Knowledgeを`current_object.json`向けに再serializationする。
  - current Version grounding Evidence、active Attribute / Relation Registryを取得する。
- `sgokb-package build`
  - Object IDからlocal build workspaceを生成する。
- `tests/test_phase_g_roundtrip.py`
  - initial Objectのbuild → stage → export → returned Result receiptを1本のlocal integration flowとして固定する。
  - update Packageでhistorical carry-forward Evidenceと`current_object.json`を確認する。

これによりPackage fileの手動組立ては標準Workflowから除外された。

---

## 2. Phase G finalized standard flow

Phase G終了時点の1 Object標準flowは次である。

```text
Canonical Object / Source / Evidence
        ↓
sgokb-package build --object <object_id>
        ↓
.local/transient/package-build/<package_id>/
        ↓
sgokb-package stage <build-directory>
        ↓
exchange/staging/<package_id>/
        ↓ preflight
sgokb-package export ... --destination <Drive sync root>
        ↓ Human / External
Google Drive → ChatGPT → result.json
        ↓ Human return
exchange/incoming/drop/<package_id>/result.json
        ↓
sgokb-package detect
        ↓
sgokb-package receive ... --package-id <package_id>
        ↓
exchange/incoming/received/<package_id>/<receipt_id>/result.json
        ↓
validation_state = pending
        ↓
Phase H / H-01
```

Google Drive API / OpenAI APIはこの標準flowに必須ではない。

---

## 3. Build / staging / export boundary

3つのfile lifecycleを混同しない。

### Build workspace

```text
.local/transient/package-build/<package_id>/
```

canonical DBから再生成可能なlocal transient artifact。

### Finalized staging Package

```text
exchange/staging/<package_id>/
```

G-04 integrity / security checkを通過したimmutable exchange artifact。

### External exported Package

```text
<explicit destination>/<package_id>/
```

Google Drive同期directory等。ここへのwriteがexternal egress boundaryである。

Resultはexport済みPackage directoryへ追加しない。

---

## 4. Update Package closure

current accepted VersionがあるObjectについてPackage Builderは次を行う。

1. current Version IDを`base_version_id`として固定する。
2. canonical DBから`current_object.json`を再serializationする。
3. current Versionの全`evidence_links`からcarry-forward Evidence IDを収集する。
4. carry-forward EvidenceをF-03通常effective scope外であってもmanual/system protected candidateとして取得する。
5. manual includeと合わせてF-04 protected setへ渡す。
6. protected Evidenceがbudgetへ収まらない場合はsilent omissionせずbuild errorとする。
7. 新しいeffective Evidenceを通常retrieval / diversity / relevance順で追加する。
8. manifest上で`carry_forward` roleと`selected_by=protected`を追跡する。

このため、過去Snapshotへgroundingされたcurrent Knowledgeを、新Snapshot追加だけを理由に根拠なしで再生成しない。

---

## 5. Phase G test surface

Phase G終了時点で少なくとも次のfocused testが存在する。

- `tests/test_package_manifest.py`
- `tests/test_object_analysis_instructions.py`
- `tests/test_package_transfer.py`
- `tests/test_result_receipt.py`
- `tests/test_phase_g_roundtrip.py`

`test_phase_g_roundtrip.py`はPhase G completion conditionをlocal sideから直接表現する。

```text
Object/Evidence
 → Package build
 → stage
 → explicit filesystem export
 → simulated returned result.json
 → immutable receipt
 → pending validation
```

ここではChatGPT生成内容の意味品質やH-01 Validation成功まではPhase Gの責務に含めない。

---

## 6. Phase H task inventory

Phase Hは4 Taskで構成する。

### H-01 [P0] Result JSON Validator

Syntax / Schema、Binding / Precondition、Referential、Grounding / Provenance、Domain Contract Validationを分離する。

### H-02 [P0] Object Version Import

H-01成功Resultのみをexplicit Import operationでcandidate Versionへ変換し、transaction-safeにaccepted/currentへ昇格する。

### H-03 [P1] Markdown Renderer

canonical DB / Versionから人間向けMarkdownを生成する。Markdownを編集正本にしない。

### H-04 [P1] Diff / Review

current→candidate差分、stale / partial / destructive omission / Registry proposal等を可視化する。

Phase H完了条件:

> ChatGPT出力を壊れた状態で正本DBへ登録できず、過去versionへ戻れる。

---

## 7. H-01 Definition of Ready

H-01に必要な前提はPhase G終了時点で揃っている。

### Result artifact

G-05:

```text
package_result_receipts
validation_state = pending
storage_ref = received/.../result.json
result_sha256
```

H-01はreceiptのimmutable raw bytesを入力にする。

### Canonical structure Schema

E-05:

```text
src/sgokb/exchange/schemas/object-result-v1.schema.json
```

### Runtime Object Result Contract

E-05:

```text
ObjectResultContract
validate_object_result()
collect_evidence_ids()
```

### Package binding authority

G-02 / G-04 audit:

```text
package_id
package schema version
manifest_sha256
package_created_at
base_version_id
included Evidence IDs
```

### Source / Evidence validation primitive

E-03:

```text
validate_evidence_references(..., package_evidence_ids=...)
evidence_provenance()
```

### Current Version stale precondition

E-04:

```text
VersionRepository.current_version_id()
base_version_id
```

したがってH-01で新しい交換Schemaを作り直す必要はない。

---

## 8. H-01 implementation boundary

H-01は次の順序でValidation layerを分離する。

```text
1. Artifact / Syntax
   - receipt file存在
   - receipt SHA-256一致
   - UTF-8 / JSON object

2. Static Schema
   - sgokb.object-result/1.0
   - unknown field reject

3. Package Binding / Preconditions
   - package_id
   - package schema version
   - manifest_sha256
   - package_created_at
   - base_version_id
   - target Object / Classification
   - current Version stale check

4. Referential
   - Object / Class
   - Facet
   - Attribute Definition
   - Relation Type
   - Relation target Object

5. Grounding / Provenance
   - Evidence存在
   - Package membership
   - Evidence → Run → Snapshot → Source provenance

6. Domain Contract
   - effective Facet full-snapshot coverage
   - Attribute type
   - Relation endpoint
   - local reference consistency
   - partial / insufficient gap requirement
```

Validatorは未知IDや壊れたfieldを推測修復しない。

---

## 9. H-01 output / receipt state contract

H-01はValidation Reportを生成し、receiptの状態を少なくとも次へ遷移できるようにする。

```text
pending
  → running
  → valid
     invalid
     error
```

`valid`はauthoritative Importを意味しない。

```text
valid receipt
  != accepted Knowledge Version
```

H-02のexplicit Import操作までVersion ID発行 / current切替を行わない。

---

## 10. H-01で先取りしないもの

次はH-01へ混ぜない。

- AI出力の意味的真偽判定
- 自動修正文生成
- Version ID発行
- candidate / accepted Version write
- Registry proposal自動適用
- Diff UI
- Markdown rendering
- Embedding / Vector Index更新

H-01はdeterministic validatorとして維持する。

---

## 11. Phase H進行状況

Phase Gの個別Task G-01〜G-05は完了している。

H-01では`ResultValidationService`、Migration 012、`sgokb-package validate-result`、focused testを追加し、G-05 immutable receiptからdeterministic Validation Reportを生成できるようにした。

ValidationはArtifact / Syntax、Static Schema、Binding / Precondition、Referential、Grounding / Provenance、Domain Contractの6層へ分離した。`valid`はauthoritative Importを意味せず、Version作成・current切替は行わない。

H-01正本:

- `docs/design/RESULT_VALIDATION.md`
- `src/sgokb/exchange/result_validation.py`
- `src/sgokb/migrations/012_result_validation.sql`
- `tests/test_result_validation.py`

H-02では`ObjectVersionImportService`、`ResultImportRepository`、Migration 013、`sgokb-package import-result`を追加した。H-01 valid receiptだけを入力とし、Version ID発行、canonical Knowledge / Evidence Link / attribution / Result metadata保存、accepted/current promotion、derived pending化を1 SQLite transactionで実行する。

H-02正本:

- `docs/design/OBJECT_VERSION_IMPORT.md`
- `src/sgokb/exchange/result_import.py`
- `src/sgokb/storage/result_import_repository.py`
- `src/sgokb/migrations/013_object_version_import.sql`
- `tests/test_object_version_import.py`

次に実施するTask:

```text
H-03 [P1] Markdown Rendererを実装する
```
