# Source Grounded Object Knowledge Base — Object Result要件

更新日: 2026-10-10

- Task: `B-04 [P0] Object Result要件を定義する`
- Status: Accepted
- Parent: Phase B — 要件定義の全面更新
- Inputs:
  - `docs/requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_TYPE_MODEL.md`
  - `docs/requirements/OBJECT_TYPE_BOUNDARIES.md`
  - `docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`
  - `docs/decisions/KNOWLEDGE_BASE_REDESIGN_DECISION.md`
- B-05 result: `docs/requirements/SEARCH_REQUIREMENTS.md`
- Next: `B-06 [P0] 人間工程と自動工程を要件として分離する`

---

## 1. 目的

本書は、Object Evidence PackageをChatGPT等で分析した結果をSGOKBへ戻すための **Object Result** の論理要件を定義する。

Object Resultは、Source / Evidenceを根拠として高度な意味統合を行った結果を、機械的にValidation・Versioning・Import可能な構造へ変換する境界である。

B-04では特に次を確定する。

- Object Resultそのものの責務。
- Object Identity / Registry metadata / Knowledge Versionとの境界。
- JSONを機械向け交換正本とすること。
- summary / attribute / Facet / Relationの論理構造。
- Evidence groundingの最小契約。
- 直接記述・synthesis・interpretation等の区別。
- contradiction / uncertainty / insufficient evidenceの表現。
- 未解決Object参照やRegistry変更提案の扱い。
- generation / package provenance。
- stale Resultや不正IDを検出するためのprecondition。
- Validationで確認することと、確認できないことの境界。

本書は論理要件を定義する。最終JSON Schema、SQL table / column、Facet Registryの物理schema、Relation Registry、Version ID形式、Google Drive layout、具体的Promptは後続Taskで決定する。

---

## 2. 結論

SGOKBではObject Resultを次のように位置付ける。

> **Object Resultは、1つの対象Objectについて、特定のEvidence Packageと既存Knowledge Versionを入力として生成された、Evidence-groundedな次期Object Knowledge Version候補である。**

標準フローは次とする。

```text
Object Identity / Registry
        +
Object Evidence Package
        +
Current Object Knowledge Version（存在する場合）
        ↓
ChatGPT / Analysis
        ↓
Object Result JSON
        ↓
Structural / Referential / Provenance Validation
        ↓
Review / Import
        ↓
New Object Knowledge Version
        ↓
current_version切替
```

重要な境界は次である。

1. ResultはObject Identityではない。
2. ResultはSource / Evidenceではない。
3. Resultを受け取っただけではKnowledge Versionにならない。
4. ResultはObject Registry metadataを自由に上書きしない。
5. Result中のKnowledgeは可能な限り具体的Evidence IDへgroundingする。
6. ResultがPersistent IDや存在しないObject / Evidence IDを勝手に発行してはならない。
7. MarkdownはResult / DBから生成する派生表示であり正本ではない。
8. Validation成功は意味内容の真実性・品質保証を意味しない。

---

## 3. Object Resultの責務

### RES-01 — ResultはKnowledge候補であり、受領時点では正本Knowledgeではない

ChatGPT等から返された`result.json`は、Validation前には外部生成されたuntrusted inputとして扱う。

Resultを受け取っただけで次を更新してはならない。

- Object Registry
- `current_version`
- Object Relation正本
- Facet正本
- Search Index
- Embedding

ValidationとImportが成功して初めて、新しいObject Knowledge Versionとして保存できる。

### RES-02 — Structured JSONを機械向け交換正本とする

ChatGPTからSGOKBへ返却する標準成果物はStructured JSONとする。

```text
Object Evidence Package
  ↓
ChatGPT
  ↓
result.json   ← 機械向け交換正本
  ↓
Validator / Importer
```

ChatGPTが同時にMarkdownや説明文を生成することは許容するが、それらをImportの正本入力にしない。

### RES-03 — Import後はローカルObject Knowledge Versionを永続正本とする

「Structured JSONが正本」という既決事項は、非構造Markdownではなく構造化Knowledgeを正本にするという意味である。

責務を次のように分ける。

```text
交換時:
  result.json = canonical machine exchange artifact

Import後:
  local Object Knowledge Version = authoritative persisted Knowledge

表示時:
  Markdown / context text = derived representation
```

原Result JSONはImport provenanceとして不変保存またはhash追跡できることを要件とするが、Google Drive上のfileを永続DBの代わりにはしない。

### RES-04 — Resultは原則1 Objectを対象とする

標準Object Resultは1件のtarget Objectだけを更新対象とする。

```text
Object Result
  target_object_id = A
```

Relationによって他Objectを参照することはできるが、同じResultでObject B / CのKnowledge Versionまで同時更新しない。

将来batch wrapperを追加する場合も、内部のatomic Resultは1 Object単位とする。

この要件により、Validation、Versioning、Diff、rollback、retryのtransaction境界を明確にする。

---

## 4. Result Envelope / Binding要件

