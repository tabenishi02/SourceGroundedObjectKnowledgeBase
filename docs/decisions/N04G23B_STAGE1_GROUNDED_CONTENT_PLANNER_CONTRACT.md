# N-04G-23B — Stage 1 Grounded Content Planner Contract

更新日: 2026-10-21

- Status: **Complete / Contract Accepted**
- Parent: `N-04G-23 — Two-Stage Grounded Generation Architecture`
- Predecessor: `N-04G-23A-E — Complete / Architecture Accepted`
- Next: `N-04G-23C — Certification / Certified Content Contract`
- N-04: **Failed / not Complete**
- N-05: **blocked**

Authority:

- `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
- `docs/decisions/N04G23AE_INTEGRATION_AND_G23B_UNBLOCK_DECISION.md`
- `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
- `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
- `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
- `docs/planning/phases/N/N04/post-g12/N04G23AE_RESIDUAL_CLASSIFIER_EVALUATION_PLAN.md`

---

## 1. Decision summary

v4 Stage 1 Grounded Content Plannerは、supplied Grounded Contextから**検証対象となるsource-fact proposition candidateだけを生成する**。

Stage 1は最終文章を生成しない。Role、Atomicity、support entailment、validation、certificationを自己判定しない。

Normative path:

```text
Grounded Context
  ↓
Stage 1 Grounded Content Planner
  ↓
model payload
  candidates[]
    claim_text
    support_refs[]
  ↓
application-owned candidate envelope construction
  ↓
stage1_fact_candidate
  ↓
V2-S / V2-P / V2-D / V2-R-A / V2-R-C
  ↓ PASS only
V3/V4 support validation
  ↓ PASS only
Certified Content
```

G-23Bで次を固定する。

1. Stage 1 request ownershipとlogical contract。
2. Stage 1 model response payload。
3. application-owned candidate envelope。
4. `claim_text` semantics。
5. `support_refs[]` semantics。
6. multiple-candidate semantics。
7. empty result semantics。
8. candidate identity / retry lineage。
9. provider structured-outputで安全に強制してよい範囲。
10. conservative prompt policy / GOOD-BAD examples。
11. Stage 1からV2-S/P/D/Rへのhandoff。
12. evidence / replay fields。

具体的なResidual Atomicity / Content-Type classifierのmodel/checkpoint/thresholdは**本Taskでは選定しない**。`N-04G-25A`の責務である。

---

## 2. Protected authority boundary

G-23BはE2〜E7の責務分解を変更しない。

Stage 1 model outputへ次を入れてauthorityとして使用してはならない。

```text
semantic_role
atomicity_status
atomicity_pass
validation_status
certification_status
support_status
entailment_status
presentation_role
context_limit
```

特に禁止する解釈:

```text
schema valid
-> Atomicity PASS

model says semantic_role=source_fact
-> source_fact accepted

support_refs present
-> supported / entailed
```

これらはすべて誤りである。

Role authorityはapplication-owned path `stage1_fact_candidate`からV2-Pが導出する。

```text
stage1_fact_candidate -> source_fact
```

Model-authored free-text `claim_text`は原則V2-R-A / V2-R-Cの対象であり、後段classifierの具体実装が未選定でもcontract自体は成立する。

---

## 3. Stage 1 request contract

### 3.1 Ownership

Stage 1 request envelopeはapplicationが所有する。

Logical request:

```json
{
  "request_contract_version": "sgokb.stage1-grounded-content-request.v1",
  "request_id": "...",
  "context_fingerprint": "...",
  "purpose": "comparison",
  "stage": "stage1",
  "path_provenance": "stage1_fact_candidate",
  "attempt": 1,
  "candidate_budget": {
    "max_candidates": 8
  },
  "grounded_context": "<existing Grounded Context payload>",
  "allowed_support_refs": ["K1", "K2", "K3"]
}
```

これはlogical contractであり、provider API固有schemaではない。Provider-specific request/schema integrationはG-23Eで固定する。

### 3.2 Application-owned fields

次はmodelに生成させない。

```text
request_contract_version
request_id
context_fingerprint
purpose
stage
path_provenance
attempt
candidate_budget
allowed_support_refs
retry lineage
```

