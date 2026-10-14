# K-01 UPDS Object Reference Minimum Use Case

更新日: 2026-10-14

Status: Accepted

対象Task: `K-01 [P1] UPDSからSGOKB Objectを参照する最小ユースケースを定義する`

関連正本:

- `docs/requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md`
- `docs/requirements/UPDS_PERSONAL_INFERENCE_LAYER_REQUIREMENTS.md`
- `docs/decisions/J02_MCP_READ_TOOL_CONTRACT.md`
- `docs/decisions/J04_CONTEXT_BUILDER_CONTRACT.md`
- `docs/planning/PHASE_K_PREPARATION.md`

---

## 1. Decision

Phase Kの最小UPDS連携ユースケースを次のように固定する。

> **UPDSが保持するSelection Event群から、既知のSGOKB Character `object_id`を取り出し、MCP read Tool `get_objects`で`values` / `personality` / `themes`の3 Facetだけをbatch取得する。UPDSは取得時に実際に解決された`resolved_version_id`を参照メタデータとして記録し、返却されたSGOKB KnowledgeをPersonal Inferenceの入力として利用する。**

このユースケースではSGOKB側でPreference推論を行わず、UPDS側でSGOKB Knowledgeを第二正本化しない。

基本フロー:

```text
UPDS Selection Event群
  ├─ selection_event_id = sel-A
  │    └─ sgokb_object_id = char-A
  ├─ selection_event_id = sel-B
  │    └─ sgokb_object_id = char-B
  └─ selection_event_id = sel-C
       └─ sgokb_object_id = char-C
            ↓
MCP get_objects
  object_ids = [char-A, char-B, char-C]
  facets = [values, personality, themes]
  include_relations = false
  include_evidence_refs = false
            ↓
SGOKB Object Knowledge
  ├─ object_id
  ├─ resolved_version_id
  ├─ requested_scope
  └─ values / personality / themes statements
            ↓
UPDS Personal Inference Layer
  ├─ Semantic Observation
  ├─ Cross-object Pattern
  └─ Preference Hypothesis
       ※ これらはUPDS所有
```

---

## 2. なぜ`get_objects`を主経路にするか

K-01の主経路は`build_context`ではなく`get_objects`とする。

理由:

1. K-01の目的はLLM向けContext生成ではなく、UPDS ConsumerがSGOKB Knowledgeを構造化参照する最小契約の確定である。
2. `get_objects`は既知`object_id`群のbatch取得と明示Facet subsetを直接表現できる。
3. Context Builderの`purpose`、文字数budget、deterministic selection policyへ依存せず、取得KnowledgeとUPDS推論の境界を単純にできる。
4. `resolved_version_id`をObjectごとに取得でき、後続K-02のcurrent / pinned Version検証へ直接接続できる。

`build_context`は不要と判断したわけではない。将来UPDSが取得済みKnowledgeをLLMへ投入する際に、決定論的Context選別が必要であれば利用候補になる。K-04では、その汎用Context Builderで不足があるかを別途評価する。

---

## 3. 前提

K-01では次を前提とする。

- UPDS runtime / DB schema / MCP consumer implementationはまだ存在しない。
- Selection Eventの具体的DB schemaはK-01で決めない。
- Selection EventからSGOKB `object_id`への関連付け方式もK-01では固定しない。
- ただし、最小ユースケース開始時点では対象Characterのstable `object_id`が既知であることを前提とする。
- `object_id`が不明な状態からのIdentity解決は`search_objects`等を利用する別工程であり、K-01最小ケースには含めない。

この前提により、UPDS詳細設計をSGOKB都合で先回りして固定しない。

---

## 4. 対象Object / Facet

最小ユースケースの対象Class:

```text
Character
```

取得Facet:

```text
values
personality
themes
```

選定理由:

- `values`: Characterが示す価値観・判断軸をPersonal Inference材料として利用できる。
- `personality`: 行動・性格傾向に関するObject Knowledgeを取得できる。
- `themes`: Characterに結び付く主題的意味を取得できる。

ここで取得するFacetは**CharacterについてのWorld / Object Knowledge**であり、「ユーザーがその価値観・性格・テーマを好む」という意味を持たない。

---

## 5. MCP request contract

標準Tool:

```text
get_objects
```

初回/current enrichment requestの概念例:

