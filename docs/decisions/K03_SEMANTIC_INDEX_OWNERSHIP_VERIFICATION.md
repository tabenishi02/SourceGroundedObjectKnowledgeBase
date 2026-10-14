# K-03 SGOKB / UPDS Semantic Index Ownership Verification

更新日: 2026-10-14

Status: Accepted

対象Task: `K-03 [P1] SGOKBとUPDSのSemantic Indexを混同しないことを確認する`

関連正本:

- `docs/requirements/UPDS_PERSONAL_INFERENCE_LAYER_REQUIREMENTS.md`
- `docs/requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md`
- `docs/requirements/SEARCH_REQUIREMENTS.md`
- `docs/decisions/K01_UPDS_OBJECT_REFERENCE_USE_CASE.md`
- `docs/decisions/K02_STABLE_OBJECT_ID_REFERENCE_VERIFICATION.md`
- `docs/decisions/J02_MCP_READ_TOOL_CONTRACT.md`
- `docs/planning/PHASE_K_PREPARATION.md`

---

## 1. 結論

K-03では、SGOKBとUPDSのSemantic Indexを同一の意味空間・同一責務として扱わないことを、現行SGOKB実装とcontract-level testで確認した。

正式な境界を次のように固定する。

```text
SGOKB Semantic / Search Index
  canonical input:
    Object Knowledge / Evidence
  representations:
    object_overall
    facet
    statement
    evidence
  purpose:
    Object / Knowledge / Evidence retrieval
    Object / Facet similarity

UPDS Semantic / Inference Index（将来実装する場合）
  canonical / logical input:
    Selection Event
    Semantic Observation
    Cross-object Pattern
    Preference Hypothesis
    User-oriented Evidence Set
  purpose:
    Personal Inference retrieval
    Pattern discovery
    Preference Hypothesis support
```

SGOKBのSimilarity / Search scoreはPersonal Preferenceの確率・confidenceではない。

---

## 2. K-03で確認する「混同」の意味

K-03の目的は、SGOKBとUPDSが必ず異なるVector DB製品を使うことではない。

禁止するのは次の意味的混同である。

1. UPDS Preference HypothesisをSGOKB Object Search Representationへ投入する。
2. Selection EventやUser ProfileをSGOKB Vector metadataへ保存する。
3. SGOKB Similarity scoreをPreference probabilityとして解釈する。
4. UPDS Personal dataをSGOKB Object rankingへpersonalization signalとして渡す。
5. UPDSがSGOKB内部Search Representation table / Vector IndexをPersonal Inferenceの正本として直接利用する。
6. SGOKB側がUPDS schema / Pattern / Hypothesis modelへ依存する。

同じVector backend製品を将来両プロジェクトで利用すること自体は禁止しない。

ただしその場合も、少なくとも次を分離する。

```text
collection / namespace
metadata ownership
representation schema
Embedding Space identity
index rebuild authority
lifecycle / retention
query semantics
score interpretation
```

---

## 3. SGOKB側Semantic Index ownership

現行SGOKBの`SearchRepresentationKind`は次に限定される。

```text
object_overall
facet
statement
evidence
```

これらはすべてWorld / Object KnowledgeまたはSource / Evidence側の表現である。

SGOKBのKnowledge Vector Index metadataは次のような情報を保持する。

```text
membership_id
representation_id
kind
object_id
version_id
primary_class
additional_classes
ancestor_classes
object_status
is_current
facet_id / facet
statement_id
derivation_kind
temporal scope
```

次のPersonal Inference metadataはSGOKB Indexへ含めない。

```text
selection_event_id
semantic_observation
preference_hypothesis
preference_probability
preference_embedding
taste_vector
user_profile
personal_ranking_signal
```

---

## 4. MCP boundary

現行MCP read ToolはPersonal Profile / Preference signalを入力として受け取らない。

K-03 testでは、少なくとも次を確認した。

```text
search_objects(user_profile=...)
find_similar_objects(preference_probability=...)
get_objects(preference_hypothesis=...)
build_context(personal_ranking_signal=...)
```

これらはすべてunknown fieldとして`MCPToolArgumentsError`になる。

したがって、標準MCP read contract経由でUPDS Personal dataをSGOKB検索rankerへsilent注入する経路は存在しない。

これはData minimizationの観点でも重要である。

---

## 5. Similarity / Search score semantics

SGOKBのSemantic Similarity resultは、現行実装では例えば次を返す。

```text
score_type = cosine_similarity
score = semantic vector similarity
```

この値の意味は次に限定する。

> SGOKBの特定Embedding Space内で、Object / Facet等のSearch Representationがどの程度近いかを表すretrieval signal。

次の意味を持たない。

```text
ユーザーが好きである確率
Preference Hypothesis confidence
Selection probability
Object Knowledge truth probability
```

UPDSがSGOKB SimilarityをPersonal Inferenceの一つの補助signalとして利用することは可能だが、その場合もUPDS側で他のSelection Event / Pattern / Alternative Explanation等と組み合わせる。

SGOKB scoreをそのままPreference fieldへ代入してはならない。

---