`purpose`はStage 1がuse-case relevantなfact候補を選択するために入力してよい。

ただしStage 1のnormalized roleはpurposeによらず`source_fact`である。

### 3.3 Grounded Context

既存Grounded Context / `K*` reference contractをそのまま消費する。

G-23Bは以下を再設計しない。

- Retrieval
- Similarity
- Context Builder
- K-reference生成
- context fingerprint algorithm
- canonical DB
- Source / Evidence / Provenance

`allowed_support_refs`は現在のGrounded Contextからapplicationが導出するallow-listであり、modelが新規IDを作成する権限を持たない。

### 3.4 Candidate budget

生成候補数の上限はapplication-owned request policyとする。

Normative rule:

```text
0 <= returned candidates <= requested max_candidates
```

具体的なdefault/max値はruntime/provider integrationに依存するためG-23Bではfreezeしない。

Modelが必要数を独自に決めることはできるが、applicationの上限を超えてはならない。

---

## 4. Stage 1 model response contract

### 4.1 Minimal provider-facing payload

v1 Stage 1 model responseは次だけを生成する。

```json
{
  "candidates": [
    {
      "claim_text": "...",
      "support_refs": ["K3"]
    }
  ]
}
```

Model responseにはapplication-owned metadataをechoさせない。

理由:

- forged / inconsistent metadata surfaceを減らす。
- model-authored fieldをauthorityと誤認する可能性を減らす。
- provider schemaを小さく保つ。
- candidate contentとorchestration metadataのownershipを明確にする。

### 4.2 Required fields

Candidate payloadごとに必須:

```text
claim_text
support_refs[] >= 1
```

Forbidden:

```text
semantic_role
presentation_role
premise_fact_ids
validation fields
certification fields
atomicity verdict
support/entailment verdict
free-form context_limit
rationale
explanation
summary
final_text
```

一つのcandidateにauthoritative natural-language content fieldは`claim_text`一つだけとする。

### 4.3 Optional semantic anchors

E3では次をoptional diagnostic候補として許容した。

```text
subject_refs[]
predicate_hint
object_refs[]
```

G-23B v1では**採用しない**。

理由:

1. Stage 1の最小contractに必須ではない。
2. grounding / Atomicity authorityにはできない。
3. model出力surfaceとprovider schema complexityを増やす。
4. 現時点でStage 1 acceptance改善の実測evidenceがない。

将来、failure evidenceにより有用性が確認された場合はcontract versionを上げて追加できる。

---

## 5. `claim_text` semantics

`claim_text`は**一つの独立してgrounding判定可能なsource-world proposition candidate**を表す。

Prompt-level normative policy:

```text
prefer supplied Grounded Context wording
minimally normalize wording
one independently judgeable proposition per candidate
no extra proposition
no interpretation conclusion
no creative addition
no context-availability statement
no model-memory source-world addition
```

### 5.1 Conservative transformation

許可方向:

- pronoun / local abbreviationの最小解消
- grammatical completion
- support textの意味を変えない最小paraphrase
- 一つのpropositionを明確化するための語順整理

避ける方向:

- explanation追加
- causal理由追加
- implication追加
- comparison conclusion追加
- motive / intent推定
- background knowledge補完
- narrative enrichment

### 5.2 Atomicity is not schema-proven

`claim_text`が一fieldであること、1文であること、短いことはsemantic Atomicityの証明ではない。

Model-authored `claim_text`は、E5/E7のruleどおりResidual Atomicity authorityへ送る。

```text
V2-R-A
  ATOMIC
  NON_ATOMIC
  AMBIGUOUS
```

`NON_ATOMIC` / `AMBIGUOUS`はgrounded PASS不可。

### 5.3 Immutability during validation

Candidate化後、validatorは`claim_text`をsilent rewriteしない。

Failure時:

```text
reject / retry
  ↓
new model payload
  ↓
new proposition_id
```

とする。

Post-hoc splitで一部だけcertifyした後、元のcompound textをrenderする方式は禁止する。

---

## 6. `support_refs[]` semantics

### 6.1 Required shape

各candidateは1件以上のsupport refを持つ。

