# N-04G-01 Grounded Generation Responsibility / Guarantee Boundary

更新日: 2026-10-18

- Status: **Accepted**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Task: `N-04G-01 [P0] grounded-generationの責務所有者と保証レベルを確定する`
- Failure baseline: `benchmark/n04-ai-use-cases-v1.json`
- Acceptance record: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- Design handoff: `docs/planning/N04_GROUNDED_GENERATION_HANDOFF.md`
- Remediation task master: `docs/planning/N04_GROUNDED_GENERATION_TASKS.md`

---

## 1. Decision

N-04 grounded-generation対策の責務モデルとして、**SGOKB-owned contract + consumer-owned orchestration + untrusted LLM**のhybrid方式を採用する。

要点は次の通り。

1. **SGOKB Application層がgrounded-generation contractの正本を所有する。**
2. **MCPはKnowledge Access / transport boundaryのままとし、LLM推論主体にはしない。**
3. **ConsumerがLLM runtimeの選択・呼出し・generation orchestrationを所有する。**
4. **LLMのraw outputはgroundedであると信頼しない。** LLMはcontractへ従うbest-effort generatorであり、groundingの権威ではない。
5. **「SGOKB-grounded output」と呼べるのは、SGOKBが定義するcontractへ適合し、必要なconformance / validation Gateを通過した結果だけ**とする。
6. Validationの具体方式、Fact ID、Structured Output、retry等は本Taskでは決めず、N-04G-02〜G-06へ委ねる。

このDecisionにより、SGOKB本体を特定LLM provider / modelへ密結合せず、ChatGPT / local LLM / UPDS / Other Clientsへ共通適用できるmodel-independent grounding contractを設計できる。

---

## 2. 背景

N-04 v1ではRetrieval / MCP / Context Builder自体にproduction defectは確認されなかった。

一方、local LLMは供給Context外の事前学習知識をfactとして追加し、Comparisonではinterpretation分離不足、Creativeではcreative additionの明示不足が発生した。

この結果から、次の2点を同時に満たす必要がある。

- Knowledge retrieval / MCPの既存責務境界を理由なく崩さない。
- 「Contextだけを使え」というprompt指示だけにgrounding保証を委ねない。

J-01 / J-06で既に次がAcceptedである。

```text
Canonical SQLite / Derived Search Index
              ↓
        Retrieval Core
              ↓
 KnowledgeReadApplication
              ↓
        Transport Adapter
              └─ MCP
```

MCPはtransport/schema adapterであり、SQLite query、Repository直接参照、Embedding runtime構築、Context selection policy、canonical mutationを所有しない。

したがってN-04対策でMCP Serverへ特定LLMのgeneration logicを埋め込む方式は採用しない。

---

## 3. 比較した責務案

### Option A — SGOKB ApplicationがLLM generationまで所有する

```text
SGOKB Application
  ├─ Retrieval / Context
  ├─ Prompt / Generation
  ├─ LLM Provider
  └─ Validation
```

#### 利点

- 1 runtime内でgenerationからvalidationまで統制しやすい。
- consumer実装差を小さくできる。
- acceptance harnessを単純化しやすい。

#### 欠点

- SGOKB本体がLLM provider / model / inference runtimeへ密結合しやすい。
- ChatGPT、local LLM、UPDS等の異なるconsumer形態をSGOKB側が吸収する必要がある。
- Knowledge Baseとgeneration engineの責務が混ざる。
- local-only / external ChatGPT等の実行環境差をApplication coreへ持ち込む。

#### Decision

**不採用。**

SGOKBはgrounding semanticsを所有するが、LLM inference runtime自体は所有しない。

---

### Option B — MCP Toolがgenerationを所有する

```text
Client
  ↓
MCP generate_grounded_response
  ↓
LLM
```

#### 利点

- Clientからは1 Toolで利用できる。
- MCP経由の利用体験は単純になる。

#### 欠点

- J-01 / J-06で固定した「MCP = transport/schema adapter / Knowledge Access Layer」と衝突する。
- MCP Server内へprovider、model、prompt、retry等のgeneration policyが入りやすい。
- Application semanticsとtransport semanticsが再結合する。
- MCP以外の将来transportで同じgrounding semanticsを再実装する危険がある。

#### Decision

**不採用。**