### BND-01 — target `object_id`を必須とする

Resultは対象Objectを安定`object_id`で指定しなければならない。

name / aliasだけでImport対象を決めてはならない。

ImporterはResultのtarget Objectが存在し、Packageのtarget Objectと一致することを検証する。

### BND-02 — ResultをEvidence Packageへbindする

Resultは、どのObject Evidence Packageを入力として生成されたかを追跡できなければならない。

論理上、少なくとも次へbindできることを要件とする。

- package identity
- package format / schema version
- package manifest hashまたは同等の不変確認情報
- package生成時刻
- package内Evidence集合

具体的field名はG-01 / G-02 / E-05で決定する。

### BND-03 — 更新Resultはbase Object Knowledge Versionへbindする

既存Knowledgeを更新するResultは、分析時に基準とした`base_version`を明示できなければならない。

```text
Object version 3
  ↓ package export
Result(base_version = 3)
```

Result返却前にObjectがversion 4へ更新されていた場合、version 3基準Resultをversion 4へ無条件上書きImportしてはならない。

### BND-04 — stale Resultを検出可能にする

Importerは少なくとも次の不一致を検出できることを要件とする。

- package target Object mismatch
- package manifest mismatch
- base version mismatch
- result schema version mismatch

stale Resultを自動mergeするか、人間reviewへ送るか、rejectするかはE-04 / H-02 / H-04で決定する。少なくともsilent overwriteは禁止する。

### BND-05 — 初回Knowledge生成ではbase versionなしを許容する

`current_version = null`のObjectについては、base versionなしの初回Resultを正常系として扱う。

Object登録とKnowledge生成を同一処理へ強制しないB-02要件を維持する。

---

## 5. Object RegistryとResultの境界

### REG-01 — Object IdentityをResult生成AIへ委ねない

Resultは既存`object_id`を参照するが、新しいtarget `object_id`をChatGPTに自由生成させない。

Persistent ID発行はSGOKB側の責務とする。

### REG-02 — ResultはObject Registry metadataをKnowledge本文として上書きしない

次はObject Registry metadataであり、通常のObject Knowledge Version内容と分離する。

- `object_id`
- `name`
- `aliases`
- `primary_class`
- `additional_classes`
- `status`
- `current_version`

ResultはValidation用contextとしてこれらをechoできるが、それだけでRegistry updateとして適用してはならない。

### REG-03 — Classification snapshotはpreconditionとして利用できる

Package / Resultには分析時点の`primary_class` / `additional_classes`を含められる。

Importerは現在のRegistry classificationと比較し、分析中にClassが変更されていた場合にstale / review対象とできる。

Result側のclassification文字列でObject Registryを自動変更しない。

### REG-04 — Registry変更提案はKnowledgeと分離する

分析中に次を発見することはあり得る。

- より適切なname
- 新しいalias
- Primary Class訂正候補
- Additional Class追加候補

これらを返す場合、通常Knowledgeとは別の`registry_proposals`相当領域へ置き、明示reviewなしで適用しない。

具体的proposal schemaと採用workflowはE-01 / H-04で決定する。

### REG-05 — Resultは`current_version`を指定・切替しない

どのVersionをcurrentにするかはImport / Versioning側の責務であり、ChatGPTが返す値ではない。

Result内に`current_version = ...`のような命令的fieldを持たせない。

---

## 6. ResultのKnowledge構造

Object Resultは論理上、少なくとも次の構造を表現できることを要件とする。

```text
Object Result
├─ binding / schema metadata
├─ target Object context
├─ generation provenance
├─ knowledge
│  ├─ summary
│  ├─ attributes / structured values
│  ├─ facets
│  └─ relations
├─ conflicts / uncertainties / gaps
├─ unresolved references
└─ registry proposals
```

最終JSONのfield配置・array/object形式はE-05で決定する。

### KNO-01 — summaryをversioned Knowledgeとして扱える

Object全体の要約をResultへ含められる。

summaryは単なる検索用snippetではなく、Object Knowledge Versionに属する派生KnowledgeであるためEvidence groundingを必要とする。

summaryを1つの巨大な自由文にして根拠対応を失わせず、必要に応じて後述Knowledge Statement単位へ分割できる構造とする。

### KNO-02 — structured attributes / valuesを保持できる

Object固有のscalar / structured valueをResultで表現できることを要件とする。

例:

- release date
- start / end date
- numeric property
- official designation
- language
- component number
- other typed metadata

これらをすべて自然言語Facetへ埋め込むことを要求しない。

一方、Object Registryの`name` / `class` / `status`等とは分離する。

属性key・型・cardinalityの詳細はE-02 / E-05で決定する。

### KNO-03 — Facetを主要な意味整理単位とする

Objectの意味的KnowledgeはClassに応じたFacetへ整理できることを要件とする。

例:

```text
Character
  personality
  values
  motivation
  behavior
  relationships
  abilities

Work
  themes
  worldview
  narrative
  tone

Concept
  definition
  properties
  implications
```

