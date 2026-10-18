# N-04G-06 Validation Failure Handling Policy

更新日: 2026-10-18

- Status: **Accepted**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Task: `N-04G-06 [P0] validation failure時のretry / reject / insufficient policyを設計する`
- Responsibility Decision: `docs/decisions/N04G01_GROUNDED_GENERATION_RESPONSIBILITY_BOUNDARY.md`
- Claim Taxonomy Decision: `docs/decisions/N04G02_CLAIM_TAXONOMY_AND_USE_CASE_BOUNDARIES.md`
- Grounding Reference Decision: `docs/decisions/N04G03_CONTEXT_GROUNDING_REFERENCE_CONTRACT.md`
- Generation / Output Decision: `docs/decisions/N04G04_GENERATION_OUTPUT_CONTRACT.md`
- Validation Decision: `docs/decisions/N04G05_GROUNDING_VALIDATION_DESIGN.md`
- Remediation task master: `docs/planning/N04_GROUNDED_GENERATION_TASKS.md`

---

## 1. Decision

N-04 grounded-generationのvalidation failure handlingとして、**bounded single retry + fail-closed terminal handling**を採用する。

基本原則:

1. **1 grounded-generation runにつきLLM再生成retryは最大1回**とする。
2. retryは**同じGrounded Context、同じgenerator model/runtime、同じgeneration settings、同じcontract version**で行う。
3. retry時に渡す追加情報は、validatorが出した**構造化failure feedbackのみ**とし、Web / external Knowledge /新規retrieval結果を追加しない。
4. retryは「偶然PASSするまで繰り返す」手段にしない。**attempt 1 + retry attempt 2で終了**する。
5. validationにFAILしたoutputから不正unitだけをconsumerがsilentに削除して部分採用しない。baselineは**whole-output regenerate or reject**とする。
6. `context_limit`はvalidation failureではない。供給Context不足を正しく表したvalid outputとして扱い、必要ならterminal outcomeを`INSUFFICIENT_CONTEXT`とする。
7. validator / canonical mapping / context integrity等のsystem failureはgenerator retryで隠さず、`SYSTEM_FAILURE`へ分離する。
8. model fallback / cloud fallback / Web fallbackはretry chain内で行わない。
9. formal N-04 acceptanceでは、retry policyを事前freezeし、caseごとにretry回数やmodelを変更しない。
10. first attempt、retry request、retry response、各validation結果をすべてevidenceとして保存する。

論理フロー:

```text
Attempt 1
  ↓
Validation
  ├─ PASS
  │    ├─ sufficient → ACCEPTED
  │    └─ valid context_limit / insufficient → INSUFFICIENT_CONTEXT
  │
  ├─ FAIL / retryable INDETERMINATE
  │    ↓
  │  Retry exactly once under same frozen generation conditions
  │    ↓
  │  Validation
  │    ├─ PASS → ACCEPTED or INSUFFICIENT_CONTEXT
  │    ├─ FAIL → REJECTED
  │    └─ INDETERMINATE → REJECTED or SYSTEM_FAILURE by cause
  │
  └─ non-retryable system / integrity failure
       → SYSTEM_FAILURE
```

Policy contract概念名を次とする。

```text
sgokb.grounding-failure-policy.v1
```

---

## 2. なぜ1回だけretryするか

### 2.1 retryなしの欠点

Structured outputでは、内容自体が修正可能でも次のような単純failureが起こり得る。

- JSON / schema format error
- support ref付け忘れ
- semantic roleの誤分類
- creative / interpretation scopeの分離漏れ
- Contextにないdetailを1 unitだけ追加

これらをすべて即Rejectにすると、local LLMのformat-following揺らぎをそのままworkflow failureへ変換し、実用性を落とす。

### 2.2 unlimited retryの欠点

一方で複数回retryすると、

- 偶然PASSするまで試行する評価汚染
- model cherry-pickに近い挙動
- latency / GPU cost増加
- failure evidenceの解釈困難化
- benchmarkへのoverfit

が生じる。

### 2.3 Decision

**最大1回**を採用する。

1回目でvalidator feedbackを得て、同じ条件のgeneratorへ明示的な修正機会を1度だけ与える。

