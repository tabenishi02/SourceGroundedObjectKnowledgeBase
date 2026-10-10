# Source Grounded Object Knowledge Base — Object要件

更新日: 2026-10-10

- Task: `B-02 [P0] Object要件を定義する`
- Status: Accepted
- Related:
  - `docs/requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md`
  - `docs/decisions/KNOWLEDGE_BASE_REDESIGN_DECISION.md`
  - `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`
  - `docs/requirements/OBJECT_TYPE_MODEL.md`
  - `docs/requirements/OBJECT_TYPE_BOUNDARIES.md`
  - `docs/reference/KNOWLEDGE_BASE_ASSET_CLASSIFICATION.md`
  - `docs/reference/KNOWLEDGE_BASE_DEPENDENCY_INVENTORY.md`

## 1. 本書の位置づけ

本書は、SGOKBでKnowledgeを管理する中心単位である **Object** の要件を定義する。

B-02では、Objectの意味、同一性、共通属性、Classification、ライフサイクル、Versionとの関係を要件として固定する。

一方、次は後続Taskへ委ねる。

- Source / Evidenceとの詳細な関連付け: B-03で完了。`SOURCE_EVIDENCE_REQUIREMENTS.md`を正本とする
- Structured Object Result / Facet / Relation / Evidence参照の交換形式: B-04で完了。`OBJECT_RESULT_REQUIREMENTS.md`を正本とする
- 検索・類似検索: B-05で完了。`SEARCH_REQUIREMENTS.md`を正本とする
- 物理DB schema / migration: E-01以降
- Facet schema: E-02
- Evidence Link / Provenance schema: E-03
- Versioningの物理実装: E-04
- JSON Schema: E-05

したがって、本書の属性名は**論理契約**であり、そのままSQL列名になることを要求しない。

---

## 2. Objectの定義

SGOKBにおけるObjectとは、ユーザーが長期的にKnowledgeを蓄積・検索・比較・再利用したい**外部世界の意味的対象を表す、永続的な論理識別単位**である。

Objectは次のいずれでもない。

- Webページそのもの
- Source / Evidenceそのもの
- フォルダやファイルパス
- 生成済みMarkdown Document
- 1回のChatGPT出力
- 1つのKnowledge Version

例えばCharacter Objectは「そのキャラクターという対象」を表し、そのObjectについて複数SourceからEvidenceを蓄積し、複数回Knowledgeを更新してもObject自体の同一性は維持される。

概念的には次の分離を採用する。

```text
Object Identity
  ├─ current display metadata
  ├─ Object Knowledge Version 1
  ├─ Object Knowledge Version 2
  ├─ Object Knowledge Version 3 ← current_version
  ├─ Relation → Other Object
  └─ Evidence Link → Source / Evidence
```

ObjectはKnowledgeの「入れ物」ではなく、Knowledgeを継続的に結び付ける**安定した意味上のアンカー**である。

---

## 3. 共通Object contract

すべてのObjectは、Primary Classに関係なく少なくとも次の共通概念を持つ。

| 属性 | 要件上の意味 |
|---|---|
| `object_id` | SGOKB内部でObjectを一意に識別する安定ID |
| `primary_class` | Class Registry上の主要Class。必須・1件 |
| `additional_classes` | 補助的なClass membership。0件以上 |
| `name` | 現在の代表表示名 |
| `aliases` | 別名、表記揺れ、旧名、翻訳名等の0件以上の集合 |
| `status` | Object自体のライフサイクル状態 |
| `current_version` | 現在有効なObject Knowledge Versionへの参照。Knowledge未生成なら空を許容 |
| `created_at` | Object登録時刻 |
| `updated_at` | Object registry上の最終更新時刻 |

物理schemaでは`aliases`を別tableへ分離する等の正規化を許容する。

---

## 4. Object要件

### OBJ-01 — Objectを永続的な意味識別単位とする

Objectは、特定のSource、Evidence、Document、Prompt、AI model、ファイル配置に依存しない永続識別単位でなければならない。

Source追加、Knowledge再生成、名称変更、Document再出力等によって同一Objectの`object_id`を作り直してはならない。

### OBJ-02 — `object_id`を表示名・パス・Versionから独立させる