Facetは独立Objectではなく、特定Object Knowledge Version内部の意味的観点である。

### KNO-04 — RelationをObject Knowledgeの構造化要素とする

独立Object同士の意味関係をResultで表現できることを要件とする。

RelationをFacet内の自然文だけに閉じ込めず、検索・Graph traversal・MCP利用可能な構造化edgeとして保持できるようにする。

### KNO-05 — Result構造をClass固有固定列へ閉じ込めない

新しいClass / Facet / attribute / Relation Type追加のたびにObject Result全体のidentity contractを作り直さない。

共通Envelope + registry-driven / schema-driven extensionを基本とする。

### KNO-06 — Knowledge contentの言語を識別可能にする

Object Knowledgeの記述言語とSource / Evidence原文の言語を混同しない。

Resultには既定のKnowledge languageを記録でき、必要なら個別Statement等で言語差を表現できる構造とする。

翻訳されたKnowledge textを保存する場合も、B-03の原Evidenceを置換せずEvidence IDへgroundingする。

具体的language field / BCP 47等の採用はE-05で決定する。

### KNO-07 — temporal scopeをKnowledge Version時刻と分離する

Object Knowledge Versionの生成時刻だけでは、「その記述がいつ成立するか」を表せない。

時間依存するStatement / structured attribute / Relationについて、必要に応じて次のようなtemporal scopeを表現可能とする。

- as-of time
- valid from / valid to
- historical period
- Work内の時系列・continuity context

例えばSoftwareの仕様変更、Organization所属、Characterの時点別状態等を、Version作成日だけで現在事実と誤解しないようにする。

最終temporal schemaはE-02 / E-05で決定する。

---

## 7. Knowledge Statement

### STM-01 — Knowledge Statementをgroundingの論理最小単位として利用可能にする

Facetやsummary中の意味内容をEvidenceへ正確に対応させるため、Result内部に **Knowledge Statement** 相当の単位を持てることを要件とする。

Knowledge Statementは通常、1文〜短い段落程度の意味的にまとまった主張・説明である。

例:

```text
Facet: personality
  Statement A: 平静に見えるが、他者の期待を強く意識して行動する。
    Evidence: E12, E18
```

### STM-02 — Knowledge Statementを旧Fragmentの代替中心モデルにしない

Knowledge Statementは次の点で旧Fragmentと異なる。

- 全Evidenceから網羅的に大量生成することを要求しない。
- `fragments_per_evidence`のようなcoverage KPIを持たない。
- 独立Knowledge Objectではない。
- Source/Evidence Storeの中間生成物ではない。
- Result / Object Knowledge Version内部のgrounding単位である。
- 必要以上に文を原子化しない。

Statement数を増やすこと自体をKnowledge品質とみなさない。

### STM-03 — Statement IDはResult / Version内ローカル参照でよい

Statementを他要素から参照するためlocal identifierを持たせることはできるが、`object_id`や`evidence_id`と同等の永続Global Identityを要求しない。

新Version生成時に同じStatement IDを無理に維持することをB-04要件とはしない。

Persistent statement identityが必要と判明した場合は実利用後に再検討する。

---

## 8. Derivation / epistemic要件

### EPI-01 — StatementがEvidenceからどのように導かれたかを区別する

LLM出力の「Fact」というラベルをそのまま客観的真実性とみなさない。

代わりに、Knowledge StatementがEvidenceからどのように導出されたかを表す`derivation_kind`相当概念を持てることを要件とする。

初期論理語彙は次を基準とする。

| kind | 意味 |
|---|---|
| `direct_statement` | Evidenceで明示された内容の近い言い換え・整理 |
| `synthesis` | 複数Evidenceを統合した比較的直接的なまとめ |
| `interpretation` | Evidenceから導いた分析・意味解釈 |
| `reported_view` | Sourceや集団が示す意見・評価・認識を帰属付きで整理したもの |

具体的enum名はE-05で最終化できる。

### EPI-02 — `direct_statement`を客観的Fact保証としない

B-03で定義したとおり、Evidenceは「Sourceがそう記述している」ことの根拠であって真実性そのものではない。

したがって`direct_statement`は、Sourceに明示されていることを示すだけであり、外部世界で客観的に真であることを意味しない。

### EPI-03 — InterpretationにもEvidence groundingを要求する

`interpretation`だからEvidenceなしで自由推論してよいとはしない。

性格、テーマ、動機、象徴性、因果等を解釈する場合も、その解釈の根拠となるEvidence IDを明示する。

### EPI-04 — 数値confidenceを必須としない

LLMが生成する`0.93`等の数値を校正済み確率として扱わない。

B-04標準contractでは数値confidenceを必須にしない。

不確実性は、Evidence role、conflict、insufficient evidence、limitation等の明示構造で表現することを優先する。

### EPI-05 — `reported_view`はattributionを失わない

レビュー、批評、世評、community perception等を`reported_view`として保存する場合、「誰がそう評価・認識しているか」を追跡できなければならない。