2回目がPASSしなければ、そのrunは成功扱いにしない。

---

## 3. 比較したfailure handling案

### Option A — 全failure即Reject

#### 利点

- 最も単純。
- acceptance結果の解釈が容易。
- retryで偶然PASSする問題がない。

#### 欠点

- format error等の修正容易なfailureまでterminalになる。
- local modelのstructured-output揺らぎに弱い。
- validator feedbackをsystem的に活かせない。

#### Decision

**単独方式として不採用。**

non-retryable failureには使用する。

---

### Option B — 成功するまで同一model retry

#### 利点

- 最終PASS率を上げやすい。

#### 欠点

- benchmark contamination。
- stochastic cherry-pick。
- retry回数が品質評価の隠れ変数になる。
- 本質的grounding weaknessを隠せる。

#### Decision

**不採用。**

---

### Option C — 別local modelへfallback

#### 利点

- generator固有failureを回避できる可能性がある。

#### 欠点

- N-04の「同じfrozen local chat modelで3 case」というGateと衝突する。
- caseごとのmodel cherry-pickにつながる。
- model policyが複雑化する。

#### Decision

**retry chain内では不採用。**

別modelで評価したい場合は別の明示run / benchmarkとして扱い、現在runのretryには数えない。formal N-04ではfreeze後のmodel変更を行わない。

---

### Option D — failing unitだけ除去してpartial resultを返す

#### 利点

- safeな部分を残しやすい。
- latencyが低い。

#### 欠点

- response全体の意味が変わる。
- Comparisonで一方のWorkだけ残る等、use-case quality Gateを壊せる。
- ConsumerがLLM outputを意味的に編集する責務を持つ。
- failing unitを削除した結果、前後unitが不自然 / misleadingになる可能性がある。

#### Decision

**baselineとして不採用。**

N-04ではwhole-output validation単位を維持する。

---

### Option E — bounded single retry + terminal classification

#### 利点

- 修正可能なoutput contract failureへ1回だけ回復機会を与えられる。
- retry回数が固定され再現可能。
- model / Contextを固定できる。
- failure evidenceを完全保存できる。
- system failureとgeneration failureを分けられる。

#### 欠点

- 最大2回のgeneration costが発生する。
- retry prompt / feedback contractが必要になる。

#### Decision

**採用。**

---

## 4. Terminal workflow outcomes

G-05のvalidation verdict `PASS / FAIL / INDETERMINATE`と、workflow terminal outcomeを分離する。

最低限次の4つを定義する。

```text
ACCEPTED
INSUFFICIENT_CONTEXT
REJECTED
SYSTEM_FAILURE
```

### 4.1 `ACCEPTED`

- final validation = PASS
- user requestのmaterial requirementを満たすresponse unitが存在する
- use-case quality Gateを満たす

このときのみ、通常のgrounded responseとしてdeterministic renderしてよい。

### 4.2 `INSUFFICIENT_CONTEXT`

供給されたGrounded Contextでは、要求されたmaterial answerを安全に構成できないことを、valid `context_limit` outputとして表した状態。

重要:

- `INSUFFICIENT_CONTEXT`はhallucination failureではない。
- model memory / Webで穴埋めしない正しい挙動である。
- Consumerが勝手にこのstatusへ変換するのではなく、output contract上の`context_limit`がvalidationを通る必要がある。
- N-04 formal acceptanceで各Caseの最低content Gateを満たさない場合、workflowとして安全でもそのCaseはacceptance PASSにはならない。

### 4.3 `REJECTED`

- retry可能failureがretry後もFAIL
- semantic indeterminateがretry後も解消しない
- non-systemなcontract / grounding failureがterminalになった

`REJECTED` outputを`SGOKB-grounded`として表示しない。

### 4.4 `SYSTEM_FAILURE`

Generatorを再実行しても改善しないsystem側failure。

例:

- validator runtime unavailable
- canonical reference mapping破損
- Grounded Context fingerprint生成 /照合系の内部不整合
- frozen contract versionをApplicationが解釈できない
- required validation component unavailable

これを`REJECTED`へ混ぜない。

---

## 5. Retry eligibility

G-05 failure classごとに標準actionを定義する。

