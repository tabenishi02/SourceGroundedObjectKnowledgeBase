# Source Grounded Object Knowledge Base — Result Validation

更新日: 2026-10-13

- Task: `H-01 [P0] Result JSON Validatorを実装する`
- Status: Complete
- Parent: Phase H — Result Validation / Import / Rendering
- Input authority: G-05 immutable Result receipt
- Static Schema authority: `src/sgokb/exchange/schemas/object-result-v1.schema.json`
- Implementation: `src/sgokb/exchange/result_validation.py`
- Audit persistence: Migration 012 / `package_result_receipts`
- CLI: `sgokb-package validate-result`
- Tests: `tests/test_result_validation.py`
- Follow-up: H-02 Object Version Import

---

## 1. 目的

H-01は、ChatGPT等から返却された`result.json`を、canonical KnowledgeへImportする前にdeterministicに検証する。

最重要境界:

```text
Result received
  != Result valid
  != Knowledge imported
```

H-01が`valid`を返しても、Version ID発行、candidate作成、accepted/current切替は行わない。
H-02のexplicit Import operationだけがcanonical Knowledgeを書き換えられる。

---

## 2. 入力

標準入力はG-05が保存したimmutable receiptである。

```text
package_result_receipts
  id
  package_id
  result_sha256
  byte_count
  storage_ref
  validation_state
```

Validatorはユーザーが指定した任意JSONを直接canonical Import入力として扱わない。
receiptの監査情報と保存済みraw bytesを再照合する。

---

## 3. Validation layer

H-01は次の6層を分離する。

```text
1. artifact_syntax
2. static_schema
3. binding_precondition
4. referential
5. grounding_provenance
6. domain_contract
```

各findingは次を保持する。

```text
stage
path
code
message
severity = error | review
```

`error`が1件でもあれば`invalid`となる。
`review`だけの場合はSchema/contract上は`valid`だが、H-02/H-04で明示レビュー対象として扱える。

---

## 4. Artifact / Syntax

検証対象:

- receipt `storage_ref`がincoming root外へescapeしない。
- exact `result.json`である。
- regular fileでありsymlinkではない。
- byte countがreceipt auditと一致する。
- SHA-256がreceipt auditと一致する。
- UTF-8である。
- JSONとしてparseできる。
- top-levelがJSON objectである。

receipt file欠落、hash不一致等、信頼できる検証入力を再構築できない場合は`validation_state=error`とする。
malformed UTF-8 / JSON等、返却Result自体の不正は`invalid`とする。

---

## 5. Static Schema

E-05 canonical Schemaをそのまま利用する。

```text
sgokb.object-result/1.0
```

検証対象:

- required field
- type / enum / format
- unknown field reject
- unsupported schema version reject
- conditional structure
- reported-view attribution shape
- Result status / gap shape
- Facet / Attribute / Relation wire shape

H-01実装時に、`date_or_datetime`が設計上「dateまたはdate-time」であるにもかかわらず、JSON Schemaの`oneOf`では利用中FormatCheckerによりdate-only値が両branchへmatchするケースを確認した。
設計意図に合わせて`anyOf`へ修正した。

---

## 6. Package Binding / Preconditions

ResultをG-04/G-05のaudited Packageへ厳密にbindする。

比較対象:

- Result schema version
- target Object ID
- Primary Class
- Additional Classes
- package ID
- package schema version
- manifest SHA-256
- package created_at
- base Version ID
- instructions version

さらに、local staged Package manifestを再読込し、canonical Package Schemaとmanifest hashを再検証する。

current canonical stateについて次を確認する。

- target Objectが存在しactiveである。
- Package時点Classificationが現在のObject Classificationと一致する。
- Package `base_version_id`が現在の`current_version_id`と一致する。
- base Versionが存在し、同一Objectのaccepted Versionである。

currentが変化したResultを別Packageへ推測rebindしない。
stale Resultは`invalid`とする。

---

## 7. Referential Validation

canonical Registry / Object / Sourceの存在を確認する。

対象:

- target Primary / Additional Class
- Facet
- Attribute Definition
- Relation Type
- Relation subject / object Object
- reported-view attribution Object / Source
- temporal scope context Object
- GapのFacet / Attribute参照
- unresolved reference candidate Class
- unresolved relation context Relation Type
- Class extension Class
- existing-Class Registry proposal参照

