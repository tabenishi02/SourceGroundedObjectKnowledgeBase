# Source Grounded Object Knowledge Base — Phase H Closure Audit

更新日: 2026-10-13

- Phase: Phase H — Result Validation / Import / Rendering
- Status: Complete
- Integration baseline: `8c976fe H-04: Implement Diff / Review`
- Next phase: Phase I — 意味検索・類似検索
- Next task: `I-01 [P0] Search Representation / Embedding対象を設計する`

---

## 1. 監査目的

Phase HのTask master、実装、設計書、テストを横断確認し、未完了TaskやPhase完了条件の抜けが残っていないことを確認する。

Phase Hの完了条件は次である。

> ChatGPT出力を壊れた状態で正本DBへ登録できず、過去Versionへ戻れる。

---

## 2. Task status

| Task | Status | 主な成果物 |
|---|---|---|
| H-01 Result JSON Validator | Complete | `docs/design/RESULT_VALIDATION.md`, `src/sgokb/exchange/result_validation.py`, Migration 012 |
| H-02 Object Version Import | Complete | `docs/design/OBJECT_VERSION_IMPORT.md`, `src/sgokb/exchange/result_import.py`, `src/sgokb/storage/result_import_repository.py`, Migration 013 |
| H-03 Markdown Renderer | Complete | `docs/design/MARKDOWN_RENDERER.md`, `src/sgokb/rendering/markdown.py`, `src/sgokb/storage/markdown_repository.py` |
| H-04 Diff / Review | Complete | `docs/design/DIFF_REVIEW.md`, `src/sgokb/review/diff.py`, `src/sgokb/review/markdown.py` |

Task master上のH-01〜H-04はすべて`[x]`であり、Phase H内に未完了Taskはない。

---

## 3. 完了条件監査

### 3.1 壊れたResultを正本DBへ登録できない

H-01はResultを以下の層へ分離してValidationする。

1. Artifact / Syntax
2. Static Schema
3. Binding / Precondition
4. Referential
5. Grounding / Provenance
6. Domain Contract

H-02は`validation_state = valid`のimmutable receiptだけをImport対象にする。

さらにImport直前にH-04 Reviewを再計算し、stale / destructive omission / partial / Registry proposal / Identity ambiguity等のReview Required状態を確認する。

`blocked`はImport不可、`review_required`は`--acknowledge-review`なしではImport不可とする。

Import transaction内でもcurrent Version / classification / Facet contract等のstale preconditionを再確認するため、Validation後にcanonical状態が変わった場合もsilent overwriteしない。

### 3.2 incomplete Versionをcurrentへ昇格させない

H-02では以下を1 SQLite transactionとして実行する。

```text
candidate Version作成
  ↓
canonical Knowledge保存
  ↓
Evidence Link / attribution / Result metadata保存
  ↓
Import audit保存
  ↓
accepted transition
  ↓
current_version切替
  ↓
derived state pending化
```

途中失敗時はtransaction rollbackし、incomplete candidateをcurrentへ昇格させない。

同一receipt / Result hashのretryはidempotentに既存Importへ収束する。

### 3.3 accepted Versionを後から破壊できない

Versioning schema / DB triggerにより、accepted / abandoned等のterminal Version contentおよびEvidence Linkはimmutableである。

修正は既存Version上書きではなく、新Versionとして行う。

### 3.4 過去Versionへ戻れる

`VersionRepository.rollback_current(object_id, target_version_id)`により、同一Objectのaccepted historical Versionへcurrent pointerを戻せる。

rollbackはhistorical Version自体を変更せず、current pointerだけを変更する。

rollback後はSearch Representation / Embedding / Vector Index / Rendering等のderived stateを対象Versionへ`pending`として再同期できる。

`tests/test_versioning.py::test_rollback_moves_only_current_pointer_and_new_version_can_branch_from_old_base`で、

- v1→v2→v3作成
- v1へrollback
- 全Versionがacceptedのまま保持
- rollback後のv1をbaseに新Versionをbranch可能

を検証済みである。

### 3.5 Markdownを正本へ逆流させない

H-03のMarkdownはaccepted Versionから再生成するderived read-only artifactであり、編集したMarkdownをparseして正本へ戻さない。

historical render / JSON pure renderもcanonical Knowledgeを変更しない。

### 3.6 full snapshotによるsilent data lossを防ぐ

H-04はbase Versionとcandidate Resultを比較し、少なくとも以下をdestructive omissionとして表示する。

- Statement削除
- known Attribute削除
- Relation削除
- `content` Facetのdowngrade /削除
- Conflict消失
- Registry proposal消失

これらはReview Requiredとなり、H-02 Importへ明示acknowledgementを要求する。

---

## 4. テスト監査

H-04完了時点の統合確認:

```text
H-01〜H-04 + Versioning / Upgrade regression
104 passed

Full suite
239 passed / 1 failed
```

唯一の失敗:

```text
tests/test_package_transfer.py::test_stage_rejects_unexpected_files_and_hash_mismatch
```

期待値は`SHA-256 mismatch`だが、実装は先に`Package file size mismatch`を報告する。

この失敗はH-01以前から再現するPhase G系の既知テスト契約差であり、Phase HのResult Validation / Import / Rendering / Review機能の失敗ではない。

既知1件を除外した統合後確認:

```text
239 passed, 1 deselected
```

変更ファイルRuff、compile、`git diff --check`も成功済みである。

---

## 5. Phase Hで追加Migrationが不要だった項目

H-04は新規Migrationを追加していない。

理由:

- immutable Result receiptはPhase G / H-01に存在する。
- Validation findingsはMigration 012で保存済み。
- Import provenance / review acknowledgement / Result metadataはMigration 013で保存済み。
- accepted Versionはcanonical DBから再読込可能。
- Diff / Reviewはこれらから決定論的に再計算できるread-only derived viewである。

H-04専用approval tableを追加せず、authoritative actionであるH-02 Import時の`review_acknowledged`を監査値とした。

---

## 6. Phase H closure judgment

Phase Hの個別Task H-01〜H-04はすべて完了している。

Phase完了条件についても、

- invalid / stale ResultのImport拒否
- review-required Resultの明示承認
- atomic / idempotent Import
- accepted Version immutability
- historical Version rollback
- derived Markdownの非正本化
- destructive omissionのReview gate

を満たしている。

したがってPhase Hを**Complete**としてcloseする。

---

## 7. Phase Iへの引き継ぎ

Phase Hが提供するPhase Iの入力境界は次である。

```text
accepted Object Knowledge Version
  ↓
current / historical scope
  ↓
Summary / Facet / Statement / Attribute / Relation
  ↓
Evidence grounding
  ↓
object_derived_states.search_representation / embedding / vector_index = pending
  ↓
Phase I
```

Phase Iはcanonical Knowledgeを変更せず、Search Representation / Embedding / Vector Indexを再構築可能なderived layerとして実装する。

次の作業は`docs/planning/PHASE_I_PREPARATION.md`を基準に`I-01 [P0] Search Representation / Embedding対象を設計する`から開始する。