| Failure class / cause | Retry | Terminal action if unresolved | 理由 |
|---|---:|---|---|
| `VALIDATION_CONTRACT_ERROR` — generator malformed output | 1回 | `REJECTED` | generatorがschemaを修正できる可能性 |
| `REFERENCE_INTEGRITY_ERROR` — unknown / mistyped `K*` from generator | 1回 | `REJECTED` | output側reference修正可能 |
| `REFERENCE_INTEGRITY_ERROR` — context fingerprint mismatch caused by orchestration / stale context | 0回 | `SYSTEM_FAILURE` | generator再生成で直すべきでない |
| `REFERENCE_INTEGRITY_ERROR` — broken canonical mapping | 0回 | `SYSTEM_FAILURE` | SGOKB Application / context projection defect |
| `MISSING_REQUIRED_SUPPORT` | 1回 | `REJECTED` | support refs追加またはclaim削除 / context_limit化可能 |
| `UNSUPPORTED_CLAIM` | 1回 | `REJECTED` | unsupported detail削除・grounded rewrite可能 |
| `CONTRADICTORY_CLAIM` | 1回 | `REJECTED` | cited Contextに合わせて修正可能 |
| `ROLE_MISMATCH` | 1回 | `REJECTED` | semantic role / textの修正可能 |
| `SEPARATION_VIOLATION` | 1回 | `REJECTED` | block / presentation scope修正可能 |
| `CREATIVE_SCOPE_VIOLATION` | 1回 | `REJECTED` | creative blockへ分離可能 |
| `SEMANTIC_INDETERMINATE` — ambiguous generator wording | 1回 | `REJECTED` | より直接的なclaimへ書換可能 |
| `SEMANTIC_INDETERMINATE` — validator capability limit that persists independently of wording | 0回 | `SYSTEM_FAILURE`またはformal review failure | generator retryで隠さない |
| `VALIDATOR_UNAVAILABLE` | 0回 | `SYSTEM_FAILURE` | generatorと無関係 |

実装ではfailure classだけでなく、より細かい`failure_code / cause`を保持してretryable判定する。

---

## 6. Retry contract

Retryは新しい自由promptではなく、最初のgeneration requestに**構造化repair feedback**を追加した同一contract再実行とする。

概念形:

```json
{
  "retry_policy_version": "sgokb.grounding-failure-policy.v1",
  "attempt": 2,
  "previous_attempt": 1,
  "failed_units": ["U2"],
  "failures": [
    {
      "failure_class": "UNSUPPORTED_CLAIM",
      "failure_code": "claim_not_supported_by_refs",
      "unit_id": "U2",
      "support_refs": ["K4"]
    }
  ],
  "repair_directives": [
    "remove_or_rewrite_unsupported_material",
    "use_only_existing_grounding_refs",
    "use_context_limit_if_context_is_insufficient"
  ]
}
```

### 6.1 retry feedbackに含めてよいもの

- failure class / code
- failed unit ID
- invalid / missing support refs
- violated schema / taxonomy / separation rule
- validなcurrent Context `K*` identifierへの参照
- `context_limit`を使えることの再提示

### 6.2 retry feedbackに含めないもの

- Web検索結果
- model memory由来の正解
- new Evidence / Sourceを追加fetchした内容
- original Grounded Contextに含まれていないcanonical fact
- validatorのprivate chain-of-thought
- Case固有の模範解答

### 6.3 full regeneration

Retryではfailing unitだけをpatchするのではなく、**structured output全体を再生成**する。

理由:

- unit間の順序 / presentation scope / interpretation dependencyが変化し得る。
- partial patch mergeはConsumerにsemantic editing責務を持たせる。
- stale unitとnew unitの不整合を避ける。

---

## 7. Retry invariants

Attempt 1とAttempt 2の間で次を固定する。

```text
context_fingerprint
Grounded Context K* set
purpose
output contract version
generator model ID
generator quantization / runtime profile
generation parameters
temperature / top_p / seed policy（利用する場合）
max output limit
```

許容される差分はvalidator feedbackだけである。

formal acceptanceではこれらをevidenceへ保存する。

### 7.1 Contextを増やさない

Retry時に追加retrievalしない。