`object_id`はSGOKB内部で一意かつ安定でなければならない。

少なくとも次をID生成・同一性判定の唯一の根拠としてはならない。

- `name`
- `aliases`
- URL
- Source ID
- フォルダ名 / ファイル名
- Repository / Project名
- `primary_class` / `additional_classes`等のClassification
- Knowledge Version番号

これにより、名称変更、型分類の訂正、Repository名変更等があってもObject参照を維持できるようにする。

UUID / ULID等の具体的なID形式はE-01で決定する。

### OBJ-03 — `name`は代表表示名でありIdentityではない

各Objectは、人間が認識するための現在の代表表示名`name`を持つ。

`name`は変更可能であり、SGOKB全体で一意である必要はない。

同名の別対象を登録できなければならない。

例:

```text
Object A: name = "Alice", object_id = A
Object B: name = "Alice", object_id = B
```

名称衝突を理由にObjectを自動統合してはならない。

### OBJ-04 — `aliases`で表記差を吸収する

Objectは0件以上のaliasを持てなければならない。

aliasには少なくとも次を格納可能とする。

- 別名
- 略称
- 旧名
- 翻訳名
- 日本語 / 英語等の言語差
- 表記揺れ
- 検索上有用な公式別表記

alias自体もSGOKB全体で一意である必要はない。

aliasの種類・言語コード等の詳細属性を保持するかはE-01で決定する。

### OBJ-05 — 初期Class RegistryはB-02Dで採用したClassを原則すべて含む

初期Class Registryは、利用頻度の高い少数Classだけに限定しない。B-02Dで正式なObject Classとして採用されたClassは、原則として通常のObjectデータを蓄積し始める前に登録し、Primary ClassまたはAdditional Classとして利用可能にする。

`Character` / `Work` / `Concept`は、既存要件との互換性と主要ユースケースのため必ず初期Registryへ含め、専用Facet等の実装優先度も高くする。

#### `Character`

物語・作品等に登場するキャラクターを表す。`Agent`系Classの下位Classとして扱う。

#### `Work`

創作・著作・表現物として独立してKnowledgeを蓄積する対象を表す。`CreativeWork`系Classの下位Classとして扱う。

#### `Concept`

性質・思想・テーマ・概念等、Objectとして定義・比較・Relation付与する価値のある抽象対象を表す。

ただし、Character / Work / Conceptだけを先にRegistryへ登録し、それ以外の既知Classを後回しにすることを基本方針とはしない。Class Registryへの包含と、Class固有Facet / UI / validation / search等の専用機能実装優先度は分離する。

### OBJ-06 — ClassificationをClass Registryで拡張可能にする

利用可能Classは、閉じた1階層enumではなくClass Registryで管理し、Class間に`subclass_of`相当の階層を持てなければならない。

各Objectは1件の`primary_class`を必須とし、必要に応じて0件以上の`additional_classes`を持てる。初期Registry確定後に新しい知識領域が発生した場合も、新Classを追加してObject identityモデルそのものを作り直してはならない。

既知の正式Classが未登録であることを理由として、意味的に異なる`Concept` / `Work` / `Character`等へObjectを自動的に丸め込んではならない。必要ClassをRegistryへ追加・review・stagingする方式を優先する。

Class hierarchy、multiple classification、初期Registry包含方針、`instance_of` / `subclass_of`相当概念の論理契約は`OBJECT_TYPE_MODEL.md`を正本とする。具体的Class hierarchyと`Structural` / `Primary-eligible` / `Additional-only`境界は`OBJECT_TYPE_BOUNDARIES.md`を正本とする。Class Registryの物理実装とvalidation詳細はE-01 / E-05で決定する。

### OBJ-07 — Class固有Knowledgeは共通Object identityから分離する

`Character`、`Work`、`Concept`等で意味的に保持したい情報は異なるが、Class固有項目をすべて共通Objectの固定属性として持たせてはならない。

例えば次の情報はSemantic Facet等の拡張構造で表現する。

- Character: personality / values / motivation / behavior / relationships / role等
- Work: themes / worldview / narrative / tone等
- Concept: definition / properties / implications / related concepts等

具体的Facet schemaはE-02で定義する。

### OBJ-08 — `status`はObjectのライフサイクルを表す

