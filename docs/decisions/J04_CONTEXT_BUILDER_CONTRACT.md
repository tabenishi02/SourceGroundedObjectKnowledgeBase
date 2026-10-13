# J-04 Context Builder Contract

更新日: 2026-10-14

Status: Accepted

対象Task: `J-04 [P0] Context Builderを設計する`

## 1. Decision

SGOKBのContext Builderは、保存済みObject KnowledgeをLLMへ渡しやすい範囲へ**決定論的に選別するApplication / Retrieval機能**とする。

Context Builder自身は次を行わない。

- LLM推論
- 要約文の新規生成
- Knowledgeの意味的書き換え
- query意図の推測
- Embedding / reranking
- Web/APIへのfallback
- 複数Object間の新しい比較結論の生成
- ユーザー嗜好に基づくpersonalization

入力された`object_id`と用途profile、明示optionだけから同じKnowledge subsetを再現できることを優先する。

Context Builder contract versionは次とする。

```text
sgokb.context-builder.v1
```

J-04完了に伴い、J-02で予約していたMCP read Tool `build_context`をactive化する。

---

## 2. Architecture boundary

```text
Canonical Object Knowledge
        ↓
ObjectKnowledgeReader
        ↓
KnowledgeReadApplication.build_context()
        ↓
ContextBuilder
        ↓
MCPReadAdapter / build_context
        ↓
LLM / Agent
```

MCP AdapterはFacet選択や長さ制御を再実装しない。

Context BuilderもSQLite / Repositoryへ直接問い合わせず、Application側でcurrent / pinned Versionを解決したObject read modelを入力として受ける。

---

## 3. Public input

`build_context`の主要inputは次とする。

```text
object_ids
purpose = general | analysis | comparison | roleplay | creative
version_ids?
facets?
max_characters = 12000
include_attributes?
include_relations?
include_evidence_refs?
```

制約:

```text
Object数: 1..20
object_ids: duplicate禁止
max_characters: 512..200000
Facet明示指定: 最大50
```

`version_ids`で指定していないObjectはcurrent accepted Versionを使用する。

`version_ids`に`object_ids`外のObjectを指定した場合はerrorとする。

---

## 4. Purpose profile

用途はKnowledgeの意味を推論するものではなく、**固定されたFacet優先リストと既定include policyを選択するenum**として扱う。

### 4.1 `general`

一般的なObject説明用。

```text
overall
definition
background
properties
purpose
history
relationships
role
themes
function
usage
significance
```

既定:

```text
attributes = include
relations = include
evidence refs = include
```

### 4.2 `roleplay`

Character / Agent等の発話・行動一貫性に有用なKnowledgeを優先する。

```text
overall
background
appearance
personality
values
motivation
behavior
relationships
role
abilities
worldview
setting
culture
```

既定:

```text
attributes = include
relations = include
evidence refs = omit
```

Evidenceを省略するのはGroundingを否定するためではなく、roleplay実行Contextでprovenance ID列が占める量を減らすためである。必要なら明示optionで再度含められる。

### 4.3 `comparison`

複数Objectを同じ観点で比較しやすくする。

```text
overall
definition
properties
values
themes
behavior
relationships
purpose
history
structure
culture
scope
chronology
significance
function
usage
mechanism
causes
conditions
effects
requirements
constraints
rules
distribution
manifestations
```

これはE-02Bで整理したcross-class比較価値の高いshared Facetを中心にする。

既定:

```text
attributes = include
relations = omit
evidence refs = include
```

Relation edgeはObjectごとに量の偏りが大きく、公平なsemantic comparisonを崩しやすいため既定では除外する。必要なら明示指定で含める。

### 4.4 `analysis`

因果・構造・歴史・解釈等を広く検討する用途。

```text
overall
definition
background
history
structure
properties
purpose
function
mechanism
causes
conditions
effects
requirements
constraints
rules
scope
chronology
changes
relationships
values
themes
worldview
narrative
interpretations
implications
significance
production
reception
usage
examples
```

