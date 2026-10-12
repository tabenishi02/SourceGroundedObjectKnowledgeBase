# Source Grounded Object Knowledge Base — Object Result JSON Schema Design

更新日: 2026-10-12

- Task: `E-05 [P1] JSON Schemaを作成する`
- Status: Complete
- Logical authority: `docs/requirements/OBJECT_RESULT_REQUIREMENTS.md`
- Prerequisites:
  - `docs/design/OBJECT_SCHEMA.md`
  - `docs/design/SEMANTIC_FACET_SCHEMA.md`
  - `docs/design/SOURCE_EVIDENCE_SCHEMA.md`
  - `docs/design/VERSIONING_SCHEMA.md`
- Canonical Schema: `src/sgokb/exchange/schemas/object-result-v1.schema.json`
- Exchange contract: `src/sgokb/exchange/object_result.py`
- Schema version: `sgokb.object-result/1.0`
- JSON Schema dialect: Draft 2020-12

## 1. 目的

本書は、Object Evidence PackageをChatGPT等で分析した結果をSGOKBへ戻すためのObject Resultを、機械検証可能なJSON Schemaへ固定するE-05の設計正本である。

E-05では次を確定する。

- 共通Object Result Envelope。
- target Object / Classification snapshotの交換形式。
- Package / base Version binding。
- generation provenance。
- summary / Facet / Attribute / Relationの共通Knowledge構造。
- Knowledge Statement / derivation kind / reported-view attribution。
- Evidence reference / Evidence role。
- Knowledge language / temporal scope。
- conflict / gap / unresolved reference / Registry proposal。
- complete / partial / insufficient-evidence Result状態。
- full snapshot時のFacet omission semantics。
- Class-specific extensionの拡張方式。
- ChatGPT出力契約とImport Validatorが同一Schemaを利用する方式。

E-05はResultをaccepted VersionへImportする処理そのものではない。DB存在確認、Package Evidence membership、Provenance integrity、authoritative Import transactionはH-01 / H-02でこのSchemaを利用して実装する。

---

## 2. 基本決定

### 2.1 Schema version

初期Object Result schema versionを次とする。

```text
sgokb.object-result/1.0
```

JSON Schema `$id`:

```text
urn:sgokb:schema:object-result:1.0
```

Schema dialectはJSON Schema Draft 2020-12とする。

### 2.2 canonical Schema fileは1つ

構造Schemaの正本は次である。

```text
src/sgokb/exchange/schemas/object-result-v1.schema.json
```

このSchemaを、

- ChatGPTへ渡す出力契約
- local Result preview / validation
- H-01 Import Validator
- test fixture

で共有する。

Prompt向けSchemaとImporter向けSchemaを別々に複製しない。

### 2.3 unknown fieldは原則reject

主要Objectは`additionalProperties: false`とする。

これによりAIが次のような独自fieldを勝手に追加してもsilentに無視しない。

```text
version_id
current_version
write_to
delete_file
execute
confidence
```

Schema evolutionが必要な場合はSchema versionまたは明示extension contractとして扱う。

### 2.4 ResultはVersion IDを発行しない

Object Resultにはpersistent `version_id`を持たせない。

```text
result.json
  -> validate
  -> H-02 Import
  -> SGOKBがVersion IDを発行
```

E-04のVersion identity contractを維持する。

---

## 3. Top-level Envelope

Object Result v1は次を必須とする。

```text
Object Result
├─ schema_version
├─ result_status
├─ target
├─ binding
├─ generation
├─ knowledge
├─ conflicts
├─ gaps
├─ unresolved_references
├─ registry_proposals
└─ class_extensions
```

全collectionは該当項目がなくても空arrayを明示する。

これにより「field omission」と「0件」を区別せずに済み、AI出力差によるParser分岐を減らす。

---

## 4. Result status

`result_status`は次の3値とする。

```text
complete
partial
insufficient_evidence
```

### `complete`

