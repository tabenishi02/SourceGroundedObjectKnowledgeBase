# Source Grounded Object Knowledge Base — Phase K Preparation

更新日: 2026-10-14

- Status: **Complete**
- Previous phase: `Phase J — MCP Knowledge Access Layer` — Complete
- Closure audit: `docs/planning/PHASE_J_CLOSURE_AUDIT.md`
- Current phase target: `Phase K — SGOKB / UPDS連携試験`
- Next phase task: `L-01 [P0] Fragment table / code / CLIの移行方針を確定する`
- K-01 decision: `docs/decisions/K01_UPDS_OBJECT_REFERENCE_USE_CASE.md`
- K-02 verification: `docs/decisions/K02_STABLE_OBJECT_ID_REFERENCE_VERIFICATION.md`
- K-03 verification: `docs/decisions/K03_SEMANTIC_INDEX_OWNERSHIP_VERIFICATION.md`
- K-04 decision: `docs/decisions/K04_UPDS_CONTEXT_PROFILE_EVALUATION.md`
- Phase K closure: `docs/planning/PHASE_K_CLOSURE_AUDIT.md`
- Phase L preparation: `docs/planning/PHASE_L_PREPARATION.md`
- Working branch: `main`（Phase K開始前のbranch cleanup後）
- External project: `tabenishi02/UserPreferenceDiscoverySystem`

---

## 1. Phase Kの目的

Phase Kでは、Phase Cで確定したSGOKB→UPDS Integration Contractと、Phase Jで完成したMCP Knowledge Access Layerを接続し、UPDSがSGOKBのWorld / Object Knowledgeを第二正本化せず再利用できることを検証する。

基本構造は次とする。

```text
SGOKB Canonical Store
        ↓
Retrieval / Application Core
        ↓
MCPReadAdapter / local stdio MCP Server
        ↓
UPDS Knowledge Consumer
        ↓
Selection Event + SGOKB Knowledge reference
        ↓
Semantic Observation / Pattern / Preference Hypothesis
```

Phase Kで重要なのは、UPDSをSGOKBの拡張機能として埋め込むことではなく、**独立したPersonal Inference Layerがstable contractを通じてSGOKB Knowledgeを参照できることを確認すること**である。

---

## 2. Phase K Task一覧

| Task | Priority | Status | 概要 |
|---|---|---|---|
| K-01 | P1 | Complete | UPDSからSGOKB Objectを参照する最小ユースケースを定義する |
| K-02 | P1 | Complete | stable Object ID / Version参照がSGOKB更新後も壊れないことを検証する |
| K-03 | P1 | Complete | SGOKBとUPDSのSemantic Index / inference ownershipを混同しないことを確認する |
| K-04 | P2 | Complete | UPDS専用Context/Profileが本当に必要か評価する |

Phase KはK-01から順に進める。

UPDS専用Contextを先に設計せず、まず汎用MCP read Tool / Facet subsetで不足があるかを実証する。

---

## 3. Phase Kのcanonical inputs

### 3.1 SGOKB → UPDS Integration Contract

正本:

`docs/requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md`

主要契約:

- SGOKB = canonical World / Object Knowledge Provider。
- UPDS = Personal Inference Consumer。
- stable `object_id`を長期参照の基本単位とする。
- 推論に利用した`knowledge_version_id`を記録する。
- current requestでも`resolved_version_id`を保存する。
- pinned accepted Versionで過去推論を再現可能にする。
- Facet subset / Relation / Evidenceへ必要に応じて辿れる。
- MCPを標準transportとする。
- UPDSからSGOKB SQLiteへ直接fallbackしない。
- Search / Similarity scoreをPreference probabilityへ変換しない。
- UPDS Personal InferenceをSGOKB canonical Knowledgeへwrite-backしない。

### 3.2 UPDS Personal Inference boundary

正本:

`docs/requirements/UPDS_PERSONAL_INFERENCE_LAYER_REQUIREMENTS.md`

UPDSが所有するもの:

```text
Selection Event
Semantic Observation
Cross-object Pattern
Preference Hypothesis
Alternative Explanation
User-oriented Evidence Set
```

UPDSが所有しないもの:

```text
Object identity / definition
canonical Object Knowledge
canonical Concept Knowledge
World / Object Relation truth
SGOKB Source / Evidence canonical store
```

### 3.3 Phase J MCP contract

正本:

- `docs/planning/PHASE_J_CLOSURE_AUDIT.md`
- `docs/decisions/J01_RETRIEVAL_MCP_APPLICATION_BOUNDARY.md`
- `docs/decisions/J02_MCP_READ_TOOL_CONTRACT.md`
- `docs/decisions/J03_MCP_RESOURCE_CONTRACT.md`
- `docs/decisions/J04_CONTEXT_BUILDER_CONTRACT.md`
- `docs/decisions/J05_MCP_WRITE_BOUNDARY.md`
- `docs/decisions/J06_LOCAL_MCP_CLIENT_ACCEPTANCE.md`