```text
support_refs[] >= 1
unique within candidate
all refs must be members of allowed_support_refs
```

複数referenceを持つこと自体は複数propositionを意味しない。一つのpropositionが複数K itemの組合せでsupportされる場合を許容する。

### 6.2 Reference integrity

Stage 1 parse後、semantic support validationより前にapplicationが最低限確認する。

```text
reference syntax valid
reference exists in current Grounded Context
reference belongs to current context_fingerprint
reference is in request allow-list
no duplicate refs within candidate
```

Unknown / stale / cross-context refはfail-closed。

### 6.3 Presence is not support proof

`support_refs[]`はmodelによる**support candidate selection**でしかない。

次を意味しない。

```text
ref exists -> claim supported
ref selected -> entailment PASS
multiple refs -> stronger truth
```

Truth / deterministic support / MiniCheck / independent fact validationはV3/V4側のauthorityとして維持する。

---

## 7. Multiple candidate representation

Stage 1 responseは`candidates[]`配列で複数candidateを表す。

各itemは独立candidateであり、cross-candidate conjunctionやshared verdictを持たない。

Normative rules:

- array orderはpresentation orderではない。
- array orderはimportance authorityではない。
- candidate間のsupport refs共有を許可する。
- candidateごとに別々にV2/V3/V4判定する。
- 一candidateのFAILで別candidateを自動FAILにしない。
- ただしMaterial Requirement判定は後段でaccepted/certified candidate集合を評価する。

Stage 1 candidateへ`main` / `interpretation` / `creative`等のpresentation metadataを付与しない。

---

## 8. Empty candidate result

Stage 1 modelは安全なsource-fact candidateを生成できない場合、次を返してよい。

```json
{
  "candidates": []
}
```

これは`context_limit` verdictではない。

意味:

```text
Stage 1 produced no candidate material
```

のみである。

ApplicationがMaterial Requirement / retry policy / system-owned context-limit policyに基づいて後続判断する。

これによりmodelにfree-form `context_limit` authorityを再導入しない。

---

## 9. Application-owned candidate envelope

Provider payloadのparse後、applicationがcandidateごとにStructured Proposition Candidateを構成する。

Logical form:

```json
{
  "candidate_contract_version": "sgokb.structured-proposition.v1-candidate",
  "request_id": "R...",
  "context_fingerprint": "...",
  "purpose": "comparison",
  "stage": "stage1",
  "path_provenance": "stage1_fact_candidate",
  "attempt": 1,
  "proposition_id": "P...",
  "candidate_index": 0,
  "retry_parent_id": null,
  "payload": {
    "claim_text": "...",
    "support_refs": ["K3"]
  }
}
```

### Ownership table

| Field | Owner | Model authority |
|---|---|---:|
| request/candidate contract version | application | No |
| request_id | application | No |
| context_fingerprint | application | No |
| purpose | application/request | No |
| stage | application | No |
| path_provenance | application | No |
| attempt | application | No |
| proposition_id | application | No |
| candidate_index | application | No |
| retry_parent_id | application | No |
| claim_text | model | Content only |
| support_refs | model selection | Limited; validator checks |

Application-owned envelopeとmodel payloadを分離して保存する。

---

## 10. Candidate identity and retry lineage

### 10.1 Proposition identity

`proposition_id`はapplicationがparse後に割り当てる。

Requirements:

- generation attempt内でunique。
- model IDを信用しない。
- validation/evidence join keyとして使用する。
- failed candidateのtextを書き換えて同じIDを再利用しない。

### 10.2 Candidate digest

Replay / audit用にcanonical candidate digestを持てる。

Digest inputは少なくとも次をbindする方向とする。

```text
candidate contract version
request_id
context_fingerprint
purpose
stage/path
attempt
proposition_id
claim_text
support_refs
```

Exact canonical serialization / hashing implementationはG-23E/G-24で固定する。

### 10.3 Retry lineage

Stage 1 retryで新しい候補を生成した場合、新しい`proposition_id`を発行する。

Application-owned lineage:

```text
retry_parent_id
retry_attempt / attempt
failure_source_proposition_id
```

を記録する。

G-23Bが固定するretry inputはcontract上必要な最小情報だけとする。