予定した分析scopeを完了したResult。

Knowledge gapやSource間conflictが0であることまでは意味しない。`complete`は処理coverageの状態であり、Knowledgeの真実性・完全性scoreではない。

### `partial`

一部scopeが未分析、token / package / process上の制約等でlimited analysisとなったResult。

少なくとも1件の`gaps`を必須とし、何が未完了かを明示する。

### `insufficient_evidence`

処理自体は正常に完了したが、Package中EvidenceがObject Knowledge生成に十分でないResult。

少なくとも1件の`gaps`を必須とする。

### Import policy

E-05では状態を表現するまでを担当する。

- `complete`を自動acceptするという意味ではない。
- `partial` / `insufficient_evidence`のauthoritative Import / current promotion判断はH-02 / H-04で扱う。

---

## 5. Target binding

`target`:

```json
{
  "object_id": "...",
  "primary_class_id": "class:character",
  "additional_class_ids": ["class:fictional_entity"]
}
```

### 必須field

- `object_id`
- `primary_class_id`
- `additional_class_ids`

### 持たせないもの

次はRegistry metadataであり、Result targetの正本fieldにしない。

- name
- aliases
- Object status
- current_version

AIがname / alias / Class訂正候補を発見した場合は`registry_proposals`へ送る。

### Classification snapshot

Primary / Additional ClassはPackage分析時点のClassification preconditionをechoする。

H-01 / application側はPackage / Object Registryから`ObjectResultContract`を構築し、ResultがそのClassificationと完全一致することを検証する。

ResultのClass IDを理由にObject Registryを変更しない。

---

## 6. Package / base Version binding

`binding`:

```text
package_id
package_schema_version
manifest_sha256
package_created_at
base_version_id
```

### `package_id`

分析に利用したEvidence Package identity。

具体的Package ID生成方式はG-02で確定する。E-05ではnon-empty stringとして交換fieldを固定する。

### `package_schema_version`

Package manifest contract version。

G-02で実値を確定する。Result ValidatorはPackage側の期待値と一致させる。

### `manifest_sha256`

Package manifestの不変binding用SHA-256。

小文字64桁hexとする。

### `package_created_at`

Package生成日時。RFC 3339 / JSON Schema `date-time` formatで検証する。

### `base_version_id`

更新Resultでは分析基準Version ID、初回Knowledge生成では`null`。

Result自身の次期Version IDではない。

E-04のcurrent/base stale判定とは別に、H-01がPackage bindingとResult bindingの一致を確認する。

---

## 7. Generation provenance

`generation`は次を保持する。

```text
instructions_version
    required
generator_kind
    interactive_ai | human_editor | tool
application
    required
provider
    optional
model_label
    optional
model_version
    optional
generated_at
    required
```

### model情報を必須にしない

ChatGPT Web/Desktop等で正確なmodel revisionが取得できない場合、推測して埋めない。

`provider / model_label / model_version`は取得できるものだけ含める。

### provider固有Knowledge fieldを作らない

`chatgpt_summary`等のfieldは導入しない。

同じResult contractをhuman editorや将来別AI Toolでも利用できる。

### Import provenanceとの境界

次はH-02がImporter側で付与するためResult自身には含めない。

- import timestamp
- Result artifact storage reference
- Result artifact hash
- Import run ID
- Persistent Knowledge Version ID

---

## 8. Knowledge root

`knowledge`:

```text
default_language
summary[]
facets[]
attributes[]
relations[]
```

`default_language`はResult Knowledge本文の既定言語を表す。

初期SchemaではBCP 47互換の基本patternを使用し、例えば次を許容する。

```text
ja
en
en-US
zh-Hant
und
```

Evidence原文言語とは別概念である。

Statement / Attributeは必要に応じ個別`language`でoverrideできる。

---

## 9. Knowledge Statement

summaryとFacet本文は同じStatement contractを使用する。

