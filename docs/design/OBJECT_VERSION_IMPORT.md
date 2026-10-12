# Source Grounded Object Knowledge Base — Object Version Import

更新日: 2026-10-13

- Task: `H-02 [P0] Object Version Importを実装する`
- Status: Complete
- Parent: Phase H — Result Validation / Import / Rendering
- Input authority: H-01 `valid` immutable Result receipt
- Validation authority: `docs/design/RESULT_VALIDATION.md`
- Version authority: `docs/design/VERSIONING_SCHEMA.md`
- Implementation:
  - `src/sgokb/exchange/result_import.py`
  - `src/sgokb/storage/result_import_repository.py`
  - `src/sgokb/storage/version_repository.py`
- Persistence: Migration 013 / `object_result_imports` etc.
- CLI: `sgokb-package import-result`
- Tests: `tests/test_object_version_import.py`
- Follow-up: H-03 Markdown Renderer

---

## 1. 目的

H-02は、H-01でdeterministic Validationを通過したObject Resultを、明示的なImport操作によって新しいimmutable Object Knowledge Versionへ変換する。

基本境界:

```text
Result received
  -> H-01 validation
  -> valid Result receipt
  -> explicit H-02 import
  -> one atomic accepted Object Version
```

Result検出、Result受領、Validation成功だけではcanonical Knowledgeを書き換えない。

---

## 2. Explicit Import

標準Import操作:

```text
sgokb-package import-result <receipt_id>
```

review-required findingを持つResult:

```text
sgokb-package import-result <receipt_id> --acknowledge-review
```

`--acknowledge-review`は、その1回のImportでreview-required状態を明示承認するための入力である。

normal complete Resultでは、Import開始後にVersion ID発行、Knowledge書込み、accept、current切替、derived state更新を追加confirmationへ分割しない。

---

## 3. Import可能条件

Importは最低限次を満たす必要がある。

- G-05 immutable receiptが存在する。
- receipt `validation_state = valid`。
- receipt artifactのbyte count / SHA-256が監査値と一致する。
- Result target / Package / manifest hash / base VersionがPackage auditと一致する。
- target Objectがactiveである。
- ResultのPrimary / Additional Classが現在のObject Classificationと一致する。
- Result `base_version_id`がImport transaction開始時点でもcurrentである。
- effective Facet contractがValidation後に変化していない。
- Result中EvidenceがPackage membership内にありcanonical Evidenceとして存在する。
- review-required Resultでは明示review acknowledgementがある。

H-01成功後にcurrent VersionやClassification等が変化した場合、Import時の再checkでblockする。

---

## 4. Atomic transaction

H-02の最重要実装条件は、次の全処理を**1つのSQLite `BEGIN IMMEDIATE` transaction**に含めることである。

```text
precondition recheck
  -> Persistent Version ID発行
  -> candidate Version作成
  -> Import provenance保存
  -> Result metadata保存
  -> Facet / Statement / Attribute / Relation書込み
  -> temporal scope / attribution保存
  -> Evidence Link作成
  -> acceptedへ遷移
  -> current pointer切替
  -> derived stateをpending化
  -> COMMIT
```

途中で例外、process interruption、constraint violation等が発生した場合はROLLBACKする。

そのため、

- incomplete candidateだけ残る
- Knowledgeの一部だけ残る
- currentだけ新Versionへ切り替わる
- Import auditだけ残る

という部分commitを許さない。

---

## 5. VersionRepository transaction API

E-04の通常APIは自らtransactionを開始・commitする。

H-02では複数のcanonical writeを同じtransactionへ束ねる必要があるため、VersionRepositoryへ次を追加した。

```text
create_candidate_in_transaction(...)
accept_candidate_in_transaction(...)
```

既存の、

```text
begin_candidate(...)
accept_candidate(...)
```

もこれらへ委譲し、従来のVersion lifecycle semanticsを維持する。

これによりH-02だけがE-04 acceptance logicを複製する構造を避ける。

---

## 6. Result → canonical Knowledge mapping

### Facet

Resultのeffective Facet full snapshotを`object_version_facets`へ保存する。

`content / insufficient_evidence / not_applicable / not_analyzed`をそのまま保持する。

### Statement

summaryとFacet Statementを`knowledge_statements`へ保存する。

- summary: `facet_id = NULL`
- Facet Statement: 対応Facet ID
- `local_key`
- `text`
- `derivation_kind`
- language
- temporal scope

### reported_view attribution

WOK-05の要件を失わないため、Migration 013で`knowledge_statement_attributions`を追加した。

保持可能なkind:

```text
source
object
named_actor
community
```

accepted Versionのattributionは他のVersion content同様immutableである。

### Attribute

`object_version_attributes`へ保存する。

Registry `value_type`に応じ、既存canonical columnへ変換する。

```text
text/date/datetime/identifier/enum -> value_text
integer                            -> value_integer
real                               -> value_real
boolean                            -> value_boolean
json                               -> value_json
```

同じAttribute IDが複数ある場合はResult順にordinalを割り当てる。

### Relation

`object_relations`へ保存する。

Relation temporal scopeは`relation_temporal_scopes`へ保存する。