既定:

```text
attributes = include
relations = include
evidence refs = include
```

### 4.5 `creative`

既存設定を材料に新しい文章・案をLLM側で作る用途。

```text
overall
background
appearance
personality
values
motivation
behavior
relationships
role
abilities
themes
worldview
narrative
tone
characters
setting
culture
symbols
significance
```

既定:

```text
attributes = include
relations = include
evidence refs = omit
```

Context Builder自身はcreative generationを行わない。生成は下流LLMの責務である。

---

## 5. Explicit Facet override

`facets`が省略された場合はpurpose profileを使用する。

`facets`が明示された場合はpurpose profileのFacet listを置き換え、その順序を優先順位として保持する。

```text
build_context(
  purpose="roleplay",
  facets=["mechanism", "personality"]
)
```

の場合、roleplay profileに`mechanism`がなくても明示指定を優先する。

Facet存在確認は既存`ObjectKnowledgeReader` / Registry contractを使用する。未知Facetを推測して別Facetへfallbackしない。

---

## 6. Deterministic selection order

1 Object内のKnowledge item選択順序を次で固定する。

```text
1. summary statements
2. Facet statements — profile / explicit Facet priority順
3. attributes — canonical read order
4. relations — canonical read order
```

同じ入力Version、purpose、option、budgetであれば同じ選択結果を返す。

Semantic relevance scoreによる並べ替えは行わない。

---

## 7. Length control

### 7.1 character budgetを採用する

J-04ではmodel-specificなtokenizerへContext Builderを依存させず、UTF-8文字列としてserializableなKnowledge itemのJSON文字数を予算単位とする。

```text
budget_metric = serialized_json_characters
```

MCP inputは次とする。

```text
max_characters
```

J-02で予約時に置いていた`token_budget`は非activeな仮contractであり、J-04で正式contractへ置換した。

理由:

- token数は利用LLM / tokenizerに依存する。
- SGOKB Knowledge Access Layerは特定LLMへ依存させない。
- character countなら完全に決定論的で追加runtimeを必要としない。

必要であればClient側で自身のtokenizerを使い`max_characters`を調整できる。

### 7.2 budget対象

budgetは選択対象となるKnowledge item本体を計測する。MCP envelope、Object identity、selection metadata等の固定overheadはbudget値に含めない。

したがって`max_characters`はwire payload全体のbyte上限ではなく、**選択Knowledge量の制御値**である。

### 7.3 partial truncation禁止

Statement textの途中切断は行わない。

1 Knowledge itemが残budgetへ収まらなければそのitem全体をomitする。

これにより引用・意味・Evidence linkの対応を壊さない。

Responseには次を含める。

```text
limit_characters
used_characters
omitted_items
truncated
```

Facetごとにも`omitted_statement_count`を保持する。

---

## 8. Multi-object fairness

複数Objectの場合、入力順を維持し、総budgetをObject数で均等分割する。

```text
budget_strategy = equal_share_per_object
```

割り切れない余りは先頭Objectから1文字ずつ割り当てる。

この方式により、最初のObjectの長大なKnowledgeが全budgetを消費し、後続Objectが空になることを防ぐ。

将来、比較目的専用のadaptive allocationを追加する場合もcontract versionを意識して変更する。

---

## 9. Version semantics

Context内では各Objectについて必ず次を返す。

```text
object_id
requested_version_id
resolved_version_id
is_current
```

これにより、current Knowledgeを利用したContextか、再現可能なpinned Knowledgeを利用したContextかを識別できる。

Context Builderがcurrentからhistoricalへ、または別ObjectのVersionへsilent fallbackすることは禁止する。

---

## 10. Evidence / Relation policy

purpose profileはEvidence refs / Relationsの**既定値**だけを決める。

呼出側は明示的に次でoverrideできる。