```text
local_key
text
derivation_kind
language?           # default_languageからoverrideする場合
temporal_scope?
attribution?        # reported_viewのみ
evidence[]
```

### `local_key`

Result内でStatementを参照するためのlocal identifier。

- Persistent global IDではない。
- Versionをまたいで維持する必要はない。
- summaryと全Facet Statementを合わせて1 Result内で一意にする。
- ImporterがDB `knowledge_statements.local_key`へ利用できる。

### `derivation_kind`

E-02の確定語彙をそのまま利用する。

```text
direct_statement
synthesis
interpretation
reported_view
```

### grounding

全Statementは`evidence`を最低1件必要とする。

```json
{
  "evidence_id": "...",
  "role": "supports"
}
```

role:

```text
supports
contradicts
contextualizes
```

Source IDだけのcitationにはdowngradeしない。

---

## 10. `reported_view` attribution

`reported_view` Statementだけは`attribution`を必須とする。

attribution kind:

```text
source
object
named_actor
community
```

### Source attribution

```json
{
  "kind": "source",
  "source_id": "source-id"
}
```

### Object attribution

```json
{
  "kind": "object",
  "object_id": "object-id"
}
```

### Named actor / community

```json
{
  "kind": "community",
  "label": "Example community"
}
```

`reported_view`以外のStatementに`attribution`を付けることはv1ではrejectする。

通常のdirect/synthesis/interpretationはEvidence grounding自体が出典追跡を担うためである。

Source / Object IDのDB存在確認はH-01で行う。

---

## 11. Temporal Scope

Statement / Attribute / Relationにinline `temporal_scope`を持たせる。

```text
as_of?
valid_from?
valid_to?
context_object_id?
label?
```

最低1項目が必要。

日付fieldはISO `date`またはRFC 3339 `date-time`を許容する。

### inline形式を採用する理由

Resultで別`temporal_scopes[]` + local reference tableを作ると、AIが管理すべきlocal IDが増える。

交換形式ではKnowledge要素へinlineし、ImporterがE-02 `temporal_scopes` rowを生成する。

同一scopeを複数Knowledgeが共有する場合のDB dedupはH-02 implementation detailとする。

`valid_from <= valid_to`、`context_object_id`の存在 / Class適合等はH-01 domain validationで扱う。

---

## 12. Facet full snapshot contract

Facet item:

```text
facet_id
status
statements[]
```

status:

```text
content
insufficient_evidence
not_applicable
not_analyzed
```

### full snapshotでは有効Facetを全件明示する

E-04で残していたomission ambiguityをE-05で解消する。

Package / Classification snapshotから解決した、

- common Facet
- Primary Class profile
- ancestor inherited profile
- Additional Class profile

のeffective Facet集合を、Resultは**ちょうど1回ずつ全件出力する**。

したがって、

```text
Facet rowがない
```

ことを削除・not applicable・未分析のいずれかに解釈しない。

Contentがない場合も、必ず適切なstatusを明示する。

### `content`

最低1件のStatementが必要。

### その他status

`statements`は空arrayでなければならない。

これにより、

```text
status = insufficient_evidence
なのに本文assertionが存在する
```

といった矛盾をSchema段階でrejectする。

### Class-specific Schema specialization

全62 ClassのFacet listを静的JSON Schemaへ複製しない。

`ObjectResultContract.facet_ids`からeffective profileを受け取り、`build_object_result_schema()`がcanonical Schemaを動的に特殊化する。

特殊化後Schemaは、

- 許可Facet ID以外をreject
- effective Facet数とarray lengthを一致
- 各expected Facetを`contains`で1回ずつ要求

する。

これがE-05におけるClass-driven schema extensionの中心方式である。

---

## 13. Structured Attribute

Attribute item:

```text
local_key
attribute_id
status
value?              # knownのみ
language?
temporal_scope?
evidence[]
```

status:

```text
known
insufficient_evidence
not_applicable
not_analyzed
```

### `known`