Relation endpointに未知Object IDがある場合、ValidatorはObjectを作成しない。
未登録ObjectはResult生成側で`unresolved_references`として表現する。

---

## 8. Grounding / Provenance Validation

Result内の全Evidence参照を収集し、次を検証する。

- Evidence IDがcanonical DBに存在する。
- Evidence IDがaudited Package membershipに含まれる。
- Evidence → Normalization Run → Snapshot → Raw Artifact → Sourceのprovenance chainが成立する。
- Package manifestのEvidence provenance metadataとcanonical DBが一致する。
- Evidence roleがactive vocabularyである。

Package外Evidenceがcanonical DBに実在していても、当該Resultから参照することは許可しない。

---

## 9. Domain Contract Validation

H-01はcanonical Registryからruntime `ObjectResultContract`を構築し、E-05 `validate_object_result()`を再利用する。

対象:

- effective Facet full-snapshot coverage
- Facetの重複 / 欠落
- Attribute ID / value type
- Relation Type
- target ObjectがRelation endpointに含まれること
- local key uniqueness
- conflict local reference consistency
- Class extension contract
- temporal `valid_from <= valid_to`
- Registry proposal payloadの最低限contract

Registry proposal payloadの初期最低限contract:

```text
object_name / object_alias
  payload.value: non-empty string

primary_class / additional_class
  payload.class_id: non-empty existing active Class ID

new_class / new_facet / new_attribute / new_relation_type
  payload.key: non-empty string
  payload.name: non-empty string

new_attribute
  payload.value_type: supported Attribute value type

new_class
  payload.assignment_policy: 指定時は既存enum
```

`payload`自体はE-05どおりopen objectのままとし、未知追加fieldをoperationとして実行しない。
Registry proposalをH-01の副作用としてRegistryへ適用しない。

---

## 10. Review findings

次は構造上validでもreview findingを付与する。

- `result_status = partial`
- `result_status = insufficient_evidence`
- Registry proposalあり
- unresolved referenceあり
- identity ambiguity gapあり
- Package export auditなし

このreview findingは`valid`と`accepted Knowledge`を区別するための補助情報である。
H-02/H-04がreview policyを扱う。

---

## 11. Receipt state / persistence

Migration 012でreceiptへ次を追加する。

```text
validation_started_at
validation_completed_at
validation_findings_json
```

状態遷移:

```text
pending
  ↓
running
  ↓
valid | invalid | error
```

同一receiptを通常再実行した場合、terminal reportを返してidempotentに扱う。
明示`--force`時のみ再検証できる。

---

## 12. CLI

1件のreceiptを検証する。

```text
sgokb-package validate-result <receipt_id>
```

incoming rootを変更する場合:

```text
sgokb-package validate-result <receipt_id> --incoming-root <path>
```

terminal receiptを明示的に再検証する場合:

```text
sgokb-package validate-result <receipt_id> --force
```

`valid`以外はCLI exit code 1とする。

---

## 13. H-01で行わないこと

- semantic truth判定
- Evidence読解の妥当性判定
- AIによる自動修正
- unknown IDの推測修復
- Persistent Version ID発行
- candidate / accepted Version作成
- current Version切替
- Registry proposal自動適用
- Markdown rendering
- Diff UI
- Embedding / Index更新

---

## 14. 完了条件

H-01は次を満たしたためCompleteとする。

1. immutable Result receiptを検証入力とした。
2. 6つのValidation layerを分離した。
3. Package / Object / base Version preconditionを検証した。
4. Registry / Relation endpoint / attribution / temporal contextをreferential検証した。
5. Evidence existence / Package membership / provenanceを検証した。
6. E-05 runtime contractをcanonical Registryから構築した。
7. malformed / stale / Package外Evidence等をcanonical Import前に拒否できる。
8. review-required条件をerrorと分離して記録できる。
9. Validation reportをreceipt auditへ永続化した。
10. Validation成功だけではObject Versionを作成しないことをテストで固定した。

次Task:

```text
H-02 [P0] Object Version Importを実装する
```
