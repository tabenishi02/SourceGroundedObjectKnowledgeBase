# Source Grounded Object Knowledge Base — Diff / Review

更新日: 2026-10-13

- Task: `H-04 [P1] Diff / Review表示を実装する`
- Status: Complete
- Parent: Phase H — Result Validation / Import / Rendering
- Validation authority: `docs/design/RESULT_VALIDATION.md`
- Import authority: `docs/design/OBJECT_VERSION_IMPORT.md`
- Version authority: `docs/design/VERSIONING_SCHEMA.md`
- Renderer authority: `docs/design/MARKDOWN_RENDERER.md`
- Implementation:
  - `src/sgokb/review/diff.py`
  - `src/sgokb/review/markdown.py`
  - `src/sgokb/exchange/result_import.py`
- CLI:
  - `sgokb-package review-result`
  - `sgokb-package diff-versions`
- Tests: `tests/test_diff_review.py`
- Follow-up: Phase I / I-01 Search Representation / Embedding対象設計

---

## 1. 目的

H-04は、Object Resultをauthoritative Importする前に、既存canonical Knowledgeとの差分と人間が確認すべき理由を可視化する。

また、Import後のaccepted Version同士についても同じ意味比較を利用し、historical Diffを生成する。

H-04の基本原則:

> **Diff / Reviewはcanonical Knowledgeではなく、正本変更前後の判断を支援するread-only derived viewである。**

H-04は次を行わない。

- Result Import
- Result approval / rejectionのcanonical記録
- stale Resultのrebase / merge
- Registry proposal適用
- Object Identity解決
- accepted Versionの書換え
- Diff自体のcanonical delta保存

---

## 2. H-02との境界

H-02は、明示Import開始後にcandidate作成からaccepted/current promotionまでを1 SQLite transactionで完了する。

そのため、H-04のために長寿命のpersisted candidate Versionを追加しない。

Import前Reviewは次の比較とする。

```text
immutable Result receipt
        +
Result binding.base_version_id
        ↓
H-04 Result candidate projection
        ↓
Diff(base accepted Version, candidate Result)
        ↓
Review reasons
        ↓
Human decision
  ├─ regenerate / do not import
  └─ explicit H-02 Import
```

Import後は、任意のaccepted Version同士を直接比較する。

```text
accepted v1
   vs
accepted v2
   ↓
Historical Diff
```

---

## 3. Review surface

H-04は2種類のsurfaceを持つ。

### 3.1 Result Review Preview

CLI:

```text
sgokb-package review-result <receipt_id>
```

人間向けMarkdown:

```text
sgokb-package review-result <receipt_id> --format markdown
```

入力はG-05 immutable Result receiptであり、H-01 Validation完了後に利用する。

表示する主要情報:

- receipt / Package / Object identity
- H-01 validation state
- Result status
- base Version
- canonical current Version
- H-01 validation / review findings
- H-04 destructive omission finding
- conflict attention
- base → candidate full-snapshot Diff
- Import済みの場合のVersion ID / review acknowledgement

### 3.2 Historical Version Diff

CLI:

```text
sgokb-package diff-versions <before_version_id> <after_version_id>
```

Markdown:

```text
sgokb-package diff-versions <before_version_id> <after_version_id> --format markdown
```

両Versionは同一Objectに属するaccepted Versionでなければならない。

Historical Diffはcurrent pointerを変更しない。

---

## 4. Structured report

Result Reviewは、表示形式と判定材料を分離するためstructured reportを先に生成する。

```text
sgokb.result-review/1.0
```

主要field:

```text
receipt_id
package_id
object_id
validation_state
review_state
base_version_id
current_version_id
result_status
result_sha256
reasons[]
diff
imported_version_id
review_acknowledged
```

Object Diff:

```text
sgokb.object-diff/1.0
```

主要field:

```text
object_id
before_version_id
after_version_id
after_kind
changes
  summary_statements
  facets
  attributes
  relations
  review_metadata
    conflicts
    gaps
    unresolved_references
    registry_proposals
destructive_omissions
```

JSONは機械利用可能なReview materialであり、canonical Knowledgeそのものではない。

---

## 5. Version / Result projection