`status`はKnowledgeの品質・信頼度・生成状態ではなく、Object registry上のライフサイクル状態を表す。

最低限、次の状態を表現できることを要件とする。

- `active`: 通常利用対象
- `archived`: 通常利用から外したが履歴・参照を保持する対象

新規Objectの既定`status`は`active`とする。

Knowledgeがまだ生成されていないことは`status`ではなく`current_version`が空であること等で表現する。

「confidence」「Evidence不足」「生成失敗」等をObject lifecycle statusへ混在させてはならない。

### OBJ-09 — 通常運用では破壊的削除よりArchiveを優先する

Objectが不要になった場合、通常のユーザー操作ではまず`archived`として参照可能性を保持する。

Objectを削除した結果、過去Version、Relation、Evidence Link、外部参照が別Objectを誤って指す状態を作ってはならない。

Hard delete、merge、split等の管理操作が必要な場合の具体的手順はE-01以降で設計する。

削除済みObject IDを別Objectへ再利用してはならない。

### OBJ-10 — Object IdentityとKnowledge Versionを分離する

Objectそのものと、そのObjectについて現在保存しているKnowledgeは別のライフサイクルを持たなければならない。

同一Objectに対し、Knowledge更新のたびに新しいVersionを追加できる構造を前提とする。

```text
object_id = stable

version 1
version 2
version 3 ← current_version
```

Knowledge Versionが増えても`object_id`は変化しない。

Versionの不変性、rollback、current切替等の詳細はE-04で定義する。

### OBJ-11 — `current_version`が存在しないObjectを許容する

ユーザーは、Knowledge生成前にObjectだけを登録できなければならない。

したがって、新規Objectについて`current_version = null`相当の状態を許容する。

これは異常状態ではない。

例:

```text
Object登録
  ↓
Source収集
  ↓
Evidence Retrieval
  ↓
Knowledge生成
  ↓
初回Object Knowledge Version作成
```

Object registrationとKnowledge generationを同一transactionへ強制してはならない。

### OBJ-12 — Objectは特定Sourceに所有されない

Object Identityを特定のWebページやSourceの子要素として扱ってはならない。

同一Objectについて複数Sourceを根拠として利用でき、同一Sourceが複数Objectの根拠になれる構造を前提とする。

```text
Object A ─┬─ Source 1
          ├─ Source 2
          └─ Source 3

Source 4 ─┬─ Object B
          └─ Object C
```

ObjectとSource / Evidenceの詳細な多対多契約はB-03で確定済みであり、`SOURCE_EVIDENCE_REQUIREMENTS.md`を正本とする。

### OBJ-13 — Object間の構造を物理フォルダ階層へ依存させない

シリーズ / 派生作品 / キャラクター等の論理構造を、Objectのファイル配置や親フォルダによってIdentity化してはならない。

Object間の意味的な所属・派生・登場・関連はRelationとして表現できる構造を前提とする。

RelationのResult上の方向・Object ID参照・Evidence grounding等の論理契約はB-04で定義済みであり、Relation Type RegistryとEvidence Linkの物理schemaはE-01 / E-03で定義する。

### OBJ-14 — 同一性は名前ではなく「同じ意味対象を指すか」で判断する

Objectの新規作成・既存Objectへの統合では、「同じ文字列か」ではなく「同じ意味対象を継続的に指しているか」を判断基準とする。

したがって、次を許容する。

- 同じ対象の名称変更 → 同じObject
- 同じCharacterが複数Workへ登場 → 原則として同じObject + Relation
- 同名だが別のCharacter / Work → 別Object
- 同じ名称でも設定上別個体・別世界・別continuityとして独立管理したい対象 → 別Object

SGOKBは名称一致だけでObjectを自動mergeしてはならない。

Identityが曖昧な場合は、誤統合よりも別Objectとして保持し、人間が明示的に判断できることを優先する。

### OBJ-15 — CharacterのWork所属をObject Identityへ埋め込まない

Characterは、特定Work配下の物理子要素としてIdentity化しない。

同一Characterが複数Workへ登場する場合、それぞれについてCharacter Objectを複製するのではなく、同じ意味上のCharacterである限り1つのObjectとして扱い、Workとの関係をRelationで表現することを基本とする。