- `value`必須。
- Evidence最低1件必須。
- Attribute Registryの`value_type`と一致しなければならない。

### non-known status

- `value`を持ってはならない。
- Evidenceは0件以上を許容する。

例えば「確認したEvidenceでは決定不能」という根拠を残すため、`insufficient_evidence`でもEvidence参照自体は禁止しない。

### Dynamic value type validation

Attribute typeはRegistry-drivenであるため、static JSON Schemaへ全Attribute IDを埋め込まない。

`ObjectResultContract.attribute_value_types`にactive Attribute Definitionを渡し、`validate_object_result()`が次を確認する。

```text
text / identifier / enum -> string
integer                  -> JSON integer, bool除外
real                     -> JSON number, bool除外
boolean                  -> JSON boolean
date                     -> ISO date string
datetime                 -> ISO datetime string
json                     -> JSON-serializable value
```

未知 / archived Attribute IDはResult contractへ含めないためrejectされる。

Class別Attribute allow-listを将来導入する場合も同じruntime contractへ追加できる。

---

## 14. Relation

Relation item:

```text
local_key
subject_object_id
relation_type_id
object_object_id
temporal_scope?
evidence[]
```

### 基本制約

- Evidence最低1件。
- Relation Typeはactive Registry entryであること。
- standard 1 Object Resultではtarget Objectがsubject/objectの少なくとも片側に存在すること。
- B→Cのようにtarget Objectと無関係なRelationをResultから確定しない。

### H-01へ残す確認

- subject / object Object IDがDBに存在すること。
- Relation Type Registry metadataの最終referential check。
- Package Evidence membership / Provenance integrity。
- Relation Typeごとのdomain-specific direction constraintが将来導入された場合の確認。

---

## 15. Conflict

`conflicts[]`は未解決のSource / Knowledge disagreementを確定Knowledge assertionから分離する。

```text
local_key
description
related_knowledge[]
evidence[]            # 最低2件
```

`related_knowledge`は、

```text
statement
attribute
relation
```

の`local_key`を参照できる。

`validate_object_result()`は存在しないlocal keyへの参照をrejectする。

Conflictを解決済みと判断した場合は、grounded Knowledge自体へ整理し、未解決`conflicts`に残し続ける必要はない。

---

## 16. Gap

`gaps[]`はKnowledge assertionではなく、分析上の不足・未確定を表す。

kind:

```text
insufficient_evidence
not_analyzed
open_question
missing_source
identity_ambiguity
other
```

field:

```text
local_key
kind
description
facet_id?
attribute_id?
evidence[]
```

Evidenceが存在しないこと自体がgap理由になり得るため、Gap Evidenceは0件を許容する。

`partial` / `insufficient_evidence` Resultでは最低1 Gapを必須とする。

Gapを通常Statement Semantic Indexへ入れるかどうかはB-05の既決事項どおり通常Knowledgeとは分離する。

---

## 17. Unresolved Reference

未登録Objectを架空Persistent IDとしてRelationへ入れない。

`unresolved_references[]`:

```text
local_key
label
candidate_class_id?
relation_context?
disambiguation_note?
evidence[]
```

### `candidate_class_id`

既存Class Registryから妥当な候補がある場合だけ指定する。

新Class自体が必要なら`registry_proposals`へ別提案する。

### `relation_context`

```text
relation_type_id
target_role = subject | object
```

対象Objectを正式登録・identity解決した後にRelation化するためのcontextであり、unresolved reference自体はcanonical Relationではない。

### 禁止field

`object_id`は持たせない。

AIに未登録ObjectのPersistent IDを発行させないためである。

---

## 18. Registry Proposal

`registry_proposals[]`は通常Knowledge Importと別review対象である。

proposal kind:

```text
object_name
object_alias
primary_class
additional_class
new_class
new_facet
new_attribute
new_relation_type
```

共通field:

```text
local_key
proposal_kind
rationale
payload
evidence[]
```

