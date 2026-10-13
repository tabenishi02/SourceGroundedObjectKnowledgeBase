# Source Grounded Object Knowledge Base — Phase J Preparation

更新日: 2026-10-14

- Status: **Ready to Start**
- Previous phase: `Phase I — 意味検索・類似検索` — Complete
- Closure audit: `docs/planning/PHASE_I_CLOSURE_AUDIT.md`
- Current phase target: `Phase J — MCP Knowledge Access Layer`
- First task: `J-01 [P0] Retrieval CoreとMCP Adapterを分離する`
- Working branch: `integration/knowledge-base-redesign`

---

## 1. Phase Jの目的

Phase Jでは、Phase Iまでに実装したObject Knowledge Retrievalを、SQLiteやQdrantの内部構造を知らないLLM / Agent / UPDSから安全に利用できるread-only Knowledge Access Layerとして公開する。

基本構造はD-04 / C-04で既に確定している。

```text
Canonical SQLite / Derived Search Index
            ↓
Retrieval Core
            ↓
Application read use cases
            ↓
MCP Adapter
            ↓
ChatGPT / Local LLM / UPDS / Other Client
```

重要な原則は、**MCPを新しい検索実装にしない**ことである。

MCPはtransport / schema adapterであり、検索・Version解決・filter・Similarity・Evidence取得の意味はApplication / Retrieval Coreが所有する。

---

## 2. Phase J Task一覧

| Task | Priority | Status | 概要 |
|---|---|---|---|
| J-01 | P0 | Next | Retrieval CoreとMCP Adapterを分離し、Application read boundaryを確立する |
| J-02 | P0 | Pending | MCP read toolsとinput/output contractを定義する |
| J-03 | P1 | Pending | MCP Resourcesを定義する |
| J-04 | P0 | Pending | deterministic Context Builderを設計する |
| J-05 | P1 | Pending | MCP write系をread系から分離して判断する |
| J-06 | P0 | Pending | local MCP Clientで受入試験する |

Phase JはJ-01から順に進める。Tool名やJSON Schemaを先に固定してApplication boundaryを後付けしない。

---

## 3. Phase Jのcanonical inputs

### 3.1 Module responsibility

`docs/decisions/SGOKB_MODULE_RESPONSIBILITY_DESIGN.md`

既に固定されている依存方向:

```text
cli      mcp
 \       /
  application
      ↓
retrieval / storage / exchange / rendering
      ↓
    domain
```

禁止:

- `mcp -> SQLite direct access`
- `mcp -> Qdrant固有API`
- MCP Adapter独自ranking
- MCP Adapter独自Version解決
- MCP Adapter独自cloud fallback

### 3.2 SGOKB → UPDS Integration Contract

`docs/requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md`

Phase Jで特に実装へ落とす契約:

- stable `object_id`を永続Identityとする。
- current requestでも`resolved_version_id`を返す。
- pinned accepted Versionを取得可能にする。
- Facet subsetを取得可能にする。
- Relation / Evidenceへ必要時に辿れる。
- Search / Similarity結果をPreference probabilityへ変換しない。
- MCP停止時にSQLite direct fallbackしない。
- contract versionを識別可能にする。
- read pathはlocal-firstとする。

### 3.3 Search / Retrieval contract

`docs/requirements/SEARCH_REQUIREMENTS.md`
`docs/planning/PHASE_I_CLOSURE_AUDIT.md`

Phase Iで確定済み:

- Hybrid Object Search
- exact identity priority
- Object / Facet / Statement multi-representation retrieval
- 1 Object = 1 result
- current / historical isolation
- Class / Facet / Version / temporal hard filter
- Object overall / Facet Similarity
- Evidence Search分離
- Qdrant Derived Index / no silent fallback

Phase Jはこれらをtransportへ写像するだけで、ranking semanticsを変更しない。

---

## 4. 現行実装の棚卸し

### 4.1 Retrieval Core — 利用可能

```text
src/sgokb/retrieval/hybrid_search.py
  HybridObjectSearch
  KnowledgeVectorIndexBuilder

src/sgokb/retrieval/similarity.py
  ObjectSimilaritySearch

src/sgokb/retrieval/evidence.py
  ObjectEvidenceRetriever

src/sgokb/retrieval/search_representation.py
src/sgokb/retrieval/embedding.py
src/sgokb/retrieval/vector_index.py
```