Source / publisher / named Object / community等へのattributionを、単なるObject自身の客観属性へ変換しない。

「一部レビューでは高く評価される」と「高く評価される作品である」を無条件に同一Knowledgeへ縮約しない。

---

## 9. Evidence grounding要件

### GRD-01 — Import対象KnowledgeはEvidence IDへgroundingする

標準Object Resultから新Object Knowledge VersionへImportするKnowledge Statement、structured attribute、Relationは、原則として1件以上の保存済みEvidence IDを参照しなければならない。

Source IDだけをgroundingの最小単位としてはならない。

### GRD-02 — Evidence reference roleを表現可能にする

単にEvidence ID一覧を持つだけでなく、そのEvidenceがKnowledgeに対してどの役割を持つかを表現できることを要件とする。

初期論理roleは少なくとも次を扱える。

- `supports`
- `contradicts`
- `contextualizes`

物理語彙はE-03 / E-05で確定する。

### GRD-03 — ResultはPackageに含まれたEvidenceを標準grounding範囲とする

標準Google Drive / ChatGPT workflowでは、Resultが参照できるEvidence IDを、入力Package manifestに含まれるEvidenceへ制限する。

これにより、次を防止する。

- ChatGPTが存在しないEvidence IDを創作する。
- 入力に含まれていない資料を見たかのように引用する。
- PackageからResultへの再現性が失われる。

ImporterはEvidence IDのDB存在確認に加え、Package membershipをValidationできなければならない。

### GRD-04 — Source IDだけの引用へdowngradeしない

Evidence IDが利用できる場合、RelationやStatementの根拠をSource IDだけへ粗くまとめない。

Source metadataは表示・フィルタ・監査用に追跡できるが、groundingは具体的Evidenceを優先する。

### GRD-05 — Evidence本文をResultへ正本複製しない

Result内に長いquoteやEvidence本文を再保存して、それを新しい根拠正本にしない。

必要な表示用excerptを含める場合も、Evidence IDを正本参照とし、excerptは検証可能な派生表示として扱う。

### GRD-06 — orphan citationを禁止する

Resultに列挙したEvidence referenceは、どのStatement / attribute / Relation / conflict等を根拠付けるかが明確でなければならない。

「使用したEvidence一覧」だけを末尾へ置き、各Knowledgeとの対応が不明な形式を標準contractとしない。

### GRD-07 — 更新Packageはcarry-forward Knowledgeの根拠も再現可能にする

B-04では更新Resultを原則full snapshotとするため、更新後も残すKnowledgeをChatGPTが評価できるよう、Package builderはcurrent Versionが参照するEvidenceを必要に応じてPackageへ含めることを要件とする。

新規Evidenceだけを渡し、旧Knowledgeの根拠を見せないまま全文再生成させる方式を標準にしない。

token budgetとの調整はF-04 / G-01で具体化する。

---

## 10. Facet要件

### FAC-01 — Facet keyは管理された語彙を使用する

Resultが任意のFacet名を無制限に生成する方式を標準としない。

Primary Class / ancestor Class / Additional Classに対応するFacet profileまたは共通Facet vocabularyから利用可能Facetを決定できるようにする。

Facet Registry / profileの物理実装はE-02で決定する。

### FAC-02 — 専用Facet未実装ClassでもResultを生成可能にする

初期Class Registryへ登録済みでも専用Facet profileがまだないClassを許容する。

その場合でも、共通summary / attributes / common facet等の共通contractでResultを保持できなければならない。

専用Facetがないことを理由に別Classへfallbackしない。

### FAC-03 — Facetごとに分析状態を区別可能にする

Facetについて少なくとも論理上、次の状態を区別できることが望ましい。

- grounded contentがある
- evidence不足
- 対象Objectにはnot applicable
- package / process上not analyzed

field名や必須性はE-05 / G-03で決定する。

「Facetが出力にない」ことを自動的に「その特徴が存在しない」と解釈しない。

### FAC-04 — Facet内で矛盾するKnowledgeを保持できる

personality等でSource間に異なる描写がある場合、一方を削除して単一結論だけにしなくてよい。

conflict / uncertainty要件とEvidence roleを用いて、複数のgrounded viewを保持できるようにする。

---

## 11. Structured Attribute要件

### ATR-01 — structured valueと自然言語説明を分離可能にする

日付・数値・識別子・短いcategory等を、自然言語Statementへだけ埋め込まずtyped valueとして保持できるようにする。

### ATR-02 — AI生成attributeにもEvidence groundingを要求する

ChatGPTがResultとして提案するversioned attributeは、原則Evidence参照を持つ。

Object Registryで人間が直接登録したmetadataと、Result由来Knowledge attributeを混同しない。

### ATR-03 — 不明値を推測で埋めない

Evidenceから値を確定できない場合、架空のdefault値や推測値を生成しない。

unknown / absent / not applicable等の意味をSchema上で区別する必要がある場合はE-02 / E-05で定義する。

---

## 12. Relation要件

### REL-01 — Relationは方向を曖昧にしない