AI由来proposalは最低1件のEvidenceを要求する。

### `payload`をopen objectにする理由

Proposalはcanonical Knowledgeではなくstaging/review情報であり、Registry種別ごとの管理contractは将来独立進化する。

Main Object Result schemaでproposal payload全種類を固定してしまうと、Registry proposal機能追加だけでObject Result major/minor schemaを頻繁に変更することになる。

したがってv1では、

- proposal kindを閉じたenumにする。
- envelope / rationale / groundingを厳格化する。
- `payload`内部はobjectとして保持する。
- H-01 / Registry-specific validatorがkind別payloadを検証する。
- proposalをKnowledge Importの副作用として自動適用しない。

という境界を採用する。

`payload`中の文字列をcommand / path / URL actionとして実行してはならない。

---

## 19. Class-specific extension

### 19.1 v1の原則

v1ではCharacter / Work / Concept等ごとに別の固定JSON payloadを必須にしない。

Class差分の大半は、

- Facet profile
- Attribute Registry
- Relation Type Registry
- common Knowledge structure

で表現する。

したがって、**初期62 Classすべてに専用extension schemaを作ることはしない。**

専用extensionがないClassもcommon schemaだけで完全に有効なResultを生成できる。

これは「専用実装がないClassを別Classへfallbackしない」というB-02 / E-02要件を維持する。

### 19.2 `class_extensions[]`

将来、common Facet/Attribute/Relationでは自然に表現できないClass固有構造が必要になった場合だけ利用する。

```text
class_id
schema_id
data
```

### 19.3 registered extensionのみ許可

`ClassExtensionContract`で、

```text
class_id
schema_id
JSON Schema
```

を明示登録する。

`validate_object_result()`は、

- schema_idが登録済み
- schemaに対応するclass_idとResult entryが一致
- extension対象ClassがResultのPrimary / Additional Classificationに含まれる
- 同一Classのextensionが重複しない
- `data`がextension-specific Schemaへ適合する

ことを検証する。

登録extensionがない場合、`class_extensions: []`で正常である。

### 19.4 ancestor extension

v1ではClass extensionをPrimary / Additional direct Classへ限定する。

ancestorから継承すべき意味は原則Facet profile inheritanceで表現する。

将来ancestor extension inheritanceが必要になった場合は明示仕様追加とする。

---

## 20. Registry-driven Class Schema

E-05は、Classごとに静的Schema fileを大量作成する代わりに、canonical base Schemaへruntime contractを合成する。

`ObjectResultContract`:

```text
target_object_id
primary_class_id
additional_class_ids
facet_ids
attribute_value_types
relation_type_ids
package_id?
package_schema_version?
manifest_sha256?
base_version_id
class_extensions
```

`build_object_result_schema(contract)`はbase Schemaをdeep copyし、少なくとも次を特殊化する。

- target Object ID = expected value。
- Primary Class = expected value。
- Additional Classes = exact set。
- package identity / schema / hash = expected value（入力された場合）。
- base Version = expected value/null。
- Facet collection = exact effective profile。

これを**Class-specific composed schema**と位置付ける。

### なぜSchema生成側がDBを読まないか

D-04のdependency contractでは、

```text
exchange -> domain
```

は許可されるが、exchange自身がstorage / SQLiteへ密結合することは避ける。

したがって、

```text
Application / H-01
  -> storageからObject / Registry / Packageを読む
  -> ObjectResultContractを構築
  -> exchange.validate_object_result()
```

という方向にする。

これによりChatGPT向けSchema出力とImporter側Validationの両方で同じ純粋contract builderを利用できる。

---

## 21. Validation layer boundary

E-05の`validate_object_result()`が担当するのは主に次である。

### Structural / Schema

- JSON Schema Draft 2020-12適合。
- required field / type / enum / format。
- unknown field reject。
- Result status / Gap整合。
- reported-view attribution。
- Facet status / Statement整合。
- known Attribute value / grounding shape。
- Statement / Relation grounding shape。