Contextが本当に不足している場合は、retryでKnowledgeを増やすのではなく`context_limit` / `INSUFFICIENT_CONTEXT`へ収束させる。

Knowledge coverage改善はN-06または別runの責務である。

### 7.2 modelを変えない

Retryで別local modelへfallbackしない。

### 7.3 cloud / Web fallback禁止

既存Gateを維持する。

---

## 8. `INSUFFICIENT_CONTEXT` policy

### 8.1 いつ使用するか

次のいずれかで、要求されたmaterial answerを供給Contextだけでは安全に作れない場合。

- 必要なsource factが存在しない
- roleplayに必要なpersonality / backstory coverageが不足
- comparisonに必要な両側premiseが不足
- creativeでsource Conceptの要求されたaspectが不足し、事実として説明できない

### 8.2 正しいoutput

LLMは`context_limit` semantic unitを生成する。

例:

```json
{
  "unit_id": "U3",
  "semantic_role": "context_limit",
  "text": "The supplied context does not provide enough personality detail to state that confidently.",
  "support_refs": []
}
```

これがG-05 validationをPASSすれば、安全なterminal outcomeとして扱える。

### 8.3 Consumerが勝手に不足を推測しない

Validation failureを見てConsumerが自動的に`INSUFFICIENT_CONTEXT`へ書き換えてはならない。

例えばunsupported claim failureは、

```text
unsupported claim
≠
automatically proven context insufficiency
```

である。

retryによってgrounded rewriteが可能かもしれないため、retryable failureとして先に扱う。

### 8.4 Acceptanceとの関係

Production workflowで`INSUFFICIENT_CONTEXT`は安全な正常終了になり得る。

ただしN-04 formal use caseが最低2 fact等のquality requirementを持つ場合、`INSUFFICIENT_CONTEXT`だけでそのCaseのAcceptance PASSにはしない。

---

## 9. Partial result policy

Baselineでは**validation FAIL outputの部分renderを禁止**する。

例えばComparisonで、

```text
U1 = Work A fact → PASS
U2 = Work B fact → FAIL
U3 = comparison → FAIL
```

の場合、U1だけをユーザーへ返さない。

理由:

- 元のuser requestを満たさない可能性が高い。
- response意味をConsumerが再編集することになる。
- validation済みunitだけ残すことで、失敗を見えなくする危険がある。

将来partial-safe contractを導入する場合は、optional / required unit semanticsを別versionで設計する。

---

## 10. Attempt state machine

### Initial attempt

```text
attempt = 1
```

結果:

- PASS → terminal outcome判定
- retryable FAIL / INDETERMINATE → attempt 2
- non-retryable system failure → SYSTEM_FAILURE

### Retry attempt

```text
attempt = 2
```

これが最終generation attemptである。

結果:

- PASS → `ACCEPTED`または`INSUFFICIENT_CONTEXT`
- FAIL → `REJECTED`
- generator-origin semantic indeterminate → `REJECTED`
- validator / system-origin indeterminate → `SYSTEM_FAILURE`

attempt 3は存在しない。

---

## 11. Rendering policy

N-04G-04 deterministic rendererは、**terminal outcomeが`ACCEPTED`またはvalid `INSUFFICIENT_CONTEXT`の場合のみ**実行する。

`REJECTED` / `SYSTEM_FAILURE`のraw LLM textをgrounded responseとしてrenderしない。

Consumer UIがfailure説明を表示する場合、そのfailure messageはsystem-generated status messageであり、rejected LLM contentをgrounded proseとして流用しない。

---

## 12. Evidence / observability

1 runについて最低限次を保存する。

```text
run_id
context_fingerprint
policy_version
model / runtime / generation settings
attempt 1 request
attempt 1 raw output
attempt 1 validation result
retry eligibility decision
retry feedback（retryした場合）
attempt 2 request
attempt 2 raw output
attempt 2 validation result
terminal outcome
rendered response（存在する場合）
```

Formal N-04ではattempt 1失敗をretry成功で上書き・削除しない。

「retryしてPASSした」こと自体も評価evidenceである。

---

## 13. N-04 v1 failuresへの適用

### Case 1 — Roleplay

unsupported backstory:

```text
UNSUPPORTED_CLAIM
→ one retry
→ unsupported detailを除去 / grounded rewrite
→ retry PASSならACCEPTED
→ retryでも混入すればREJECTED
```

Contextにpersonality detailがない場合、retryでmodel memory補完せず`context_limit`を使用できる。

### Case 2 — Comparison

外部franchise fact / unsupported interpretation:

```text
UNSUPPORTED_CLAIM / SEPARATION_VIOLATION
→ one retry
→ cited K*だけで比較を再構成
→ 不足ならcontext_limit
→ retry failureならREJECTED
```

Similarity再検索や別Workへの差し替えはretry中に行わない。

### Case 3 — Creative

creative scope未分離:

```text
SEPARATION_VIOLATION / CREATIVE_SCOPE_VIOLATION
→ one retry
→ creative blockへ明示分離
→ content自体はcreative_additionとして許容
```

創作detailそのものを削除対象にはしない。

---

## 14. Responsibility boundary

### SGOKB Application / Grounding Contract

所有:

- failure class semantics
- retry eligibility semantics
- max retry count = 1
- terminal outcome semantics
- retry feedback contract
- evidence requirements

### Consumer Orchestrator

実行:

- validation result受領
- retry eligibility判定の適用
- attempt count管理
- same model / Context invariants維持
- retry request構築
- terminal outcome処理
- rendering可否制御

### MCP

failure handlingを独自に実装しない。

必要なApplication capabilityを公開する場合もtransport adapterに限定する。

### LLM

retry feedbackを受けてbest-effortで再生成するだけであり、retry要否やterminal outcomeを自己決定しない。

---

## 15. Architecture impact

Canonical Knowledge:

```text
変更なし
```

Context Builder / Retrieval:

```text
変更なし
```

MCP Knowledge Access boundary:

```text
変更なし
```

追加される論理workflow:

```text
Generation
  ↓
Validation
  ↓
Failure Policy
  ├─ Accept
  ├─ Retry once
  ├─ Insufficient Context
  ├─ Reject
  └─ System Failure
```

物理module / class配置はN-04G-07 Design FreezeおよびN-04G-09 Implementationで確定する。

---

## 16. Acceptance impact

N-04 v2 formal runでは次をfreeze対象へ追加する。

- failure policy version
- max generation attempts = 2
- retry eligibility table
- retry feedback schema
- model / settings invariants
- partial salvage prohibition
- terminal outcome classification

Caseごとにretry回数を変えない。

Attempt 1でFAILしAttempt 2でPASSしたcaseは、policy上はworkflow PASS候補になり得るが、evidenceには両attemptを残す。

N-04G-08で、formal acceptance上「retry PASSをCase PASSとして認める」条件を本Design Freezeと整合させて明文化する。

---

## 17. Deferred / non-decisions

本Taskでは次を決めない。

- specific Python class名
- retry promptの最終文面
- semantic validator model名
- provider固有retry API
- UI上のfailure message wording
- 将来のmulti-retry policy
- partial-safe rendering extension

---

## 18. Definition of Done

- [x] retry採用 / 不採用主要案を比較した。
- [x] retry上限を**1回**に固定した。
- [x] same Context / model / settings invariantを固定した。
- [x] failure class / causeごとのretry eligibilityを定義した。
- [x] retry feedbackへ渡してよい情報 / 禁止情報を定義した。
- [x] model / cloud / Web fallbackをretry chainから排除した。
- [x] whole-output regenerationを採用し、partial salvageをbaseline不採用とした。
- [x] `INSUFFICIENT_CONTEXT`をgrounding failureと分離した。
- [x] `REJECTED`と`SYSTEM_FAILURE`を分離した。
- [x] attempt 1 / retry evidence保存を必須化した。
- [x] N-04 v1 Case 1〜3への適用を説明した。
- [x] canonical / Retrieval / MCP境界変更不要を確認した。

---

## 19. Next task

次はN-04G-01〜G-06を統合する。

```text
N-04G-07 [P0]
End-to-End grounded-generation designを統合しDesign Freezeする
```

G-07では、責務、taxonomy、K* reference、structured generation、Hybrid validation、bounded single retryを1つのsequence / data contractへ統合し、未決P0設計論点が残っていないことを確認する。