ResultのRelationはsubject / predicate / objectの意味を明示できなければならない。

標準1 Object Resultでは少なくとも片側endpointがtarget Objectであることを要件とする。

### REL-02 — Relation targetは既存Object IDを優先する

Result中の確定Relationは、Relation先をname文字列だけで指定せず、既存Object IDを利用する。

同名Objectの誤接続を防ぐためである。

### REL-03 — 存在しないObject IDをAIに発行させない

ChatGPTが新しい関連対象を発見しても、存在しないUUID等を作成してRelation targetへ入れてはならない。

既存Objectへresolveできない対象は`unresolved reference`として別領域へ返す。

### REL-04 — AI生成RelationはEvidence groundingを持つ

Resultから提案されるRelationは、原則としてその関係を支持・文脈化するEvidence IDを持つ。

Relationの存在をObject名共起だけで無根拠に確定しない。

### REL-05 — Relation Typeを無制限自由文字列にしない

検索・MCP・Graph traversalで再利用するため、Relation Typeはregistryまたは管理されたvocabularyでValidation可能にする。

Relation Type Registryの物理schema、方向、inverse、symmetry等はE-01以降で決定する。

未知Relation Typeが必要な場合は、自動的に近い別predicateへ変換せずproposal / reviewへ送れる設計とする。

### REL-06 — Resultがtarget以外の2 Object間Relationを勝手に更新しない

Object AのResult内で、B→CというAと無関係なRelationを正本更新することを標準contractにしない。

必要なら別Object Resultまたは明示的Relation管理workflowへ送る。

これにより1 Result = 1 Object transaction境界を維持する。

---

## 13. Conflict / Uncertainty / Gap要件

### CUG-01 — 矛盾を強制的に単一結論へ潰さない

B-03で保持したSource間矛盾を、Object Result生成時に根拠なしで解消しない。

例えば次を表現できる必要がある。

```text
Statement A
  supports: E1, E2
  contradicts: E9
```

または互いに競合する複数StatementとそのEvidence集合を保持できる。

### CUG-02 — unresolved conflictを明示可能にする

どちらの記述を採用すべきかEvidenceだけでは判断できない場合、`conflict` / `unresolved`相当として保持できることを要件とする。

無理に多数決やSource件数だけで解決しない。

### CUG-03 — insufficient evidenceを正常に返せる

Packageに十分なEvidenceがない場合、ChatGPTが空白を創作して埋める必要はない。

Facetやattributeについて`insufficient_evidence`相当の結果を返せるようにする。

### CUG-04 — Knowledge gap / open questionをKnowledge assertionと分離する

「不明」「追加Sourceが必要」「AとBのどちらか判定不能」等は、確定Statementとは別のgap / limitation情報として保持できるようにする。

これらを事実assertionとして検索・Embeddingして誤解を生まないようにする。

### CUG-05 — 不確実性を数値confidenceだけへ縮約しない

Evidence不足・Source矛盾・推論距離・Object同定不確実性は別問題である。

1つのconfidence scoreへまとめず、可能な限り構造化された理由として保持する。

---

## 14. Unresolved Reference / Proposal要件

### URP-01 — 新Object候補をRelation targetへ直接昇格させない

Result分析中に未登録の人物・作品・概念等を発見した場合、それ自体を自動Object作成・自動Relation作成しない。

少なくとも次を候補情報として返せる構造を許容する。

- human-readable label
- candidate class
- relation context
- supporting Evidence IDs
- disambiguation note

### URP-02 — unresolved referenceはKnowledge Storeの確定Relationと分離する

未解決対象は、Object登録・同一性確認後に既存Object IDへresolveして初めてRelation化する。

### URP-03 — Registry proposalとnew Object proposalを区別する

既存target Objectのname / alias / class訂正候補と、新しい別Objectの発見候補を同じ処理にしない。

前者はRegistry proposal、後者はObject candidate / unresolved referenceとして扱う。

---

## 15. Generation Provenance要件

### GEN-01 — Result生成来歴を保持する

Resultがどの条件で生成されたかを後から追跡できなければならない。

論理上、少なくとも次を記録可能とする。

- result schema version
- target object ID
- package identity / hash
- base Object Knowledge Version
- instructions / prompt contract version
- generator kind
- provider / application
- model label / model version（取得できる場合）
- generation timestamp
- import timestamp（Import側）

### GEN-02 — 不明なmodel情報を捏造しない

ChatGPT Web/Desktop等で正確なmodel revisionが取得できない場合、推測値を保存しない。

`unknown` / unavailableを許容し、取得できた範囲だけをprovenanceとして残す。

### GEN-03 — AI providerをKnowledge semanticsへ埋め込まない

同じObject Result contractを、将来ChatGPT以外のAIや人間編集Toolでも利用可能にする。

Knowledge内容を`chatgpt_summary`等のprovider固有field名へ固定しない。

### GEN-04 — 原Result artifactを監査可能にする