accepted Version側はH-03の`MarkdownRenderReadRepository`を再利用する。

これにより、H-03とH-04で別々のcanonical read SQLを重複実装しない。

Result側はimmutable Result artifactから、比較に必要なpresentation-independent candidate modelへ投影する。

Candidate modelはDB Version IDを持たない。

```text
result target        -> object identity
result binding       -> base Version
result knowledge     -> summary / facets / attributes / relations
result review fields -> conflict / gap / unresolved / proposal
```

Result candidate modelをcanonical DBへinsertしてからDiffする方式は採用しない。

---

## 6. Immutable Result loader共有

H-04がH-02のprivate methodへ依存しないよう、Result artifact読み込み契約を次へ切り出した。

```text
load_immutable_result_artifact()
```

H-02 ImporterとH-04 Reviewが同じ処理を利用する。

確認項目:

- receipt `storage_ref`がincoming root relative pathである。
- path traversalを許可しない。
- exact `result.json` regular fileである。
- receipt byte countと一致する。
- receipt SHA-256と一致する。
- UTF-8 JSON objectとしてparseできる。

Review用だからといって、Validation / Importとは別の緩いartifact loaderを作らない。

---

## 7. Diffはsemantic snapshot comparison

E-04の原則どおり、Diffをcanonical deltaとして保存しない。

```text
Diff(A, B)
  = immutable full snapshot A と full snapshot B の派生比較
```

Statement DB row ID等のruntime IDをVersion間semantic identityとはみなさない。

Diff change type:

```text
added
removed
modified
```

Facetでは追加で、status変化と内部Statement差分を表示する。

---

## 8. Statement対応付け

StatementはまずResult / Version内の`local_key`が双方に一意なら対応付ける。

```text
same local_key
  + same semantics    -> unchanged
  + changed semantics -> modified
```

ただしB-04 / E-04ではStatement local keyを永続Global Identityとしていない。

したがってlocal keyが変化していても、次のsemantic fingerprintが完全一致する場合は同一内容としてpairingし、偽のremove + addを抑制する。

Fingerprint対象:

- text
- derivation kind
- language
- temporal scope
- attribution
- Evidence ID / role集合

完全一致しない類似文をheuristicで同一Statementと推測しない。

---

## 9. Attribute対応付け

Attributeは次で対応付ける。

```text
attribute_id + ordinal
```

H-02 canonical storageは同一Attribute IDの複数値へordinalを持つ。

Result JSONにordinalはないため、candidate投影ではResult配列順にAttribute IDごとのordinalを決定する。

比較semantic:

- attribute ID
- ordinal
- status
- typed value
- language
- temporal scope
- Evidence ID / role

DB row IDは比較しない。

---

## 10. Relation対応付け

Relationは初期H-04では次のedge identityで対応付ける。

```text
subject_object_id
relation_type_id
object_object_id
```

同一edgeでtemporal scopeまたはEvidence groundingが変化した場合は`modified`とする。

Relation DB row IDはVersion間identityに利用しない。

同じendpoint/typeの複数Relationを将来別edgeとして区別する必要が出た場合は、Relation semantic identity設計を拡張する。

---

## 11. Facet Diff

Facetは`facet_id`で対応付ける。

比較対象:

- Facet存在
- Facet status
- Facet内部Statement

特に、

```text
content -> insufficient_evidence
content -> not_analyzed
content -> not_applicable
```

のように`content`から非contentへ変化する場合、単なるstatus変更に加えてdestructive omissionとして表示する。

Facet行そのものが消えた場合もdestructiveとする。

通常H-01 Facet contract validationがFacet全件を要求するため、Result candidateではFacet行欠落はValidation errorになり得るが、Historical Diffでは欠落状態も表示可能である。

---

## 12. Review metadata Diff

H-02でVersionに保持した次のResult metadataもDiffする。

```text
conflicts
gaps
unresolved_references
registry_proposals
```

local keyが一意ならlocal keyで対応付け、完全semantic一致fallbackも利用する。

`class_extensions`はH-04初期Diffの主要review対象には含めない。H-03では表示可能であり、必要性が判明した場合にH-04へ追加できる。

---

## 13. Destructive omission