```json
{
  "object_ids": ["char-A", "char-B", "char-C"],
  "facets": ["values", "personality", "themes"],
  "include_relations": false,
  "include_evidence_refs": false
}
```

`version_ids`を省略するため、各Objectについてcurrent accepted Knowledge Versionが解決される。

MCP public contract上の`get_objects`上限は100 Object / requestである。K-01は上限変更を行わず、具体例として3 Characterを使用する。UPDS側の恒久的な分析batch sizeはUPDS設計時に決める。

### 5.1 Relationを既定で含めない理由

RelationはPersonal Inferenceに有用になり得るが、K-01の目的はFacet参照の最小成立確認である。

Relationが必要な分析では後から次を使用できる。

```text
get_object_relations
```

### 5.2 Evidence referenceを既定で含めない理由

UPDSの通常分析ではaccepted Object Knowledgeを標準入力とする。一次Evidenceの監査・再確認が必要な場合は明示的に`get_object_evidence`またはEvidence Resource / Searchへ進む。

K-01でEvidence referenceを常時転送しないことで、最小データ転送と責務分離を維持する。

---

## 6. Response acceptance

UPDS Consumerは少なくとも次を確認する。

### Envelope

```text
tool_contract_version = sgokb.mcp-read-tools.v1
application_contract_version = 認識可能なversion
```

未知またはbreakingなcontractを旧contractとしてsilent受理しない。

### Objectごと

最低限:

```text
object_id
requested_version_id
resolved_version_id
is_current
object_status
requested_scope
knowledge
warnings
```

特に`version_ids`省略時でも`resolved_version_id`を必ず保存可能でなければならない。

Response orderへIdentity意味を依存させず、UPDS側では`object_id`でSelection Eventとの対応を解決する。

---

## 7. UPDS側で保持するSGOKB reference metadata

K-01ではUPDSの物理DB schemaを確定しない。

ただし、SGOKB Knowledgeに依存するSemantic Observation等から、論理上少なくとも次へ遡れることを要求する。

```text
selection_event_id
sgokb_object_id
sgokb_version_id        # response.resolved_version_id
retrieved_at
requested_facets        # values / personality / themes
requested_scope         # responseで実際に解決されたscope
mcp_tool_contract_version
application_contract_version
```

必要に応じて複数Selection Eventが同一`sgokb_object_id`を参照してよい。

同一ObjectのKnowledgeを一度取得した場合でも、どのSelection Event / Observation / Pattern / HypothesisがどのVersionに依存したかを追跡できることを優先する。

---

## 8. Canonical ownership / cache boundary

UPDSは次を正本化しない。

- SGOKB Object identity definition
- SGOKB Character Knowledge本文
- SGOKB Facet taxonomy
- SGOKB World / Object Relation truth
- SGOKB Source / Evidence canonical store

UPDS側でPerformance目的のcacheを持つことは許容するが、cacheはderived dataとし、SGOKBに代わる第二正本にしない。

UPDSが生成する次の情報はUPDS側の所有物である。

```text
Selection Event
Semantic Observation
Cross-object Pattern
Preference Hypothesis
Alternative Explanation
User-oriented Evidence Set
```

SGOKB Knowledge StatementをそのままPreference factへ変換してはならない。

---

## 9. Current / pinned Version利用規則

### 9.1 通常の新規分析

新規Semantic enrichmentでは`version_ids`を省略し、current accepted Versionを取得する。

取得後、必ず`resolved_version_id`を保存する。

```text
request: current
response: char-A + ver-7
UPDS reference: char-A + ver-7
```

### 9.2 過去推論の再現

過去Semantic Observation / Pattern / Preference Hypothesisの再現時は、保存済み`sgokb_version_id`を`version_ids`へ指定してpinned取得する。

概念例:

```json
{
  "object_ids": ["char-A", "char-B"],
  "version_ids": {
    "char-A": "ver-5",
    "char-B": "ver-3"
  },
  "facets": ["values", "personality", "themes"],
  "include_relations": false,
  "include_evidence_refs": false
}
```

### 9.3 新Version発生時

SGOKBで`char-A`が`ver-5`から`ver-6`へ更新されても、`ver-5`を使用した既存UPDS推論をsilent rewriteしない。

current Knowledgeで再分析する場合は、新しいObservation / Pattern / Hypothesis revisionとして扱う。