将来grounding関連capabilityをMCPで公開する場合でも、MCPはApplication capabilityのtransport adapterに限定する。MCP自身をgrounding semanticsやLLM generationの所有者にはしない。

---

### Option C — SGOKB提供consumer libraryだけが責務を所有する

```text
MCP
  ↓
SGOKB Consumer Library
  ↓
LLM
```

#### 利点

- MCPを薄く保てる。
- local consumerではorchestration実装を共通化できる。
- provider adapterをconsumer側へ隔離しやすい。

#### 欠点

- ChatGPT等、SGOKBのPython libraryを直接実行できないconsumerへ適用できない。
- libraryを使用しないclientでは同じ保証を得られない。
- library実装そのものがnormative contractになり、言語/runtimeへ依存する危険がある。

#### Decision

**単独方式としては不採用。**

将来、contract準拠を容易にするreference consumer library / helperを提供することは許容する。ただしそれはgrounding semanticsの正本ではなく、SGOKB Application側contractのreference implementationとする。

---

### Option D — 外部client responsibility + 文書contractのみ

```text
SGOKB Context
  ↓
External Client
  ↓
LLM
```

#### 利点

- SGOKB実装への影響が最小。
- consumerの自由度が最大。
- provider / model依存を完全に外部へ隔離できる。

#### 欠点

- N-04 v1が示した通り、prompt / written instructionだけではContext外知識混入を十分抑止できない。
- clientごとにgrounding semanticsや判定が分岐する。
- 「SGOKB-grounded」と名乗るための共通conformance条件が存在しない。
- consumer実装ミスをsystematicに検出できない。

#### Decision

**不採用。**

外部consumerは実行責務を持つが、grounding contract自体を自由定義してはならない。

---

### Option E — Hybrid: SGOKB-owned contract + consumer orchestration

```text
SGOKB
  ├─ Canonical Knowledge / Retrieval
  ├─ Context Builder
  └─ Grounding Contract / Conformance Semantics
           ↓ public boundary
Consumer Orchestrator
  ├─ Context / contract受領
  ├─ LLM invocation
  ├─ output収集
  ├─ conformance / validation実行・照会
  └─ Accept / failure handling
           ↓
Local LLM / ChatGPT等
  └─ untrusted best-effort generator
```

#### 利点

- SGOKBがgrounding semanticsのsingle source of truthを維持できる。
- MCPをKnowledge Access / transport boundaryとして維持できる。
- provider / model runtimeをconsumer側へ隔離できる。
- ChatGPT / local LLM / UPDS / Other Clientsへ同一contractを適用できる。
- raw LLM outputをgroundedと誤認せず、conformance後だけ認定できる。
- 将来consumer helperを追加してもcontract ownershipが変わらない。

#### 欠点

- consumerは単純な「ContextをLLMへ渡すだけ」より実装責務が増える。
- contract version / conformance resultの扱いが必要になる。
- MCPだけではgeneration workflow全体を自動完結しない。

#### Decision

**採用。**

この欠点は、SGOKBをLLM runtimeへ密結合させるより小さく、N-04 failureをsystem-levelに扱うために必要な責務増加と判断する。

---

## 4. 採用する責務境界

### 4.1 SGOKB Application / Grounding Contract Layer

SGOKBが所有する。

責務:

- grounded-generation contractのversionedな正本。
- grounded outputとして認めるためのnormative semantics。
- Context / claim / support / classification / conformanceに関する共通概念の定義。
- provider / model非依存のinput / output contract。
- conformance / validation結果の意味定義。
- failure classと、後続Taskで定義するpolicyの正本。
- current accepted Knowledge / provenance / Context selectionの既存保証との接続。

非責務:

- 特定LLM providerのSDK / endpoint管理。
- model download / load / GPU offload。
- Chat completion APIの直接実行。
- provider固有prompt tuning。
- natural-language品質そのものの保証。

ここでいう`Grounding Contract Layer`は論理責務名であり、N-04G-01時点で新しい物理module / class / DB tableの実装を決めるものではない。

---

### 4.2 Retrieval / Context Builder

既存SGOKB Application責務を維持する。

責務:

- current / pinned Version semantics。
- deterministic Context selection。
- purpose / budget。
- selected Knowledgeのidentity / scope / warning。
- N-04G-03で必要と判断された場合のgrounding reference情報を、Application contractとして提供できること。

非責務:

- LLMへ「正しく考えさせる」こと。
- raw model outputのgrounding保証。
- Context不足をmodel memoryで補完すること。

---

### 4.3 MCP

既存のKnowledge Access / transport boundaryを維持する。

責務:

- Application capabilityを公開contractへ変換する。
- protocol / schema / transport validation。
- read-only semanticsを維持する。

非責務:

- LLM generation。
- model selection。
- provider runtime。
- grounding semanticsの独自定義。
- Applicationとは異なるvalidator semanticsの実装。

N-04G-03〜G-05でgrounding関連Application capabilityをMCP経由で公開する必要が生じた場合でも、MCPはそのtransport adapterに限定する。

---

### 4.4 Consumer Orchestrator

Consumerが実行責務を所有する。

対象例:

- N-04 acceptance harness
- local LLM client
- ChatGPT側workflow
- UPDS
- Other Clients

責務:

- SGOKB public boundaryからKnowledge / Context / contract metadataを取得する。
- contract-compatibleなgeneration requestを構築する。
- LLM runtimeを選択・呼び出す。
- raw request / responseと必要なmetadataを保持する。
- SGOKB-defined conformance / validation Gateを実行または照会する。
- conformance前のraw outputを`SGOKB-grounded`として扱わない。
- N-04G-06で確定するfailure handling policyを適用する。
- acceptance時はmodel / rubric / protocolをcaseごとにcherry-pickしない。

非責務:

- SGOKB canonical factの再定義。
- grounding taxonomyの独自変更。
- SGOKB contractをsilentに緩和すること。
- Context不足を外部Web / model memoryのfactでsilent補完すること。

---

### 4.5 LLM

LLMは**信頼境界外のbest-effort generator**として扱う。

責務:

- 与えられたgeneration instruction / contractに従って出力を試みる。

保証しないこと:

- instruction-following完全性。
- Context外knowledgeを絶対に使用しないこと。
- 自己申告citation / classificationの正しさ。
- 自己評価の正しさ。
- raw outputのgrounding。

LLMの「私はContextだけを使った」という自己申告をgrounding証明として使用しない。

---

## 5. 責務表

| Concern | SGOKB Application / Contract | MCP | Consumer | LLM |
|---|---|---|---|---|
| Canonical Knowledge semantics | **Owner** | Transport only | Use | None |
| Retrieval / Context selection | **Owner** | Transport only | Request / consume | None |
| Grounding contract semantics | **Owner** | Transport only | Must conform | Follow best-effort |
| Claim taxonomy semantics | **Owner**（G-02で定義） | Transport only | Apply | Emit requested form |
| Grounding reference semantics | **Owner**（G-03で定義） | Transport only | Preserve / use | Refer as instructed |
| Output contract semantics | **Owner**（G-04で定義） | Transport only | Enforce | Generate |
| Validator semantics | **Owner**（G-05で定義） | Optional transport only | Invoke / consume result | Not authority |
| LLM provider / model runtime | No | No | **Owner** | Runtime target |
| Prompt/request assembly | Contract requirementsを定義 | No | **Owner** | Consume |
| Raw response generation | No | No | Invoke | **Owner of generation only** |
| `SGOKB-grounded`認定 | Contract / Gateを定義 | No | Gate通過時のみ付与 | Cannot self-certify |
| Failure handling execution | Policy定義（G-06） | No | **Owner** | Retry target if allowed |
| Canonical mutation | Existing explicit workflow only | Read-only | No implicit mutation | No |

---

## 6. 保証レベル

N-04以降のgrounded-generation保証を次のlayerに分ける。

### Level 0 — Knowledge / Context Integrity

SGOKBが保証する。

対象:

- current accepted Version resolution。
- requested scope / purpose / budget。
- historical silent mixingの防止。
- canonical Knowledge / Evidence / Provenance semantics。

N-04 v1でこのLevelはproduction defectなしと確認済み。

---

### Level 1 — Grounding Contract Integrity

SGOKBが保証する。

対象:

- versioned grounded-generation contract。
- claim category / reference / output / validation semantics。
- provider / model-independentなconformance条件。

具体schemaはN-04G-02〜G-05で確定する。

---

### Level 2 — Output Conformance

**raw LLM outputには保証しない。**

SGOKB-defined conformance Gateを通過した出力に限り、`SGOKB-grounded`として扱える。