### Registry-derived contract

`ObjectResultContract`が渡された場合:

- target / Classification exact match。
- package/base binding exact match。
- effective Facet exact coverage。
- Attribute ID / value type。
- Relation Type ID。
- target ObjectがRelation endpointに含まれる。
- optional Class extension schema。

### Result-internal referential integrity

- Statement local key重複禁止。
- Attribute local key重複禁止。
- Relation local key重複禁止。
- conflict等のlocal key重複禁止。
- ConflictのKnowledge local reference存在確認。

---

## 22. H-01へ残すValidation

E-05 Schemaだけでは、canonical DB / Packageの現在状態を確認できない。

H-01はこのSchema validatorを第1層として利用し、その後に次を追加する。

### Binding / Precondition

- target ObjectがDBに存在する。
- Package targetと一致する。
- Package manifest hashが実Artifactと一致する。
- base VersionがPackage / current preconditionへ一致する。
- Classification snapshotがPackage / current Registry条件へ一致する。

### Referential

- Class / Facet / Attribute / Relation Typeがactive Registry entryである。
- Relation endpoint Objectが存在する。
- attribution Object / Source IDが存在する。
- temporal context Objectが存在する。
- unresolved reference candidate Classが存在する。

### Grounding / Provenance

- Evidence IDがcanonical DBに存在する。
- Evidence → Raw / Snapshot / Source chainが成立する。
- Resultが参照する全EvidenceがPackage manifestに含まれる。
- Evidence roleがactive Registry vocabularyと一致する。

### Domain

- Class/F​​acet profile解決がPackage時点Classificationと一致する。
- temporal interval整合。
- Registry proposal payloadのkind-specific validation。
- Identity ambiguity / review-required condition。

### Semantic review

Schema適合しても、

- 内容が正しい
- 解釈が妥当
- Evidenceを正しく読んでいる
- 重要事項を取りこぼしていない

ことは保証しない。

---

## 23. Evidence collection helper

`collect_evidence_ids(result)`をE-05で追加した。

次からEvidence IDを一括収集する。

- summary Statement
- Facet Statement
- Attribute
- Relation
- Conflict
- Gap
- Unresolved Reference
- Registry Proposal

H-01はこの集合をE-03 `SourceRepository.validate_evidence_references()`へ渡し、

- DB存在
- Provenance integrity
- Package membership

を検証できる。

E-05自身はDBへアクセスしない。

---

## 24. Full snapshot omission semanticsの確定

E-04では「Versionに存在しないKnowledgeはcarry-forwardされない」と確定した一方、AIのFacet omissionを削除意図とみなさない境界を残していた。

E-05では**Facetについてはomissionを禁止**する。

```text
effective Facet profile
  personality
  values
  motivation
  ...

Result
  personality -> content
  values -> insufficient_evidence
  motivation -> not_analyzed
  ...
```

のように、全Facetをstatus付きで出す。

これにより、Facet単位では、

```text
欠落 = 削除
欠落 = not applicable
欠落 = 未分析
```

の曖昧さをなくす。

### Statement / Attribute / Relation omission

full snapshot内に存在しない個別Statement / Attribute / Relationは次Versionへcarry-forwardされない。

ただし、それが意図的な削除か生成漏れかの人間向けDiff / destructive omission reviewはH-04で扱う。

Attributes / Relationsは「存在しない全候補をnot_analyzed rowとして列挙する」方式にはしない。Registry全体を毎Resultで埋めると過剰になるためである。

Facet profileは有限でClass意味contractそのものなので全件明示、Attribute / Relationは実Knowledge要素として必要分だけ出力する、という差を採用する。

---

## 25. Security / untrusted input

Object Resultは外部生成untrusted inputである。

Schemaに、

```text
write_to
delete_file
execute
command
```

等のoperation fieldを持たせない。

unknown top-level fieldはrejectする。