Phase Iの主要検索Coreは`retrieval/`へ分離済みである。

### 4.2 Domain response contract — 一部利用可能

`src/sgokb/domain/search.py`には次が存在する。

```text
ObjectSearchFilters
ObjectSearchResponse
ObjectSearchResult
ObjectSearchMatch
ObjectSimilarityResponse
SimilarObjectResult
```

ただしMCP / UPDS向けのObject Knowledge取得Response envelope、batch response、Relation response等はまだPhase J contractとして固定されていない。

### 4.3 Application — 部分的

現行`src/sgokb/application.py`はF-03〜F-05のuse caseとして、

- `retrieve_object_evidence()`
- `select_object_evidence()`
- Source↔Object association操作

をApplication経由で公開している。

一方、Phase Iで完成した、

- `HybridObjectSearch.search()`
- `ObjectSimilaritySearch.find_similar_objects()`

はApplicationの標準read use caseへまだ接続されていない。

したがってMCP実装がretrieval classを直接構築し始める前に、J-01でApplication boundaryを作る必要がある。

### 4.4 MCP package — 未作成

長期設計では`src/sgokb/mcp/`を正規adapter領域としているが、現在は存在しない。

これはPhase J開始前として正常であり、J-01以降で必要最小限から作成する。

---

## 5. J-01で解消するGap

J-01ではMCP Toolを大量に作るのではなく、まずMCPから呼べるApplication / Retrieval APIを確立する。

主要Gap:

### Gap 1 — Object Search Application APIがない

`HybridObjectSearch`は完成しているが、Application façadeがない。

J-01ではconceptually次を提供できる境界が必要になる。

```text
search_objects(query, mode, filters, limit, ...)
```

MCPと将来CLIは同じuse caseを呼ぶ。

### Gap 2 — Similarity Application APIがない

```text
find_similar_objects(object_id, facet?, source_version_id?, cross_class?, limit?)
```

をApplication boundaryから呼べるようにする。

### Gap 3 — Knowledge Get APIが統一されていない

C-04 / J-02で必要な、

```text
get_object
get_objects
get_object_relations
get_object_evidence
```

のread semanticsをStorage direct callではなくApplication read use caseへ揃える必要がある。

J-01では少なくとも「MCP AdapterがStorage Repositoryを直接呼ばなくても成立する境界」を作る。

### Gap 4 — Retrieval runtime compositionを固定していない

Hybrid / SimilarityにはEmbedding ProviderとVectorIndexAdapterが必要である。

MCP Adapter内でQdrant clientやHarrier modelを勝手に生成せず、application composition rootから注入する。

```text
configuration
   ↓
EmbeddingProvider
VectorIndexAdapter
   ↓
Application Retrieval Service
   ↓
MCP Adapter
```

### Gap 5 — transport-neutral error contractが必要

例えば、

- unknown Object / Version / Facet
- vector backend unavailable
- missing embedding
- invalid filter
- partial / unavailable data

をMCP固有例外へ直結させない。

Application / domain levelのerror semanticsをMCP Adapterがtransport responseへ変換する構造を優先する。

---

## 6. J-01推奨実装境界

D-04では最終的に`application/` package化する方針だが、J-01で大規模なmoveとbehavior changeを同時に行わない。

推奨順序:

1. 現行ApplicationとRetrieval Coreの依存を棚卸しする。
2. read-only retrieval orchestrationを狭いservice / façadeへ抽出する。
3. Hybrid Search / Similarityをそのfaçade経由へ接続する。
4. Object / Version readを同じ境界へ揃える。
5. unit testで「adapterなしでもApplication APIだけで検索できる」ことを確認する。
6. その後に`mcp/` adapterを追加する。

物理的な`application.py -> application/` package conversionが必要なら、D-05の原則どおりstructural moveとbehavior追加を可能な限り分離する。

---

## 7. J-02以降へ想定するread capability

正式Tool名はJ-02で決定するが、論理capabilityは既にタスク・C-04から次が必要である。