ImporterがResultを正規化してDBへ分解保存する場合でも、入力された原Result JSONそのもの、またはその不変hashと保存参照を監査可能にする。

Validation処理が入力Resultをsilent rewriteしてから正本扱いしない。

---

## 16. Full Snapshot / Version更新要件

### VER-01 — 初期標準Resultはfull Knowledge snapshotとする

B-04時点の標準workflowでは、Object Resultをdelta patchではなく、次期Object Knowledge Versionの完全な構造化snapshotとして扱う。

```text
Version 3 + Package
  ↓
Result = candidate Version 4 full snapshot
```

これにより、patch適用順序、field delete semantics、partial update競合を初期設計から排除する。

### VER-02 — omissionの意味を曖昧にしない

full snapshot方式では、ResultからKnowledge要素が消えることは新Versionでその要素を採用しないことを意味し得る。

そのためcurrent Object KnowledgeをPackageへ含め、Diff / Reviewで削除を確認可能にする。

Facet自体の未出力を自動削除と解釈するか等の細部はE-04 / E-05で明文化するが、silent data lossを許容しない。

### VER-03 — Patch方式は初期標準にしない

大量Objectやtoken制約等で将来差分更新が必要になる可能性はあるが、B-04ではpatch Resultを必須機能にしない。

導入する場合もbase version preconditionと明確なadd / replace / remove semanticsを要求する。

### VER-04 — Version IDはImporter側が発行する

ChatGPT Resultが永続`version_id`を自由生成し、それを正本として採用する方式にしない。

Validation / Import成功時にSGOKB側がVersion Identityを割り当てる。

### VER-05 — Result再Importを検出可能にする

同じResult artifactを誤って複数回Importし、同内容Versionを無制限作成しないよう、Result artifact hash / import provenance等で重複候補を検出可能にする。

具体的idempotency policyはH-02で決定する。

---

## 17. Validation要件

Result Validationは少なくとも次の層を分離する。

```text
1. Syntax / Schema Validation
2. Binding / Precondition Validation
3. Referential Validation
4. Grounding / Provenance Validation
5. Domain Contract Validation
6. Human / Semantic Review（必要に応じて）
```

### VAL-01 — Schema validation

少なくとも次を機械的に検証可能とする。

- JSONとしてparse可能。
- schema versionが対応範囲内。
- required fieldが存在する。
- field typeが正しい。
- unknown fieldを許可するか拒否するかがschemaで明示される。
- local ID重複等の構造矛盾がない。

### VAL-02 — Object binding validation

- target object IDが存在する。
- Package targetとResult targetが一致する。
- base version preconditionが一致する。
- classification snapshot等のpreconditionを必要に応じて確認する。

### VAL-03 — Evidence validation

- 参照Evidence IDが存在する。
- 標準workflowでは参照EvidenceがPackage manifestに含まれる。
- Evidence provenance chainが破損していない。
- Evidence reference roleが許可語彙である。

### VAL-04 — Facet / Attribute validation

- Facet keyが対象Classで利用可能である。
- attribute key / value typeがschemaへ適合する。
- 必須groundingが存在する。
- 専用Facet未実装Classでも共通contractは利用できる。

### VAL-05 — Relation validation

- Relation Typeが既知またはreview可能状態である。
- subject / object endpointが明確。
- 確定Relation target Objectが存在する。
- standard Resultではtarget ObjectがRelation endpointに含まれる。
- AIが未知Persistent IDを発行していない。
- grounding要件を満たす。

### VAL-06 — Registry proposalをKnowledge Importと分離する

Registry proposalが含まれていても、通常Object Knowledge Importの副作用として自動適用しない。

### VAL-07 — Validation成功を意味品質合格とみなさない

JSON Schema、ID存在確認、Evidence参照整合等がすべて成功しても、次は自動的に保証されない。

- 解釈が妥当である。
- Evidenceを正しく読解している。
- 重要事項を取りこぼしていない。
- Relation predicate選択が最善である。
- Sourceの主張が現実に真である。

Prototype時代の「Schema適合 = Knowledge品質合格」という誤認を繰り返さない。

### VAL-08 — Validatorは意味内容を無断修復しない

不正field、存在しないID、型不一致等があった場合、Validatorが推測で別値へ置換してImportを続行しない。

明確なdeterministic normalization以外はreject / reviewへ送る。

---

## 18. Result status / partial result

### STA-01 — Evidence不足Resultを失敗JSONにしなくてよい

分析自体は正常に完了したがEvidence不足だった場合を、JSON parse error等の処理失敗と区別する。

論理上、例えば次の状態を区別できる設計とする。

- normal candidate
- partial / limited analysis
- insufficient evidence

具体的status名はE-05で決定する。

### STA-02 — partial ResultのImport policyを明示する

partial ResultをKnowledge VersionとしてImportできるかはH-02 / B-06でworkflowとして決定する。

少なくともpartialであることを失ってnormal Resultとして扱わない。

### STA-03 — processing failureとKnowledge gapを分離する

次を区別する。