Registry proposal `payload`やClass extension `data`内に文字列が存在しても、それをfile / shell / network operationへ直接利用してはならない。

ResultにURL等が含まれる将来extensionを追加しても、自動Capture / external request permissionとはみなさない。

---

## 26. Static Schemaとruntime contractの役割分担

### Static canonical JSON Schema

担当:

- wire format
- required/optional field
- nested structure
- enum
- basic format
- unknown field policy
- conditional structure

### Runtime `ObjectResultContract`

担当:

- どのObject向けか
- どのClassification snapshotか
- どのFacet profileか
- 現在activeなAttribute / Relation vocabulary
- Package/base precondition
- optional class extension schema

この分離により、RegistryへFacetを追加するたびにcanonical JSON Schema versionを上げる必要がない。

一方、Resultのwire shapeや意味契約が変わる場合はSchema versionを変更する。

---

## 27. JSON例

以下は概略例であり、実際にはtarget Classのeffective Facetを全件出力する。

```json
{
  "schema_version": "sgokb.object-result/1.0",
  "result_status": "complete",
  "target": {
    "object_id": "2de2d146-...",
    "primary_class_id": "class:character",
    "additional_class_ids": ["class:fictional_entity"]
  },
  "binding": {
    "package_id": "package-...",
    "package_schema_version": "sgokb.evidence-package/1.0",
    "manifest_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "package_created_at": "2026-10-12T10:00:00Z",
    "base_version_id": null
  },
  "generation": {
    "instructions_version": "object-analysis/1.0",
    "generator_kind": "interactive_ai",
    "application": "ChatGPT",
    "generated_at": "2026-10-12T10:05:00Z"
  },
  "knowledge": {
    "default_language": "ja",
    "summary": [
      {
        "local_key": "summary-1",
        "text": "根拠付きのObject要約。",
        "derivation_kind": "synthesis",
        "evidence": [
          {"evidence_id": "evidence-1", "role": "supports"}
        ]
      }
    ],
    "facets": [
      {
        "facet_id": "facet:personality",
        "status": "content",
        "statements": [
          {
            "local_key": "personality-1",
            "text": "周囲への配慮を優先する傾向が描写される。",
            "derivation_kind": "interpretation",
            "evidence": [
              {"evidence_id": "evidence-2", "role": "supports"}
            ]
          }
        ]
      },
      {
        "facet_id": "facet:values",
        "status": "insufficient_evidence",
        "statements": []
      }
    ],
    "attributes": [],
    "relations": []
  },
  "conflicts": [],
  "gaps": [],
  "unresolved_references": [],
  "registry_proposals": [],
  "class_extensions": []
}
```

---

## 28. E-05で意図的に決めない事項

### Phase G

- Evidence Package directory layout最終形。
- Package ID生成方式。
- Package manifest JSON Schema。
- `package_schema_version`実値。
- Package export先 / Google Drive workflow。
- `instructions_version`の実際のprompt contract。

### H-01

- Validation report JSON shape。
- validation layer別error/warning codeの外部contract。
- DB / Packageを組み合わせたValidator orchestration。
- Registry proposal kind別payload schema。

### H-02

- original Result artifact保存table。
- Result artifact hash / idempotency key。
- Result -> candidate Version Import mapping implementation。
- Result local_key -> persistent DB row ID mapping。
- temporal scope dedup方針。
- partial Result explicit acceptance workflow。

### H-04

- Statement / Attribute / Relation semantic Diff algorithm。
- destructive omission Review UI。
- conflict / gap / proposal review UI。

### Phase I

- Result/VersionからSearch Representationを生成する具体的builder。
- Embedding / Vector Index。

---

## 29. 実装成果物

### `src/sgokb/exchange/schemas/object-result-v1.schema.json`

- Draft 2020-12 canonical static schema。
- Schema version / Envelope / Knowledge / review metadataを定義。
- package dataとして配布対象に追加。

### `src/sgokb/exchange/object_result.py`