```text
search_objects
semantic_search_objects または mode=semantic
find_similar_objects
get_object
get_objects
get_object_relations
get_object_evidence
search_evidence
build_context
```

注意:

- `semantic_search_objects`を別Toolにするか`search_objects(mode=semantic)`へ統合するかはJ-02で判断する。
- Facet Similarityは`find_similar_objects(facet=...)`で表現できるため、別Tool化は必須ではない。
- `build_context`はJ-04でdeterministic selectionとして設計する。

---

## 8. Object Knowledge responseで必要な情報

MCP ResponseはStorage rowをそのまま公開せず、少なくとも次を識別可能にする。

```text
contract_version
object_id
requested_version_id?
resolved_version_id
is_current
object_status
name / aliases
primary_class
additional_classes
requested_scope
knowledge
  summary
  facets
  statements
  attributes
  relations
optional evidence_refs
warnings / resolution info
```

特にVersion未指定のcurrent取得でも`resolved_version_id`を必ず返す。

Facet subset等の部分取得はfull Knowledge snapshotと誤認できないよう`requested_scope` / response scopeを保持する。

---

## 9. Read-only / write boundary

Phase J初期MVPはread-onlyを第一候補とする。

```text
MCP read
  → Application read use case
  → canonical / derived dataを読む

MCP write
  → J-05で別判断
```

UPDS Preference HypothesisやPersonal InferenceをSGOKBへwrite-backしない。

将来proposal writeを追加する場合もcanonical writeとは分離する。

---

## 10. Failure / degradation boundary

Phase Iのfailure contractをMCPでも維持する。

```text
Qdrant unavailable
  → semantic / similarity unavailable またはHybrid degraded
  → SQLite canonical dataは維持
  → Lexical capabilityは利用可能な範囲で継続

MCP unavailable
  → clientはSGOKB SQLiteへdirect fallbackしない

local provider unavailable
  → external cloud providerへsilent fallbackしない
```

MCP Responseではpartial / degraded / unavailableを完全成功として隠さない。

---

## 11. Security / privacy input

Phase Jではlocal-firstを維持する。

初期標準:

- loopback / local clientを基準にする。
- Object取得のためにUPDS Personal ProfileをSGOKBへ送らない。
- requestはObject ID / Version / Facet / Relation / query等の必要最小限にする。
- loopback外公開を将来許可する場合はexplicit enable + authentication / scopeを要求する。

J-06でMCP停止時とlocal client接続を受入試験する。

---

## 12. J-01 Definition of Ready

J-01開始条件を次とする。

- [x] Phase I I-01〜I-07完了。
- [x] Search goldでHybrid / Similarity / Evidenceの品質を確認済み。
- [x] Domain Search contractが存在する。
- [x] Retrieval Coreが`retrieval/`へ分離されている。
- [x] D-04で`mcp -> application`依存方向が確定している。
- [x] C-04でstable Object ID / Version / MCP read contractが確定している。
- [x] local-only / no silent fallback境界が確定している。
- [ ] Application read façadeへHybrid / Similarity / Object Getを接続する。

最後の1項目がJ-01そのものであり、事前blockerではない。

**J-01は開始可能。**

---

## 13. J-01 Definition of Done案

J-01は少なくとも次を満たして完了とする。

- MCP AdapterがRepository / SQLite SQLを直接呼ばない。
- Object SearchをApplication API経由で実行できる。
- Object SimilarityをApplication API経由で実行できる。
- current / pinned Version Object readをApplication API経由で行える。
- Retrieval runtime dependencyをAdapter外から注入できる。
- Application APIと直接Retrievalでranking/filter semanticsが変わらない。
- backend/provider障害のno-silent-fallback contractを維持する。
- J-02がTool schemaを設計できるtransport-neutral response contractが存在する。
- focused regression testsが通る。

J-01ではTool名・Resource URI・Context Builder・write permissionを先取りして固定しない。

---

## 14. Phase J開始判定

Phase I Closure Auditにより未完了Taskは0件。

Phase Jに必要な意味契約、検索Core、Version contract、module dependency directionは揃っている。

**Phase Jへ移行する準備は完了している。**

次に実施するTask:

```text
J-01 [P0] Retrieval CoreとMCP Adapterを分離する
```