---

## 10. Failure / unavailable時

MCP / SGOKBが利用不能でも、Selection Eventの記録自体は継続可能とする。

```text
Selection Event recording
  → continue

SGOKB semantic enrichment
  → pending / unavailable
```

禁止:

```text
UPDS → SGOKB SQLite direct fallback
UPDS → external cloud silent fallback
name一致による別Objectへのsilent置換
```

復旧後に同じstable `object_id`で再取得できる。

---

## 11. Data minimization

K-01 requestでSGOKBへ送る情報は次に限定する。

```text
object_id群
必要ならversion_id
Facet keys
include option
```

次をSGOKB requestへ送らない。

```text
Preference Hypothesis
全Selection history
User Profile
ユーザー嗜好Embedding
Personal ranking signal
```

SGOKBはUPDS Personal Inferenceを知らなくても同じObject Knowledgeを返す。

---

## 12. Search / Similarityの境界

K-01では既知`object_id`から取得するため、`search_objects`と`find_similar_objects`を主フローに含めない。

将来それらを使用する場合も、Search / Similarity scoreはretrieval relevanceであり、次へ直接変換しない。

```text
Preference probability
Preference confidence
Selection likelihood
```

---

## 13. K-02へ引き継ぐacceptance scenario

K-02では次を自動試験へ落とす。

```text
1. Character Aのstable object_idを作成する。
2. current accepted Knowledge = v1 とする。
3. K-01 requestでAのvalues/personality/themesをcurrent取得する。
4. responseのresolved_version_id = v1をUPDS-shaped referenceへ保存する。
5. SGOKBでAの新accepted Version v2を作成する。
6. 同じobject_idをcurrent取得するとv2が返る。
7. version_idsでv1をpinned取得するとv1が返る。
8. v1を参照する既存UPDS-shaped referenceは変更されない。
9. Object display name / aliasが変更されてもobject_id参照は維持される。
```

---

## 14. K-03へ引き継ぐacceptance scenario

K-03では次の責務分離を検証する。

```text
SGOKB side
  Object / Facet / Statement / Evidence retrieval

UPDS-shaped side
  Selection Event / Semantic Observation / Pattern / Preference Hypothesis
```

最低限確認する禁止事項:

- Preference HypothesisをSGOKB Object Knowledgeへ書き戻さない。
- UPDS Personal dataをSGOKB Search Representationへ混入しない。
- SGOKB Similarity scoreをPreference probabilityとして扱わない。
- UPDS ConsumerがSGOKB SQLite / search representation tableを直接参照しない。
- SGOKB側がUser Profileによって`get_objects`のKnowledge semanticsをpersonalizeしない。

---

## 15. K-01で決めないこと

次はUPDS設計または後続Taskへ残す。

- Selection Event物理schema
- Selection EventとSGOKB Objectの自動対応付け方式
- Semantic Observation schema / taxonomy
- Pattern生成アルゴリズム
- Preference Hypothesis schema
- UPDSのEmbedding / Vector Index設計
- UPDS query / UI
- UPDS専用Context/Profile
- Push型SGOKB更新通知
- Relation / EvidenceをPersonal Inferenceへ取り込む具体的ルール

これにより、構想段階のUPDSをPhase Kで過剰設計しない。

---

## 16. Definition of Done

- [x] 具体的なSelection Event → Object Knowledge参照フローを固定した。
- [x] 対象Object ClassをCharacterへ固定した。
- [x] 利用Facetを`values` / `personality` / `themes`へ固定した。
- [x] 標準Toolを`get_objects`へ固定した。
- [x] current / pinned Version利用規則を固定した。
- [x] UPDS側で保持すべきSGOKB reference metadataを論理契約として固定した。
- [x] SGOKB Knowledge本文をUPDSの第二正本にしない境界を固定した。
- [x] Search / Similarity scoreをPreference probabilityへ変換しない境界を維持した。
- [x] Personal ProfileをSGOKB requestへ送らないことを固定した。
- [x] MCP停止時のpending / unavailable動作を固定した。
- [x] K-02 / K-03へ引き継ぐacceptance scenarioを定義した。
- [x] UPDS未設計領域を先回りして固定しない範囲を明記した。

**K-01は完了とする。**

---

## 17. Next task

```text
K-02 [P1] Stable Object ID参照を検証する
```