一方、別continuity・別個体・別人格などを独立したKnowledge対象として扱う必要がある場合は、別Objectを作成できる。

どこまでを「同一Character」とみなすかを自動推論のみで確定してはならない。

### OBJ-16 — CreativeWork構造はClass + Relationで表現する

B-02Dでは`Work` / `Series` / `Franchise` / `Episode` / `Chapter` / `Volume` / `Season` / `Arc`等をClass Registry上で区別する。SeriesやFranchiseを単なるWork属性へ押し込まない。

個別Object間の包含・派生・順序はRelationで表現し、Class hierarchyだけで作品構造を表現しない。

例:

```text
Series Object
  ├─ includes → Work Object A
  └─ includes → Work Object B

Work Object B
  └─ has_part → Episode Object
```

親Objectの`object_id`を子ObjectのIDへ埋め込む等、構造変更によってIDが変わる設計を採用してはならない。詳細境界は`OBJECT_TYPE_BOUNDARIES.md`を正本とする。

### OBJ-17 — Concept系Objectは外部世界の意味対象として扱う

ConceptおよびTheme / Ideology / Trait / Emotion / Motivation / StateConcept / RoleConcept / ArtifactTypeConcept等のConcept系Objectは、作品横断で参照・比較・Relation付与できる抽象概念を表す。

例:

- 自己犠牲
- 復讐
- 成長
- 忠誠
- 孤独

SGOKBが保持するのは「自己犠牲というConceptの意味・性質・他Objectとの関係」である。

「ユーザーは自己犠牲を好む」のようなユーザー自身に関する推論はConcept Objectへ保存しない。これはUserPreferenceDiscoverySystem（UPDS）の責務である。

SGOKB / UPDSの詳細な境界はPhase Cで確定する。

### OBJ-18 — Object参照は名称変更・Version更新後も有効でなければならない

Relation、Evidence Link、MCP等の外部アクセス、将来のUPDS参照は、可能な限り安定した`object_id`を利用する。

`name`を外部参照keyの正本としてはならない。

これにより、Objectの表示名変更やalias追加、Knowledge Version更新によって既存Relationや外部参照が切断されないようにする。

### OBJ-19 — Object registry metadataの変更とKnowledge内容の変更を区別する

少なくとも次の変更は、Object Identityを変更するものではない。

- `name`の訂正
- alias追加・削除
- `status`変更
- `primary_class` / `additional_classes`の分類訂正（意味対象自体が同一である場合）

一方、性格、テーマ、定義等の意味的Knowledgeの変更はObject Knowledge Versionとして扱う。

Registry metadataの変更履歴をどの粒度で監査するかはE-01で決定する。

### OBJ-20 — Class追加・再分類が既存Object contractを壊してはならない

新しいClassをClass Registryへ追加しても、既存のCharacter / Work / Conceptの`object_id`、Relation参照、Version参照、Source / Evidence参照を変更する必要がない構造とする。

同一意味対象のPrimary Class変更やAdditional Class追加もObject Identityを変更する理由にしてはならない。Class固有Knowledgeは共通Object contractではなく拡張構造で持つ。

---

## 5. Object identity判定の例

### 5.1 同名だが別対象

```text
"Alice" (作品AのCharacter)
"Alice" (作品BのCharacter)
```

同名でも意味対象が別なら別`object_id`とする。

### 5.2 名称変更

```text
旧name → 新name
```

同じ意味対象である限り`object_id`は維持し、旧nameは必要に応じてaliasへ残せる。

### 5.3 Characterが複数Workへ登場

```text
Character X
 ├─ appears_in → Work A
 └─ appears_in → Work B
```

同一CharacterであればCharacter Objectを複製しない。

### 5.4 シリーズと派生作品

```text
Work: Series A
Work: Series A / Title B
Work: Series A / Title C
```

独立してKnowledgeを保持したい単位ごとにWork Objectを作り、Relationでシリーズ構造を表現する。

### 5.5 ConceptとPersonal Inference

```text
SGOKB:
Concept = "自己犠牲"
Character A -- embodies --> 自己犠牲

UPDS:
User -- tends_to_prefer --> 自己犠牲
```

外部世界のConcept定義はSGOKB、ユーザー嗜好推論はUPDSへ分離する。

---

## 6. 共通属性の要件まとめ