Phase KではMCP Tool / Resource名を再設計せず、既存contractをconsumer側から利用する。

---

## 4. UPDS repositoryの現状

`tabenishi02/UserPreferenceDiscoverySystem`の`main`を2026-10-14時点で確認した。

主な内容:

```text
README.md
docs/PROJECT_CONCEPT.md
```

README / Project Conceptでは、Selection Event → Semantic Observation → Pattern → Preference Hypothesisという基本思想は既に定義されている。

一方、現時点では次が存在しない。

- executable UPDS runtime
- canonical UPDS DB schema / migration
- MCP consumer implementation
- Selection Event persistence implementation
- Semantic Observation implementation
- SGOKB integration test harness

したがってPhase Kで「実UPDSを用いた」と表現する場合は、実装済runtimeがあるかをTaskごとに確認する。

現段階では、K-01は設計Taskとして完全に実施可能である。

K-02 / K-03はまずSGOKB repository内のconsumer-shaped fixture / contract testで意味契約を検証し、UPDS runtimeが実装された時点でcross-repository end-to-end testへ拡張するのが安全である。

---

## 5. K-01で定義すべき最小ユースケース

K-01は「UPDS全体」を実装するTaskではない。

推奨する最小ユースケースはCharacter Selection Event群のsemantic enrichmentである。

```text
UPDS Selection Events
  ├─ Character A object_id
  ├─ Character B object_id
  └─ Character C object_id
        ↓
MCP get_objects / build_context
        ↓
requested facets
  ├─ values
  ├─ personality
  └─ themes
        ↓
SGOKB response
  ├─ object_id
  ├─ resolved_version_id
  ├─ requested_scope
  └─ facet statements
        ↓
UPDS Semantic Observations
```

このユースケースはC-04で既に例示されており、K-01では具体的なrequest / response / UPDS-side stored referenceへ落とす。

---

## 6. K-01で最低限固定する項目

K-01では少なくとも次を決める。

### Input

- Selection Event側が保持するSGOKB `object_id`。
- 1回の分析で扱うObject数。
- requested Facet。
- current / pinned Versionの選択規則。

### SGOKB access

- `get_objects`を使うか`build_context`を使うか。
- 汎用Facet subsetで足りるか。
- Relation / Evidenceを初回ユースケースへ含めるか。

### UPDS-side reference

Semantic Observation等が少なくとも次を追跡できること。

```text
selection_event_id
sgokb_object_id
sgokb_version_id
retrieved_at
requested_scope / facet keys
contract_version
```

SGOKB Knowledge本文をUPDSの第二正本として保存することは要求しない。

---

## 7. K-02の検証シナリオ準備

K-02ではstable IdentityとKnowledge Versionを分離して検証する。

最低限のシナリオ:

```text
1. object_id = A / current version = v1
2. UPDS-shaped referenceがA + v1を保存
3. SGOKBでAの新accepted version v2を作成
4. current取得 → A + v2
5. pinned取得 → A + v1
6. 保存済referenceはAのまま壊れない
7. v1を用いた過去Semantic Observationをsilent rewriteしない
```

名前変更・alias変更が起きても`object_id`参照が維持されることも候補とする。

---

**K-02 Acceptance: PASS**

詳細: `docs/decisions/K02_STABLE_OBJECT_ID_REFERENCE_VERIFICATION.md`

---

## 8. K-03の境界準備

K-03ではSGOKBとUPDSでEmbedding / Semantic Indexを共有しないこと自体が目的ではなく、**意味責務を混同しないこと**を検証する。

```text
SGOKB Semantic Index
= Object / Facet / Statement / Evidenceの意味検索

UPDS Semantic / inference layer
= Selection Event / Semantic Observation / Pattern / Preference Hypothesis
```

禁止例:

- UPDS Preference HypothesisをSGOKB Object embeddingへ混入する。
- SGOKB Similarity scoreをPreference probabilityとして保存する。
- UPDSがSGOKB search representation tableを直接使用する。
- SGOKBがUser Profileを受け取ってObject ranking semanticsを個人化する。

必要なら物理index backendが同じ製品でもよいが、collection / namespace / metadata ownership / rebuild authorityを分離する。

---

**K-03 Acceptance: PASS**

詳細: `docs/decisions/K03_SEMANTIC_INDEX_OWNERSHIP_VERIFICATION.md`

---

## 9. K-04の評価基準準備

K-04ではUPDS専用Context/Profileを追加することを前提にしない。

まず次で不足があるか確認する。

- `get_objects(facets=[...])`
- `build_context(purpose="analysis", facets=[...])`
- `get_object_relations`
- `get_object_evidence`

専用Profile追加を正当化する不足の例:

- 毎回同一Facet集合・scope指定が複雑でerror-prone。
- 汎用Contextでは不要情報が多くbudget効率が明確に悪い。
- UPDS側で毎回同一のdeterministic selectionを再実装する必要がある。

追加理由として認めない例:

- Personal PreferenceをSGOKB側で推論したい。
- User Profileを送ってrankingを個人化したい。
- Preference HypothesisをSGOKB Contextへ混ぜたい。

---

**K-04 Acceptance: PASS — UPDS専用Context/Profileは追加しない。**

詳細: `docs/decisions/K04_UPDS_CONTEXT_PROFILE_EVALUATION.md`

---

## 10. Failure / privacy acceptance

Phase Kでは正常系だけでなく次を維持する。

### MCP unavailable

```text
Selection Event recording
  → 継続可能

SGOKB semantic enrichment
  → pending / unavailable

禁止
  → SQLite direct fallback
  → external cloud silent fallback
```

### Data minimization

SGOKB requestへ送る情報は原則として次に限定する。

- object_id
- version_id
- facet / relation scope
- search query

Preference Hypothesis、全Selection history、User ProfileをObject取得のためにSGOKBへ送らない。

---

## 11. Contract compatibility

Phase K consumerは最低限次を確認する。

- `application_contract_version`
- MCP Tool contract version
- Context Builder contract version（使用時）
- Resource contract version（Resource使用時）

breaking semantic changeを旧contractとしてsilent受理しない。

一方、optional/additive fieldへ過剰結合しない。

---

## 12. Phase K test strategy

UPDS runtime未実装の現状では2段階とする。

### Stage A — contract-level integration

SGOKB repository内でconsumer-shaped fixtureを用いる。

確認対象:

- Object / batch read
- Facet subset
- stable Object ID
- current / pinned Version
- no direct DB fallback
- contract version
- Semantic Index ownership boundary

### Stage B — cross-repository integration

UPDS runtime実装後に、`tabenishi02/UserPreferenceDiscoverySystem`側からSGOKB MCP Serverへ接続する。

確認対象:

- Selection Event → SGOKB Object resolve
- resolved Version保存
- Semantic Observation生成
- stale / current比較
- SGOKB停止時のpending化
- no direct DB fallback

K-01ではStage A / B双方が使用できる最小ユースケースcontractを先に定義する。

---

## 13. K-01 Definition of Ready

- [x] Phase J J-01〜J-06完了。
- [x] local MCP read Tool / Resource contractが存在する。
- [x] Reference Workstationでlocal stdio MCP acceptance成功。
- [x] stable `object_id` / immutable Version契約がC-04で確定している。
- [x] `get_objects`でbatch取得できる。
- [x] Facet subset取得が可能。
- [x] `build_context`がdeterministic selectorとして利用可能。
- [x] read/write boundaryが分離されている。
- [x] SGOKB / UPDS ownership boundaryがC-01〜C-04で確定している。
- [x] UPDS repositoryの現状を確認した。

**K-01は2026-10-14に完了した。成果物は`docs/decisions/K01_UPDS_OBJECT_REFERENCE_USE_CASE.md`。**

---

## 14. K-01 Definition of Done案

K-01は少なくとも次を満たして完了とする。

- 1つの具体的Selection Event → Object Knowledge参照フローを固定する。
- 対象Object Classと利用Facetを固定する。
- request Tool / Resourceと引数を固定する。
- current / pinned Version利用規則を固定する。
- UPDS側で保存するSGOKB reference metadataを固定する。
- SGOKB Knowledge本文を第二正本化しない境界を明記する。
- Search / Similarity scoreをPreference probabilityへ変換しない。
- Personal ProfileをSGOKB requestへ送らない。
- MCP停止時のpending / unavailable動作を定義する。
- K-02 / K-03で自動試験に落とせるacceptance scenarioを作る。

---

## 15. Phase K完了判定

Phase J Closure Auditにより未完了Taskは0件。

Phase Kに必要なIntegration Contract、stable Identity / Version contract、MCP read transport、Facet subset、Context Builder、failure boundaryは揃っている。

K-01〜K-04はすべて完了した。K-01で標準参照経路を固定し、K-02でstable Object ID / Version参照、K-03でSemantic Index ownership、K-04で専用Context/Profile不要を確認した。

UPDS runtimeは未実装だが、SGOKB側Integration Contractはconsumer-shaped contract testと既存MCP / Context Builder contractにより検証済みである。実UPDS実装後のcross-repository E2EはStage Bとして残す。

**Phase K完了条件を満たす。**

Closure Audit: `docs/planning/PHASE_K_CLOSURE_AUDIT.md`
Phase L Preparation: `docs/planning/PHASE_L_PREPARATION.md`

次に実施するTask:

```text
L-01 [P0] Fragment table / code / CLIの移行方針を確定する
```