このLevelで何を機械的に検証するか、どの程度fail-closedにするかはN-04G-05で決める。

重要な原則:

```text
LLM generated
≠
SGOKB-grounded

LLM generated
+ SGOKB contract conformance
+ required validation pass
=
SGOKB-grounded eligible
```

`eligible`は「文章中のあらゆる意味が世界の絶対真実である」という意味ではない。供給SGOKB Contextに対するgrounding contractへ適合したことを意味する。

---

### Level 3 — Workflow Enforcement

Consumer Orchestratorが実行責務を持つ。

対象:

- validation結果を無視しない。
- Accept / Retry / Reject / Insufficient等の正式actionを適用する。
- failure evidenceを保持する。
- unvalidated outputをgroundedとしてuserへ提示しない。

SGOKBはpolicy semanticsを定義するが、外部consumerがprotocolを意図的に迂回した場合までgroundingを保証しない。

具体actionはN-04G-06で確定する。

---

### Level 4 — Model Quality / Literary Quality

SGOKBのgrounding保証対象外とする。

例:

- 文体が魅力的か。
- Roleplayが原作らしいか。
- Creative outputが面白いか。
- Comparisonが洞察深いか。
- modelが高速か。

ただしN-04 acceptance rubricで明示されたuse-case成立条件は別であり、groundingとは別軸でPASSする必要がある。

---

## 7. `SGOKB-grounded`という表示の意味

将来consumerがoutputへ`grounded`状態を付ける場合、最低限次を満たす結果だけに限定する。

```text
1. SGOKB public boundary由来のContextを使用
2. 対応contract versionを識別
3. contractに従うgeneration flowを使用
4. 必須conformance / validation GateをPASS
5. unresolved critical failureがない
```

consumerがSGOKB Contextを取得しただけでは`SGOKB-grounded`とはみなさない。

逆に、LLMが偶然正しい内容を書いた場合でも、required Gateを通っていなければ正式なgrounded認定対象にはしない。

この状態名や具体fieldはN-04G-04 / G-05で確定する。

---

## 8. Consumer実装ミスへの境界

SGOKBはすべての外部consumerの挙動を強制できない。

そこで次の境界を採用する。

### SGOKB側で防止・検出すべきもの

- breaking contract versionをsilentに旧versionとして扱うこと。
- groundingに必要なmetadataが欠落した状態をvalid contractとして返すこと。
- validator / conformance結果の意味がconsumerごとに変わること。
- invalid outputをPASSとして扱うSGOKB公式実装。

### Consumer側で守るもの

- Contextを別knowledgeでsilent拡張しない。
- validationをskipしない。
- FAILをPASS表示しない。
- contract version mismatchを無視しない。
- acceptance条件をcaseごとに変えない。

外部consumerがこのcontractを迂回した場合、SGOKBはその出力をgroundedとは保証しない。

---

## 9. Model-independent contractの範囲

N-04G-01では、次をmodel-independent領域としてSGOKB側で所有できると判断する。

- claim categoryの意味。
- Context supportの参照方法。
- grounded / interpretation / creative / unsupported等の意味境界。
- output envelope / contract version。
- conformance / validation result semantics。
- insufficient context semantics。
- failure class。
- Accept / Reject等のpolicy semantics。

一方、次はmodel/runtime-specific領域としてconsumer側へ残す。

- model identifier / quantization。
- endpoint / provider SDK。
- GPU offload。
- generation parameterのprovider固有表現。
- model-specific prompt wrapper / chat template。
- tokenization / context-window実装差。

N-04 v2 benchmarkではmodel settingsをfreezeして記録するが、それをSGOKB general contractの意味論へ昇格させない。

---

## 10. ChatGPT / local LLM / UPDSへの適用

### ChatGPT

ChatGPTはSGOKB内部libraryを直接実行することを前提にしない。

- MCP等のpublic boundaryからContext / contract情報を受け取る。
- generationはChatGPT側runtimeで行う。
- SGOKB-groundedと認定するworkflowでは、SGOKB-defined conformance Gateを満たす必要がある。

### Local LLM

- Consumer harness / local applicationがMCPからContextを取得する。
- local model endpointをconsumerが呼ぶ。
- raw outputはuntrustedとしてconformanceへ渡す。

N-04 formal re-acceptanceはこの形を基準にする。

### UPDS