```text
same Grounded Context / same context_fingerprint
same purpose
same Stage 1 path
failed proposition identity
failed claim text
relevant support refs
failure code
expected rule
structured repair directive
```

Detailed retry orchestration、provider message layout、retry上限統合はG-23Eで固定する。

---

## 11. Provider structured-output constraints

Provider schemaへ移してよいのは**構造的に安全に証明できるconstraintだけ**とする。

Recommended provider-facing constraints:

```text
root object only
additionalProperties = false
required: candidates
candidates: array
candidate object additionalProperties = false
required: claim_text, support_refs
claim_text: non-empty string
support_refs: array, minItems = 1, uniqueItems = true
support ref lexical pattern when provider supports it reliably
```

Candidate countはapplication-owned `candidate_budget`で最終検査する。
Providerがdynamic request-dependent `maxItems`を表現できない場合、schema capabilityのためにcontractを緩和せずapplication validationでrejectする。

Provider schemaへ入れてはならないsemantic proof:

```text
Atomicity PASS
source-fact semantic class PASS
support entailment PASS
truth PASS
certification PASS
```

Schema capability probe / LM Studio / llama.cpp固有制約はG-23Eの責務とする。

---

## 12. Conservative prompt policy

Stage 1 promptはrule-onlyではなくGOOD/BAD exampleを含める。

### GOOD 1 — direct fact

Grounded Context:

```text
K1: Aは1998年に公開された。
```

GOOD:

```json
{"claim_text":"Aは1998年に公開された。","support_refs":["K1"]}
```

### GOOD 2 — multiple refs, one proposition

Grounded Context:

```text
K2: AはB社が開発した。
K3: B社はAの開発元として記載されている。
```

GOOD:

```json
{"claim_text":"AはB社が開発した。","support_refs":["K2","K3"]}
```

複数support refsでもmaterial propositionは一つである。

### BAD 1 — two independent facts

```json
{"claim_text":"Aは1998年に公開され、B社が開発した。","support_refs":["K1","K2"]}
```

独立して別grounding verdictを持ち得る2 propositionを一candidateへ圧縮しているため避ける。

### BAD 2 — fact + interpretation

```json
{"claim_text":"Aは1998年に公開されたため、当時として革新的だった。","support_refs":["K1"]}
```

後半はinterpretationでありStage 1 source-fact candidateへ混在させない。

### BAD 3 — model-memory addition

```text
K1 only says A was released in 1998.
Candidate additionally states an unprovided award/history fact.
```

Context外命題の追加は禁止。

### BAD 4 — context-limit escape

```json
{"claim_text":"与えられた資料では判断できない。","support_refs":["K1"]}
```

これはsource-world factではなくcontext availability statementである。安全なfactがない場合は`candidates: []`を返す。

Prompt wordingはprovider/runtimeへ合わせてG-23Eでfreezeできるが、上記意味規則はG-23B authorityとする。

---

## 13. Entry into V2-S / V2-P / V2-D / V2-R

Stage 1 outputは次の順序で既存E2-E7 authorityへ入る。

```text
model response
  ↓ parse/schema
application envelope construction
  ↓
reference-integrity precondition
  ↓
V2-S Structural Proposition Gate
  ↓
V2-P path provenance
  stage1_fact_candidate -> source_fact
  ↓
V2-D deterministic compatibility
  purpose allowed
  no presentation metadata
  support_refs present
  premise_fact_ids absent
  ↓ PASS only
V2-R-A Residual Atomicity
  ↓ ATOMIC only
V2-R-C Content Type
  ↓ SOURCE_FACT_CONTENT only
V3/V4 support / truth validation
```

No Stage 1 field duplicates these authorities。

`claim_text`とsupport refsがschema-validでもV2-R-A/V2-R-C/V3/V4をskipしない。

具体classifier identityはG-25Aまでpluggable / unresolvedのままでよい。

---

## 14. Failure semantics

Stage 1関連failureを少なくとも次のfamilyとしてmachine-addressableにする方向を固定する。