full snapshot方式では「次Resultにない」ことが新Versionでcarry forwardしないことを意味する。

H-04は、次を**destructive omission**として機械的に強調する。

- summary Statement削除
- Facet Statement削除
- Attribute削除
- Relation削除
- Facet削除
- `content` Facetの非contentへのdowngrade
- unresolved Conflict recordの削除
- pending Registry proposalの削除

これらを「AIが解決した」「不要になった」と自動推測しない。

### Gap / unresolved reference削除

Gapやunresolved reference自体は、次回分析で解決されることが正常にあり得るため、削除しただけでは初期H-04のdestructive omission reasonへ昇格しない。

ただしDiffにはremoveとして表示する。

必要に応じて将来、解決provenanceやresolution workflowを追加する。

---

## 14. Large Diff thresholdを導入しない

B-06はlarge Diffをreview-required候補に挙げているが、exact thresholdは後続設計へ延期している。

H-04では、

```text
変更数 > N
変更率 > X%
```

のような任意thresholdを新規に決めない。

初期実装は意味が明確な構造変化、特にdestructive omissionをreview reasonとする。

実運用dataから適切なthresholdが得られた場合に追加する。

---

## 15. Review reason severity

H-04はreasonを次の3段階で表示する。

### `blocked`

通常Importしてはならない状態。

主にH-01 error findingを引き継ぐ。

例:

- stale base Version
- binding mismatch
- referential failure
- Evidence provenance failure
- schema error

H-04がこれらをoverrideしてImport可能にしない。

### `review`

Validation上はImport可能でも、人間が明示確認すべき状態。

例:

- partial / insufficient Result
- Registry proposal
- unresolved reference
- identity ambiguity
- export audit warning
- destructive omission

H-02 Importでは`--acknowledge-review`が必要となる。

### `attention`

目立たせるが、それ単独ではreview-requiredへ昇格しない情報。

初期例:

- grounded Conflictが存在する。

Conflictを保持できること自体がSGOKBの機能であるため、Conflict存在だけをImport失敗にしない。

---

## 16. H-01 finding再利用

H-04独自にH-01 validation ruleを再実装しない。

receiptに保存されたH-01 findingsをそのままreview reasonへ投影する。

```text
H-01 severity=error
  -> H-04 blocked reason

H-01 severity=review
  -> H-04 review reason
```

H-04固有reasonは現在、

```text
destructive_omission
conflicts_present
```

を追加する。

これによりH-01とH-04の同じstale / proposal / ambiguityルールが分岐しない。

---

## 17. Review state

Result review surfaceの表示stateを次とする。

```text
H-01 pending / running
  -> validation_required
     H-04 review commandは開始しない

H-01 invalid / error
  -> blocked

H-01 valid
  + review reasonなし
  -> ready_to_import

H-01 valid
  + review reasonあり
  -> review_required

H-02 Import commit済み
  -> imported
```

`attention`だけでは`review_required`にしない。

CLI `review-result`はH-01 pending / runningの場合、completed H-01 Validationを要求して停止する。

---

## 18. 手動承認の状態遷移

H-04専用のpersistent `approved` flagやReview tableは追加しない。

既存H-02の明示Import operationを承認境界として利用する。

### normal Result

```text
ready_to_import
  ↓ human: import-result
H-02 atomic Import
  ↓
imported
```

### review-required Result

```text
review_required
  ↓ human reviews H-04 output
  ├─ regenerate / do not import
  │     -> canonical DB unchanged
  │
  └─ accept
        ↓
      import-result --acknowledge-review
        ↓
      H-02 atomic Import
        ↓
      imported (review_acknowledged = 1)
```

この方式により、Review承認だけが孤立して保存され、その後Result/currentが変化するTOCTOU状態を増やさない。

`ObjectVersionImportService.import_receipt()`はImport直前にH-04 Reviewを再計算する。

そのためH-01由来のreview findingだけでなく、H-04で新たに検出された`destructive_omission`も`--acknowledge-review`なしではImportできない。

その後、H-02 Import transactionがcurrent / Classification / Facet contract等のstale preconditionをもう一度再確認する。

---

## 19. stale Result

stale ResultはH-01でValidation errorとなり、H-04では`blocked`として表示する。