### Evidence Link

Statement / Attribute / RelationのEvidence referenceを`evidence_links`へ保存する。

```text
origin_kind = result_import
origin_ref  = import_id
```

Evidence roleはactive `evidence_roles` Registry entryへ解決する。

---

## 7. Result review metadata

次はcanonical assertionそのものとは分離したまま、Versionに付随するResult metadataとして保存する。

```text
result_status
default_language
generation
conflicts
gaps
unresolved_references
registry_proposals
class_extensions
```

保存先:

```text
object_version_result_metadata
```

これによりH-03/H-04は原Result artifactを再解釈せず、Versionに結び付いた情報として表示できる。

### Registry proposal

`registry_proposals`は保存するが、H-02 Importの副作用として、

- Object name / alias
- Primary / Additional Class
- Class Registry
- Facet Registry
- Attribute Registry
- Relation Type Registry

を変更しない。

Registry変更は独立したreview / mutation operationで扱う。

---

## 8. Import provenance

Migration 013の`object_result_imports`へ、少なくとも次をimmutable auditとして保存する。

```text
import_id
receipt_id
package_id
manifest_sha256
result_sha256
result_byte_count
result_storage_ref
object_id
base_version_id
version_id
result_status
validation_completed_at
validation_findings_json
review_acknowledged
imported_at
```

H-01を`--force`で後から再検証してreceiptの現在状態が変化しても、Import時点で利用したValidation report snapshotを失わない。

---

## 9. Duplicate / idempotency

同じimmutable receiptを再Importしても新Versionを追加しない。

`object_result_imports`は、

```text
UNIQUE(receipt_id)
UNIQUE(package_id, result_sha256)
UNIQUE(version_id)
```

を持つ。

通常のretryでは既存Import / Versionを返し、`duplicate = true`とする。

これは「DB commitは完了したが、CLI responseを受け取る前にprocessが中断した」場合にも同じVersionへ収束させるためである。

---

## 10. Review-required policy

次のようなH-01 review findingを含むResultは、Validation上`valid`でも標準Importをblockする。

例:

- `result_status = partial`
- `result_status = insufficient_evidence`
- Registry proposalあり
- unresolved referenceあり
- identity ambiguity gapあり
- Package export audit不足等

Importする場合は明示的に、

```text
--acknowledge-review
```

を要求する。

acknowledgement後はVersion発行からcurrent promotionまでを追加confirmationへ分割しない。

---

## 11. Stale protection

H-01 ValidationとH-02 Importの間には時間差が存在できる。

したがってH-02 transaction開始後に、少なくとも次を再検証する。

```text
current Version == Result base Version
current Primary Class == Result Primary Class
current Additional Classes == Result Additional Classes
current effective Facets == Result Facets
```

staleの場合:

```text
Import block
current unchanged
candidate remains 0
Import audit remains 0
```

ValidatorやImporterがResultを新しいcurrentへ自動rebaseしない。

---

## 12. Derived artifacts

accepted/current promotionと同じtransactionで、E-04のderived coordination stateを更新する。

初期kind:

```text
search_representation
embedding
vector_index
rendering
```

状態:

```text
pending
```

実際のEmbedding / Index / Markdown生成はcanonical commit transactionへ含めない。

後続worker/jobは独立して`ready / failed / stale`へ遷移できる。

---

## 13. current_object.jsonとの整合

H-02で新たにcanonical保存する、

- Result `default_language`
- reported-view attribution

が次のObject Evidence Packageで失われないよう、`PackageBuildReadRepository.current_object_snapshot()`も更新した。

H-02 Import後にPackageを再生成すると、`current_object.json`へこれらが再出力される。

---

## 14. H-02で行わないこと

- Result検出だけでのsilent Import
- invalid / pending receiptのImport
- stale Resultの自動rebase
- unknown IDの推測修復
- Registry proposalの自動適用
- Diff / review UI
- Markdown rendering
- Embedding / vector生成そのもの
- semantic truthの再判定

---

## 15. 完了条件

H-02は次を満たしたためCompleteとする。

1. H-01 valid receiptだけをImport入力にした。
2. Importを明示操作として実装した。
3. review-required Resultに追加acknowledgementを要求した。
4. Persistent Version IDをSGOKB側で発行した。
5. canonical Knowledge / Evidence Link / temporal scope / attributionをVersionへ保存した。
6. conflict / gap / unresolved / Registry proposal等をVersion metadataとして保持した。
7. Import / Package / original Result / H-01 Validation provenanceをimmutable auditへ保存した。
8. stale preconditionをImport transaction内で再確認した。
9. candidate作成からcurrent promotionまでをsingle transaction化した。
10. interruption時にcandidate/current/content/auditが部分commitされないことをtestで固定した。
11. retry / duplicate Importが同じVersionへ収束することをtestで固定した。
12. Registry proposalを副作用で適用しないことをtestで固定した。
13. 旧accepted Versionを破壊せず、新Versionをcurrentへ切り替えることをtestで固定した。
14. derived artifactsを`pending` coordination stateとして分離した。

次Task:

```text
H-03 [P1] Markdown Rendererを実装する
```