- ChatGPTが不正JSONを返した。
- Result schema validationに失敗した。
- Evidenceが不足している。
- Objectについて本当に情報が存在しない。
- Facetがnot applicableである。

これらを単一`failed`へまとめない。

---

## 19. Markdown / Derived Representation要件

### REN-01 — Markdownを正本にしない

Markdownはaccepted Object Knowledge Versionから決定論的に生成可能な人間向け表示とする。

Markdown編集だけで正本Knowledgeが変更された状態を作らない。

### REN-02 — RendererはEvidence citationを再現できる

人間向けMarkdownでは、Statement / Relation / attributeからEvidence / Sourceへ辿れるcitationを表示できることを要件とする。

Citation labelの見た目はH-03で決定する。

### REN-03 — ChatGPT生成Markdownは補助成果物とする

ChatGPTがResult JSONと同時にMarkdownを生成した場合でも、そのMarkdownをDBへparseし直してKnowledge正本にしない。

必要ならpreviewとして利用する。

---

## 20. Security / Untrusted Input要件

### SEC-01 — Resultを外部生成されたuntrusted inputとして扱う

JSON内の文字列・path・URL・Markdown・HTML等を信頼してfile operationやcommand実行へ直接利用しない。

### SEC-02 — Resultに任意file write命令を持たせない

ResultはKnowledge dataを返す契約であり、`write_to`, `delete_file`, `execute`等の操作命令を標準schemaへ含めない。

### SEC-03 — Package外Evidence / 外部URLを自動取得しない

ResultにURLや新Source候補が含まれていても、Importerが自動でWeb取得してEvidence化し、そのままKnowledgeへ混ぜることをしない。

新Sourceは通常のCapture / Import workflowへ戻す。

---

## 21. 論理例

以下は概念を説明するための例であり、E-05の最終JSON Schemaではない。

```json
{
  "schema_version": "object-result-v1",
  "target": {
    "object_id": "obj-character-a",
    "primary_class": "Character",
    "additional_classes": []
  },
  "binding": {
    "package_id": "package-123",
    "package_hash": "...",
    "base_version": "version-3"
  },
  "knowledge": {
    "summary": [
      {
        "text": "他者への配慮を優先する傾向が一貫して描写される。",
        "derivation_kind": "synthesis",
        "evidence": [
          {"evidence_id": "ev-12", "role": "supports"},
          {"evidence_id": "ev-18", "role": "supports"}
        ]
      }
    ],
    "facets": [
      {
        "facet": "personality",
        "statements": [
          {
            "text": "自分の希望より周囲の期待を優先する場面がある。",
            "derivation_kind": "interpretation",
            "evidence": [
              {"evidence_id": "ev-22", "role": "supports"}
            ]
          }
        ]
      }
    ],
    "relations": [
      {
        "subject_object_id": "obj-character-a",
        "predicate": "appears_in",
        "object_object_id": "obj-work-b",
        "evidence": [
          {"evidence_id": "ev-04", "role": "supports"}
        ]
      }
    ]
  },
  "unresolved_references": [
    {
      "label": "未登録の組織名",
      "candidate_class": "Organization",
      "evidence_ids": ["ev-31"]
    }
  ]
}
```

重要なのはfield名ではなく、次の契約である。

- target Objectは既存IDでbindされる。
- ResultはPackage / base versionへbindされる。
- Knowledgeは構造化される。
- Statement / attribute / RelationはEvidenceへgroundingされる。
- unresolved targetに架空IDを割り当てない。
- Registry metadata変更は別proposalとする。

---

## 22. 旧Prototypeからの変更点

### 22.1 Final Document → Object Result

旧:

```text
Fragments
  ↓
Final Document / Structured Document
  ↓
Markdownが主要成果物
```

新:

```text
Evidence Package
  ↓
Object Result JSON
  ↓ Validation / Import
Object Knowledge Version
  ↓
Markdown / Search / MCP
```

### 22.2 Fragment ID citation → Evidence ID grounding

旧FinalではFragmentをcitation中間層として利用していた。

新SGOKBでは標準Knowledge Resultが直接Evidence IDへgroundingする。

```text
旧:
Final claim → Fragment → Evidence

新:
Knowledge Statement / Attribute / Relation → Evidence
```

### 22.3 Huge Document → Structured Facet / Relation

巨大な単一Markdownを完成品とするのではなく、summary / structured attribute / Facet / Relationを再利用可能な構造として保持する。

### 22.4 AI output = accepted Knowledge ではない

外部AI出力はcandidate Resultであり、Validation / Import / Versioningを経由する。

---

## 23. B-05 / Phase E-Hへの引き継ぎ

### B-05 Search

- accepted Object Knowledge Versionを検索対象とする。
- summary / Facet / structured attribute / Relationのlexical / semantic検索境界を決定する。
- Statementを独立検索単位へするかは、旧Fragment肥大化を再発させない観点で判断する。
- conflict / gap metadataを通常Knowledge検索へ混ぜるか分離するか決定する。
- class / facet / version / source / evidence等のfilterを定義する。