## 6. Search Representation lifecycle

SGOKB Search Representation / Embedding / Vector Indexはcanonical Knowledgeではなくderived layerである。

```text
SGOKB canonical Object Knowledge
        ↓
Search Representation
        ↓
Embedding
        ↓
Vector Index
```

SGOKBがrebuild authorityを持つ。

将来UPDSがPersonal Inference用Embedding / Indexを持つ場合、次のように別のderived pipelineとする。

```text
UPDS Selection / Observation / Pattern / Hypothesis
        ↓
UPDS Search Representation
        ↓
UPDS Embedding
        ↓
UPDS Vector Index
```

SGOKB canonical version promotionによってUPDS Personal Indexを直接書き換えず、UPDS側が参照Version更新を検出して必要な再解析・再indexを決定する。

---

## 7. Physical backend policy

K-03では物理backendを次のように扱う。

### 許容

```text
同じQdrant process
同じSQLite vector extension
同じEmbedding model
同じEmbedding provider runtime
```

ただし論理collection / namespace / ownershipが分離される場合に限る。

### 禁止

```text
SGOKBとUPDSが同じcollectionへ無区別にpointを投入する
同一metadata schemaでObject KnowledgeとPreference Hypothesisを混在させる
SGOKB rebuildがUPDS pointsを削除・再生成する
UPDS rebuildがSGOKB pointsを削除・再生成する
同じscoreをWorld similarityとPreference probabilityの双方として扱う
```

したがって、「backend共有」と「Semantic Index共有」は別概念として扱う。

---

## 8. K-03 automated verification

追加test:

```text
tests/test_k03_semantic_index_boundary.py
```

確認事項:

1. `SearchRepresentationKind`がWorld/Object/Evidence側の4 kindだけである。
2. MCP read Tool input schemaにPersonal Inference fieldが存在しない。
3. Personal Profile / Preference fieldをMCP read Toolへ渡すと拒否される。
4. SGOKB Vector Index metadataにPersonal Inference fieldが混入しない。
5. Object Similarity resultのscore typeが`cosine_similarity`としてretrieval semanticsを維持する。
6. Similarity resultに`preference_probability` / `preference_confidence` fieldが存在しない。
7. `src/sgokb`がUPDS固有Personal model classへimport依存していない。

実行結果:

```text
K-03 + J-01 similarity + J-02 MCP regression
14 passed

K-03 focused
6 passed

Ruff tests/test_k03_semantic_index_boundary.py
All checks passed
```

---

## 9. UPDS未実装状態での判定

UPDSは現在構想・初期設計段階であり、実際のUPDS Semantic Indexはまだ存在しない。

そのためK-03では次の2段階で扱う。

### Stage A — Complete in this task

SGOKB側でPersonal Inferenceを受け入れないcontract、Search Representation ownership、score semantics、MCP boundaryを実装・自動試験で固定する。

### Stage B — future UPDS implementation

UPDS側でSemantic Indexを実装する場合、次をcross-repository testで追加確認する。

- SGOKB / UPDS collectionまたはnamespaceが分離されている。
- UPDS Personal representationがSGOKB indexへ書き込まれない。
- rebuild authorityが分離されている。
- SGOKB scoreがPreference probabilityへ直接変換されない。
- SGOKB停止時にUPDSがSGOKB内部indexへdirect fallbackしない。

Stage Bが未実施であることは、現在UPDS実装が存在しない以上、K-03のblockerとはしない。

---

## 10. K-04への引き継ぎ

K-04ではUPDS専用Context/Profileの追加要否を評価する。

K-03の境界から、専用Context/Profileを追加するとしても次を満たす必要がある。

```text
許容:
  汎用Object KnowledgeからUPDS利用に適したFacet subsetを決定論的に選ぶ
  data transfer / context budgetを削減する

禁止:
  User ProfileをSGOKBへ渡す
  Preference HypothesisでSGOKB rankingをpersonalizeする
  UPDS Personal EmbeddingをSGOKB Object Indexへ混ぜる
  SGOKB側でPreference推論する
```

この境界を満たしたうえで、既存`get_objects` / `build_context`で不足が実証されるかを評価する。

---

## 11. Definition of Done

- [x] SGOKB Semantic Indexの所有対象をObject / Facet / Statement / Evidenceへ固定した。
- [x] UPDS Personal InferenceとSGOKB Search Representationを混在させないことを確認した。
- [x] MCP read contractがPersonal Profile / Preference signalを受け取らないことを確認した。
- [x] SGOKB Vector metadataにPersonal Inference fieldがないことを自動試験化した。
- [x] Similarity scoreをPreference probabilityへ変換しない意味境界を確認した。
- [x] SGOKB sourceがUPDS Personal modelへ依存しないことを確認した。
- [x] 物理backend共有とSemantic Index ownershipを分離して定義した。
- [x] UPDS実装後に必要なStage B verificationを明記した。
- [x] K-04へ引き継ぐContext/Profile境界を固定した。

**K-03 Acceptance: PASS**

次Task:

```text
K-04 [P2] UPDS向けContext/Profileを追加するか評価する
```