一方、artifact自体がparse可能でbase Versionが残っている場合は、

```text
base Version -> stale candidate Result
```

のDiffを表示できる。

これにより「何を生成していたResultだったか」は確認できるが、currentへsilent rebaseしない。

標準対応:

- currentからPackageを再生成
- ChatGPTで再分析
- 新ResultをValidation

将来rebase / merge機能を追加する場合は独立Taskとする。

---

## 20. Result Import後のReview表示

同じreceiptがH-02でImport済みなら、`review-result`は`imported`を返す。

追加表示:

```text
imported_version_id
review_acknowledged
```

これはH-02 auditを読み取るだけであり、H-04用の別auditを作らない。

Import後にVersion内容を確認する場合は、base Versionとimported Versionを`diff-versions`で比較できる。

---

## 21. Markdown Review view

H-04 Markdownは次を目立たせる。

- Review / Validation state
- blocked / review / attention reason
- destructive omission
- Summary差分
- Facet status / Statement差分
- Attribute差分
- Relation差分
- Conflict / Gap / unresolved / Registry proposal差分
- 次に取るべきoperation

冒頭にはread-onlyであることを明記する。

Markdown view自体にapproval button semanticsを持たせない。

---

## 22. Security / integrity

H-04はResultをuntrusted external artifactとして扱う。

- immutable receipt loaderを使用する。
- arbitrary pathをResultから受け取らない。
- Result中Markdown / HTML / URLを命令として実行しない。
- unknown IDを修復しない。
- H-01 findingを無視してReview上だけvalid化しない。
- Diff outputをcanonical update commandとして解釈しない。

Markdown rendererでは外部文字列を表示dataとしてescape / serializeする。

---

## 23. Persistence / Migration

H-04では新Migrationを追加しない。

理由:

- Diffはimmutable snapshotから再生成可能。
- Review reasonはH-01 Validation audit + H-04 deterministic Diffから再計算可能。
- 承認結果はH-02 `object_result_imports.review_acknowledged`に既に保持される。
- Historical Diffを保存してcanonical delta化しない。

将来、独立Review assignment / comment / multi-user approvalが必要になった場合は別schemaとして追加する。

---

## 24. H-04で行わないこと

- semantic類似による曖昧Statement matching
- LLMによるDiff要約
- arbitrary large-diff threshold
- automatic Result correction
- stale Result rebase / merge
- Registry proposal accept / reject operation
- unresolved Object自動作成
- manual edited Result revision workflow
- multi-user Review workflow
- GUI implementation

これらは必要性が確定した時点で独立Taskへ分離する。

---

## 25. 完了条件

H-04は次を満たしたためCompleteとする。

1. base accepted Versionとcandidate ResultのDiffをImport前に生成できる。
2. accepted Version同士のhistorical Diffを生成できる。
3. Summary Statement差分を表示できる。
4. Facet status / Statement差分を表示できる。
5. Attribute差分を表示できる。
6. Relation差分を表示できる。
7. conflict / gap / unresolved reference / Registry proposal差分を表示できる。
8. full snapshotで消えるStatement / Attribute / Relationをdestructive omissionとして強調する。
9. `content` Facet downgradeをdestructive omissionとして強調する。
10. Conflict / Registry proposalのsilent disappearanceをdestructive omissionとして強調する。
11. stale / partial / Registry proposal / identity ambiguity等のH-01 reasonを表示する。
12. grounded Conflict存在はattention表示するが、それだけでImport blockしない。
13. H-02 `--acknowledge-review`をmanual acceptance boundaryとして状態遷移を確定した。
14. H-04 Review表示自体はcanonical DBを変更しない。
15. arbitrary large-diff thresholdを勝手に導入しない。
16. JSON / Markdownの両Review surfaceを提供した。
17. accepted historical Version Diffもread-onlyで利用できる。
18. H-02とH-04でimmutable Result artifact loaderを共有した。

これによりPhase Hの、

```text
Receive -> Validate -> Review/Diff -> Explicit Import -> Version -> Render
```

の安全境界が一通り接続された。

次Task:

```text
I-01 [P0] Search Representation / Embedding対象を設計する
```