### E-01 Object schema

- Object Registry metadataとObject Knowledge Version dataを分離する。
- Relation Type vocabulary / Registryの物理表現を設計する。
- registry proposalを通常Knowledge importと分離する。

### E-02 Semantic Facet schema

- Facet Registry / Class-to-Facet profile。
- common FacetとClass固有Facet。
- Facet status / statement / attributeの配置。
- typed attribute key / value contract。

### E-03 Source / Evidence / Evidence Link / Provenance schema

- Statement / attribute / RelationからEvidenceへのLink。
- `supports` / `contradicts` / `contextualizes`等のEvidence role。
- Package membership Validation。
- Source / Snapshot / Rawまでのtracking。

### E-04 Versioning

- full snapshot Version semantics。
- base version precondition。
- stale Result処理。
- current Version切替。
- rollback / diff。
- omission / deletion semantics。

### E-05 JSON Schema

- Object Result Envelope。
- common Knowledge structure。
- derivation kind / reported-view attribution。
- Knowledge language / temporal scope。
- Facet / attribute / Relation extension。
- unresolved reference / proposal。
- generation provenance。
- partial / insufficient evidence状態。

### G-01 / G-02 Evidence Package

- current Knowledgeを更新する場合、carry-forward Knowledgeを検証できるEvidenceをPackageへ含める。
- package ID / manifest hash / base versionをResult bindingへ渡す。

### G-03 instructions

- Evidence IDだけを引用する。
- Package外IDを創作しない。
- `direct_statement` / `synthesis` / `interpretation` / `reported_view`の使い分け。
- insufficient evidenceを創作で補わない。
- unknown Object IDを生成しない。

### H-01 Validator

- schema / binding / reference / grounding / domain validationを分離する。
- Validation成功と意味品質を区別する。

### H-02 Import

- Resultを新Versionへ変換する。
- persistent Version IDをSGOKB側で発行する。
- duplicate Result importを検出する。
- Registry proposalを自動適用しない。

### H-04 Diff / Review

- base Versionとcandidate Resultのsummary / attribute / Facet / Relation差分を確認可能にする。
- deletion / conflict / proposalを目立たせる。

---

## 24. B-04で意図的に決めない事項

次は後続Taskへ延期する。

- 最終JSON field名・JSON Schema syntax。
- Result schema version文字列。
- result artifact IDの具体形式。
- Object Knowledge Version ID形式。
- Statement local ID形式。
- Facet Registry / Facet profileの物理schema。
- Relation Type一覧・inverse / symmetry定義。
- Attribute type registry。
- Evidence roleの最終語彙。
- conflict recordの最終JSON形状。
- partial Resultを自動Importできるか。
- stale Resultのrebase / merge algorithm。
- delta / patch Resultを将来採用するか。
- Review UI。
- Markdown citation format。
- generator provenanceの保存table。
- Result artifactのretention期間。

---

## 25. 完了条件への対応

### JSONを機械向け正本とする

Object Resultのcanonical exchange artifactをStructured JSONとし、Markdownを派生表示へ限定した。

### Primary / Additional Classに応じたFacetを定義可能にする

Facet vocabularyをClass hierarchy / profileから適用できる契約とし、専用Facet未実装Classでも共通contractを利用できるようにした。

### Relationを構造化する

Relationをsubject / predicate / object + Evidence groundingを持つ構造化Knowledgeとして定義し、未登録Objectをunresolved referenceへ分離した。

### Evidence参照を保持する

Statement / attribute / Relationを具体的Evidence IDへgroundingし、標準workflowではPackage membershipまでValidationする要件とした。

### 生成来歴を保持する

Package、base Version、instructions、provider / model（取得可能な範囲）、generation timestamp等を追跡可能にした。

### Versioningへ安全に接続する

Resultをcandidateとし、full snapshot、base version precondition、stale detection、Importer-side Version ID発行を定義した。

### 旧Fragment中心設計を再導入しない

Knowledge StatementをResult内部のgrounding単位に限定し、全Evidenceから大量生成する独立Fragment modelへ戻さないことを明記した。

---

## 26. 結論

SGOKBのObject Resultは、**1つの既存Objectについて、特定Evidence Packageと必要に応じて既存Knowledge Versionを入力として生成される、Evidence-groundedな構造化Knowledge Version候補**とする。

ResultはJSONを機械向け交換正本とし、summary / structured attribute / Facet / Relationを構造化して保持する。Knowledge StatementはEvidence groundingのためのResult内部単位として使用できるが、旧Fragmentのような独立大量生成対象にはしない。

Resultから確定Knowledgeへ進むには、Schema、Object binding、Package/base Version、Evidence、Facet、Relation等のValidationを必須とし、AI出力を直接正本へ昇格させない。

B-04は以上をもって完了とし、B-05 Search / Retrieval要件も完了済みである。次のTaskは `B-06 [P0] 人間工程と自動工程を要件として分離する` とする。

**Status: Complete (2026-10-10)**