```text
stage1_malformed_output
stage1_schema_violation
stage1_candidate_budget_exceeded
stage1_empty_claim_text
stage1_missing_support_refs
stage1_duplicate_support_ref
stage1_unknown_support_ref
stage1_cross_context_support_ref
stage1_forbidden_field
stage1_unexpected_presentation_metadata
stage1_forbidden_premise_binding
stage1_candidate_identity_error
```

V2以降のfailure codeはE2-E5 authorityを使用する。

Failure code exact namingのimplementation freezeはG-23E/G-24で整合確認するが、failure classをsemantic classifierで救済しないことは本Decisionで固定する。

---

## 15. Evidence / replay contract

G-23C/G-23E/G-26でStage 1を再現可能にするため、最低限次を保存できる構造とする。

```text
stage1/
  request-envelope
  grounded-context identity / context_fingerprint
  prompt artifact identity / hash
  provider schema identity / hash
  model/runtime identity
  generation settings
  raw provider output
  parsed model payload
  application-built candidate envelopes
  candidate digests
  parse/reference-integrity failures
  retry feedback
  retry lineage
```

各candidateはrequest / context / attempt / proposition identityへ追跡可能でなければならない。

Historical v3 artifactを上書きしない。v4は別contract/versionとして保存する。

---

## 16. G-23C handoff contract

G-23CはG-23Bから次を前提としてよい。

### Input to certification design

Stage 1 candidateは必ずlogicalに:

```text
application-owned envelope
  stage = stage1
  path = stage1_fact_candidate
  purpose
  context_fingerprint
  proposition_id
  attempt / retry lineage

model payload
  claim_text
  support_refs[] >= 1
```

を持つ。

G-23CはCandidate artifactを書き換えず、V2/V3/V4 validation evidenceとCertified Content identityを別artifactとして設計する。

G-23Cが再導入してはならないもの:

```text
model-owned certification status
model-owned support PASS
generator-declared semantic role authority
silent candidate rewrite
```

Certified source factはStage 2へ渡せるstable `certified_fact_id`を持つ方向をE3から継承する。

Exact Certified Content schemaはG-23C authorityとする。

---

## 17. Explicitly deferred

G-23Bでは次を決めない。

- Concrete V2-R-A classifier model/checkpoint
- Concrete V2-R-C classifier model/checkpoint
- classifier threshold / calibration
- G-25A development corpus implementation
- Certified Content schema details
- Stage 2 output/presentation schema
- Stage 2 interpretation/creative contract details
- provider-specific schema capability freeze
- exact retry message orchestration
- production code implementation
- Reference Workstation v4 harness

Execution homes:

```text
G-23C Certified Content contract
G-23D Stage 2 Presentation Generator contract
G-23E Provider schema + stage-local retry
G-23F v4 Design Freeze
G-24 implementation
G-25A Residual Classifier Benchmark / Selection
G-25B Integrated v4 Adversarial Regression
G-26 Reference Workstation Freeze
G-27 Formal v4 Re-Acceptance
```

---

## 18. Completion checklist

- [x] Stage 1 request ownership fixed.
- [x] Minimal model response fixed to `candidates[{claim_text,support_refs}]`.
- [x] application-owned metadata removed from model response.
- [x] Stage 1 path fixed to `stage1_fact_candidate`.
- [x] normalized role remains application-owned `source_fact`.
- [x] no Stage 1 presentation role.
- [x] `support_refs[] >= 1` fixed for non-empty candidate.
- [x] support ref allow-list / reference integrity boundary fixed.
- [x] support presence explicitly separated from entailment authority.
- [x] one-proposition-per-candidate prompt policy fixed.
- [x] schema-valid free text does not self-prove Atomicity.
- [x] optional semantic anchors excluded from v1.
- [x] empty candidate list semantics fixed without model-authored context-limit.
- [x] candidate identity / retry lineage ownership fixed.
- [x] safe provider structured-output constraints bounded.
- [x] V2-S/P/D/R entry path fixed without duplicate authority.
- [x] Stage 1 evidence/replay requirements fixed.
- [x] concrete classifier selection explicitly deferred to G-25A.
- [x] protected E2-E7 boundaries preserved.

Result:

```text
N-04G-23B = Complete / Contract Accepted
N-04G-23C = NEXT
N-04       = Failed / not Complete
N-05       = blocked
```