| 属性 | 必須性 | Mutable | 一意性 | 備考 |
|---|---|---|---|---|
| `object_id` | 必須 | 原則不可 | 全SGOKBで一意 | Identityの正本 |
| `primary_class` | 必須 | 訂正可能 | 非一意 | B-02Dで採用されClass Registryへ登録されたClassから選択 |
| `additional_classes` | 0件以上 | 可 | 非一意 | 補助Classification |
| `name` | 必須 | 可 | 非一意 | 代表表示名 |
| `aliases` | 0件以上 | 可 | 非一意 | 表記差・旧名等 |
| `status` | 必須 | 可 | 非一意 | 新規登録時の既定値は`active` |
| `current_version` | 任意 | 可 | - | Knowledge未生成時は空 |
| `created_at` | 必須 | 不可 | - | 登録監査用 |
| `updated_at` | 必須 | 可 | - | Registry metadata更新用 |

この表は論理要件であり、DBで全項目を同一tableへ格納することを要求しない。

## 7. B-02で確定しない事項

B-02では次を意図的に確定しない。

- `object_id`の具体形式
- SQL table / column / index
- Class Registry / Class hierarchyの物理実装
- aliasのlanguage / category schema
- Relation type一覧
- Relationの方向・対称性
- Facet一覧とClass別必須Facet
- Object Result JSON形式
- Evidence Link schema
- merge / split / redirectの具体アルゴリズム
- Hard delete管理手順
- Search ranking
- Embedding対象・index設計
- MCP Tool名・response schema

これらは後続Phaseで、本書のIdentity要件を壊さない形で具体化する。

---

## 8. 旧PrototypeのEntityとの違い

旧PrototypeのEntityは、Fragment生成・Final Document生成対象を指定する役割が強かった。

新しいObjectは、生成処理の一時的Targetではなく、Knowledge Base全体で長期参照されるIdentityである。

```text
旧Prototype:
Entity
  ↓
Fragment
  ↓
Final Document

新SGOKB:
Stable Object Identity
  ├─ Versioned Knowledge
  ├─ Facets
  ├─ Relations
  ├─ Evidence Links
  ├─ Search / Similarity
  └─ MCP / external references
```

したがって、既存Entity tableを単純に名称変更するだけではObject要件を満たすとは限らない。

既存Entity IDの移行可否・保持方法はA-03の調査結果を踏まえ、E-01 / Phase Lで具体化する。

---

## 9. B-02完了条件

B-02は次を満たした時点で完了とする。

- ObjectがSource / Document / Versionから独立した安定Identityとして定義されている。
- Character / Work / Conceptを含め、B-02Dで正式採用したObject Classを初期Class Registryへ原則登録する方針が定義されている。
- Class Registry包含とClass固有機能の実装優先度が分離されている。
- 稼働後もClassを追加でき、multiple classificationを扱える要件が定義されている。
- `object_id` / `primary_class` / `additional_classes` / `name` / `aliases` / `status` / `current_version` / timestampの共通概念が定義されている。
- 同名別Object、名称変更、複数Work所属等のIdentity判断方針が定義されている。
- Object lifecycleとKnowledge Versionが分離されている。
- ConceptとUPDS Personal Inferenceの境界がB-02レベルで明確である。
- 物理schemaやFacet詳細を後続Taskへ適切に延期している。

以上をObject Identity要件の基準とする。B-02CでClassificationは`Primary Class + Additional Classes + hierarchical Class Registry`へ精緻化し、B-02Dで正式Class hierarchy、Object / Facet / Relation / value境界、初期Registry seed集合、fallback条件を`OBJECT_TYPE_BOUNDARIES.md`として確定した。B-03ではSource / Snapshot / Evidence / Provenance契約を`SOURCE_EVIDENCE_REQUIREMENTS.md`、B-04ではStructured Object Result / Evidence grounding / Version候補契約を`OBJECT_RESULT_REQUIREMENTS.md`、B-05ではObject / Facet / Statement / Relation / Evidenceの検索契約を`SEARCH_REQUIREMENTS.md`、B-06ではHuman Decision / local automation / external export / authoritative Import境界を`WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md`として確定した。B-07以降およびPhase E-Fはこれらの境界を前提とする。