- `load_object_result_schema()`
- `build_object_result_schema()`
- `validate_object_result()`
- `collect_evidence_ids()`
- `ObjectResultContract`
- `ClassExtensionContract`
- structured validation issue / exception contract

### `src/sgokb/exchange/__init__.py`

E-05 public exchange contractを明示exportする。

### `tests/test_object_result_schema.py`

E-05 contract regressionを固定する。

---

## 30. Validation result

E-05固有testでは少なくとも次を確認する。

- canonical Schema `$id` / version / Draft 2020-12。
- persistent Version ID fieldがSchemaに存在しない。
- valid complete Result。
- effective Facet全件coverage。
- duplicate / missing Facet reject。
- target / Package / base binding mismatch reject。
- `reported_view` attribution必須。
- non-content FacetへStatementを隠せない。
- partial / insufficient ResultにGap必須。
- Attribute Registry type validation。
- known Attribute grounding。
- unknown Attribute reject。
- Relation Type Registry validation。
- target ObjectがRelation endpointへ含まれること。
- duplicate local key reject。
- Conflict local reference validation。
- unresolved referenceが架空`object_id`を持てないこと。
- optional Class extension schema validation。
- 専用extensionなしClassもcommon Schemaで有効なこと。
- Evidence ID collection。
- unknown top-level field / operation-like field reject。

Validation baseline:

```text
E-05 focused tests: 15 passed
full test suite:    137 passed
ruff:               passed
```

Migrationは追加していないためschema migration countは7のままである。

---

## 31. Phase E完了条件への対応

### ChatGPT出力とDBの共通契約

Object Result wire formatをDraft 2020-12 JSON Schemaへ固定し、Version / Facet / Attribute / Relation / Evidenceの既存physical contractへ対応付けた。

### Class別Knowledge

Class差分はeffective Facet profileをruntime Schemaへ合成する。初期62 Classごとの重複Schemaは作らない。

### 専用extension未実装Class

common Result contractだけでvalid Resultを生成可能とした。別Classへのfallback不要。

### Evidence grounding

Statement / known Attribute / RelationをEvidence ID + roleへbindするshapeを確定した。

### Versioning

base VersionをResultへbindし、persistent next Version IDはResultから排除した。

### Search / MCPへの接続

Knowledgeをsummary / Facet Statement / typed Attribute / Relationへ構造化したため、Phase I / Jが同じcanonical Version modelを利用できる。

### Validation

Static Schemaとruntime registry contractを分離し、H-01でDB / Package / Provenance validationを追加できる境界を確定した。

以上により、Phase Eの「ChatGPT出力、DB、検索、MCPの共通契約となるObject schemaを確定する」という完了条件を満たす。

---

## 32. 結論

E-05により、SGOKB Object Resultは**`sgokb.object-result/1.0`という単一の厳格な共通JSON Schema**へ固定された。

Class差分を54個以上の静的Schemaへ複製せず、Package / Registryから解決したClassificationとeffective Facet profileを`ObjectResultContract`としてcanonical Schemaへ合成する。これによりClass Registry / Facet Registryの拡張とResult wire formatのversioningを分離できる。

full snapshot Resultでは有効Facetを全件status付きで明示するため、Facet omissionを削除・未分析・not applicableのいずれかへ推測する必要がない。一方、Statement / Attribute / RelationはVersion snapshot中に存在するものだけをKnowledgeとして扱い、baseとの差分ReviewはH-04へ残す。

Resultはpersistent Version IDを発行せず、Registry proposalやunresolved Objectをcanonical Knowledgeと分離する。Evidence referenceはStatement / Attribute / Relation等の具体的Knowledge単位へ保持し、H-01がPackage membership / Provenanceを追加検証できる。

**E-01〜E-05が完了したためPhase E — Object Knowledgeデータモデルは完了。次Taskは`F-01 [P0] 既存Capture / Import / Normalize / Evidenceを新設計へ接続する`とする。**
