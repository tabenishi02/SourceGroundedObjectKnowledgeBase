# Source Grounded Object Knowledge Base — Phase G Completion

更新日: 2026-10-13

- Phase: `G — Google Drive / ChatGPT交換ワークフロー`
- Status: **Complete**
- Branch: `integration/knowledge-base-redesign`
- Next phase: `H — Result Validation / Import / Rendering`
- Next task: `H-01 [P0] Result JSON Validatorを実装する`
- Phase H preparation: `docs/planning/PHASE_H_PREPARATION.md`

## 1. 完了判定

Phase Gの完了条件は次である。

> APIを利用せず、ユーザーがChatGPTとの手動工程を介して1 Objectを往復できる。

G-01〜G-05の成果物と実装を再監査した結果、個別Taskはすべて完了していたが、canonical DBからObject Evidence Package workspaceを生成する接続処理が欠けていた。

Phase G closureとして`ObjectEvidencePackageBuilder`を追加し、次のlocal workflowを接続した。

```text
Canonical Object / Source / Evidence
  -> Package build
  -> local staging
  -> explicit external export
  -> Google Drive / ChatGPT manual step
  -> result.json return
  -> immutable local receipt
  -> pending H-01 validation
```

このclosureにより、Package fileを人間が手作業で構成する必要はなくなった。

## 2. Task status

- [x] **G-01 [P0] Object Evidence Package formatを確定する**
  - Authority: `docs/design/OBJECT_EVIDENCE_PACKAGE_FORMAT.md`
  - Closure implementation: `src/sgokb/exchange/package_builder.py`
  - current Versionがある場合、`current_object.json`とcarry-forward Evidenceを生成する。

- [x] **G-02 [P0] `manifest.json` schemaを定義する**
  - Authority: `docs/design/OBJECT_EVIDENCE_PACKAGE_MANIFEST_SCHEMA.md`
  - Schema: `src/sgokb/exchange/schemas/object-evidence-package-v1.schema.json`
  - Runtime: `src/sgokb/exchange/package_manifest.py`

- [x] **G-03 [P0] ChatGPT用`instructions.md`を設計する**
  - Authority: `docs/design/OBJECT_ANALYSIS_INSTRUCTIONS.md`
  - Runtime: `src/sgokb/exchange/instructions.py`
  - Template: `src/sgokb/prompts/object_analysis.md`
  - Version: `sgokb.object-analysis/1.0`

- [x] **G-04 [P0] Local Package staging / Google Drive export方式を実装する**
  - Authority: `docs/design/PACKAGE_STAGING_DRIVE_EXPORT.md`
  - Runtime: `src/sgokb/exchange/package_transfer.py`
  - Audit: Migration 010 / `PackageExchangeAuditRepository`
  - Initial standardはGoogle Drive APIではなく明示filesystem exportを使用する。

- [x] **G-05 [P1] Result受け取り運用を定義する**
  - Authority: `docs/design/RESULT_RECEIPT_WORKFLOW.md`
  - Runtime: `src/sgokb/exchange/result_receipt.py`
  - Audit: Migration 011 `package_result_receipts`
  - Result receiptはValidation / Importと分離する。

## 3. Phase G closure implementation

追加した主要成果物:

```text
src/sgokb/exchange/package_builder.py
src/sgokb/storage/package_repository.py
tests/test_phase_g_roundtrip.py
docs/planning/PHASE_G_COMPLETION.md
docs/planning/PHASE_H_PREPARATION.md
```

`sgokb-package`には次の一連の操作が存在する。

```text
build
stage
preflight
export
detect
receive
receipts
pending-validation
```

## 4. Version contract synchronization

E-05時点のtest fixtureに残っていた暫定値をPhase Gの正式contractへ同期した。

```text
Package schema:
  sgokb.object-evidence-package/1.0

Instructions version:
  sgokb.object-analysis/1.0
```

`tests/test_object_result_schema.py`は`PACKAGE_SCHEMA_VERSION` / `INSTRUCTIONS_VERSION`を参照するよう更新し、今後のversion driftを抑制した。

## 5. Verification surface

Phase G関連test:

```text
tests/test_package_manifest.py
tests/test_object_analysis_instructions.py
tests/test_package_transfer.py
tests/test_result_receipt.py
tests/test_phase_g_roundtrip.py
```

`test_phase_g_roundtrip.py`は、initial Objectについてbuild → stage → export → Result receiptまでを接続し、receipt後もObject Versionが自動作成されないことを確認する。

update Objectについては、current accepted Versionを`current_object.json`へserializationし、historical grounding Evidenceが`carry_forward` / `protected`としてPackage membershipへ残ることを確認する。

なお、本会話環境ではrepository test suiteの実行環境を利用できていないため、追加testの実行結果そのものは未確認である。Phase H実装時または利用可能なCI/local環境で実行確認する。

## 6. Phase H handoff

Phase G終了状態ではResult receiptが次の状態でH-01へ渡る。

```text
immutable received result.json
result_sha256
package_id
parsed routing metadata
validation_state = pending
```

H-01はこのreceiptを入力とし、Syntax / Schema / Binding / Referential / Grounding / Provenance / Domain Contractをdeterministicに検証する。

`valid`判定だけでauthoritative Importを行わない。Version生成・current切替はH-02のexplicit Import boundaryに残す。

Phase H開始条件は満たしている。