UPDSが将来SGOKB Knowledgeを使ってLLM inferenceを行う場合も同じ責務境界を適用できる。

- SGOKBはWorld / Object Knowledgeとgrounding contractを所有。
- UPDSはPersonal Inferenceとconsumer orchestrationを所有。
- SGOKBへPersonal Inferenceを逆流させない。

### Other Clients

contract versionとconformance Gateを守れば、特定SDK / providerへ依存せず適用できる。

---

## 11. N-04G-02以降への拘束条件

本Decisionにより後続Taskへ次を引き渡す。

### N-04G-02 Claim taxonomy

- taxonomy semanticsはSGOKB-owned contractの一部として設計する。
- LLMの自己分類だけを権威にしない。
- Roleplay / Comparison / Creativeで共通利用可能なcore taxonomyを優先する。

### N-04G-03 Context grounding / reference

- reference semanticsはSGOKB Application contract側の正本とする。
- MCP固有ID体系をgrounding identityの正本にしない。
- consumer独自Fact IDだけを正本にしない。
- canonical schema変更の要否は別途判断する。

### N-04G-04 Generation / output contract

- provider-independentなnormative contractをSGOKB側で定義する。
- provider固有chat templateはconsumer側へ隔離する。

### N-04G-05 Validation

- validation semantics / PASS・FAIL意味はSGOKB-owned contractとする。
- validation実装場所・deterministic / LLM judge / hybridの採否は未決。
- LLM self-checkだけを最終authorityにはしない。

### N-04G-06 Failure handling

- failure policy semanticsはSGOKB contract側で定義する。
- retry / reject等のexecutionはconsumer orchestrationが担当する。
- retry採用自体は未決。

---

## 12. 本Taskで意図的に未決の事項

N-04G-01では以下を採用済みにしない。

- Fact ID / Statement ID / Evidence IDのどれを使うか。
- Context-local referenceを使うか。
- Structured Outputを採用するか。
- 1-stage / 2-stage generation。
- post-generation validatorを必須にするか、その実装方式。
- deterministic validatorとLLM judgeの構成。
- retryを行うか。
- retry回数。
- creative modeの具体field / section。
- `SGOKB-grounded`状態の具体schema。

これらは責務境界を前提にN-04G-02〜G-06で個別に比較する。

---

## 13. Architecture impact

### Canonical Knowledge

変更なし。

- Object identity
- Version
- Statement / Attribute / Relation
- Evidence / Provenance

N-04G-01のためのDB migrationは要求しない。

### Retrieval / Context Builder

既存ownershipを維持する。

後続G-03でpresentation / reference metadata追加が必要かを検討するが、Retrieval semantics自体は変更しない。

### MCP

既存のtransport adapter境界を維持する。

### Consumer

N-04 v1より責務が明確に増える。

```text
Before:
Context → prompt → LLM → response

After conceptual boundary:
Context + contract → LLM → raw output → conformance Gate → accepted output / failure action
```

ただし具体的なGate構成はG-05で決める。

---

## 14. Acceptance impact

N-04 v2では少なくとも次を評価可能にする必要がある。

- 使用したgrounded-generation contract versionが識別できる。
- raw outputとaccepted output / decisionを区別できる。
- consumerがrequired Gateを迂回していないことを証跡化できる。
- LLMの自己申告ではなく、SGOKB-defined conformance semanticsに基づいてgroundingを評価できる。
- existing v1 core rubricを緩和しない。

v2 benchmark具体仕様はN-04G-08でfreezeする。

---

## 15. Definition of Done

- [x] 責務所有者候補を比較した。
- [x] Hybrid方式を採用した。
- [x] SGOKB / MCP / Consumer / LLMの責務を分離した。
- [x] SGOKBが保証する範囲と保証しない範囲を定義した。
- [x] raw LLM outputをgroundedとみなさない境界を確定した。
- [x] model-independent contractとmodel-specific runtimeの境界を定義した。
- [x] ChatGPT / local LLM / UPDS / Other Clientsへ適用可能な責務モデルを定義した。
- [x] Fact ID / Structured Output / validator / retry等を先取りして採用していない。
- [x] N-04G-02以降へ拘束条件を引き渡した。

N-04G-01は**Complete**とする。

次Task:

```text
N-04G-02 [P0]
claim taxonomyと用途別意味境界を確定する
```
