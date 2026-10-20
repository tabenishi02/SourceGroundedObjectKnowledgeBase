# N-04G-23 Two-Stage Grounded Generation Architecture Decision

更新日: 2026-10-20

- Status: **Accepted**
- Trigger: `N-04G-22 Formal v3 Re-Acceptance` valid formal FAIL (`0 / 3 Case PASS`)
- Root-cause investigation: `docs/evaluation/N04G22_FAILURE_ROOT_CAUSE_INVESTIGATION.md`
- Historical v3 freeze: `docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md`
- Historical v3 harness freeze: `docs/decisions/N04G21_V3_ACCEPTANCE_REFERENCE_WORKSTATION_HARNESS_FREEZE.md`
- Current N-04 state: **Failed / not Complete**
- N-05: **blocked**

---

## 1. Decision

SGOKBのGrounded Generationは、次期v4候補から**LLMによる生成責務を2段階へ分離する**。

```text
Grounded Context
       │
       ▼
┌──────────────────────────────┐
│ Stage 1: Grounded Content    │
│ Planner                      │
│                              │
│ - atomic source facts        │
│ - support refs               │
│ - interpretation premises    │
│ - presentation allowance     │
└──────────────┬───────────────┘
               │
               ▼
      Reference Integrity
               │
        Atomicity Gate
               │
        Role Boundary
               │
     Deterministic Support
               │
          MiniCheck
               │
      Source Fact Judge
               │
               ▼
       Certified Content
               │
               ▼
┌──────────────────────────────┐
│ Stage 2: Presentation        │
│ Generator                    │
│                              │
│ - certified facts only       │
│ - interpretation             │
│ - allowed creative content   │
│ - presentation/output shape  │
└──────────────┬───────────────┘
               │
               ▼
        Final V0-V5 checks
               │
      Material Requirement
               │
        Terminal / Render
```

ここで2段階化するのは**LLM生成責務**である。

既存のfail-closed validation、MiniCheck、Material Requirement、Terminal、Render authorizationは廃止せず、段階間および最終出力後に継続利用する。

---

## 2. Why this is adopted

G-22では1回のGenerator callへ次の責務が集中していた。

```text
content generation
+ factual restriction
+ atomic decomposition
+ semantic-role assignment
+ support selection
+ interpretation generation
+ creative generation
+ presentation planning
+ output schema construction
```

その結果、異なるfailure classが同じgeneration attempt内で同時に観測された。

- unsupported source-world additions
- NON_ATOMIC source facts
- role-INDETERMINATE
- unsupported interpretation premise
- duplicate_presentation_role

一方でG-22では次がPASSしている。

- Retrieval / Similarity
- canonical DB / integrity
- MiniCheck offline reproduction
- frozen runtime identity
- engineering regression Gates

したがって、RetrievalやMiniCheckを再設計するよりも、**「何が言えるか」と「どう表現するか」を分離する**方がfailure evidenceへ直接対応する。

---

## 3. Versioning / historical evidence rule

G-18/G-21のv3 Frozen artifactは変更しない。

```text
benchmark/n04-ai-use-cases-v3.json
benchmark/n04-v3-formal-harness-v1.json
benchmark/n04-v3-material-profiles-v1.json
benchmark/n04-v3-source-fact-verifier-profile-v1.json
```

これらはG-22 formal FAILを再現できるhistorical authorityとして保持する。

2段階生成は**v4 candidate**として新しいschema/profile/harnessを作成する。

過去のG-22結果を後からPASSへ書き換えない。

---

## 4. Stage 1 — Grounded Content Planner

### 4.1 Responsibility

Stage 1は「最終文章を書く」のではなく、supplied Grounded Contextから**利用可能な原子的内容計画を作る**。

最低限の責務:

1. Context内からsource-world fact候補を選ぶ。
2. 1 fact = 1 independently judgeable propositionへ分解する。
3. 各factへsupport refを付与する。
4. interpretationで使用可能なpremise候補をfact IDで示す。
5. use-case purposeに応じたpresentation allowanceを示す。
6. Context外の背景知識・model memoryをsource factとして追加しない。

### 4.2 Candidate intermediate contract

新規candidate schemaを設計する。

```text
sgokb.grounded-content-plan.v1
```

概念形:

```json
{
  "plan_id": "...",
  "context_fingerprint": "...",
  "source_facts": [
    {
      "fact_id": "F1",
      "text": "...",
      "support_refs": ["K5"]
    }
  ],
  "interpretation_slots": [
    {
      "slot_id": "I1",
      "premise_fact_ids": ["F1"]
    }
  ],
  "presentation_allowance": {
    "main": true,
    "interpretation": true,
    "creative": false
  }
}
```

このJSON例は設計方向を示すものであり、G-23Bで正式schemaを確定する。

### 4.3 Prompt policy

Stage 1 Promptはrule-onlyにせず、少なくとも次を含める。

- neutral GOOD/BAD atomic examples
- `prefer exact Grounded Context wording`
- `minimally normalize wording`
- `one proposition per fact`
- Contextにない追加命題を禁止
- support_refsとfact textの対応例

source_factでは文章表現の豊かさより**保守性と監査可能性**を優先する。

---

## 5. Certification boundary between Stage 1 and Stage 2

Stage 1 outputをそのままStage 2へ渡してはならない。

次を通過したfactのみ`Certified Content`へ昇格する。

```text
Reference Integrity
  ↓
Atomicity
  ↓
Role Boundary
  ↓
Deterministic Source Support
  ↓ unresolved only
MiniCheck
  ↓ supported candidate only
Independent Source Fact Judge
  ↓ ENTAILED only
Certified Fact
```

### 5.1 Atomicity / Role separation

AtomicityとSemantic Roleは**別の論理Gate**として扱う。

G-22で両方を同一bounded judge responseへ結合した結果、Case 2で妥当なsource_fact候補までrole-INDETERMINATEとなったため、G-23AでGold Benchmarkを作り以下を比較する。

1. exact G-22 prompt/payload replay
2. same Phi-4 + clarified prompt/examples
3. same Phi-4 + atomicity / role separate calls
4. それでも不十分な場合のみalternative judge model

モデル交換を最初の対処にしない。

### 5.2 Certified Content

Stage 2へ渡す中間objectは、candidate factではなく**certified factのみ**を含む。

新規candidate contract:

```text
sgokb.certified-content.v1
```

各certified factには少なくとも次を保持する。

- fact_id
- text
- support_refs
- source-support result
- verifier/judge evidence binding
- context fingerprint

---

## 6. Stage 2 — Presentation Generator

### 6.1 Responsibility

Stage 2は「何が事実か」を再決定しない。

責務は次に限定する。

1. certified factsの選択・配置
2. certified factをpremiseとするinterpretation生成
3. purposeで許可されたcreative content生成
4. presentation role / block構成
5. final structured output構築

### 6.2 Input restriction

Stage 2のprimary factual inputは`Certified Content`とする。

原則としてraw Grounded Context全文をStage 2へ再提示しない。

理由:

- Stage 1 certificationを迂回した新規source fact生成を防ぐ。
- model memoryやraw Kからの再解釈によるfactual leakageを減らす。
- Stage 2 failureをpresentation/reasoning問題へ局所化する。

### 6.3 Source-fact binding

Stage 2がsource_factを出力する場合、certified factとのbindingを必須にする。

v4設計では次のいずれかを比較し、よりfail-closedな方法を採用する。

A. `certified_fact_id`を出力し、applicationがtext/support refsをdeterministicにmaterializeする。

B. Stage 2がtextを出すが、certified factとのexact/minimally-normalized bindingをdeterministicに検証する。

安全性の観点ではAを第一候補とする。

### 6.4 Interpretation

interpretationはcertified fact IDだけをpremiseとして参照する。

未certified fact、raw K ID、model memoryから新しいpremiseを導入した場合はFAILとする。

### 6.5 Creative content

creativeはpurpose/material profileが許可した場合だけ生成する。

creative textへsource-world factual assertionを混入させない既存境界は維持する。

---

## 7. Final validation remains multi-stage

2段階生成へ移行しても最終validationを省略しない。

Stage 2 outputに対して既存v3の安全思想を継承する。

```text
V0 Structural Contract
V1 Reference / Certified binding
V2 Atomicity / Semantic Role / Scope
V3 Deterministic Support
V4 Fact / Interpretation validation
V5 Grounding Aggregate
Material Requirement
Terminal Decision
Render Authorization
```

v4で各Gateの入力contractを再定義するが、**fail-closed principleを緩和しない**。

---

## 8. Retry policy redesign

retryはstage-localにする。

### Stage 1 retry

対象:

- NON_ATOMIC
- invalid support ref
- unsupported fact
- role-boundary failure

Stage 1だけを再実行する。

### Stage 2 retry

対象:

- presentation/schema violation
- duplicate presentation role
- invalid certified fact binding
- interpretation premise violation
- creative scope violation

Stage 2だけを再実行する。

### Retry feedback

failure code / unit IDだけでなく、最低限次を含める。

- failed unit text
- failed stage
- relevant support/certified fact IDs
- expected rule
- structured repair directive

前attempt全体を無条件に再投入するのではなく、必要なfailure evidenceだけを返す。

---

## 9. Provider schema / presentation-role cardinality

`duplicate_presentation_role`を可能ならprovider structured-output段階で防ぐ。

G-23DでLM Studio / llama.cppの実runtimeに対して以下をprobeする。

- `contains`
- `minContains`
- `maxContains`
- role別cardinality

対応している場合はschemaへ移す。

対応していない場合でもAcceptance ruleを緩めず、Stage 2 planning + V0 deterministic checkでfail-closedにする。

`uniqueItems`だけではrole fieldの重複禁止にならないため代替にはしない。

---

## 10. Material Requirement

Material Requirementの意味基準は維持する。

ただし評価対象を可能な限りcertified contentへ寄せる。

例:

- Case 1: certified source facts >= required count
- Case 2: comparison対象双方からcertified factsを確保し、interpretation premiseもcertified factのみ
- Case 3:各Conceptからcertified factsを確保し、その上でcreative requirementを満たす

Stage 1終了時点で必要なsource materialが成立しないことが確定した場合、Stage 2を無駄に実行せずfail-closed terminalへ進める設計を検討する。

---

## 11. Evidence / reproducibility

各stageを独立して証跡化する。

最低限:

```text
context/
stage1/
  request
  raw-output
  parsed-plan
  retry-feedback
certification/
  atomicity
  role
  deterministic-support
  verifier
  source-fact-judge
  certified-content
stage2/
  request
  raw-output
  parsed-output
  retry-feedback
final-validation/
material/
terminal/
render/
```

Stage 1 / Stage 2それぞれについてprompt artifactとhashをtracked/frozen対象にする。

Atomicity / Role judge promptもfirst-class artifactとしてhash固定できる構造へ改める。

---

## 12. What is explicitly not changed by this decision

新しいfailure evidenceなしに次を変更しない。

- Object identity / Version semantics
- Source / Evidence / Provenance
- canonical DB
- MCP read-only boundary
- Retrieval / Similarity algorithm
- Context Builder budget / purpose selection
- N-03 fixed dataset
- MiniCheck selection / threshold `>= 0.50`
- G-12 / G-20 / G-20R / G-21 / G-22 historical evidence
- fail-closed acceptance principle
- unsupported rendered claim = unacceptable
- role escape = unacceptable

---

## 13. Architecture expansion rule

最初から3段階以上へ分割しない。

v4の標準構成は:

```text
Stage 1  Grounded Content Planning
Stage 2  Presentation Generation
```

とする。

ただし将来Stage 2内でinterpretation / creative / surface realizationの責務衝突が実測された場合に限り、

```text
Stage 1  Grounded Content
Stage 2  Reasoning / Creative Plan
Stage 3  Surface Realization
```

への拡張を検討する。

段階数は増やせるようinterfaceを設計するが、failure evidenceなしにstageを増やさない。

---

## 14. Acceptance direction

v4をformal re-acceptanceへ進める前に、dev benchmarkで少なくとも以下を測定する。

```text
Stage 1:
  unsupported proposition rate
  NON_ATOMIC rate
  valid role rate
  certified fact yield
  required material coverage

Atomicity / Role:
  critical false-pass
  valid-unit false-reject
  INDETERMINATE rate
  repeatability

Stage 2:
  new unsupported source-fact introduction = 0
  invalid certified binding = 0
  duplicate presentation role rate
  invalid interpretation premise rate
  creative scope violation rate

End-to-end:
  Material PASS eligibility
  terminal ACCEPTED rate
  unsupported rendered material claim = 0
  accepted role escape = 0
```

formal Gateをdev結果に合わせて緩めない。

---

## 15. Decision summary

採用する中心原則は次である。

> **LLMに「事実を決めること」と「表現すること」を同じgeneration callで行わせない。**

Stage 1で何が言えるかを原子的に計画・certifyし、Stage 2はcertified contentだけを使ってどう表現するかを決める。

これによりG-22で観測されたfactual leakage、atomicity failure、role判定問題、presentation planning failureを別々の境界で診断・retry・rejectできる構造へ移行する。