```text
include_relations
include_evidence_refs
include_attributes
```

Evidence本文自体をContextへ自動展開しない。

Contextに含まれるEvidence referenceから本文が必要なら、J-03の`sgokb://evidence/{evidence_id}` ResourceまたはJ-02のEvidence Toolを使用する。

これによりContext BuilderとEvidence retrieval / dereferenceを分離する。

---

## 11. Output contract

Context responseは概ね次の構造を持つ。

```text
context_contract_version
purpose
selection_policy
objects[]
  object_id
  name
  requested_version_id
  resolved_version_id
  is_current
  primary_class
  additional_classes
  context_scope
  knowledge
    summary
    facets
    attributes
    relations
  omitted
  budget
  warnings
budget
warnings
```

`selection_policy`には実際に使用したFacet priority、include policy、budget metric / strategyを含める。

このmetadata自体を下流LLMが推論材料として必須利用する必要はないが、どのKnowledgeがどの規則で選ばれたかを追跡できるようにする。

---

## 12. Failure contract

次は明示errorとする。

- Object 0件
- 21件以上のObject
- duplicate `object_id`
- unknown purpose
- unknown Object / Version / Facet
- `version_ids`に対象外Objectがある
- budget範囲外

推測修復やsilent fallbackは行わない。

---

## 13. MCP contract update

J-04完了後のactive MCP read Toolsは8個となる。

```text
search_objects
find_similar_objects
get_object
get_objects
get_object_relations
get_object_evidence
search_evidence
build_context
```

MCP Tool contract version自体は`sgokb.mcp-read-tools.v1`を維持する。

J-02での`build_context`は明示的に`reserved_j04`でありpublic active contractではなかったため、J-04での正式activationをv1 read surfaceの完成として扱う。

---

## 14. Implementation

```text
src/sgokb/retrieval/context_builder.py
  ContextBuilder
  ContextPurposeProfile
  fixed purpose profiles

src/sgokb/application_read.py
  KnowledgeReadApplication.build_context()

src/sgokb/mcp/tool_contracts.py
  active build_context Tool schema

src/sgokb/mcp/adapter.py
  build_context dispatch / delegation
```

AdapterはJ-01境界を維持し、Repository / SQLite / storageへ直接依存しない。

---

## 15. Verification

対象test:

```text
tests/test_j04_context_builder.py
```

J-03〜J-01およびPhase I retrieval regressionも同時実行した。

検証結果:

```text
Ruff: All checks passed
Pytest: 55 passed, 2 skipped
```

確認事項:

- purposeごとに固定Facet subsetが変化する。
- explicit Facet listがpurpose profileをoverrideする。
- creative / roleplayではEvidence refsを既定で省略できる。
- comparisonではRelationを既定で省略する。
- character budgetを超えてKnowledge itemを部分切断しない。
- 複数Objectへbudgetを均等配分する。
- pinned Versionを維持する。
- `build_context`がactive MCP ToolとしてApplicationへdelegateする。
- J-01/J-02/J-03 read surfaceを回帰させない。

検証用GitHub Actions Workflowは結果確認後に削除した。

---

## 16. J-04 Definition of Done

- [x] Context BuilderをLLM推論から分離した。
- [x] general / analysis / comparison / roleplay / creative profileを定義した。
- [x] 用途別Facet priorityを固定した。
- [x] 明示Facet overrideを定義した。
- [x] attributes / relations / evidence refsの用途別既定値を定義した。
- [x] deterministic selection orderを固定した。
- [x] model-independentなlength controlを定義した。
- [x] partial statement truncationを禁止した。
- [x] multi-object公平配分を定義した。
- [x] current / pinned Version semanticsを維持した。
- [x] `build_context`をApplication / MCP Toolとして実装・active化した。
- [x] focused regression testが通った。

---

## 17. Next task

次のTaskは次とする。

```text
J-05 [P1] MCP write系はread系と分離する
```
